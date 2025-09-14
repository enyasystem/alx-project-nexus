from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthTests(TestCase):
    """Tests for JWT-based authentication endpoints.

    Covers registration, token obtain, token refresh and access-protected endpoints.
    These tests serve as both unit checks and a smoke test for auth flows.
    """

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.token_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.hello_url = reverse('hello')

    def test_register_creates_user(self):
        """Posting valid data to register should create a new user and return 201."""
        data = {'username': 'testuser', 'email': 'test@example.com', 'password': 'safepass123'}
        resp = self.client.post(self.register_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Ensure the user exists and the password is not stored in plaintext
        user = User.objects.filter(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('safepass123'))

    def test_token_obtain_with_valid_credentials(self):
        """Valid credentials should return access and refresh tokens."""
        User.objects.create_user(username='alice', email='a@x.com', password='safepass123')
        resp = self.client.post(self.token_url, {'username': 'alice', 'password': 'safepass123'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_token_obtain_with_invalid_credentials(self):
        """Invalid credentials should not return tokens."""
        resp = self.client.post(self.token_url, {'username': 'noone', 'password': 'badpass'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Refresh endpoint should issue a new access token when provided a valid refresh token."""
        User.objects.create_user(username='bob', email='b@x.com', password='safepass123')
        token_resp = self.client.post(self.token_url, {'username': 'bob', 'password': 'safepass123'}, format='json')
        refresh = token_resp.data.get('refresh')
        self.assertIsNotNone(refresh)
        refresh_resp = self.client.post(self.refresh_url, {'refresh': refresh}, format='json')
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_resp.data)

    def test_protected_endpoint_requires_auth(self):
        """Protected endpoint should return 401 when no credentials supplied."""
        resp = self.client.get(self.hello_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_token(self):
        """Access protected endpoint with a valid access token."""
        User.objects.create_user(username='carol', email='c@x.com', password='safepass123')
        token_resp = self.client.post(self.token_url, {'username': 'carol', 'password': 'safepass123'}, format='json')
        access = token_resp.data.get('access')
        self.assertIsNotNone(access)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get(self.hello_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('message', resp.data)
