import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Dump a JSON summary of products (name, price, category, slug)'

    def handle(self, *args, **options):
        from catalog.models import Product

        qs = Product.objects.select_related('category').all()
        data = {
            'total': qs.count(),
            'products': [
                {
                    'name': p.name,
                    'slug': p.slug,
                    'price': float(p.price),
                    'inventory': p.inventory,
                    'category': p.category.slug if p.category else None,
                }
                for p in qs[:25]
            ],
        }
        self.stdout.write(json.dumps(data, indent=2))
