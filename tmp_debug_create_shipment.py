import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','nexus.settings')
django.setup()
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from catalog.models import Category, Product
User = get_user_model()
client = APIClient()
user = User.objects.create_user(username='apiuser2', password='pass')
cat = Category.objects.create(name='Books2', slug='books2')
prod = Product.objects.create(name='Book B', slug='book-b', price='10.00', inventory=3, category=cat)
# create cart
from django.urls import reverse
resp = client.post(reverse('cart-list'), {}, format='json')
print('cart create status', resp.status_code, resp.data)
cart_id = resp.data['id']
# add item
resp = client.post(f'/api/orders/carts/{cart_id}/add-item/', {'product': prod.id, 'quantity': 1}, format='json')
print('add item', resp.status_code, resp.data)
# create order
# authenticate
resp = client.post(reverse('token_obtain_pair'), {'username':'apiuser2','password':'pass'}, format='json')
print('token', resp.status_code, resp.data)
token = resp.data.get('access')
client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
resp = client.post(reverse('order-create-from-cart'), {'cart_id': cart_id}, format='json')
print('create order', resp.status_code, resp.data)
order_id = resp.data['id']
# create admin user and authenticate
admin = User.objects.create_superuser(username='admin2', email='a@a.com', password='pw')
resp = client.post(reverse('token_obtain_pair'), {'username':'admin2','password':'pw'}, format='json')
print('admin token', resp.status_code, resp.data)
token = resp.data.get('access')
client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
# call create-shipment
resp = client.post(f'/api/orders/orders/{order_id}/create-shipment/', {'carrier':'DHL','tracking_number':'T-1'}, format='json')
print('create shipment', resp.status_code, resp.data)
