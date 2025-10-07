import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','nexus.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User=get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin','admin@example.com','password')
    print('superuser created: admin')
else:
    print('superuser already exists:', list(User.objects.filter(is_superuser=True).values('username','email')))
