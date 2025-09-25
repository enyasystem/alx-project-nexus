r"""Seed products and profile list endpoint latency.

This script seeds N products via the Django ORM (it's meant to be run from
the project root). It will attempt to configure Django automatically when
run from the repo. It can also make HTTP requests to a running server to
measure latency. For real performance testing use a Postgres dev stack via
docker-compose.

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
import os
from pathlib import Path

# If running from the project root, configure Django automatically so
# seeding via the ORM works when invoking this script directly.
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')

USE_DJANGO = False
try:
    import django
    django.setup()
    USE_DJANGO = True
except Exception:
    # If Django cannot be configured, seed() will raise a clear error.
    USE_DJANGO = False


def seed(count=1000):
    """Seed `count` products using Django ORM."""
    if not USE_DJANGO:
        raise RuntimeError("Django is not configured. Run this from the project root or use `manage.py shell`.")
    from catalog.models import Category, Product
    cat, _ = Category.objects.get_or_create(name='Perf', slug='perf')
    objs = []
    for i in range(count):
        objs.append(Product(name=f'Perf{i}', slug=f'perf-{i}', description='perf', price=round(1.0 + (i % 100),2), inventory=10, category=cat))
    Product.objects.bulk_create(objs)
    print(f"Seeded {count} products")

def profile(host='http://localhost:8000', path='/api/catalog/products/', limit=50, iterations=5):
    """Hit the product list endpoint and report latency statistics.

    `path` lets you override the URL path when your API mounts differently.
    """
    import requests
    url = f"{host.rstrip('/')}{path}"
    times = []
    for i in range(iterations):
        params = {'limit': limit}
        t0 = time.perf_counter()
        r = requests.get(url, params=params)
        t1 = time.perf_counter()
        try:
            r.raise_for_status()
        except Exception:
            print(f"Request failed (status={r.status_code}): {r.text}")
            raise
        times.append(t1 - t0)
        # gracefully handle different pagination response shapes
        try:
            count = len(r.json().get('results', []))
        except Exception:
            try:
                count = len(r.json())
            except Exception:
                count = 0
        print(f"Iter {i+1}: status={r.status_code} time={times[-1]:.3f}s count={count}")
    print(f"avg={sum(times)/len(times):.3f}s min={min(times):.3f}s max={max(times):.3f}s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='http://localhost:8000')
    parser.add_argument('--path', default='/api/catalog/products/')
    parser.add_argument('--count', type=int, default=1000)
    parser.add_argument('--profile-only', action='store_true')
    parser.add_argument('--limit', type=int, default=50)
    parser.add_argument('--iterations', type=int, default=5)
    args = parser.parse_args()
    if not args.profile_only:
        # attempt to seed using Django ORM
        try:
            seed(args.count)
        except Exception as e:
            print('Seeding failed:', e, file=sys.stderr)
    profile(args.host, path=args.path, limit=args.limit, iterations=args.iterations)


if __name__ == '__main__':
    main()
