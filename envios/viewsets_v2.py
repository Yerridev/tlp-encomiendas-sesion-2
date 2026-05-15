"""
ViewSets version 2 de la API de Encomiendas.

Cambios respecto a v1:
- Ordenamiento por defecto por codigo (ascendente)
- Paginacion personalizada (EncomiendaPagination con metadata extra)
- Serializer con campo 'meta' en cada encomienda (EncomiendaV2Serializer)
- Accion adicional: /encomiendas/estadisticas_v2/ con distribucion por ruta
- Accion adicional: pendientes/ con paginacion
- El historial devuelve los ultimos 10 registros (en v1 eran 5)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import Encomienda, Empleado
from .serializers import (
    EncomiendaV2Serializer,
    EncomiendaListSerializer,
    HistorialEstadoSerializer,
)
from api.pagination import EncomiendaPagination, HistorialPagination
from api.filters import EncomiendaFilter
from api.permissions import EsEmpleadoActivo, EsPropietarioOAdmin
from api.throttles import EmpleadoRateThrottle, CambioEstadoThrottle
from config.choices import EstadoEnvio
from rutas.models import Ruta


@extend_schema_view(
    list=extend_schema(
        summary='[v2] Listar encomiendas',
        description=(
            'Lista paginada de encomiendas ordenadas por codigo. '
            'Cada elemento incluye el campo "meta" con informacion de version y permisos.'
        ),
        tags=['Encomiendas v2'],
    ),
    create=extend_schema(
        summary='[v2] Crear encomienda',
        description='Registra una nueva encomienda. Respuesta incluye campo "meta".',
        tags=['Encomiendas v2'],
    ),
    retrieve=extend_schema(
        summary='[v2] Detalle de encomienda',
        description='Detalle completo con remitente, destinatario, ruta, historial (ultimos 10) y meta.',
        tags=['Encomiendas v2'],
    ),
    update=extend_schema(summary='[v2] Actualizar encomienda',      tags=['Encomiendas v2']),
    partial_update=extend_schema(summary='[v2] Actualizar parcial', tags=['Encomiendas v2']),
    destroy=extend_schema(summary='[v2] Eliminar encomienda',       tags=['Encomiendas v2']),
)
class EncomiendaViewSetV2(viewsets.ModelViewSet):
    """
    API v2 - ModelViewSet para Encomiendas.

    Diferencias clave con v1:
    - Queryset ordenado por codigo ascendente por defecto.
    - Usa EncomiendaV2Serializer (con campo 'meta') para create/retrieve/update.
    - Para listado usa EncomiendaListSerializer (liviano, igual que v1).
    - Nuevas acciones: estadisticas_v2, pendientes (paginada).
    - Historial devuelve los ultimos 10 cambios (v1 devuelve 5).
    """
    queryset           = Encomienda.objects.con_relaciones().order_by('codigo')
    permission_classes = [EsEmpleadoActivo]
    pagination_class   = EncomiendaPagination
    throttle_classes   = [EmpleadoRateThrottle]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EncomiendaFilter
    search_fields   = ['codigo', 'remitente__apellidos', 'destinatario__apellidos', 'descripcion']
    ordering_fields = ['codigo', 'fecha_registro', 'peso_kg', 'costo_envio']
    ordering        = ['codigo']   # v2 ordena por codigo; v1 ordena por -fecha_registro

    # ── Serializer: listado ligero, detalle/escritura con meta ────────
    def get_serializer_class(self):
        if self.action == 'list':
            return EncomiendaListSerializer
        return EncomiendaV2Serializer

    # ── Permisos segun accion ─────────────────────────────────────────
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [EsEmpleadoActivo(), EsPropietarioOAdmin()]
        return [EsEmpleadoActivo()]

    # ── Throttle segun accion ─────────────────────────────────────────
    def get_throttles(self):
        if self.action == 'cambiar_estado':
            return [CambioEstadoThrottle()]
        return super().get_throttles()

    # ── QuerySet optimizado ───────────────────────────────────────────
    def get_queryset(self):
        return Encomienda.objects.con_relaciones().order_by('codigo')

    def perform_create(self, serializer):
        serializer.save(empleado_registro=self.request.user.empleado)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response['X-API-Version'] = 'v2'
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response['X-API-Version'] = 'v2'
        return response

    # ── Accion: cambiar estado ────────────────────────────────────────
    @extend_schema(
        summary='[v2] Cambiar estado de encomienda',
        description='Cambia el estado y registra el cambio en el historial. Respuesta incluye campo meta.',
        tags=['Encomiendas v2'],
    )
    @action(detail=True, methods=['post'], url_path='cambiar_estado')
    def cambiar_estado(self, request, pk=None):
        enc          = self.get_object()
        nuevo_estado = request.data.get('estado')
        observacion  = request.data.get('observacion', '')

        if not nuevo_estado:
            return Response(
                {'error': 'El campo estado es requerido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            empleado = Empleado.objects.get(email=request.user.email)
            enc.cambiar_estado(nuevo_estado, empleado, observacion)
            return Response(self.get_serializer(enc).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ── Accion: encomiendas con retraso ───────────────────────────────
    @extend_schema(
        summary='[v2] Encomiendas con retraso',
        description='Lista paginada de encomiendas activas cuya fecha estimada de entrega ya paso.',
        tags=['Encomiendas v2'],
    )
    @action(detail=False, methods=['get'], url_path='con_retraso')
    def con_retraso(self, request):
        qs   = Encomienda.objects.con_retraso().con_relaciones().order_by('codigo')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    # ── Accion: pendientes con paginacion (nueva en v2) ───────────────
    @extend_schema(
        summary='[v2] Encomiendas pendientes',
        description='Lista paginada de encomiendas en estado Pendiente, ordenadas por codigo.',
        tags=['Encomiendas v2'],
    )
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        qs   = Encomienda.objects.pendientes().con_relaciones().order_by('codigo')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    # ── Accion: historial (ultimos 10 en v2) ──────────────────────────
    @extend_schema(
        summary='[v2] Historial de estados',
        description='Historial de cambios de estado paginado. v2 muestra 10 registros por defecto.',
        tags=['Encomiendas v2'],
    )
    @action(detail=True, methods=['get'], url_path='historial')
    def historial(self, request, pk=None):
        enc       = self.get_object()
        qs        = enc.historial.select_related('empleado').order_by('-fecha_cambio')
        paginator = HistorialPagination()
        paginator.default_limit = 10   # v2: 10 registros; v1: 5
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                HistorialEstadoSerializer(page, many=True).data
            )
        return Response(HistorialEstadoSerializer(qs, many=True).data)

    # ── Accion: estadisticas extendidas (exclusiva de v2) ─────────────
    @extend_schema(
        summary='[v2] Estadisticas extendidas',
        description=(
            'Contadores globales del sistema mas distribucion de encomiendas por ruta. '
            'Endpoint exclusivo de v2.'
        ),
        tags=['Encomiendas v2'],
        responses={200: OpenApiResponse(description='Contadores y distribucion por ruta')},
    )
    @action(detail=False, methods=['get'], url_path='estadisticas_v2')
    def estadisticas_v2(self, request):
        hoy = timezone.now().date()

        # Distribucion por ruta: nuevo en v2
        distribucion_por_ruta = list(
            Ruta.objects
            .annotate(total_encomiendas=Count('encomiendas'))
            .values('codigo', 'origen', 'destino', 'total_encomiendas')
            .order_by('-total_encomiendas')
        )

        return Response({
            'version': 'v2',
            'generado': timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'totales': {
                'activas':        Encomienda.objects.activas().count(),
                'en_transito':    Encomienda.objects.en_transito().count(),
                'con_retraso':    Encomienda.objects.con_retraso().count(),
                'entregadas_hoy': Encomienda.objects.filter(
                    estado=EstadoEnvio.ENTREGADO,
                    fecha_entrega_real=hoy
                ).count(),
            },
            'distribucion_por_ruta': distribucion_por_ruta,
        })

    # ── Accion: bulk_create (disponible tambien en v2) ────────────────
    @extend_schema(
        summary='[v2] Crear multiples encomiendas',
        description='Crea varias encomiendas en una sola peticion. Body: lista de objetos.',
        tags=['Encomiendas v2'],
    )
    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            empleado = Empleado.objects.get(email=request.user.email)
        except Empleado.DoesNotExist:
            return Response(
                {'error': 'Usuario sin empleado asociado.'},
                status=status.HTTP_403_FORBIDDEN
            )
        encomiendas = serializer.save(empleado_registro=empleado)
        return Response(
            self.get_serializer(encomiendas, many=True).data,
            status=status.HTTP_201_CREATED
        )
