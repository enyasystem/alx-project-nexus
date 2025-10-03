from django.db import models
from django.conf import settings
from catalog.models import Product, ProductVariant


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=255)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128)
    state = models.CharField(max_length=128, blank=True)
    postal_code = models.CharField(max_length=32)
    country = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.name}, {self.line1}, {self.city}"


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    total_cents = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    product_slug = models.CharField(max_length=255)
    unit_price_cents = models.IntegerField()
    quantity = models.PositiveIntegerField()
    variant_sku = models.CharField(max_length=64, null=True, blank=True)

    def line_total(self):
        return self.unit_price_cents * self.quantity


class IdempotencyKey(models.Model):
    """Simple storage of idempotency keys to prevent duplicate order creation.

    In production you'd typically use a cache (Redis) with expiry and associate
    keys with a user or idempotency-owner. This model is a safe, persistent
    fallback for demonstration.
    """
    key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # store resulting order id if created to return same response
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.key


class PaymentRecord(models.Model):
    """Record of external payment events for reconciliation."""
    order = models.ForeignKey(Order, related_name='payments', on_delete=models.CASCADE)
    provider = models.CharField(max_length=64)  # e.g., 'stripe'
    provider_id = models.CharField(max_length=255, null=True, blank=True)  # gateway's payment id
    amount_cents = models.BigIntegerField()
    currency = models.CharField(max_length=8, default='USD')
    status = models.CharField(max_length=32)  # e.g., 'succeeded', 'failed'
    raw = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider}:{self.provider_id} ({self.status})"


class StockReservation(models.Model):
    """Reserve stock for a given product and owner (cart or order) by
    decrementing product.inventory immediately. Reservations must be
    committed (turned into an order) or cancelled (released) to restore
    inventory.

    Note: We decrement inventory on reservation to simplify concurrency
    (single authoritative inventory value). All inventory changes must be
    performed inside transactions with select_for_update on the Product row.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('committed', 'Committed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='reservations')
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    owner_type = models.CharField(max_length=32, help_text='e.g., cart, order, session')
    owner_id = models.CharField(max_length=255, help_text='id of the owning entity')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['owner_type', 'owner_id']),
        ]

    def __str__(self):
        return f"Reservation {self.id} {self.product} x{self.quantity} ({self.status})"

    def release(self):
        """Cancel the reservation and restore product.inventory."""
        from django.db import transaction
        from catalog.models import Product

        if self.status != 'active':
            return

        with transaction.atomic():
            p = Product.objects.select_for_update().get(pk=self.product_id)
            p.inventory = models.F('inventory') + self.quantity
            p.save()
            # refresh to ensure value is concrete
            p.refresh_from_db()
            self.status = 'cancelled'
            self.save()

    def commit(self):
        """Mark reservation as committed (finalized into an order)."""
        if self.status != 'active':
            return
        self.status = 'committed'
        self.save()


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order = models.ForeignKey(Order, related_name='shipments', on_delete=models.CASCADE)
    address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.SET_NULL)
    carrier = models.CharField(max_length=64, blank=True)
    tracking_number = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shipment {self.id} for Order {self.order_id} ({self.status})"
