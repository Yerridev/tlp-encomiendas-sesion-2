from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiResponse, OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes

from .models import Encomienda, Empleado
from .serializers import (
    EncomiendaSerializer,
    EncomiendaListSerializer,
    EncomiendaDetailSerializer,
    EncomiendaV2Serializer,
    HistorialEstadoSerializer,
)
from api.pagination import EncomiendaPagination, HistorialPagination
from api.filters import EncomiendaFilter
from api.permissions import EsEmpleadoActivo, EsPropietarioOAdmin
from api.throttles import EmpleadoRateThrottle, CambioEstadoThrottle
from config.choices import EstadoEnvio


@extend_schema_view(
    list=extend_schema(
        summary='Listar encomiendas',
        description='Devuelve la lista paginada de encomiendas. Soporta filtros por estado, búsqueda y ordenamiento.',
        tags=['Encomiendas'],
    ),
    create=extend_schema(
        summary='Crear encomienda',
        description='Registra una nueva encomienda en el sistema.',
        tags=['Encomiendas'],
    ),
    retrieve=extend_schema(
        summary='Detalle de encomienda',
        description='Devuelve los datos completos de una encomienda con remitente, destinatario, ruta e historial.',
        tags=['Encomiendas'],
    ),
    update=extend_schema(summary='Actualizar encomienda',        tags=['Encomiendas']),
    partial_update=extend_schema(summary='Actualizar parcial',   tags=['Encomiendas']),
    destroy=extend_schema(summary='Eliminar encomienda',         tags=['Encomiendas']),
)
class EncomiendaViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet genera automáticamente:
      list()           → GET    /encomiendas/
      create()         → POST   /encomiendas/
      retrieve()       → GET    /encomiendas/{pk}/
      update()         → PUT    /encomiendas/{pk}/
      partial_update() → PATCH  /encomiendas/{pk}/
      destroy()        → DELETE /encomiendas/{pk}/
    """
    queryset           = Encomienda.objects.con_relaciones()
    permission_classes = [EsEmpleadoActivo]
    pagination_class   = EncomiendaPagination
    throttle_classes   = [EmpleadoRateThrottle]

    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = EncomiendaFilter
    search_fields    = ['codigo', 'remitente__apellidos', 'destinatario__apellidos', 'descripcion']
    ordering_fields  = ['fecha_registro', 'peso_kg', 'costo_envio']
    ordering         = ['-fecha_registro']

    # ── Serializer según versión y acción ─────────────────────────────
    def get_serializer_class(self):
        version = getattr(self.request, 'version', 'v1')
        if version == 'v2':
            return EncomiendaV2Serializer
        if self.action == 'list':
            return EncomiendaListSerializer
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        return EncomiendaSerializer

    # ── Permisos según acción ─────────────────────────────────────────
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [EsEmpleadoActivo(), EsPropietarioOAdmin()]
        return [EsEmpleadoActivo()]

    # ── Throttle según acción ─────────────────────────────────────────
    def get_throttles(self):
        if self.action == 'cambiar_estado':
            return [CambioEstadoThrottle()]
        return super().get_throttles()

    # ── QuerySet optimizado ───────────────────────────────────────────
    def get_queryset(self):
        qs = Encomienda.objects.con_relaciones()
        return qs

    def perform_create(self, serializer):
        serializer.save(empleado_registro=self.request.user.empleado)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response['X-API-Version'] = getattr(request, 'version', 'v1')
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response['X-API-Version'] = getattr(request, 'version', 'v1')
        return response

    # ── Acción: cambiar estado ────────────────────────────────────────
    @extend_schema(
        summary='Cambiar estado de encomienda',
        description='''
            Cambia el estado de una encomienda y registra el cambio en el historial.
            Estados disponibles: PE (Pendiente), TR (En tránsito), DE (En destino), EN (Entregado), DV (Devuelto).
        ''',
        request=OpenApiTypes.OBJECT,
        responses={
            200: EncomiendaSerializer,
            400: OpenApiResponse(description='Estado inválido o transición no permitida'),
        },
        examples=[
            OpenApiExample('Pasar a En tránsito',
                value={'estado': 'TR', 'observacion': 'Recogido en agencia Lima'},
                request_only=True),
            OpenApiExample('Marcar como Entregado',
                value={'estado': 'EN', 'observacion': 'Entregado al destinatario'},
                request_only=True),
        ],
        tags=['Encomiendas'],
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
            return Response(EncomiendaSerializer(enc).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ── Acción: encomiendas con retraso ───────────────────────────────
    @extend_schema(
        summary='Encomiendas con retraso',
        description='Lista todas las encomiendas activas cuya fecha estimada de entrega ya pasó.',
        tags=['Encomiendas'],
        responses={200: EncomiendaSerializer(many=True)},
    )
    @action(detail=False, methods=['get'], url_path='con_retraso')
    def con_retraso(self, request):
        qs = Encomienda.objects.con_retraso().con_relaciones()
        return Response(self.get_serializer(qs, many=True).data)

    # ── Acción: pendientes ────────────────────────────────────────────
    @extend_schema(
        summary='Encomiendas pendientes',
        description='Lista todas las encomiendas en estado Pendiente.',
        tags=['Encomiendas'],
    )
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        qs = Encomienda.objects.pendientes().con_relaciones()
        return Response(self.get_serializer(qs, many=True).data)

    # ── Acción: historial con paginación propia ───────────────────────
    @extend_schema(
        summary='Historial de estados',
        description='Devuelve el historial de cambios de estado de una encomienda, paginado con limit/offset.',
        parameters=[
            OpenApiParameter('limit',  type=int, description='Número de resultados', default=10),
            OpenApiParameter('offset', type=int, description='Posición de inicio',   default=0),
        ],
        tags=['Encomiendas'],
    )
    @action(detail=True, methods=['get'], url_path='historial')
    def historial(self, request, pk=None):
        enc  = self.get_object()
        qs   = enc.historial.select_related('empleado').order_by('-fecha_cambio')
        paginator = HistorialPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                HistorialEstadoSerializer(page, many=True).data
            )
        return Response(HistorialEstadoSerializer(qs, many=True).data)

    # ── Acción: estadísticas ──────────────────────────────────────────
    @extend_schema(
        summary='Estadísticas globales',
        description='Contadores del sistema: activas, en tránsito, con retraso y entregadas hoy.',
        tags=['Encomiendas'],
        responses={200: OpenApiResponse(description='Objeto con contadores')},
    )
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        hoy = timezone.now().date()
        return Response({
            'total_activas': Encomienda.objects.activas().count(),
            'en_transito':   Encomienda.objects.en_transito().count(),
            'con_retraso':   Encomienda.objects.con_retraso().count(),
            'entregadas_hoy': Encomienda.objects.filter(
                estado='EN', fecha_entrega_real=hoy
            ).count(),
        })

    # ── Acción: bulk_create ───────────────────────────────────────────
    @extend_schema(
        summary='Crear múltiples encomiendas',
        description='Crea varias encomiendas en una sola petición. Body: lista de objetos.',
        tags=['Encomiendas'],
    )
    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            empleado = Empleado.objects.get(email=request.user.email)
        except Empleado.DoesNotExist:
            return Response({'error': 'Usuario sin empleado asociado.'}, status=403)
        encomiendas = serializer.save(empleado_registro=empleado)
        return Response(
            self.get_serializer(encomiendas, many=True).data,
            status=status.HTTP_201_CREATED
        )

    # ── Acción: bulk_estado ───────────────────────────────────────────
    @extend_schema(
        summary='Cambiar estado a múltiples encomiendas',
        description='Cambia el estado de varias encomiendas. Reporta cuáles tuvieron errores.',
        tags=['Encomiendas'],
    )
    @action(detail=False, methods=['patch'], url_path='bulk_estado')
    def bulk_estado(self, request):
        ids          = request.data.get('ids', [])
        nuevo_estado = request.data.get('estado')
        observacion  = request.data.get('observacion', '')

        if not ids:
            return Response({'error': 'El campo ids es requerido.'}, status=400)
        if not nuevo_estado:
            return Response({'error': 'El campo estado es requerido.'}, status=400)

        try:
            empleado = Empleado.objects.get(email=request.user.email)
        except Empleado.DoesNotExist:
            return Response({'error': 'Usuario sin empleado asociado.'}, status=403)

        encomiendas    = Encomienda.objects.filter(id__in=ids)
        actualizadas   = []
        errores        = []

        for enc in encomiendas:
            try:
                enc.cambiar_estado(nuevo_estado, empleado, observacion)
                actualizadas.append(enc.id)
            except ValueError as e:
                errores.append({'id': enc.id, 'error': str(e)})

        ids_procesados = list(encomiendas.values_list('id', flat=True))
        no_encontrados = [i for i in ids if i not in ids_procesados]

        return Response({
            'actualizadas':   actualizadas,
            'errores':        errores,
            'no_encontrados': no_encontrados,
            'total':          len(actualizadas),
        })
