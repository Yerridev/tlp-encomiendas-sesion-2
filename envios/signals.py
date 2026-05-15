from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone


@receiver(post_save)
def encomienda_cambio_estado(sender, instance, **kwargs):
    """Notifica a los clientes WebSocket cuando cambia el estado de una encomienda."""
    from envios.models import Encomienda

    if sender != Encomienda:
        return

    if not kwargs.get('created', True):
        if hasattr(instance, '_estado_anterior') and instance._estado_anterior != instance.estado:
            channel_layer = get_channel_layer()

            empleado_nombre = 'Sistema'
            if hasattr(instance, 'empleado_registro') and instance.empleado_registro:
                try:
                    empleado_nombre = f"{instance.empleado_registro.apellidos}, {instance.empleado_registro.nombres}"
                except:
                    empleado_nombre = str(instance.empleado_registro)

            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'dashboard_actualizar',
                    'stats': {
                        'activas': Encomienda.objects.activas().count(),
                        'en_transito': Encomienda.objects.en_transito().count(),
                        'con_retraso': Encomienda.objects.con_retraso().count(),
                        'entregadas_hoy': Encomienda.objects.filter(
                            estado='EN', fecha_entrega_real=timezone.now().date()
                        ).count(),
                    },
                }
            )

            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'estado_cambio',
                    'encomienda_id': instance.pk,
                    'codigo': instance.codigo,
                    'estado_anterior': instance._estado_anterior,
                    'estado_nuevo': instance.estado,
                    'empleado': empleado_nombre,
                    'timestamp': timezone.now().isoformat(),
                }
            )