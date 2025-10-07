"""Bulk-load JSON fixtures using Django bulk_create to speed up imports over remote DBs.

Usage:
  Set DATABASE_URL in the environment for the target DB (or ensure settings pick it up),
  then run:
    python scripts/bulk_load_fixtures.py fixtures/catalog.utf8.json

Notes:
  - This loader only handles the common catalog models (Category, Product, ProductImage, ProductVariant).
  - It uses bulk_create in batches to reduce round-trips. It is conservative and prints progress.
"""
import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import nexus` works when running this script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')
django.setup()

from django.db import transaction
from catalog.models import Category, Product, ProductImage, ProductVariant


MODEL_MAPPING = {
    'catalog.category': Category,
    'catalog.product': Product,
    'catalog.productimage': ProductImage,
    'catalog.productvariant': ProductVariant,
}


def load_fixture(path: Path, batch_size: int = 200):
    print(f"Loading fixture {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Group objects by model
    by_model = {}
    for obj in data:
        model_label = obj.get('model')
        if not model_label:
            continue
        by_model.setdefault(model_label.lower(), []).append(obj)

    # Process simple models in a safe order
    order = ['catalog.category', 'catalog.product', 'catalog.productvariant', 'catalog.productimage']

    for model_label in order:
        items = by_model.get(model_label, [])
        if not items:
            print(f"No objects for {model_label}")
            continue

        Model = MODEL_MAPPING.get(model_label)
        if Model is None:
            print(f"Skipping unsupported model: {model_label}")
            continue

        instances = []
        pks = []
        for o in items:
            fields = o.get('fields', {})
            # Map JSON fields to model kwargs; for FK fields use the '<name>_id' form
            kwargs = {}
            for k, v in fields.items():
                try:
                    field = Model._meta.get_field(k)
                except Exception:
                    field = None

                # Skip many-to-many here; Django fixtures store M2M separately
                if field is not None and getattr(field, 'many_to_many', False):
                    continue

                if field is not None and field.is_relation and getattr(field, 'many_to_one', False):
                    # ForeignKey: use the *_id assignment
                    kwargs[f"{k}_id"] = v
                else:
                    kwargs[k] = v

            # If fixture has pk, set it explicitly
            pk = o.get('pk')
            if pk is not None:
                kwargs['id'] = pk

            instances.append(Model(**kwargs))
            pks.append(pk)

        # Remove instances whose PK already exists on the target DB
        existing_ids = set()
        pk_list = [p for p in pks if p is not None]
        if pk_list:
            existing_ids = set(Model.objects.filter(id__in=pk_list).values_list('id', flat=True))

        # Filter out instances with existing PKs
        filtered = []
        for inst, pk in zip(instances, pks):
            if pk is not None and pk in existing_ids:
                # Skip existing object
                continue
            filtered.append(inst)

        print(f"Preparing to bulk create {len(filtered)} objects for {model_label} (skipped {len(instances)-len(filtered)} existing)")
        # Bulk create in batches inside a transaction
        with transaction.atomic():
            for i in range(0, len(filtered), batch_size):
                batch = filtered[i:i + batch_size]
                Model.objects.bulk_create(batch, batch_size)
                print(f"Inserted {i + len(batch)} / {len(filtered)} for {model_label}")


def main(argv):
    if len(argv) < 2:
        print("Usage: python scripts/bulk_load_fixtures.py <fixture1.json> [fixture2.json ...]")
        return 2

    for path in argv[1:]:
        p = Path(path)
        if not p.exists():
            print(f"Fixture not found: {p}")
            continue
        load_fixture(p)

    print("Done.")
    return 0


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
