from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.decorators import throttle_classes
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .permissions import IsStaffOrReadOnly
from .filters import ProductFilter
from .pagination import ProductCursorPagination


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]


@extend_schema_view(
    create=extend_schema(
        description="Create product (multipart/form-data with optional image).",
        request=ProductSerializer,
        responses=ProductSerializer,
        examples=[
            OpenApiExample(
                'Create product with image',
                summary='Create product (multipart)',
                value={
                    'name': 'Sample Product',
                    'slug': 'sample-product',
                    'description': 'A product with image',
                    'price': '19.99',
                    'inventory': '5',
                    'category_id': 1,
                    'image': '<binary file>'
                },
                media_type='multipart/form-data'
            ),
        ],
    ),
    partial_update=extend_schema(
        description="Partial update product (supports multipart to update image).",
        request=ProductSerializer,
        responses=ProductSerializer,
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProductFilter
    ordering_fields = ['price', 'created_at', 'name']
    search_fields = ['name', 'description']
    # Use cursor pagination by default for product lists (large data sets)
    pagination_class = ProductCursorPagination
    # allow image uploads via multipart/form-data
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'products'

    def get_queryset(self):
        # Ensure we prefetch related category for list/detail to reduce queries
        return Product.objects.select_related('category').all()

    # Cache the list view when caching is enabled in settings
    if getattr(settings, 'USE_REDIS', False):
        from rest_framework.response import Response

        def _build_list_cache_key(request):
            # Use full path (path + query string) to differentiate pages/filters
            return f"product:list:{request.get_full_path()}"

        def list(self, request, *args, **kwargs):
            # Manual caching allows targeted invalidation from signals
            cache_key = _build_list_cache_key(request)
            try:
                cached = cache.get(cache_key)
                if cached is not None:
                    return Response(cached)
            except Exception:
                # On any cache error, fall back to normal behavior
                return super().list(request, *args, **kwargs)

            resp = super().list(request, *args, **kwargs)
            try:
                # Store serialized response data (resp.data) for quick return
                cache.set(cache_key, resp.data, getattr(settings, 'CACHE_TTL', 60))
            except Exception:
                pass
            return resp
\n