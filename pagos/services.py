"""Reglas de pagos parciales y saldos (DERCAS RF-18)."""

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum

from pedidos import services as pedidos_services

from .models import Pago


class PagoInvalido(Exception):
    """El pago no cumple las reglas de saldo."""


class PagoNoEncontrado(Exception):
    """El pago solicitado no existe."""


def _monto_positivo(valor) -> Decimal:
    if isinstance(valor, bool):
        raise PagoInvalido("El monto debe ser numérico.")
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise PagoInvalido("El monto debe ser un número válido.") from None
    if not monto.is_finite() or monto <= 0 or monto.quantize(Decimal("0.01")) != monto:
        raise PagoInvalido(
            "El monto debe ser mayor que cero y tener hasta dos decimales."
        )
    return monto


def saldo_pedido(pedido) -> Decimal:
    pagado = Pago.objects.filter(pedido=pedido, anulado=False).aggregate(
        total=Sum("monto")
    )["total"] or Decimal("0.00")
    return pedido.total - pagado


def listar_pagos(codigo: str, usuario):
    pedido = pedidos_services.obtener_pedido_por_codigo(codigo, usuario)
    return Pago.objects.filter(pedido=pedido).select_related(
        "registrado_por", "anulado_por"
    )


def registrar_pago(codigo: str, monto, usuario) -> tuple[Pago, Decimal]:
    monto = _monto_positivo(monto)
    with transaction.atomic():
        pedido = pedidos_services.obtener_pedido_bloqueado_por_codigo(codigo)
        saldo = saldo_pedido(pedido)
        if saldo <= 0:
            raise PagoInvalido("El pedido no tiene saldo pendiente.")
        if monto > saldo:
            raise PagoInvalido("El monto supera el saldo pendiente del pedido.")
        pago = Pago.objects.create(pedido=pedido, monto=monto, registrado_por=usuario)
        return pago, saldo - monto


def anular_pago(pago_id: int, usuario) -> tuple[Pago, Decimal]:
    with transaction.atomic():
        referencia = Pago.objects.select_related("pedido").filter(pk=pago_id).first()
        if referencia is None:
            raise PagoNoEncontrado
        pedido = pedidos_services.obtener_pedido_bloqueado_por_codigo(
            referencia.pedido.codigo
        )
        pago = Pago.objects.select_for_update().filter(pk=pago_id).first()
        if pago is None:
            raise PagoNoEncontrado
        if pago.anulado:
            raise PagoInvalido("El pago ya está anulado.")
        pago.anulado = True
        pago.anulado_por = usuario
        pago.save(update_fields=["anulado", "anulado_por"])
        return pago, saldo_pedido(pedido)
