"""Migrate existing Product.image values into ProductImage rows.

Usage:
    python manage.py shell -c "import scripts.migrate_product_images as m; m.run(dry_run=False)"
"""
import os
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')
    import django
    django.setup()
except Exception:
    pass


def run(dry_run=True):
    from catalog.models import Product, ProductImage
    qs = Product.objects.filter(image__isnull=False).exclude(image='')
    created = 0
    for p in qs:
        # skip if a ProductImage already exists for this product with same image name
        if ProductImage.objects.filter(product=p, image=p.image.name).exists():
            continue
        print('migrate', p.id, p.image.name)
        if not dry_run:
            ProductImage.objects.create(product=p, image=p.image.name, alt=p.name or '', order=0)
            created += 1
    print('done; created', created)
\n
