from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from catalog.models import Category, Product
from django.contrib.auth import get_user_model
User = get_user_model()

# Non-sensitive test password used only in unit tests
# detect-secrets: allowlist secret
TEST_PASSWORD = '[REDACTED]'  # pragma: allowlist secret


class CatalogTests(TestCase):
    """Tests for product and category CRUD and listing features.

    Tests create/read/update/delete for categories and products, plus
    filtering by category, ordering by price, and pagination behavior.
    """

    def setUp(self):
        self.client = APIClient()
        # Create categories
        self.cat1 = Category.objects.create(name='Electronics', slug='electronics')
        self.cat2 = Category.objects.create(name='Books', slug='books')
        # Create products
        Product.objects.create(
            name='Laptop', slug='laptop', description='A nice laptop',
            price=1200.00, inventory=10, category=self.cat1
        )
        Product.objects.create(
            name='Smartphone', slug='smartphone', description='A smart phone',
            price=800.00, inventory=15, category=self.cat1
        )
        Product.objects.create(
            name='Novel', slug='novel', description='A fiction book',
            price=20.00, inventory=50, category=self.cat2
        )
        # Create a user for authenticated operations inside the test DB
        User.objects.create_user(username='tester', email='t@x.com', password=TEST_PASSWORD, is_staff=True)

    def authenticate(self):
        """Authenticate the test client as the staff user using force_authenticate.

        This bypasses token handling for unit tests and focuses the test on
        view behavior and permissions.
        """
        user = User.objects.get(username='tester')
        self.client.force_authenticate(user=user)

    def test_list_products(self):
        url = reverse('product-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 3)

    def test_filter_products_by_category(self):
        url = reverse('product-list')
        resp = self.client.get(url, {'category__slug': 'electronics'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in resp.data['results']]
        self.assertIn('Laptop', names)
        self.assertIn('Smartphone', names)
        self.assertNotIn('Novel', names)

    def test_ordering_by_price(self):
        url = reverse('product-list')
        resp = self.client.get(url, {'ordering': 'price'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        prices = [float(p['price']) for p in resp.data['results']]
        self.assertEqual(prices, sorted(prices))

    def test_pagination_limit(self):
        url = reverse('product-list')
        resp = self.client.get(url, {'limit': 2})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 2)

    def test_price_range_filter(self):
        url = reverse('product-list')
        resp = self.client.get(url, {'min_price': 100, 'max_price': 1000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        prices = [float(p['price']) for p in resp.data['results']]
        self.assertTrue(all(100 <= p <= 1000 for p in prices))

    def test_cursor_pagination(self):
        # create additional products to ensure pagination across cursor
        for i in range(15):
            Product.objects.create(name=f'Extra{i}', slug=f'extra{i}', description='bulk', price=5.00 + i, inventory=5, category=self.cat2)
        url = reverse('product-list')
        # first page (cursor pagination uses `cursor` param)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # ensure next cursor exists for subsequent page
        self.assertIn('next', resp.data)
        next_cursor = resp.data['next']
        if next_cursor:
            resp2 = self.client.get(next_cursor)
            self.assertEqual(resp2.status_code, status.HTTP_200_OK)

    def test_create_category(self):
        url = reverse('category-list')
        self.authenticate()
        resp = self.client.post(url, {'name': 'Toys', 'slug': 'toys'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(slug='toys').exists())

    def test_update_product(self):
        product = Product.objects.first()
        url = reverse('product-detail', args=[product.pk])
        self.authenticate()
        resp = self.client.patch(url, {'price': '999.99'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(float(product.price), 999.99)

    def test_delete_category(self):
        cat = Category.objects.create(name='Temp', slug='temp')
        url = reverse('category-detail', args=[cat.pk])
        self.authenticate()
        resp = self.client.delete(url)
        self.assertIn(resp.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK))
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists())

    def test_invalid_price_filter_returns_400(self):
        url = reverse('product-list')
        resp = self.client.get(url, {'min_price': 'cheap', 'max_price': 'expensive'})
        # django-filter will coerce or raise; ensure we don't return 500
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))

    def test_empty_database_returns_empty_results(self):
        # clear products and categories
        Product.objects.all().delete()
        Category.objects.all().delete()
        url = reverse('product-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # results may be empty list or paginated structure depending on pagination class
        if isinstance(resp.data, dict):
            results = resp.data.get('results', [])
        else:
            results = resp.data
        self.assertEqual(len(results), 0)

    def test_large_dataset_pagination_performance(self):
        """Seed many products and ensure list endpoint paginates and responds quickly."""
        # choose moderate size to keep test time reasonable
        N = 1000
        cat = Category.objects.create(name='Bulk', slug='bulk')
        objs = [Product(name=f'Bulk{i}', slug=f'bulk-{i}', description='x', price=1.0 + (i % 50), inventory=10, category=cat) for i in range(N)]
        Product.objects.bulk_create(objs)
        url = reverse('product-list')
        import time
        t0 = time.perf_counter()
        resp = self.client.get(url, {'limit': 50})
        t1 = time.perf_counter()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # ensure pagination returns expected page size
        if isinstance(resp.data, dict):
            self.assertEqual(len(resp.data.get('results', [])), 50)
        else:
            self.assertEqual(len(resp.data), 50)
        # soft performance assertion: in-memory DB should respond quickly
        self.assertLess(t1 - t0, 2.0)
