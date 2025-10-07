# Generated manually to add index for Product.name
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_add_product_image'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['name'], name='catalog_pro_name_idx'),
        ),
    ]
\n
