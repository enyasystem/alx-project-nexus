from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache, caches
from django.conf import settings

from .models import Product

# helper to compute cache keys used by ProductViewSet
def _product_list_key_for_request_path(path):
    return f"product:list:{path}"

def _product_detail_key(product_id):
    return f"product:detail:{product_id}"

@receiver(post_save, sender=Product)
def clear_product_cache_on_save(sender, instance, **kwargs):
    """Clear product-related cache when a product is created or updated."""
    try:
        # Targeted invalidation: remove product detail for this id and any list pages
        # Note: we can't enumerate all list keys easily; remove a few common variants.
        cache.delete(_product_detail_key(instance.pk))
        # remove root list and possible filtered variants by prefix if backend supports it
        try:
            default_cache = caches['default']
            if hasattr(default_cache, 'delete_pattern'):
                # django-redis supports delete_pattern
                default_cache.delete_pattern('product:list:*')
            else:
                # Best-effort: delete common root key
                cache.delete(_product_list_key_for_request_path('/api/products/'))
        except Exception:
            # Fallback to deleting the root key
            cache.delete(_product_list_key_for_request_path('/api/products/'))
    except Exception:
        # Best-effort: do not raise in signal handlers.
        pass

@receiver(post_delete, sender=Product)
def clear_product_cache_on_delete(sender, instance, **kwargs):
    """Clear product-related cache when a product is deleted."""
    try:
        cache.delete(_product_detail_key(instance.pk))
        try:
            default_cache = caches['default']
            if hasattr(default_cache, 'delete_pattern'):
                default_cache.delete_pattern('product:list:*')
            else:
                cache.delete(_product_list_key_for_request_path('/api/products/'))
        except Exception:
            cache.delete(_product_list_key_for_request_path('/api/products/'))
    except Exception:
        pass
\n
