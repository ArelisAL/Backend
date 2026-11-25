"""Vistas de inventario; reglas de stock en inventario.services."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from pedidos import services as pedidos_services

from . import services
from .permissions import EsAdministradora, EsPersonalTaller, PuedeRegistrarConsumos
from .serializers import (
    CrearTelaSerializer,
    EditarTelaSerializer,
    PaginaTelaOpcionConsumoSerializer,
    PaginaUsoTelaSerializer,
    RegistrarConsumosSerializer,
    TelaOpcionConsumoSerializer,
    TelaSerializer,
    UsoTelaSerializer,
)


def _error(codigo: str, detalle: str, estado: int) -> Response:
    return Response({"error": codigo, "detalle": detalle}, status=estado)


def _pagina(queryset, request, view):
    paginador = api_settings.DEFAULT_PAGINATION_CLASS()
    pagina = paginador.paginate_queryset(queryset, request, view=view)
    return paginador.get_paginated_response(TelaSerializer(pagina, many=True).data)


class TelaListView(APIView):
    permission_classes = [EsAdministradora]

    @extend_schema(responses={200: TelaSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return _pagina(services.listar_telas(), request, self)

    @extend_schema(
        request=CrearTelaSerializer,
        responses={
            201: TelaSerializer,
            400: OpenApiResponse(description="Datos de tela inválidos"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Solo administradora"),
        },
    )
    def post(self, request, *args, **kwargs):
        entrada = CrearTelaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            tela = services.crear_tela(entrada.validated_data)
        except services.DatosInventarioInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        return Response(TelaSerializer(tela).data, status=status.HTTP_201_CREATED)


class TelaStockBajoView(APIView):
    permission_classes = [EsAdministradora]

    @extend_schema(responses={200: TelaSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return _pagina(services.listar_telas_stock_bajo(), request, self)


class TelaOpcionesConsumoView(APIView):
    permission_classes = [PuedeRegistrarConsumos]

    @extend_schema(responses={200: PaginaTelaOpcionConsumoSerializer})
    def get(self, request, *args, **kwargs):
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(
            services.listar_telas(), request, view=self
        )
        return paginador.get_paginated_response(
            TelaOpcionConsumoSerializer(pagina, many=True).data
        )


class PedidoConsumosView(APIView):
    permission_classes = [EsPersonalTaller]

    def get_permissions(self):
        permiso = (
            PuedeRegistrarConsumos
            if self.request.method == "POST"
            else EsPersonalTaller
        )
        return [permiso()]

    @extend_schema(responses={200: PaginaUsoTelaSerializer})
    def get(self, request, codigo: str, *args, **kwargs):
        try:
            pedido = pedidos_services.obtener_pedido_por_codigo(codigo, request.user)
        except pedidos_services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except PermissionError as exc:
            return _error("sin_permiso", str(exc), status.HTTP_403_FORBIDDEN)
        usos = pedido.usos_tela.select_related(
            "tela", "registrado_por", "reemplazado_por"
        ).order_by("-fecha", "-id")
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(usos, request, view=self)
        return paginador.get_paginated_response(
            UsoTelaSerializer(pagina, many=True).data
        )

    @extend_schema(
        request=RegistrarConsumosSerializer,
        responses={
            200: UsoTelaSerializer(many=True),
            400: OpenApiResponse(description="Pedido o consumos inválidos"),
            401: OpenApiResponse(description="JWT ausente o inválido"),
            403: OpenApiResponse(description="Rol sin permiso"),
            404: OpenApiResponse(description="Pedido o tela inexistente"),
        },
    )
    def post(self, request, codigo: str, *args, **kwargs):
        entrada = RegistrarConsumosSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            pedido = pedidos_services.obtener_pedido_por_codigo(codigo, request.user)
            usos = services.registrar_consumos(
                pedido, entrada.validated_data["usos"], request.user
            )
        except pedidos_services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except PermissionError as exc:
            return _error("sin_permiso", str(exc), status.HTTP_403_FORBIDDEN)
        except services.DatosInventarioInvalidos as exc:
            return _error("consumos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        except services.TelaNoEncontrada:
            return _error(
                "no_encontrado",
                "Una tela no existe en inventario.",
                status.HTTP_404_NOT_FOUND,
            )
        return Response(UsoTelaSerializer(usos, many=True).data)


class TelaDetailView(APIView):
    permission_classes = [EsAdministradora]

    @extend_schema(responses={200: TelaSerializer})
    def get(self, request, tela_id: int, *args, **kwargs):
        try:
            tela = services.obtener_tela(tela_id)
        except services.TelaNoEncontrada:
            return _error(
                "no_encontrado", "La tela no existe.", status.HTTP_404_NOT_FOUND
            )
        return Response(TelaSerializer(tela).data)

    @extend_schema(
        request=EditarTelaSerializer,
        responses={
            200: TelaSerializer,
            400: OpenApiResponse(description="Datos de tela inválidos"),
            403: OpenApiResponse(description="Solo administradora"),
            404: OpenApiResponse(description="Tela inexistente"),
        },
    )
    def patch(self, request, tela_id: int, *args, **kwargs):
        entrada = EditarTelaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        try:
            tela = services.editar_tela(
                services.obtener_tela(tela_id), entrada.validated_data
            )
        except services.TelaNoEncontrada:
            return _error(
                "no_encontrado", "La tela no existe.", status.HTTP_404_NOT_FOUND
            )
        except services.DatosInventarioInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        return Response(TelaSerializer(tela).data)
