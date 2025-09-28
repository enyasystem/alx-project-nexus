"""Create an admin user from environment variables if one does not exist.
This script is safe to run multiple times (idempotent).
Set the following env vars in Render environment settings:
- ADMIN_USERNAME
- ADMIN_EMAIL
- ADMIN_PASSWORD

Usage: python scripts/create_admin_if_missing.py
"""
import os
import django
from django.core.management import execute_from_command_line

# Ensure Django settings are loaded when running as a script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('ADMIN_USERNAME')
email = os.getenv('ADMIN_EMAIL')
password = os.getenv('ADMIN_PASSWORD')

if not username or not email or not password:
    print('Admin env vars not set — skipping admin creation')
else:
    if User.objects.filter(username=username).exists():
        print(f'Admin user "{username}" already exists — skipping')
    else:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f'Created admin user "{username}"')
