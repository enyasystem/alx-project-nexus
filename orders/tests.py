from django.test import TestCase
from catalog.models import Category, Product
from django.contrib.auth import get_user_model
from .models import Cart, CartItem
from .serializers import create_order_from_cart


User = get_user_model()


class OrdersTestCase(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Toys', slug='toys')
        self.p = Product.objects.create(name='Toy Car', slug='toy-car', price='9.99', inventory=5, category=self.cat)
        self.user = User.objects.create_user(username='buyer', email='b@test.com', password='pass')

    def test_create_order_from_cart_success(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.p, quantity=2)
        order = create_order_from_cart(cart, user=self.user)
        self.assertEqual(order.items.count(), 1)
        self.p.refresh_from_db()
        self.assertEqual(self.p.inventory, 3)

    def test_create_order_from_cart_insufficient_inventory(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.p, quantity=10)
        try:
            create_order_from_cart(cart, user=self.user)
            self.fail('Expected ValueError')
        except ValueError as exc:
            self.assertIn('Not enough inventory', str(exc))
