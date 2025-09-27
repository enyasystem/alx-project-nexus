import io
import os
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

User = get_user_model()

@override_settings(MEDIA_ROOT=os.path.join(os.path.dirname(__file__), 'tmp_media'))
class ProductImageUploadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat = None
        # create category via models to avoid importing catalog models at top-level
        from catalog.models import Category, Product
        self.Category = Category
        self.Product = Product
        self.cat = Category.objects.create(name='TestCat', slug='testcat')
        self.user = User.objects.create_user(username='imgtester', email='img@test.com', password='pass', is_staff=True)

    def tearDown(self):
        # cleanup any uploaded files
        media_dir = os.path.join(os.path.dirname(__file__), 'tmp_media')
        if os.path.exists(media_dir):
            for root, dirs, files in os.walk(media_dir, topdown=False):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                    except Exception:
                        pass
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except Exception:
                        pass
            try:
                os.rmdir(media_dir)
            except Exception:
                pass

    def test_upload_product_image_local_storage(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('product-list')
        # create in-memory image
        img = Image.new('RGB', (20, 20), color='blue')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        # use SimpleUploadedFile so the upload has a filename/extension
        uploaded = SimpleUploadedFile('test.png', buf.read(), content_type='image/png')
        data = {
            'name': 'ImgProduct',
            'slug': 'img-product',
            'description': 'product with image',
            'price': '3.50',
            'inventory': '2',
            'category_id': str(self.cat.pk),
            'image': uploaded,
        }
        resp = self.client.post(url, data, format='multipart')
        self.assertEqual(resp.status_code, 201)
        self.assertIn('image', resp.data)
        # check file exists on disk
        image_url = resp.data.get('image')
        self.assertIsNotNone(image_url)
        # ensure the file path exists under MEDIA_ROOT
        media_root = os.path.join(os.path.dirname(__file__), 'tmp_media')
        # get filename portion
        filename = os.path.basename(image_url)
        self.assertTrue(os.path.exists(os.path.join(media_root, 'products', filename)))
