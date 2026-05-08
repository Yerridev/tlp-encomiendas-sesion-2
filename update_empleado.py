import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from envios.models import Empleado
from datetime import date

User = get_user_model()

# Usar el empleado existente y asignar al usuario test
user = User.objects.get(username="testuser")
emp = Empleado.objects.get(codigo="EMP001")

# Associate the user with the existing empleado
print(f"Before: empleado email: {emp.email}")
emp.email = user.email
emp.save()
print(f"Updated empleado email to: {user.email}")