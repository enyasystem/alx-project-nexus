from django.core.management.base import BaseCommand
from catalog.models import Category, Product


class Command(BaseCommand):
    help = 'Seed the database with sample categories and products for development.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        categories = [
            ('Electronics', 'electronics'),
            ('Books', 'books'),
            ('Toys', 'toys'),
        ]
        for name, slug in categories:
            cat, created = Category.objects.get_or_create(name=name, slug=slug)
            if created:
                self.stdout.write(f'Created category: {name}')

        # sample products
        products = [
            ('Laptop', 'laptop', 'A developer laptop', 1200.00, 10, 'electronics'),
            ('Smartphone', 'smartphone', 'A modern smartphone', 800.00, 15, 'electronics'),
            ('Novel', 'novel', 'A popular fiction novel', 20.00, 50, 'books'),
            ('Action Figure', 'action-figure', 'Collectible toy', 35.00, 25, 'toys'),
        ]
        for name, slug, desc, price, inv, cat_slug in products:
            category = Category.objects.get(slug=cat_slug)
            prod, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': desc,
                    'price': price,
                    'inventory': inv,
                    'category': category,
                }
            )
            if created:
                self.stdout.write(f'Created product: {name}')

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
