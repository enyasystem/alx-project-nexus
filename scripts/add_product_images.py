"""Attach product images by downloading from a public image source (Picsum).

Usage (dry-run):
    python manage.py shell -c "import scripts.add_product_images as a; a.attach_images(count=50, force=False, dry_run=True)"

Usage (download & attach):
    python manage.py shell -c "import scripts.add_product_images as a; a.attach_images(count=200, force=False, dry_run=False)"

Notes:
 - This script downloads images into MEDIA_ROOT/products/ and sets the Product.image field.
 - It uses the picsum.photos service (no API key needed). For Unsplash use you'd need an API key.
"""

import os
import random
import requests
from pathlib import Path

try:
    # configure Django when run via `python scripts/add_product_images.py` directly
    import django
    from django.conf import settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')
    django.setup()
except Exception:
    pass


def _ensure_media_path():
    from django.conf import settings
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        raise RuntimeError('MEDIA_ROOT is not set in Django settings')
    products_dir = Path(media_root) / 'products'
    products_dir.mkdir(parents=True, exist_ok=True)
    return products_dir


def _download_image(url, dest_path):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(dest_path, 'wb') as f:
        f.write(resp.content)


def attach_images(count=200, force=False, dry_run=True):
    """Attach `count` images to products that don't already have images (unless force=True).

    - count: number of products to attach images for
    - force: if True, replace existing images
    - dry_run: if True, don't actually download or save files; just print actions
    """
    from catalog.models import Product
    products = list(Product.objects.all())
    if not products:
        print('no products found')
        return

    products_to_update = [p for p in products if force or not p.image]
    if not products_to_update:
        print('no products to update')
        return

    # limit to requested count
    products_to_update = products_to_update[:count]

    media_products_dir = _ensure_media_path()

    print(f'Preparing to attach images to {len(products_to_update)} products (dry_run={dry_run})')
    for p in products_to_update:
        # Use picsum.photos random id to get a reasonable variety; using 800x600
        img_id = random.randint(1, 1000)
        url = f'https://picsum.photos/id/{img_id}/800/600'
        filename = f'{p.slug or p.id}-{img_id}.jpg'
        dest = media_products_dir / filename

        print(f'Product {p.id} -> {filename} from {url}')
        if dry_run:
            continue

        try:
            _download_image(url, dest)
        except Exception as e:
            print('download failed for', p.id, e)
            continue

        # update model
        p.image.name = f'products/{filename}'
        p.save(update_fields=['image'])

    print('done')


if __name__ == '__main__':
    # allow running the script directly for small quick tests (not recommended for large runs)
    attach_images(count=50, force=False, dry_run=True)
\n
