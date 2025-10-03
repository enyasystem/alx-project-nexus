from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'inventory', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'alt', 'order')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'sku', 'name', 'price', 'inventory')
    search_fields = ('sku', 'name')
