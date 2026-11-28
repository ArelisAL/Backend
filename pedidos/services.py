"""Reglas de pedidos (DERCAS RF-04..08)."""

from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from catalogo import services as catalogo_services
from clientes import services as clientes_services

from .models import Pedido


class PedidoNoEncontrado(Exception):
    """El pedido no existe o no pertenece a la costurera."""


class DatosPedidoInvalidos(Exception):
    """Los datos no cumplen los criterios de pedido."""


class CodigoPedidoEnConflicto(Exception):
    """No se pudo reservar un código único."""


def _siguiente_codigo() -> str:
    mayor = 0
    for codigo in Pedido.objects.filter(codigo__startswith="FC-").values_list(
        "codigo", flat=True
    ):
        sufijo = codigo.removeprefix("FC-")
        if sufijo.isdigit():
            mayor = max(mayor, int(sufijo))
    return f"FC-{mayor + 1:04d}"


def crear_pedido(datos: dict) -> Pedido:
    try:
        cliente = clientes_services.obtener_cliente(datos["cliente"])
    except clientes_services.ClienteNoEncontrado:
        raise DatosPedidoInvalidos("El cliente seleccionado no existe.")
    try:
        prenda = catalogo_services.obtener_prenda(datos["prenda"])
    except catalogo_services.PrendaNoEncontrada:
        raise DatosPedidoInvalidos("La prenda seleccionada no existe en el catálogo.")
    fecha_entrega = datos["fecha_entrega"]
    if fecha_entrega < timezone.localdate():
        raise DatosPedidoInvalidos("La fecha de entrega no puede ser anterior a hoy.")

    for _ in range(3):
        try:
            with transaction.atomic():
                return Pedido.objects.create(
                    codigo=_siguiente_codigo(),
                    cliente=cliente,
                    prenda=prenda,
                    descripcion=datos.get("descripcion", "").strip(),
                    fecha_entrega=fecha_entrega,
                )
        except IntegrityError:
            if _ == 2:
                raise CodigoPedidoEnConflicto from None
    raise CodigoPedidoEnConflicto


def listar_pedidos(
    usuario,
    busqueda: str | None = None,
    incluir_entregados=False,
    estado: str | None = None,
):
    pedidos = Pedido.objects.select_related("cliente", "prenda", "costurera")
    if getattr(usuario, "rol", None) == "costurera":
        pedidos = pedidos.filter(costurera=usuario)
    if not incluir_entregados:
        pedidos = pedidos.exclude(estado=Pedido.ENTREGADO)
    if estado:
        pedidos = pedidos.filter(estado=estado)
    termino = (busqueda or "").strip()
    if termino:
        pedidos = pedidos.filter(
            Q(codigo__iexact=termino) | Q(cliente__nombre__icontains=termino)
        )
    return pedidos.order_by("fecha_entrega", "id")


def obtener_pedido_por_codigo(codigo: str, usuario) -> Pedido:
    pedido = (
        Pedido.objects.select_related("cliente", "prenda", "costurera")
        .filter(codigo__iexact=codigo)
        .first()
    )
    if pedido is None:
        raise PedidoNoEncontrado
    if (
        getattr(usuario, "rol", None) == "costurera"
        and pedido.costurera_id != usuario.pk
    ):
        raise PermissionError("No tienes permiso para consultar este pedido.")
    return pedido


def ultimas_medidas(pedido: Pedido):
    return clientes_services.ultima_medida(pedido.cliente_id, pedido.prenda_id)


def prendas_asignadas_de_cliente(costurera, cliente_id: int):
    return list(
        Pedido.objects.filter(cliente_id=cliente_id, costurera=costurera)
        .values_list("prenda_id", "prenda__categoria__nombre")
        .distinct()
    )


def puede_trabajar_con_medidas(
    costurera, cliente_id: int, prenda_id: int | None
) -> bool:
    pedidos = Pedido.objects.filter(cliente_id=cliente_id, costurera=costurera)
    if prenda_id is not None:
        pedidos = pedidos.filter(prenda_id=prenda_id)
    return pedidos.exists()


def cambiar_fecha_entrega(pedido: Pedido, fecha: date) -> Pedido:
    if fecha < timezone.localdate():
        raise DatosPedidoInvalidos("La fecha de entrega no puede ser anterior a hoy.")
    pedido.fecha_entrega = fecha
    pedido.save(update_fields=["fecha_entrega"])
    return pedido


def cambiar_nota_interna(pedido: Pedido, nota: str) -> Pedido:
    pedido.nota_interna = nota.strip()
    pedido.save(update_fields=["nota_interna"])
    return pedido


