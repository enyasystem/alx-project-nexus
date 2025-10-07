from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductVariant

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'image_tag', 'price', 'inventory', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        # Prefer the first ProductImage (if present) so list view shows images
        try:
            first = obj.images.all().first()
        except Exception:
            first = None
        if first and getattr(first, 'image', None):
            return format_html('<img src="{}" style="max-height:60px; max-width:100px; object-fit:cover;" />', first.image.url)
        if getattr(obj, 'image', None):
            return format_html('<img src="{}" style="max-height:60px; max-width:100px; object-fit:cover;" />', obj.image.url)
        return ''

    image_tag.short_description = 'Image'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ('image_tag',)
    # Include the actual image field so existing images are rendered and
    # new images can be uploaded/changed from the inline.
    fields = ('image_tag', 'image', 'alt', 'order')

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:60px; max-width:100px; object-fit:cover;" />', obj.image.url)
        return ''

    image_tag.short_description = 'Image'


# Attach the inline to ProductAdmin so images appear in the product change form
ProductAdmin.inlines = (ProductImageInline,)



@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'image_tag', 'alt', 'order')
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:60px; max-width:100px; object-fit:cover;" />', obj.image.url)
        return ''

    image_tag.short_description = 'Image'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'sku', 'name', 'price', 'inventory')
    search_fields = ('sku', 'name')
\n