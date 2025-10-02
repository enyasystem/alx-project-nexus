from rest_framework import serializers
from .models import Address, Cart, CartItem, Order, OrderItem
from catalog.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']


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
    """Create an Order from a Cart snapshot. This captures product details and reserves inventory.

    Note: This is intentionally simple: it reduces product.inventory immediately and does not integrate
    with a payment gateway. Real implementations should use reservation windows and more robust locking.
    """
    if cart.items.count() == 0:
        raise ValueError("Cart is empty")

    order = Order.objects.create(user=user)
    total = 0
    for ci in cart.items.select_related('product'):
        p = ci.product
        if p.inventory < ci.quantity:
            # rollback simple: delete the order and raise
            order.delete()
            raise ValueError(f"Not enough inventory for {p.slug}")
        # decrement inventory
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
