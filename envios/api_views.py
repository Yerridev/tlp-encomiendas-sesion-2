"""
Vistas de la API para el sistema de encomiendas.
Incluye FBV con @api_view, CBV con APIView y Generic Views.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

from .models import Encomienda
from clientes.models import Cliente
from rutas.models import Ruta
from .serializers import (
    EncomiendaSerializer, EncomiendaDetailSerializer,
    ClienteSerializer, RutaSerializer,
)
from api.pagination import ClientePagination


# ──────────────────────────────────────────────────────────────────────
# FBV con @api_view  (5.2.2)
# ──────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def encomienda_list(request):
    if request.method == 'GET':
        qs = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(
            qs, many=True, context={'request': request}
        )
        return Response(serializer.data)

    serializer = EncomiendaSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save(empleado_registro=request.user.empleado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def encomienda_detail(request, pk):
    enc = get_object_or_404(Encomienda, pk=pk)

    if request.method == 'GET':
        return Response(EncomiendaSerializer(enc).data)

    if request.method in ['PUT', 'PATCH']:
        s = EncomiendaSerializer(
            enc, data=request.data,
            partial=(request.method == 'PATCH'),
            context={'request': request}
        )
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    enc.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────
# CBV con APIView  (5.3)
# ──────────────────────────────────────────────────────────────────────

class EncomiendaListAPIView(APIView):
    """GET /api/v1/encomiendas/   POST /api/v1/encomiendas/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(
            qs, many=True, context={'request': request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = EncomiendaSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(empleado_registro=request.user.empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EncomiendaDetailAPIView(APIView):
    """GET/PUT/PATCH/DELETE /api/v1/encomiendas/{pk}/"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)

    def get(self, request, pk):
        return Response(EncomiendaDetailSerializer(self.get_object(pk)).data)

    def put(self, request, pk):
        enc = self.get_object(pk)
        s = EncomiendaSerializer(
            enc, data=request.data, context={'request': request}
        )
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        enc = self.get_object(pk)
        s = EncomiendaSerializer(
            enc, data=request.data, partial=True, context={'request': request}
        )
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────
# Generic Views  (5.5)
# ──────────────────────────────────────────────────────────────────────

@extend_schema(
    summary='Listar clientes activos',
    description='Devuelve todos los clientes con estado Activo, paginados de 20 en 20.',
    tags=['Clientes'],
)
class ClienteListView(generics.ListAPIView):
    serializer_class   = ClienteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = ClientePagination

    def get_queryset(self):
        return Cliente.objects.activos()


@extend_schema(
    summary='Listar rutas activas',
    description='Devuelve todas las rutas con estado Activo. Sin paginación.',
    tags=['Rutas'],
)
class RutaListView(generics.ListAPIView):
    serializer_class   = RutaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = None

    def get_queryset(self):
        return Ruta.objects.activas()
