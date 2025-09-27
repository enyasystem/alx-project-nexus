from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from django.core import mail
from django.core.cache import cache
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

User = get_user_model()

class RegistrationAndLockoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def test_registration_sends_verification_and_activation(self):
        url = reverse('register')
        data = {'username': 'reguser', 'email': 'reg@example.com', 'password': 'strongpass'}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, 201)
        # user should be created but inactive
        user = User.objects.get(username='reguser')
        self.assertFalse(user.is_active)
        # an email should have been sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn('Verify', message.subject)
        # simulate clicking verification link
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verify_url = reverse('verify_email') + f'?uid={uid}&token={token}'
        resp2 = self.client.get(verify_url)
        self.assertEqual(resp2.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    @override_settings(ACCOUNT_LOCKOUT_THRESHOLD=3, ACCOUNT_LOCKOUT_TIMEOUT=60)
    def test_login_lockout_after_failed_attempts(self):
        # create active user
        user = User.objects.create_user(username='lockuser', email='lock@example.com', password='secret', is_active=True)
        token_url = reverse('token_obtain_pair')
        # fail login multiple times
        for i in range(3):
            resp = self.client.post(token_url, {'username': 'lockuser', 'password': 'wrong'}, format='json')
            self.assertIn(resp.status_code, (400, 401, 403))
        # next attempt should be locked
        resp2 = self.client.post(token_url, {'username': 'lockuser', 'password': 'wrong'}, format='json')
        self.assertEqual(resp2.status_code, 403)
        self.assertIn('locked', resp2.data.get('detail').lower())

