"""Seed products and profile list endpoint latency.

This script seeds N products via the Django ORM (it's meant to be run with
`python manage.py runscript` or invoked by a manage.py shell), then makes
HTTP requests to the API to measure latency. For real performance testing
use a Postgres dev stack via docker-compose.

Usage (local Django shell):
  & .\venv\Scripts\Activate.ps1
  python manage.py shell -c "import scripts.seed_and_profile as s; s.seed(1000)"

Or run against a running server (requires `requests`):
  python scripts/seed_and_profile.py --host http://localhost:8000 --count 1000
"""

import argparse
import time
import random
import sys

try:
    import django
    django.setup()
except Exception:
    # If running standalone against running server, django not needed
    pass


def seed(count=1000):
    """Seed `count` products using Django ORM."""
    from catalog.models import Category, Product
    cat, _ = Category.objects.get_or_create(name='Perf', slug='perf')
    objs = []
    for i in range(count):
        objs.append(Product(name=f'Perf{i}', slug=f'perf-{i}', description='perf', price=round(1.0 + (i % 100),2), inventory=10, category=cat))
    Product.objects.bulk_create(objs)
    print(f"Seeded {count} products")


def profile(host='http://localhost:8000', limit=50, iterations=5):
    """Hit the product list endpoint and report latency statistics."""
    import requests
    url = f"{host}/api/products/"
    times = []
    for i in range(iterations):
        params = {'limit': limit}
        t0 = time.perf_counter()
        r = requests.get(url, params=params)
        t1 = time.perf_counter()
        r.raise_for_status()
        times.append(t1 - t0)
        print(f"Iter {i+1}: status={r.status_code} time={times[-1]:.3f}s count={len(r.json().get('results', []))}")
    print(f"avg={sum(times)/len(times):.3f}s min={min(times):.3f}s max={max(times):.3f}s")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='http://localhost:8000')
    parser.add_argument('--count', type=int, default=1000)
    parser.add_argument('--profile-only', action='store_true')
    args = parser.parse_args()
    if not args.profile_only:
        # attempt to seed using Django ORM
        try:
            seed(args.count)
        except Exception as e:
            print('Seeding failed:', e, file=sys.stderr)
    profile(args.host)
