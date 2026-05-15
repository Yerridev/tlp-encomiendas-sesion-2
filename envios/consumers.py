import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = 'dashboard'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        stats = await self.get_stats()
        await self.send(text_data=json.dumps({
            'tipo': 'stats_iniciales',
            'stats': stats,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('tipo') == 'solicitar_stats':
            stats = await self.get_stats()
            await self.send(text_data=json.dumps({
                'tipo': 'stats',
                'stats': stats,
            }))

    async def dashboard_actualizar(self, event):
        await self.send(text_data=json.dumps({
            'tipo': 'stats_actualizado',
            'stats': event['stats'],
        }))

    async def estado_cambio(self, event):
        await self.send(text_data=json.dumps({
            'tipo': 'estado_cambio',
            'encomienda_id': event['encomienda_id'],
            'codigo': event['codigo'],
            'estado_anterior': event['estado_anterior'],
            'estado_nuevo': event['estado_nuevo'],
            'empleado': event['empleado'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def get_stats(self):
        from envios.models import Encomienda
        hoy = timezone.now().date()
        return {
            'activas': Encomienda.objects.activas().count(),
            'en_transito': Encomienda.objects.en_transito().count(),
            'con_retraso': Encomienda.objects.con_retraso().count(),
            'entregadas_hoy': Encomienda.objects.filter(
                estado='EN', fecha_entrega_real=hoy
            ).count(),
        }