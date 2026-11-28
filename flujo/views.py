"""Vistas del flujo: autenticación, dueño del pedido y llamada a servicios."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from inventario import services as inventario_services
from pedidos import services as pedidos_services

from . import services
from .permissions import EsPersonalTaller, PuedeCambiarEstado
from .serializers import ConfirmarCambioEstadoSerializer, HistorialEstadoSerializer


def _error(codigo: str, detalle: str, estado: int) -> Response:
    return Response({"error": codigo, "detalle": detalle}, status=estado)


class PedidoEstadoView(APIView):
    permission_classes = [PuedeCambiarEstado]

    @extend_schema(
        request=ConfirmarCambioEstadoSerializer,
        responses={
            200: HistorialEstadoSerializer,
            400: OpenApiResponse(description="Transición inválida o sin confirmar"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(
                description="Pedido ajeno o transición no permitida para el rol"
            ),
            404: OpenApiResponse(description="Pedido inexistente"),
            409: OpenApiResponse(
                description="Stock insuficiente o entrega con saldo pendiente"
            ),
        },
    )
    def post(self, request, codigo: str, *args, **kwargs):
        entrada = ConfirmarCambioEstadoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            pedidos_services.obtener_pedido_por_codigo(codigo, request.user)
            _, historial = services.cambiar_estado(
                codigo,
                request.user,
                entrada.validated_data["confirmar"],
            )
        except pedidos_services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except PermissionError as exc:
            return _error("sin_permiso", str(exc), status.HTTP_403_FORBIDDEN)
        except services.TransicionInvalida as exc:
            return _error("transicion_invalida", str(exc), status.HTTP_400_BAD_REQUEST)
        except services.EntregaConSaldo as exc:
            return _error("saldo_pendiente", str(exc), status.HTTP_409_CONFLICT)
        except inventario_services.StockInsuficiente as exc:
            return _error("stock_insuficiente", str(exc), status.HTTP_409_CONFLICT)
        except inventario_services.DatosInventarioInvalidos as exc:
            return _error("usos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        except inventario_services.TelaNoEncontrada:
            return _error(
                "no_encontrado",
                "Una tela no existe en inventario.",
                status.HTTP_404_NOT_FOUND,
            )
        return Response(HistorialEstadoSerializer(historial).data)


class PedidoHistorialView(APIView):
    permission_classes = [EsPersonalTaller]

    @extend_schema(responses={200: HistorialEstadoSerializer(many=True)})
    def get(self, request, codigo: str, *args, **kwargs):
        try:
            pedido = pedidos_services.obtener_pedido_por_codigo(codigo, request.user)
            historial = services.listar_historial(pedido)
        except pedidos_services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except PermissionError as exc:
            return _error("sin_permiso", str(exc), status.HTTP_403_FORBIDDEN)
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(historial, request, view=self)
        return paginador.get_paginated_response(
            HistorialEstadoSerializer(pagina, many=True).data
        )
