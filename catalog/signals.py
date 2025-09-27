from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings

from .models import Product

@receiver(post_save, sender=Product)
def clear_product_cache_on_save(sender, instance, **kwargs):
    """Clear product-related cache when a product is created or updated."""
    try:
        # Coarse-grained invalidation: clear the default cache so cached list pages are refreshed.
        cache.clear()
    except Exception:
        # Best-effort: do not raise in signal handlers.
        pass

@receiver(post_delete, sender=Product)
def clear_product_cache_on_delete(sender, instance, **kwargs):
    """Clear product-related cache when a product is deleted."""
    try:
        cache.clear()
    except Exception:
        pass
