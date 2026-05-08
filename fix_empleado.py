import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from envios.models import Empleado
from datetime import date

User = get_user_model()

user = User.objects.get(username="testuser")
print(f"User email: {user.email}")

# Buscar por email, no por código
emp = Empleado.objects.filter(email=user.email).first()
if emp:
    print(f"Found empleado: {emp.codigo}, estado: {emp.estado}")
    emp.estado = 1
    emp.fecha_ingreso = date.today()
    emp.save()
    print("Updated empleado to active")
else:
    print("No empleado found with that email")