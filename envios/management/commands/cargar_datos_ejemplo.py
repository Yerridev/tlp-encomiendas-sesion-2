"""
Comando para cargar datos de ejemplo en la base de datos.
Uso: python manage.py cargar_datos_ejemplo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos de ejemplo en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write('Cargando datos de ejemplo...')

        # 1. Crear usuario superuser si no existe
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@encomiendas.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Usuario creado: admin / admin123'))
        else:
            self.stdout.write(f'  - Usuario admin ya existe')

        # 2. Crear empleado
        from envios.models import Empleado
        empleado, created = Empleado.objects.get_or_create(
            email=user.email,
            defaults={
                'codigo': f'EMP-{str(uuid.uuid4())[:4].upper()}',
                'nombres': 'Administrador',
                'apellidos': 'Sistema',
                'cargo': 'GERENTE',
                'estado': 1,
                'fecha_ingreso': date.today(),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Empleado creado: {empleado.codigo}'))
        else:
            self.stdout.write(f'  - Empleado ya existe: {empleado.codigo}')

        # 3. Crear clientes
        from clientes.models import Cliente
        clientes_data = [
            {'nombres': 'Juan', 'apellidos': 'Pérez García', 'tipo_doc': 'DNI', 'nro_doc': '12345678', 'telefono': '999888777', 'direccion': 'Av. Lima 123'},
            {'nombres': 'María', 'apellidos': 'López Sánchez', 'tipo_doc': 'DNI', 'nro_doc': '87654321', 'telefono': '999888666', 'direccion': 'Jr. Amazonas 456'},
            {'nombres': 'Carlos', 'apellidos': 'Rodríguez Mendoza', 'tipo_doc': 'RUC', 'nro_doc': '20123456789', 'telefono': '999888555', 'direccion': 'Calle Comercial 789'},
            {'nombres': 'Ana', 'apellidos': 'Torres Flores', 'tipo_doc': 'DNI', 'nro_doc': '11223344', 'telefono': '999888444', 'direccion': 'Psje. Los Jazmines 101'},
            {'nombres': 'Luis', 'apellidos': 'Hernández Castro', 'tipo_doc': 'DNI', 'nro_doc': '55667788', 'telefono': '999888333', 'direccion': 'Av. Principal 202'},
        ]

        clientes = []
        for data in clientes_data:
            cliente, created = Cliente.objects.get_or_create(
                nro_doc=data['nro_doc'],
                defaults={
                    **data,
                    'estado': 1,
                }
            )
            clientes.append(cliente)
            if created:
                self.stdout.write(f'  ✓ Cliente: {cliente.nombre_completo}')

        # 4. Crear rutas
        from rutas.models import Ruta
        rutas_data = [
            {'codigo': 'RUT-001', 'origen': 'Lima', 'destino': 'Arequipa', 'precio_base': Decimal('45.00'), 'dias_entrega': 2},
            {'codigo': 'RUT-002', 'origen': 'Lima', 'destino': 'Cusco', 'precio_base': Decimal('55.00'), 'dias_entrega': 3},
            {'codigo': 'RUT-003', 'origen': 'Lima', 'destino': 'Trujillo', 'precio_base': Decimal('35.00'), 'dias_entrega': 1},
            {'codigo': 'RUT-004', 'origen': 'Lima', 'destino': 'Piura', 'precio_base': Decimal('50.00'), 'dias_entrega': 2},
            {'codigo': 'RUT-005', 'origen': 'Lima', 'destino': 'Iquitos', 'precio_base': Decimal('60.00'), 'dias_entrega': 4},
            {'codigo': 'RUT-006', 'origen': 'Lima', 'destino': 'Tacna', 'precio_base': Decimal('48.00'), 'dias_entrega': 2},
        ]

        rutas = []
        for data in rutas_data:
            ruta, created = Ruta.objects.get_or_create(
                codigo=data['codigo'],
                defaults={
                    **data,
                    'estado': 1,
                }
            )
            rutas.append(ruta)
            if created:
                self.stdout.write(f'  ✓ Ruta: {ruta.origen} → {ruta.destino}')

        # 5. Crear encomiendas de ejemplo
        from envios.models import Encomienda
        estados = ['PE', 'TR', 'DE', 'EN']
        encomiendas_creadas = 0

        for i in range(10):
            cliente_remitente = clientes[i % len(clientes)]
            cliente_destinatario = clientes[(i + 1) % len(clientes)]
            ruta = rutas[i % len(rutas)]
            estado = estados[i % len(estados)]

            # Verificar si ya existe una encomienda con este código
            codigo = f'ENC-{date.today().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}-{i+1:02d}'

            if not Encomienda.objects.filter(codigo=codigo).exists():
                peso = Decimal(str(round(1.5 + (i * 0.5), 2)))
                encomienda = Encomienda.objects.create(
                    codigo=codigo,
                    descripcion=f'Paquete de ejemplo #{i+1} -contains various items',
                    peso_kg=peso,
                    remitente=cliente_remitente,
                    destinatario=cliente_destinatario,
                    ruta=ruta,
                    empleado_registro=empleado,
                    estado=estado,
                    costo_envio=round(ruta.precio_base + (peso - Decimal('5.0')) * Decimal('2.50') if peso > Decimal('5.0') else ruta.precio_base, 2),
                    fecha_entrega_est=date.today() + timedelta(days=ruta.dias_entrega),
                    observaciones=f'Encomienda de prueba #{i+1}',
                )

                if estado == 'EN':
                    encomienda.fecha_entrega_real = encomienda.fecha_entrega_est
                    encomienda.save()

                encomiendas_creadas += 1

        if encomiendas_creadas > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✓ {encomiendas_creadas} encomiendas creadas'))
        else:
            self.stdout.write(f'  - Ya existen encomiendas hoy')

        # Resumen final
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Datos de ejemplo cargados ==='))
        self.stdout.write(f'  Usuarios: {User.objects.count()}')
        self.stdout.write(f'  Empleados: {Empleado.objects.count()}')
        self.stdout.write(f'  Clientes: {Cliente.objects.count()}')
        self.stdout.write(f'  Rutas: {Ruta.objects.count()}')
        self.stdout.write(f'  Encomiendas: {Encomienda.objects.count()}')
        self.stdout.write('')
        self.stdout.write('  Credenciales de acceso:')
        self.stdout.write('    Usuario: admin')
        self.stdout.write('    Contraseña: admin123')