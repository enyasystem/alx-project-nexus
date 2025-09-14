from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

# Non-sensitive test password used only in unit tests
TEST_PASSWORD = 'test-pass-1'


class AuthTests(TestCase):
	"""Authentication endpoint tests (registration, JWT flows, protected endpoint)."""

	def setUp(self):
		self.client = APIClient()
		self.register_url = reverse('register')
		self.token_url = reverse('token_obtain_pair')
		self.refresh_url = reverse('token_refresh')
		self.hello_url = reverse('hello')

	def test_register_creates_user(self):
		data = {'username': 'testuser', 'email': 'test@example.com', 'password': TEST_PASSWORD}
		resp = self.client.post(self.register_url, data, format='json')
		self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
		user = User.objects.filter(username='testuser').first()
		self.assertIsNotNone(user)
		self.assertTrue(user.check_password('safepass123'))

	def test_token_obtain_with_valid_credentials(self):
		User.objects.create_user(username='alice', email='a@x.com', password=TEST_PASSWORD)
		resp = self.client.post(self.token_url, {'username': 'alice', 'password': TEST_PASSWORD}, format='json')
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertIn('access', resp.data)
		self.assertIn('refresh', resp.data)

	def test_token_obtain_with_invalid_credentials(self):
		resp = self.client.post(self.token_url, {'username': 'noone', 'password': 'badpass'}, format='json')
		self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_token_refresh(self):
		User.objects.create_user(username='bob', email='b@x.com', password=TEST_PASSWORD)
		token_resp = self.client.post(self.token_url, {'username': 'bob', 'password': TEST_PASSWORD}, format='json')
		refresh = token_resp.data.get('refresh')
		self.assertIsNotNone(refresh)
		refresh_resp = self.client.post(self.refresh_url, {'refresh': refresh}, format='json')
		self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
		self.assertIn('access', refresh_resp.data)

	def test_protected_endpoint_requires_auth(self):
		resp = self.client.get(self.hello_url)
		self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_protected_endpoint_with_token(self):
		User.objects.create_user(username='carol', email='c@x.com', password=TEST_PASSWORD)
		token_resp = self.client.post(self.token_url, {'username': 'carol', 'password': TEST_PASSWORD}, format='json')
		access = token_resp.data.get('access')
		self.assertIsNotNone(access)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
		resp = self.client.get(self.hello_url)
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertIn('message', resp.data)
