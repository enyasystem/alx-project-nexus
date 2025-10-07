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
        objs.append(
            Product(
                name=f'Perf{i}',
                slug=f'perf-{i}',
                description='perf',
                price=round(1.0 + (i % 100), 2),
                inventory=10,
                category=cat,
            )
        )

    # Try ORM bulk_create first; if the DB schema differs (extra NOT NULL columns
    # like `allow_backorder`), fall back to a raw INSERT path that detects DB
    # columns and inserts values accordingly.
    try:
        Product.objects.bulk_create(objs)
        print(f"Seeded {count} products")
        return
    except Exception as orm_exc:
        # Fall back to raw insertion
        from django.db import connection
        print('ORM bulk_create failed, falling back to raw INSERT (reason:', orm_exc, ')')
        with connection.cursor() as cursor:
            # Detect columns in a DB-agnostic way. Try SQLite PRAGMA first,
            # otherwise query information_schema for Postgres.
            cols = []
            try:
                cursor.execute("PRAGMA table_info('catalog_product')")
                rows = cursor.fetchall()
                # PRAGMA returns tuples where name is at index 1
                cols = [r[1] for r in rows]
            except Exception:
                # Postgres (and others) - query information_schema
                try:
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='catalog_product'")
                    cols = [r[0] for r in cursor.fetchall()]
                except Exception:
                    raise RuntimeError('Could not detect catalog_product columns for raw insert')

            # Prepare insert columns and rows. Map category to category_id column name.
            insert_cols = []
            wanted = ['name', 'slug', 'description', 'price', 'inventory', 'category_id', 'created_at', 'updated_at', 'image', 'allow_backorder']
            for c in wanted:
                if c in cols:
                    insert_cols.append(c)

            if not insert_cols:
                raise RuntimeError('No suitable columns found on catalog_product to insert')

            placeholders = ','.join(['?'] * len(insert_cols)) if connection.vendor == 'sqlite' else ','.join(['%s'] * len(insert_cols))
            col_list_sql = ','.join(insert_cols)
            insert_sql = f"INSERT INTO catalog_product ({col_list_sql}) VALUES ({placeholders})"

            batch = []
            from datetime import datetime
            now_val = datetime.utcnow().isoformat(sep=' ')
            for i in range(count):
                row = []
                # build values in the same order as insert_cols
                for col in insert_cols:
                    if col == 'name':
                        row.append(f'Perf{i}')
                    elif col == 'slug':
                        row.append(f'perf-{i}')
                    elif col == 'description':
                        row.append('perf')
                    elif col == 'price':
                        # store as numeric/string acceptable to DB
                        row.append(str(round(1.0 + (i % 100), 2)))
                    elif col == 'inventory':
                        row.append(10)
                    elif col == 'category_id':
                        row.append(cat.id)
                    elif col == 'allow_backorder':
                        # default sensible value
                        row.append(0)
                    elif col == 'image':
                        row.append(None)
                    elif col == 'created_at' or col == 'updated_at':
                        # provide a timestamp string acceptable to SQLite/Postgres
                        row.append(now_val)
                    else:
                        row.append(None)
                batch.append(tuple(row))

            # Execute in batches to avoid overly large single statements
            batch_size = 200
            for start in range(0, len(batch), batch_size):
                chunk = batch[start:start + batch_size]
                try:
                    cursor.executemany(insert_sql, chunk)
                except Exception as e:
                    # re-raise with context
                    raise RuntimeError('Raw insert failed: ' + str(e))

            print(f"Seeded {count} products (raw INSERT fallback)")

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


