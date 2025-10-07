"""Fill products without images with a small set of placeholder images.

Usage:
    python manage.py shell -c "import scripts.fill_with_placeholders as f; f.run(dry_run=True, count=5)"

The script downloads `count` placeholder images into MEDIA_ROOT/products/placeholders/
and creates a `ProductImage` row for every Product that currently has no images.
If dry_run is True the script will only print actions.
"""
import os
import sys
from pathlib import Path
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')
    import django
    django.setup()
except Exception:
    pass

from django.conf import settings
from catalog.models import Product, ProductImage

import requests
from urllib.parse import urljoin


PLACEHOLDER_DIR = Path(getattr(settings, 'MEDIA_ROOT')) / 'products' / 'placeholders'


def _ensure_dir():
    PLACEHOLDER_DIR.mkdir(parents=True, exist_ok=True)


def _download_placeholders(count=5, size=(800, 600)):
    """Download `count` placeholder images from picsum.photos if not already present.
    Returns list of relative paths (as strings) suitable for saving to ImageField.
    """
    _ensure_dir()
    downloaded = []
    for i in range(count):
        filename = f'placeholder-{i+1}-{size[0]}x{size[1]}.jpg'
        target = PLACEHOLDER_DIR / filename
        if target.exists() and target.stat().st_size > 0:
            # store as POSIX path so Django builds correct URLs on all platforms
            downloaded.append(str(Path('products') / 'placeholders' / filename).replace('\\', '/'))
            continue

        url = f'https://picsum.photos/{size[0]}/{size[1]}?random={i+1}'
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            with open(target, 'wb') as f:
                f.write(resp.content)
                downloaded.append(str(Path('products') / 'placeholders' / filename).replace('\\', '/'))
            print('downloaded', filename)
        except Exception as e:
            print('failed to download', url, '->', e)
    return downloaded


def run(dry_run=True, count=5, size=(800, 600), verbose=True):
    """Main entry point.

    dry_run: if True, only print actions
    count: number of placeholder images to maintain
    size: size tuple for placeholder images
    """
    # Ensure settings are loaded and MEDIA_ROOT is available
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        print('MEDIA_ROOT not configured; aborting')
        return

    placeholders = _download_placeholders(count=count, size=size)
    if not placeholders:
        print('No placeholders available; aborting')
        return

    # Find products without images (neither Product.image nor ProductImage rows)
    products_no_image = Product.objects.filter(image__isnull=True).filter().exclude(image='')

    # More robust: product has no productimage rows
    products = [p for p in Product.objects.all() if p.images.count() == 0]
    total = len(products)
    print(f'Products without ProductImage rows: {total}')
    if total == 0:
        return

    if dry_run:
        print('Dry-run: would assign placeholders to the following product ids:')
        for idx, p in enumerate(products):
            ph = placeholders[idx % len(placeholders)]
            print(f'  Product {p.id} -> {ph}')
        return

    # Apply: create ProductImage records and point to placeholder files
    created = 0
    for idx, p in enumerate(products):
        ph = placeholders[idx % len(placeholders)]
        # Skip if ProductImage with same image already exists (safety)
        if ProductImage.objects.filter(product=p, image=ph).exists():
            continue
        ProductImage.objects.create(product=p, image=ph, alt=(p.name or ''), order=0)
        created += 1
        if verbose and created % 100 == 0:
            print('created', created, 'so far...')

    print('done; created', created)


if __name__ == '__main__':
    # Small CLI convenience when executed directly
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=5)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(dry_run=args.dry_run, count=args.count)
\n