def obtener_pedido_bloqueado_por_codigo(codigo: str) -> Pedido:
    try:
        return Pedido.objects.select_for_update().get(codigo__iexact=codigo)
    except Pedido.DoesNotExist:
        raise PedidoNoEncontrado from None


def guardar_estado(pedido: Pedido, estado: str) -> Pedido:
    pedido.estado = estado
    if estado == Pedido.ENTREGADO:
        pedido.entregado_en = timezone.now()
    pedido.save(update_fields=["estado", "entregado_en"])
    return pedido


def siguiente_estado(estado: str) -> str | None:
    return {
        Pedido.PENDIENTE: Pedido.EN_PROCESO,
        Pedido.EN_PROCESO: Pedido.TERMINADO,
        Pedido.TERMINADO: Pedido.ENTREGADO,
    }.get(estado)


def asignar_costurera(pedido: Pedido, costurera) -> Pedido:
    if pedido.costurera_id is not None:
        raise DatosPedidoInvalidos("El pedido ya tiene una costurera asignada.")
    pedido.costurera = costurera
    pedido.save(update_fields=["costurera"])
    return pedido


# --- Servicios del pedido y cierre del total (auditoría C1) -----------------
# Decisión de la cliente (27/11/2026): el precio de cada prenda sale del
# catálogo de servicios y la recepcionista cierra el total cuando la clienta ya
# no tiene más prendas que añadir. Supuesto mientras A2.0 no defina impuestos,
# descuentos ni redondeo: total = suma de cantidad × tarifa, sin ajustes.


class TotalYaCerrado(Exception):
    """El total del pedido ya se cerró y no admite más cambios."""


def listar_servicios_pedido(pedido: Pedido):
    from .models import ServicioPedido

    return ServicioPedido.objects.filter(pedido=pedido).select_related("servicio")


def agregar_servicio_pedido(
    codigo: str, servicio_id: int, cantidad: int, detalle: str, usuario
):
    from servicios import services as servicios_services

    from .models import ServicioPedido

    if cantidad < 1:
        raise DatosPedidoInvalidos("La cantidad debe ser al menos 1.")
    try:
        servicio = servicios_services.obtener_servicio(servicio_id)
    except servicios_services.ServicioNoEncontrado:
        raise DatosPedidoInvalidos("El servicio no existe en el catálogo.") from None
    if not servicio.activo:
        raise DatosPedidoInvalidos("El servicio no está activo en el catálogo.")
    if servicio.tarifa_base is None:
        raise DatosPedidoInvalidos(
            "El servicio no tiene tarifa en el catálogo; pide a la administradora "
            "que la configure."
        )
    with transaction.atomic():
        pedido = obtener_pedido_bloqueado_por_codigo(codigo)
        if pedido.total_cerrado_en is not None:
            raise TotalYaCerrado("El total del pedido ya está cerrado.")
        return ServicioPedido.objects.create(
            pedido=pedido,
            servicio=servicio,
            cantidad=cantidad,
            precio_unitario=servicio.tarifa_base,
            detalle=(detalle or "").strip(),
            registrado_por=usuario,
        )


def quitar_servicio_pedido(codigo: str, linea_id: int) -> None:
    from .models import ServicioPedido

    with transaction.atomic():
        pedido = obtener_pedido_bloqueado_por_codigo(codigo)
        if pedido.total_cerrado_en is not None:
            raise TotalYaCerrado("El total del pedido ya está cerrado.")
        borradas, _ = ServicioPedido.objects.filter(pedido=pedido, pk=linea_id).delete()
        if not borradas:
            raise DatosPedidoInvalidos("La prenda no pertenece a este pedido.")


def cerrar_total(codigo: str, usuario) -> Pedido:
    from .models import ServicioPedido

    with transaction.atomic():
        pedido = obtener_pedido_bloqueado_por_codigo(codigo)
        if pedido.total_cerrado_en is not None:
            raise TotalYaCerrado("El total del pedido ya está cerrado.")
        lineas = list(ServicioPedido.objects.filter(pedido=pedido))
        if not lineas:
            raise DatosPedidoInvalidos(
                "Agrega al menos una prenda del catálogo antes de cerrar el total."
            )
        pedido.total = sum(
            (linea.precio_unitario * linea.cantidad for linea in lineas),
            start=Decimal("0.00"),
        )
        pedido.total_cerrado_en = timezone.now()
        pedido.total_cerrado_por = usuario
        pedido.save(update_fields=["total", "total_cerrado_en", "total_cerrado_por"])
        return pedido
