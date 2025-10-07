import io
import os
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from moto import mock_aws
import boto3
from django.conf import settings

User = get_user_model()

# Ensure django-storages finds the expected bucket setting (AWS_STORAGE_BUCKET_NAME)
@mock_aws
@override_settings(
    USE_S3=True,
    AWS_S3_BUCKET_NAME='test-bucket',
    AWS_STORAGE_BUCKET_NAME='test-bucket',
    AWS_S3_CUSTOM_DOMAIN='test-bucket.s3.amazonaws.com',
    AWS_ACCESS_KEY_ID='testing',
    AWS_SECRET_ACCESS_KEY='testing',
    AWS_S3_REGION_NAME='us-east-1',
    # Use STORAGES mapping to avoid DEFAULT_FILE_STORAGE deprecation on newer Django
    STORAGES={
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        }
    },
)
class S3UploadTest(TestCase):
    def setUp(self):
        # create mock bucket
        self.s3 = boto3.client('s3', region_name='us-east-1')
        self.s3.create_bucket(Bucket='test-bucket')
        self.client = APIClient()
        from catalog.models import Category
        self.cat = Category.objects.create(name='S3Cat', slug='s3cat')
        self.user = User.objects.create_user(username='s3tester', email='s3@test.com', password='pass', is_staff=True)

    def test_upload_product_image_to_s3(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('product-list')
        img = Image.new('RGB', (20, 20), color='green')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        uploaded = SimpleUploadedFile('s3test.png', buf.read(), content_type='image/png')
        data = {
            'name': 'S3Product',
            'slug': 's3-product',
            'description': 'product with s3 image',
            'price': '5.00',
            'inventory': '1',
            'category_id': str(self.cat.pk),
            'image': uploaded,
        }
        resp = self.client.post(url, data, format='multipart')
        self.assertEqual(resp.status_code, 201)
        image_url = resp.data.get('image')
        self.assertIsNotNone(image_url)
        # compute the key by stripping the custom domain or bucket url
        domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None) or f"{getattr(settings, 'AWS_S3_BUCKET_NAME', 'test-bucket')}.s3.amazonaws.com"
        if image_url.startswith('http') and domain in image_url:
            key = image_url.split(domain + '/')[1]
        else:
            # fallback to basename
            key = image_url.split('/')[-1]
        # ensure object exists in the mocked bucket
        objs = self.s3.list_objects_v2(Bucket='test-bucket', Prefix=key)
        self.assertIn('Contents', objs)
\n