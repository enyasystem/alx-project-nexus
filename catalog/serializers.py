from rest_framework import serializers
from .models import Category, Product
from .models import ProductImage, ProductVariant

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True, source='category')
    image = serializers.ImageField(required=False, allow_null=True)
    images = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price', 'inventory', 'category', 'category_id', 'image', 'created_at', 'updated_at']

    def get_images(self, obj):
        return [{'id': i.id, 'url': i.image.url if i.image else None, 'alt': i.alt, 'order': i.order} for i in obj.images.all()]

    def get_variants(self, obj):
        return [{'id': v.id, 'sku': v.sku, 'name': v.name, 'price': str(v.price) if v.price is not None else None, 'inventory': v.inventory, 'attributes': v.attributes} for v in obj.variants.all()]
