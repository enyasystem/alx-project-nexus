from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='pwuser', email='pw@x.com', password='oldpass')

    def test_request_password_reset(self):
        url = reverse('password_reset')
        resp = self.client.post(url, {'email': 'pw@x.com'}, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_reset_confirm_invalid_token(self):
        url = reverse('password_reset_confirm')
        resp = self.client.post(url, {'uid': 'bad', 'token': 'bad', 'new_password': 'newpass123'}, format='json')
        self.assertEqual(resp.status_code, 400)
\n
