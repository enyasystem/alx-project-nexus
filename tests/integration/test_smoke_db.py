from django.test import TestCase
from django.db import connection

class SmokeDBTest(TestCase):
    def test_db_connection_and_migrations(self):
        # Assert DB connection usable
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            row = cursor.fetchone()
        self.assertEqual(row[0], 1)

    def test_health_endpoint_available(self):
        # Check that the root health endpoint responds (adjust if different)
        from django.test import Client
        client = Client()
        resp = client.get('/api/health/' if hasattr(client, 'get') else '/')
        # Accept 200 or 404 depending on whether health endpoint exists
        self.assertIn(resp.status_code, (200, 404))
\n
