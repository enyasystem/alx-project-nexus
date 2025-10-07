"""Print sample Product.image values and the full URLs using MEDIA_URL env var.
Run with the same environment variables you use for migrate/loaddata so it targets the desired DB.
"""
import os
import django
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')
django.setup()

from catalog.models import Product

def main():
    media_url = os.environ.get('MEDIA_URL', '/media/')
    qs = Product.objects.exclude(image='').all()[:20]
    print('Products with image sample count:', qs.count())
    for p in qs:
        img_field = str(p.image)
        full = media_url + img_field
        print(p.id, repr(img_field), full)

if __name__ == '__main__':
    main()
