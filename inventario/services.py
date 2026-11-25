"""Reglas de telas y descuento atómico al iniciar confección (RF-13/14)."""

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from pedidos.models import Pedido

from .models import Tela, UsoTela


class DatosInventarioInvalidos(Exception):
    """Datos de tela o consumo inválidos."""


class StockInsuficiente(Exception):
    """No hay metros suficientes para iniciar el pedido."""


class TelaNoEncontrada(Exception):
    """Una tela solicitada no está en inventario."""


def _decimal_positivo(valor, etiqueta: str) -> Decimal:
    if isinstance(valor, bool):
        raise DatosInventarioInvalidos(f"{etiqueta} debe ser numérico.")
    try:
        decimal = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise DatosInventarioInvalidos(
            f"{etiqueta} debe ser un número válido."
        ) from None
    if (
        not decimal.is_finite()
        or decimal <= 0
        or decimal.quantize(Decimal("0.01")) != decimal
    ):
        raise DatosInventarioInvalidos(
            f"{etiqueta} debe ser mayor que cero y usar hasta dos decimales."
        )
    return decimal


def listar_telas():
    return Tela.objects.all().order_by("nombre", "id")


def listar_telas_stock_bajo():
    return Tela.objects.filter(metros_disponibles__lte=F("stock_minimo")).order_by(
        "metros_disponibles", "nombre", "id"
    )


def crear_tela(datos: dict) -> Tela:
    metros = Decimal(str(datos["metros_disponibles"]))
    precio = _decimal_positivo(datos["precio_metro"], "El precio por metro")
    minimo = Decimal(str(datos.get("stock_minimo", 5)))
    if (
        not metros.is_finite()
        or metros < 0
        or metros.quantize(Decimal("0.01")) != metros
    ):
        raise DatosInventarioInvalidos(
            "Los metros disponibles no pueden ser negativos ni superar dos decimales."
        )
    if (
        not minimo.is_finite()
        or minimo < 0
        or minimo.quantize(Decimal("0.01")) != minimo
    ):
        raise DatosInventarioInvalidos(
            "El stock mínimo no puede ser negativo ni superar dos decimales."
        )
    return Tela.objects.create(
        nombre=datos["nombre"].strip(),
        color=datos["color"].strip(),
        metros_disponibles=metros,
        precio_metro=precio,
        proveedor=datos["proveedor"].strip(),
        stock_minimo=minimo,
    )


def obtener_tela(tela_id: int) -> Tela:
    tela = Tela.objects.filter(pk=tela_id).first()
    if tela is None:
        raise TelaNoEncontrada
    return tela


def editar_tela(tela: Tela, datos: dict) -> Tela:
    for campo in ("nombre", "color", "proveedor"):
        if campo in datos:
            setattr(tela, campo, datos[campo].strip())
    if "metros_disponibles" in datos:
        try:
            metros = Decimal(str(datos["metros_disponibles"]))
        except (InvalidOperation, ValueError):
            raise DatosInventarioInvalidos(
                "Los metros disponibles deben ser un número válido."
            ) from None
        if (
            not metros.is_finite()
            or metros < 0
            or metros.quantize(Decimal("0.01")) != metros
        ):
            raise DatosInventarioInvalidos(
                "Los metros disponibles no pueden ser negativos ni superar dos decimales."
            )
        tela.metros_disponibles = metros
    if "precio_metro" in datos:
        tela.precio_metro = _decimal_positivo(
            datos["precio_metro"], "El precio por metro"
        )
    if "stock_minimo" in datos:
        try:
            minimo = Decimal(str(datos["stock_minimo"]))
        except (InvalidOperation, ValueError):
            raise DatosInventarioInvalidos(
                "El stock mínimo debe ser un número válido."
            ) from None
        if (
            not minimo.is_finite()
            or minimo < 0
            or minimo.quantize(Decimal("0.01")) != minimo
        ):
            raise DatosInventarioInvalidos(
                "El stock mínimo no puede ser negativo ni superar dos decimales."
            )
        tela.stock_minimo = minimo
    tela.save()
    return tela


def registrar_consumos(pedido, usos: list[dict], usuario) -> list[UsoTela]:
    """Guarda el consumo propuesto sin descontar stock; recepción o admin."""
    if getattr(usuario, "rol", None) not in {"administradora", "recepcionista"}:
        raise PermissionError(
            "Solo administración o recepción puede registrar consumos."
        )
    if pedido.estado != "PENDIENTE":
        raise DatosInventarioInvalidos(
            "Los consumos solo se pueden registrar mientras el pedido está pendiente."
        )
    if not usos:
        raise DatosInventarioInvalidos("Indica al menos una tela y sus metros usados.")

    requeridos: dict[int, Decimal] = {}
    for uso in usos:
        tela_id = uso.get("tela")
        if isinstance(tela_id, bool) or not isinstance(tela_id, int) or tela_id < 1:
            raise DatosInventarioInvalidos("Cada uso debe indicar una tela válida.")
        metros = _decimal_positivo(uso.get("metros_usados"), "Los metros usados")
        requeridos[tela_id] = requeridos.get(tela_id, Decimal(0)) + metros

    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
        if pedido.estado != "PENDIENTE":
            raise DatosInventarioInvalidos(
                "Los consumos solo se pueden registrar mientras el pedido está pendiente."
            )
        telas = {
            tela.pk: tela for tela in Tela.objects.filter(pk__in=sorted(requeridos))
        }
        if len(telas) != len(requeridos):
            raise TelaNoEncontrada
        existentes = UsoTela.objects.select_for_update().filter(
            pedido=pedido, vigente=True
        )
        if existentes.filter(confirmado=True).exists():
            raise DatosInventarioInvalidos(
                "El consumo ya fue confirmado y no se puede modificar."
            )
        existentes.filter(confirmado=False).update(
            vigente=False, reemplazado_por=usuario, reemplazado_en=timezone.now()
        )
        return [
            UsoTela.objects.create(
                pedido=pedido,
                tela=telas[tela_id],
                metros_usados=metros,
                registrado_por=usuario,
            )
            for tela_id, metros in requeridos.items()
        ]


def confirmar_consumos(pedido) -> list[UsoTela]:
    """Descuenta atómicamente los consumos guardados al iniciar producción."""
    consumos = list(
        UsoTela.objects.select_for_update()
        .filter(pedido=pedido, confirmado=False, vigente=True)
        .order_by("tela_id", "id")
    )
    if not consumos:
        raise DatosInventarioInvalidos(
            "Recepción debe registrar los consumos antes de iniciar el pedido."
        )

    requeridos: dict[int, Decimal] = {}
    for consumo in consumos:
        requeridos[consumo.tela_id] = (
            requeridos.get(consumo.tela_id, Decimal(0)) + consumo.metros_usados
        )
    telas = {
        tela.pk: tela
        for tela in Tela.objects.select_for_update()
        .filter(pk__in=sorted(requeridos))
        .order_by("pk")
    }
    for tela_id, metros in requeridos.items():
        if tela_id not in telas:
            raise TelaNoEncontrada
        if telas[tela_id].metros_disponibles < metros:
            raise StockInsuficiente(
                f"Stock insuficiente de {telas[tela_id].nombre}: disponibles {telas[tela_id].metros_disponibles} m, solicitados {metros} m."
            )
    for tela_id, metros in requeridos.items():
        tela = telas[tela_id]
        tela.metros_disponibles -= metros
        tela.save(update_fields=["metros_disponibles"])
    UsoTela.objects.filter(pk__in=[item.pk for item in consumos]).update(
        confirmado=True
    )
    return consumos
