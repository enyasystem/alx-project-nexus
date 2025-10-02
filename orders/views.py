from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem, Order
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, create_order_from_cart
from .models import IdempotencyKey
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

    @action(detail=False, methods=['post'], url_path='webhook', permission_classes=[permissions.AllowAny])
    def webhook(self, request):
        # Placeholder for payment gateway webhooks (stripe, paypal, etc.)
        # In production validate signatures and process events idempotently.
        event = request.data
        # For now just ack
        return Response({'status': 'received', 'event_type': event.get('type')}, status=status.HTTP_200_OK)
