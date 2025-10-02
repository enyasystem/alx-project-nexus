from rest_framework import serializers
from django.db import transaction
from .models import Address, Cart, CartItem, Order, OrderItem
from catalog.models import Product


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

    # Acquire a transaction and lock product rows referenced by the cart
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
            if p.inventory < ci.quantity:
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
