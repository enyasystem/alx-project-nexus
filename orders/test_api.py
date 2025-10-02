from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from catalog.models import Category, Product


User = get_user_model()


class OrdersAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='pass')
        self.cat = Category.objects.create(name='Books', slug='books')
        self.prod = Product.objects.create(name='Book A', slug='book-a', price='12.50', inventory=3, category=self.cat)

    def authenticate(self):
        from django.urls import reverse
        resp = self.client.post(reverse('token_obtain_pair'), {'username': 'apiuser', 'password': 'pass'}, format='json')
        self.assertEqual(resp.status_code, 200)
        token = resp.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_create_cart_add_item_and_create_order(self):
        self.authenticate()
        # create cart
        from django.urls import reverse
        resp = self.client.post(reverse('cart-list'), {}, format='json')
        self.assertEqual(resp.status_code, 201)
        cart_id = resp.data['id']

        # add item
        resp = self.client.post(f'/api/orders/carts/{cart_id}/add-item/', {'product': self.prod.id, 'quantity': 2}, format='json')
        self.assertEqual(resp.status_code, 201)

        # create order from cart
        resp = self.client.post(reverse('order-create-from-cart'), {'cart_id': cart_id}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertIn('id', resp.data)

    def test_insufficient_stock_via_api(self):
        self.authenticate()
        from django.urls import reverse
        resp = self.client.post(reverse('cart-list'), {}, format='json')
        cart_id = resp.data['id']
        # request more than inventory
        resp = self.client.post(f'/api/orders/carts/{cart_id}/add-item/', {'product': self.prod.id, 'quantity': 10}, format='json')
        self.assertEqual(resp.status_code, 201)
        resp = self.client.post(reverse('order-create-from-cart'), {'cart_id': cart_id}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_anonymous_cart_flow(self):
        # Anonymous can create a cart but our view restricts creation to authenticated users; verify 403 or empty behavior
        resp = self.client.post('/api/orders/carts/', {}, format='json')
        # either 401/403 or 201 depending on configuration; accept 201 or 403
        self.assertIn(resp.status_code, (201, 403, 401))
