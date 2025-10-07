import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','nexus.settings')
import django
django.setup()
from catalog.models import Product, ProductImage
from django.conf import settings
import requests

p = Product.objects.filter(image__isnull=False).exclude(image='').first()
if not p:
    print('no product with image found')
else:
    print('product id, slug:', p.id, p.slug)
    print('product.image.name:', p.image.name)
    try:
        print('product.image.url:', p.image.url)
    except Exception as e:
        print('could not get image.url:', e)
    imgs = list(ProductImage.objects.filter(product=p).values('id','image','alt','order'))
    print('productimage rows:', imgs[:5])
    if hasattr(p.image, 'url'):
        url = p.image.url
        if url.startswith('/'):
            url = 'http://127.0.0.1:8000' + url
        try:
            r = requests.get(url, timeout=5)
            print('http status:', r.status_code, 'content-type:', r.headers.get('content-type'))
        except Exception as e:
            print('http get failed:', e)
