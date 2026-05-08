import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from envios.models import Empleado

User = get_user_model()

try:
    user = User.objects.get(username="testuser")
except User.DoesNotExist:
    user = User.objects.create_superuser("testuser", "test@test.com", "test1234")
    print(f"Created user: {user.username}")
else:
    print(f"User exists: {user.username}")

emp = Empleado.objects.filter(email=user.email).first()
if emp:
    print(f"Found empleado: {emp.codigo}, estado: {emp.estado}")
    emp.estado = 1
    emp.save()
    print("Updated to active")
else:
    print("Creating new empleado")
    emp = Empleado.objects.create(
        codigo="EMP001",
        nombres="Usuario",
        apellidos="Prueba",
        email=user.email,
        cargo="ADMIN",
        estado=1,
        fecha_ingreso="2026-01-01"
    )
    print(f"Created: {emp.codigo}")