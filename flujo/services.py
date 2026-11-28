"""Transiciones válidas e historial inmutable (DERCAS RF-09/RF-10)."""

from django.db import transaction

from inventario import services as inventario_services
from pagos import services as pagos_services
from pedidos import services as pedidos_services

from .models import HistorialEstado


class TransicionInvalida(Exception):
    """La transición solicitada no es el siguiente estado permitido."""


class EntregaConSaldo(Exception):
    """El pedido no se puede entregar mientras tenga saldo pendiente."""


def cambiar_estado(codigo: str, usuario, confirmar: bool):
    if not confirmar:
        raise TransicionInvalida("Confirma el cambio de estado para continuar.")
    with transaction.atomic():
        pedido = pedidos_services.obtener_pedido_bloqueado_por_codigo(codigo)
        if usuario.rol == "costurera" and pedido.costurera_id != usuario.pk:
            raise PermissionError("No puedes modificar un pedido ajeno.")
        nuevo = pedidos_services.siguiente_estado(pedido.estado)
        if nuevo is None:
            raise TransicionInvalida("El pedido ya fue entregado y no admite cambios.")
        # Decisión de la cliente (27/11/2026): la costurera avanza hasta TERMINADO
        # y solo la recepción (o la administradora) registra la entrega.
        if nuevo == "ENTREGADO" and usuario.rol == "costurera":
            raise PermissionError("La entrega del pedido la registra recepción.")
        if nuevo != "ENTREGADO" and usuario.rol == "recepcionista":
            raise PermissionError(
                "La recepcionista solo puede marcar el pedido como entregado."
            )
        if nuevo == "ENTREGADO":
            if pedido.total_cerrado_en is None:
                raise EntregaConSaldo(
                    "Cierra el total del pedido y registra el pago antes de entregar."
                )
            saldo = pagos_services.saldo_pedido(pedido)
            if saldo > 0:
                raise EntregaConSaldo(
                    f"El pedido tiene saldo pendiente de ${saldo:.2f}. "
                    "Registra el abono antes de entregar."
                )
        anterior = pedido.estado
        if nuevo == "EN_PROCESO":
            inventario_services.confirmar_consumos(pedido)
        pedido = pedidos_services.guardar_estado(pedido, nuevo)
        historial = HistorialEstado.objects.create(
            pedido=pedido,
            estado_anterior=anterior,
            estado_nuevo=nuevo,
            usuario=usuario,
        )
        return pedido, historial


def listar_historial(pedido):
    return HistorialEstado.objects.filter(pedido=pedido).select_related("usuario")
