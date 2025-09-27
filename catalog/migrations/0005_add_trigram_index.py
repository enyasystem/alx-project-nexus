from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_add_name_index'),
    ]

    operations = [
        # Enable pg_trgm extension if using PostgreSQL
        migrations.RunSQL(
            sql=(
                "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
            ),
            reverse_sql=(
                "DROP EXTENSION IF EXISTS pg_trgm;"
            )
        ),
        # Create GIN trigram index for name and description to accelerate ILIKE searches
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS catalog_product_trgm_idx ON catalog_product USING GIN ((coalesce(name, '')) gin_trgm_ops)"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS catalog_product_trgm_idx"
            )
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS catalog_product_description_trgm_idx ON catalog_product USING GIN ((coalesce(description, '')) gin_trgm_ops)"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS catalog_product_description_trgm_idx"
            )
        ),
    ]
