from rest_framework import serializers
from django.db import transaction
from .models import Address, Cart, CartItem, Order, OrderItem, StockReservation
from catalog.models import Product
from .models import Shipment


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be a positive integer')
        return value

    def validate_product(self, value):
        # ensure product exists and is active (simple existence check here)
        if value is None:
            raise serializers.ValidationError('Product is required')
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_name', 'product_slug', 'unit_price_cents', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_cents', 'created_at', 'items']


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ['id', 'order', 'address', 'carrier', 'tracking_number', 'status', 'created_at']
        read_only_fields = ('id', 'order', 'created_at')


def create_order_from_cart(cart, user=None):
    """Create an Order from a Cart snapshot.

    This implementation uses a DB transaction and `select_for_update` on product rows
    to avoid overselling in concurrent checkouts. It still keeps the logic simple:
    - locks all products referenced by the cart
    - verifies inventory, decrements, and creates order + order items
    - rolls back atomically on any error
    """
    if cart.items.count() == 0:
        raise ValueError("Cart is empty")

    # If there are active reservations for this cart, prefer to consume them.
    reservations = list(StockReservation.objects.filter(
        owner_type='cart', owner_id=str(cart.id), status='active'
    ).select_related('product'))

    if reservations:
        # ensure reservations cover all cart items (by product id)
        res_map = {r.product_id: r for r in reservations}
        for ci in cart.items.all():
            r = res_map.get(ci.product_id)
            if r is None or r.quantity < ci.quantity:
                raise ValueError('Reservation does not cover cart items')

        # create order from reservations (no further inventory ops required)
        with transaction.atomic():
            order = Order.objects.create(user=user)
            total = 0
            for r in reservations:
                p = r.product
                unit_cents = int(p.price * 100)
                OrderItem.objects.create(
                    order=order,
                    product_name=p.name,
                    product_slug=p.slug,
                    unit_price_cents=unit_cents,
                    quantity=r.quantity,
                )
                total += unit_cents * r.quantity
                # mark reservation committed
                r.status = 'committed'
                r.save()

            order.total_cents = total
            order.save()
            return order

    # Fallback: no reservations exist, perform the lock-and-decrement flow
    with transaction.atomic():
        # create order inside transaction so it will be rolled back on failure
        order = Order.objects.create(user=user)
        total = 0

        # Lock all product rows in the cart to prevent races
        product_ids = [ci.product_id for ci in cart.items.all()]
        products_qs = Product.objects.select_for_update().filter(id__in=product_ids)
        locked_products = {p.id: p for p in products_qs}

        for ci in cart.items.select_related('product'):
            p = locked_products.get(ci.product_id)
            if p is None:
                # Should not happen: product deleted after cart created
                raise ValueError(f"Product {ci.product_id} not available")
            if p.inventory < ci.quantity and not p.allow_backorder:
                # raise to rollback transaction
                raise ValueError(f"Not enough inventory for {p.slug}")
            # decrement inventory and persist
            p.inventory = p.inventory - ci.quantity
            p.save()

            unit_cents = int(p.price * 100)
            OrderItem.objects.create(
                order=order,
                product_name=p.name,
                product_slug=p.slug,
                unit_price_cents=unit_cents,
                quantity=ci.quantity,
            )
            total += unit_cents * ci.quantity

        order.total_cents = total
        order.save()
        return order
