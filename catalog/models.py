from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    inventory = models.PositiveIntegerField(default=0)
    # whether the product can be sold into negative inventory (backorders)
    allow_backorder = models.BooleanField(default=False)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)  # optional product image stored under MEDIA_ROOT/products/


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/images/')
    alt = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image {self.id} for {self.product.slug}"


class ProductVariant(models.Model):
    """Variants allow different SKUs, inventory and price per variant while keeping the
    main Product as a grouping entity. Backwards compatible: existing flows can still
    use Product directly until CartItem/OrderItem are extended to reference variants.
    """
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                help_text='Optional override price for this variant')
    inventory = models.IntegerField(default=0)
    attributes = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.product.slug}:{self.sku}"
    class Meta:
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['product']),
        ]
        ordering = ['sku']
\n