def seed_varieties(count=1000, clear_existing=False):
    """Seed `count` varied products across multiple categories.

    - clear_existing: if True, deletes products with slugs starting with 'var-' before seeding.
    """
    if not USE_DJANGO:
        raise RuntimeError("Django is not configured. Run this from the project root or use `manage.py shell`.")
    from catalog.models import Category, Product
    # create some sensible categories
    category_names = ['Electronics', 'Books', 'Home', 'Toys', 'Clothing', 'Sports', 'Beauty', 'Garden', 'Automotive', 'Grocery']
    cats = []
    for name in category_names:
        slug = name.lower().replace(' ', '-')
        # use defaults so we don't try to create a Category with the same
        # name but a different slug (which would violate the unique name)
        c, _ = Category.objects.get_or_create(name=name, defaults={'slug': slug})
        cats.append(c)

    if clear_existing:
        Product.objects.filter(slug__startswith='var-').delete()

    adjectives = ['Fresh', 'Modern', 'Classic', 'Eco', 'Smart', 'Compact', 'Durable', 'Lightweight', 'Premium', 'Budget']
    nouns = ['Speaker', 'Mug', 'Chair', 'Lamp', 'Watch', 'T-Shirt', 'Sneakers', 'Backpack', 'Mixer', 'Bottle']

    objs = []
    for i in range(count):
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        name = f"{adj} {noun} {i}"
        slug = f"var-{i}-{random.randint(1000,9999)}"
        description = f"{adj} {noun} perfect for everyday use. Model {i}."
        # price distribution: many affordable, some expensive
        if random.random() < 0.75:
            price = round(random.uniform(5.0, 150.0), 2)
        else:
            price = round(random.uniform(150.0, 1200.0), 2)
        inventory = random.randint(0, 500)
        category = random.choice(cats)
        objs.append(Product(name=name, slug=slug, description=description, price=price, inventory=inventory, category=category))

    # Use existing bulk_create path (it will fallback if DB schema differs)
    try:
        Product.objects.bulk_create(objs)
        print(f"Seeded {count} varied products")
    except Exception:
        # Reuse the raw-insert fallback by calling seed() raw path behavior: detect columns and insert
        # We'll insert directly using the same logic as fallback in seed()
        from django.db import connection
        with connection.cursor() as cursor:
            # detect columns
            cols = []
            try:
                cursor.execute("PRAGMA table_info('catalog_product')")
                rows = cursor.fetchall()
                cols = [r[1] for r in rows]
            except Exception:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='catalog_product'")
                cols = [r[0] for r in cursor.fetchall()]

            wanted = ['name', 'slug', 'description', 'price', 'inventory', 'category_id', 'created_at', 'updated_at', 'image', 'allow_backorder']
            insert_cols = [c for c in wanted if c in cols]
            if not insert_cols:
                raise RuntimeError('No suitable columns found on catalog_product to insert')

            placeholders = ','.join(['?'] * len(insert_cols)) if connection.vendor == 'sqlite' else ','.join(['%s'] * len(insert_cols))
            col_list_sql = ','.join(insert_cols)
            insert_sql = f"INSERT INTO catalog_product ({col_list_sql}) VALUES ({placeholders})"

            from datetime import datetime
            now_val = datetime.utcnow().isoformat(sep=' ')

            batch = []
            for p in objs:
                row = []
                for col in insert_cols:
                    if col == 'name':
                        row.append(p.name)
                    elif col == 'slug':
                        row.append(p.slug)
                    elif col == 'description':
                        row.append(p.description)
                    elif col == 'price':
                        row.append(str(p.price))
                    elif col == 'inventory':
                        row.append(p.inventory)
                    elif col == 'category_id':
                        row.append(p.category.id)
                    elif col == 'allow_backorder':
                        row.append(0)
                    elif col == 'image':
                        row.append(None)
                    elif col in ('created_at', 'updated_at'):
                        row.append(now_val)
                    else:
                        row.append(None)
                batch.append(tuple(row))

            batch_size = 200
            for start in range(0, len(batch), batch_size):
                chunk = batch[start:start + batch_size]
                cursor.executemany(insert_sql, chunk)

            print(f"Seeded {count} varied products (raw INSERT fallback)")


if __name__ == '__main__':
    main()
\n