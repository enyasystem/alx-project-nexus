import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')
django.setup()
from django.contrib.auth import get_user_model, authenticate
User = get_user_model()
su = User.objects.filter(is_superuser=True)
print('superusers:', list(su.values('id','username','email')))
if not su.exists():
    print('no superuser found')
for u in su:
    auth = authenticate(username=u.get_username(), password='password')
    print(f"username={u.get_username()}, authenticate_return={'OK' if auth else 'FAIL'}")
    print('check_password=', u.check_password('password'))
