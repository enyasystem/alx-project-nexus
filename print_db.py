import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')
import django
django.setup()
from django.conf import settings
import pprint
pprint.pprint(settings.DATABASES)
