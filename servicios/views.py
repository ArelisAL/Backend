"""Endpoints del catálogo; permisos HTTP y delegación a servicios de dominio."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from . import services
from .permissions import EsAdministradora, EsAdministradoraORecepcionista
from .serializers import (
    HistorialServicioSerializer,
    PaginaHistorialServicioSerializer,
    PaginaServicioSerializer,
    ServicioCotizableSerializer,
    ServicioSerializer,
)


def _error(codigo, detalle, estado):
    return Response({"error": codigo, "detalle": detalle}, status=estado)


def _pagina(queryset, request, view, serializer):
    paginador = api_settings.DEFAULT_PAGINATION_CLASS()
    pagina = paginador.paginate_queryset(queryset, request, view=view)
    respuesta = serializer(pagina, many=True).data
    return paginador.get_paginated_response(respuesta)


class ServicioListView(APIView):
    permission_classes = [EsAdministradora]

    @extend_schema(
        operation_id="servicios_listar",
        responses={200: PaginaServicioSerializer},
    )
    def get(self, request, *args, **kwargs):
        return _pagina(services.listar_servicios(), request, self, ServicioSerializer)

    @extend_schema(
        request=ServicioSerializer,
        operation_id="servicios_crear",
        responses={
            201: ServicioSerializer,
            400: OpenApiResponse(description="Datos o configuración inválidos"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Solo administradora"),
        },
    )
    def post(self, request, *args, **kwargs):
        entrada = ServicioSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            servicio = services.crear_servicio(entrada.validated_data, request.user)
        except services.DatosServicioInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        return Response(
            ServicioSerializer(servicio).data, status=status.HTTP_201_CREATED
        )


class ServicioDetailView(APIView):
    permission_classes = [EsAdministradora]

    @extend_schema(operation_id="servicio_detalle", responses={200: ServicioSerializer})
    def get(self, request, servicio_id: int, *args, **kwargs):
        try:
            servicio = services.obtener_servicio(servicio_id)
        except services.ServicioNoEncontrado:
            return _error("no_encontrado", "El servicio no existe.", 404)
        return Response(ServicioSerializer(servicio).data)

    @extend_schema(
        request=ServicioSerializer,
        operation_id="servicio_editar",
        responses={
            200: ServicioSerializer,
            400: OpenApiResponse(description="Datos o configuración inválidos"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Solo administradora"),
            404: OpenApiResponse(description="Servicio inexistente"),
        },
    )
    def patch(self, request, servicio_id: int, *args, **kwargs):
        try:
            actual = services.obtener_servicio(servicio_id)
        except services.ServicioNoEncontrado:
            return _error("no_encontrado", "El servicio no existe.", 404)
        entrada = ServicioSerializer(actual, data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        try:
            servicio = services.editar_servicio(
                servicio_id, entrada.validated_data, request.user
            )
        except services.ServicioNoEncontrado:
            return _error("no_encontrado", "El servicio no existe.", 404)
        except services.DatosServicioInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        return Response(ServicioSerializer(servicio).data)


class ServicioHistorialView(APIView):
    permission_classes = [EsAdministradora]

    @extend_schema(
        operation_id="servicio_historial_listar",
        responses={200: PaginaHistorialServicioSerializer},
    )
    def get(self, request, servicio_id: int, *args, **kwargs):
        try:
            historial = services.listar_historial(servicio_id)
        except services.ServicioNoEncontrado:
            return _error("no_encontrado", "El servicio no existe.", 404)
        return _pagina(historial, request, self, HistorialServicioSerializer)


class ServicioCotizableListView(APIView):
    """Lectura para recepción: servicios activos con tarifa (sin datos internos)."""

    permission_classes = [EsAdministradoraORecepcionista]

    @extend_schema(
        operation_id="servicios_cotizables",
        responses={200: ServicioCotizableSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return _pagina(
            services.listar_servicios_cotizables(),
            request,
            self,
            ServicioCotizableSerializer,
        )
