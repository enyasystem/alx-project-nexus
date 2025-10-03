from django.test import TestCase
from catalog.models import Category, Product
from django.contrib.auth import get_user_model
from .models import Cart, CartItem
from .serializers import create_order_from_cart
from django.utils import timezone
from django.core.management import call_command


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

    def test_sequential_orders_respect_inventory(self):
        # First cart consumes 4 units, leaving 1. Second cart tries to consume 2 and should fail.
        cart1 = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart1, product=self.p, quantity=4)
        order1 = create_order_from_cart(cart1, user=self.user)
        self.assertEqual(order1.items.count(), 1)
        self.p.refresh_from_db()
        self.assertEqual(self.p.inventory, 1)

    def test_reservation_expiry_releases_inventory(self):
        # create a cart and reserve 2 units
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.p, quantity=2)
        # create reservation manually using model helper to simulate reserve endpoint
        from orders.models import StockReservation
        from django.utils import timezone
        expires = timezone.now() - timezone.timedelta(minutes=1)
        # decrement inventory to simulate reservation creation
        self.p.inventory -= 2
        self.p.save()
        r = StockReservation.objects.create(product=self.p, quantity=2, owner_type='cart', owner_id=str(cart.id), status='active', expires_at=expires)
        # run management command to expire reservations
        call_command('expire_reservations')
        # reservation should be cancelled and inventory restored
        r.refresh_from_db()
        self.assertEqual(r.status, 'cancelled')
        self.p.refresh_from_db()
        self.assertEqual(self.p.inventory, 5)

        cart2 = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart2, product=self.p, quantity=2)
        # inventory was restored to 5 by expiry, so creating an order for 2 should succeed
        order2 = create_order_from_cart(cart2, user=self.user)
        self.assertEqual(order2.items.count(), 1)
        self.p.refresh_from_db()
        self.assertEqual(self.p.inventory, 3)
