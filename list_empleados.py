import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from envios.models import Empleado

empleados = Empleado.objects.all()
print(f"Total empleados: {empleados.count()}")
for emp in empleados:
    print(f"  {emp.codigo} - {emp.email} - estado: {emp.estado}")