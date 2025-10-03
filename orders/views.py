from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem, Order, PaymentRecord
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, create_order_from_cart
from .models import IdempotencyKey
from .models import StockReservation
from .models import Shipment
from .serializers import ShipmentSerializer
from drf_spectacular.utils import extend_schema, OpenApiExample


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # If authenticated, restrict to user's carts; otherwise all (for demo simplicity)
        user = self.request.user
        if user and user.is_authenticated:
            return Cart.objects.filter(user=user)
        return Cart.objects.none()

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        cart = self.get_object()
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # ensure product/quantity are set
        ci = serializer.save(cart=cart)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='reserve')
    def reserve(self, request, pk=None):
        """Create stock reservations for all items in the cart.

        This endpoint will attempt to decrement product.inventory immediately
        inside a transaction and create StockReservation rows. It returns 201 on
        success or 400 if inventory is insufficient.
        """
        cart = self.get_object()
        from django.db import transaction
        reservations = []
        try:
            with transaction.atomic():
                # lock products and variants referenced by the cart
                product_ids = [ci.product_id for ci in cart.items.all()]
                variant_ids = [ci.variant_id for ci in cart.items.all() if getattr(ci, 'variant_id', None)]
                from catalog.models import Product, ProductVariant
                products_qs = Product.objects.select_for_update().filter(id__in=product_ids)
                locked_products = {p.id: p for p in products_qs}
                locked_variants = {}
                if variant_ids:
                    variants_qs = ProductVariant.objects.select_for_update().filter(id__in=variant_ids)
                    locked_variants = {v.id: v for v in variants_qs}

                for ci in cart.items.select_related('product', 'variant'):
                    # If item references a variant, operate on variant inventory
                    if getattr(ci, 'variant_id', None):
                        v = locked_variants.get(ci.variant_id)
                        if v is None:
                            raise ValueError('Variant not available')
                        if v.inventory < ci.quantity:
                            raise ValueError(f'Not enough inventory for {v.sku}')
                        v.inventory = v.inventory - ci.quantity
                        v.save()
                        r = StockReservation.objects.create(
                            product=v.product,
                            variant=v,
                            quantity=ci.quantity,
                            owner_type='cart',
                            owner_id=str(cart.id),
                            status='active',
                        )
                        reservations.append(r)
                    else:
                        p = locked_products.get(ci.product_id)
                        if p is None:
                            raise ValueError('Product not available')
                        if p.inventory < ci.quantity and not p.allow_backorder:
                            raise ValueError(f'Not enough inventory for {p.slug}')
                        # decrement inventory and persist
                        p.inventory = p.inventory - ci.quantity
                        p.save()
                        r = StockReservation.objects.create(
                            product=p,
                            quantity=ci.quantity,
                            owner_type='cart',
                            owner_id=str(cart.id),
                            status='active',
                        )
                        reservations.append(r)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'reservations': [r.id for r in reservations]}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel-reservations')
    def cancel_reservations(self, request, pk=None):
        cart = self.get_object()
        qs = StockReservation.objects.filter(owner_type='cart', owner_id=str(cart.id), status='active')
        for r in qs:
            r.release()
        return Response({'cancelled': qs.count()}, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        # Associate created cart with the authenticated user when available
        user = self.request.user if self.request.user and self.request.user.is_authenticated else None
        serializer.save(user=user)


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            return CartItem.objects.filter(cart__user=user)
        return CartItem.objects.none()


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Admins should be able to access all orders for management
        if user and getattr(user, 'is_staff', False):
            return Order.objects.all()
        return Order.objects.filter(user=user)

    @action(detail=False, methods=['post'], url_path='create-from-cart')
    @extend_schema(
        description="Create an order from an existing cart. Use 'Idempotency-Key' header to avoid duplicates.",
        examples=[OpenApiExample('Create order', value={'cart_id': 1}, request_only=True)]
    )
    def create_from_cart(self, request):
        cart_id = request.data.get('cart_id')
        if not cart_id:
            return Response({'detail': 'cart_id required'}, status=status.HTTP_400_BAD_REQUEST)
        cart = get_object_or_404(Cart, pk=cart_id)
        # simple idempotency: use header 'Idempotency-Key' to prevent duplicate creations
        key = request.headers.get('Idempotency-Key') or request.META.get('HTTP_IDEMPOTENCY_KEY')
        if key:
            ik, created = IdempotencyKey.objects.get_or_create(key=key)
            if not created and ik.order is not None:
                # return previous order response
                return Response(OrderSerializer(ik.order).data, status=status.HTTP_200_OK)
        try:
            order = create_order_from_cart(cart, user=request.user if request.user.is_authenticated else None)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if key:
            ik.order = order
            ik.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='create-shipment', permission_classes=[permissions.IsAdminUser])
    def create_shipment(self, request, pk=None):
        order = self.get_object()
        serializer = ShipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(order=order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    @action(detail=False, methods=['post'], url_path='webhook', permission_classes=[permissions.AllowAny])
    def webhook(self, request):
        # Placeholder for payment gateway webhooks (stripe, paypal, etc.)
        # In production validate signatures and process events idempotently.
        event = request.data
        # Handle a simple payment succeeded event shape (provider-agnostic)
        evt_type = event.get('type') or event.get('event')
        data = event.get('data', {})
        if evt_type in ('payment_intent.succeeded', 'payment.succeeded', 'charge.succeeded'):
            # try to find order id from metadata or payload
            order_id = data.get('order_id') or data.get('metadata', {}).get('order_id')
            if order_id:
                try:
                    order = Order.objects.get(pk=order_id)
                    amount = data.get('amount') or data.get('amount_cents') or data.get('amount_money', {}).get('amount')
                    if amount is None:
                        # as fallback compute from order
                        amount = order.total_cents
                    pr = PaymentRecord.objects.create(
                        order=order,
                        provider=event.get('provider', 'unknown'),
                        provider_id=data.get('id') or data.get('payment_id'),
                        amount_cents=int(amount),
                        currency=data.get('currency') or 'USD',
                        status='succeeded',
                        raw=event,
                    )
                    order.status = 'paid'
                    order.save()
                    return Response({'status': 'processed', 'order': order.id}, status=status.HTTP_200_OK)
                except Order.DoesNotExist:
                    return Response({'status': 'no_order_found'}, status=status.HTTP_400_BAD_REQUEST)
        # Unhandled event: ack
        return Response({'status': 'received', 'event_type': evt_type}, status=status.HTTP_200_OK)
