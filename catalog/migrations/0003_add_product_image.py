# Generated manually to add ImageField for Product.image
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_product_catalog_pro_categor_7c1c1f_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(upload_to='products/', null=True, blank=True),
        ),
    ]
