"""Reglas para asignar pedidos a costureras (DERCAS RF-11)."""

from django.db import transaction

from pedidos import services as pedidos_services
from usuarios import services as usuarios_services


class AsignacionInvalidas(Exception):
    """Pedido o costurera no disponibles para asignación."""


def asignar_pedido(codigo: str, costurera_id: int):
    costurera = usuarios_services.obtener_costurera_activa(costurera_id)
    if costurera is None:
        raise AsignacionInvalidas("Selecciona una costurera activa.")
    with transaction.atomic():
        try:
            pedido = pedidos_services.obtener_pedido_bloqueado_por_codigo(codigo)
        except pedidos_services.PedidoNoEncontrado:
            raise AsignacionInvalidas("El pedido no existe.") from None
        try:
            return pedidos_services.asignar_costurera(pedido, costurera)
        except pedidos_services.DatosPedidoInvalidos as exc:
            raise AsignacionInvalidas(str(exc)) from exc
