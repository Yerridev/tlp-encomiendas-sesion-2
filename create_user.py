import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="testuser").exists():
    user = User.objects.create_superuser("testuser", "test@test.com", "test1234")
    print(f"Created user: {user.username}")
else:
    print("User already exists")