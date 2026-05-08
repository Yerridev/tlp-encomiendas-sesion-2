import os
import django
from datetime import date
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from envios.models import Empleado

User = get_user_model()
user = User.objects.get(username="testuser")

if not hasattr(user, 'empleado'):
    empleado = Empleado.objects.create(
        codigo="EMP001",
        nombres="Usuario",
        apellidos="Prueba",
        email=user.email,
        cargo="ADMIN",
        estado=1,
        fecha_ingreso=date.today()
    )
    print(f"Created empleado: {empleado.codigo}")
else:
    print("Empleado already exists")