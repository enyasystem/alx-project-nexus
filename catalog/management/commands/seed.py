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
            ('Home', 'home'),
        ]
        for name, slug in categories:
            cat, created = Category.objects.get_or_create(name=name, slug=slug)
            if created:
                self.stdout.write(f'Created category: {name}')

        # generate 20 varied products across categories
        sample_products = []
        # electronics (5)
        for i, (name, price) in enumerate([
            ('Laptop', 1200.00),
            ('Smartphone', 800.00),
            ('Headphones', 150.00),
            ('Monitor', 300.00),
            ('Keyboard', 80.00),
        ], start=1):
            sample_products.append((f'{name}', f'{name.lower().replace(" ", "-")}-{i}', f'{name} description', price, 10 * i, 'electronics'))

        # books (5)
        for i, (name, price) in enumerate([
            ('Novel', 20.00),
            ('Cookbook', 25.00),
            ('Biography', 18.00),
            ('Children Book', 12.50),
            ('Science Text', 95.00),
        ], start=1):
            sample_products.append((name, f'{name.lower().replace(" ", "-")}-{i}', f'{name} description', price, 5 * i, 'books'))

        # toys (5)
        for i, (name, price) in enumerate([
            ('Action Figure', 35.00),
            ('Board Game', 45.00),
            ('Puzzle', 15.00),
            ('Doll', 25.00),
            ('RC Car', 140.00),
        ], start=1):
            sample_products.append((name, f'{name.lower().replace(" ", "-")}-{i}', f'{name} description', price, 8 * i, 'toys'))

        # home (5)
        for i, (name, price) in enumerate([
            ('Blender', 60.00),
            ('Vacuum', 220.00),
            ('Lamp', 30.00),
            ('Desk', 150.00),
            ('Chair', 85.00),
        ], start=1):
            sample_products.append((name, f'{name.lower().replace(" ", "-")}-{i}', f'{name} description', price, 7 * i, 'home'))

        for name, slug, desc, price, inv, cat_slug in sample_products:
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

        total_cats = Category.objects.count()
        total_prods = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Seeding complete. Categories: {total_cats}, Products: {total_prods}'))
\n
