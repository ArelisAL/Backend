"""Endpoints REST de abonos y saldos; reglas en pagos.services."""

import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from pedidos import services as pedidos_services

from . import services
from .permissions import EsAdministradora, PuedeRegistrarPago
from .serializers import (
    CrearPagoSerializer,
    PaginaPagosSerializer,
    PagoConSaldoSerializer,
    PagoSerializer,
)

logger = logging.getLogger("pagos")


def _error(codigo, detalle, estado):
    return Response({"error": codigo, "detalle": detalle}, status=estado)


def _respuesta_pago(pago, saldo):
    data = PagoConSaldoSerializer(pago).data
    data["saldo"] = str(saldo)
    return data


class PagosPedidoView(APIView):
    permission_classes = [PuedeRegistrarPago]

    @extend_schema(
        responses={
            200: PaginaPagosSerializer,
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Rol sin permiso"),
            404: OpenApiResponse(description="Pedido inexistente"),
        }
    )
    def get(self, request, codigo):
        try:
            pedido = pedidos_services.obtener_pedido_por_codigo(codigo, request.user)
        except pedidos_services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        queryset = services.listar_pagos(codigo, request.user)
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(queryset, request, view=self)
        respuesta = paginador.get_paginated_response(
            PagoSerializer(pagina, many=True).data
        )
        respuesta.data["saldo"] = str(services.saldo_pedido(pedido))
        return respuesta

    @extend_schema(
        request=CrearPagoSerializer,
        responses={
            201: PagoConSaldoSerializer,
            400: OpenApiResponse(description="Monto inválido o superior al saldo"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Rol sin permiso"),
            404: OpenApiResponse(description="Pedido inexistente"),
        },
    )
    def post(self, request, codigo):
        entrada = CrearPagoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            pago, saldo = services.registrar_pago(
                codigo, entrada.validated_data["monto"], request.user
            )
        except pedidos_services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except services.PagoInvalido as exc:
            return _error("pago_invalido", str(exc), status.HTTP_400_BAD_REQUEST)
        logger.info(
            "Pago %s registrado para pedido %s por usuario %s",
            pago.pk,
            pago.pedido.codigo,
            request.user.pk,
        )
        return Response(_respuesta_pago(pago, saldo), status=status.HTTP_201_CREATED)


class AnularPagoView(APIView):
    permission_classes = [EsAdministradora]

    @extend_schema(
        request=None,
        responses={
            200: PagoConSaldoSerializer,
            400: OpenApiResponse(description="Pago ya anulado"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Solo administradora"),
            404: OpenApiResponse(description="Pago inexistente"),
        },
    )
    def post(self, request, pago_id):
        try:
            pago, saldo = services.anular_pago(pago_id, request.user)
        except services.PagoNoEncontrado:
            return _error(
                "no_encontrado", "El pago no existe.", status.HTTP_404_NOT_FOUND
            )
        except services.PagoInvalido as exc:
            return _error("pago_invalido", str(exc), status.HTTP_400_BAD_REQUEST)
        logger.info("Pago %s anulado por usuario %s", pago.pk, request.user.pk)
        return Response(_respuesta_pago(pago, saldo))
