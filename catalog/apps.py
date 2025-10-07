from django.apps import AppConfig

class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'

    def ready(self):
        # Import signal handlers to register them at app ready time
        from . import signals  # noqa: F401
\n
