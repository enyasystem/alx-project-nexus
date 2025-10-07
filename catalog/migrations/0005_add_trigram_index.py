from django.db import migrations


def _apply_trigram_indexes(apps, schema_editor):
    # Only apply when running against PostgreSQL
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cursor.execute("CREATE INDEX IF NOT EXISTS catalog_product_trgm_idx ON catalog_product USING GIN ((coalesce(name, '')) gin_trgm_ops)")
        cursor.execute("CREATE INDEX IF NOT EXISTS catalog_product_description_trgm_idx ON catalog_product USING GIN ((coalesce(description, '')) gin_trgm_ops)")


def _reverse_trigram_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS catalog_product_trgm_idx")
        cursor.execute("DROP INDEX IF EXISTS catalog_product_description_trgm_idx")
        cursor.execute("DROP EXTENSION IF EXISTS pg_trgm")


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_add_name_index'),
    ]

    operations = [
        migrations.RunPython(_apply_trigram_indexes, _reverse_trigram_indexes),
    ]
