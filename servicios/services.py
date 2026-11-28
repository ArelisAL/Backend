"""Operaciones del catálogo; las validaciones de negocio viven aquí."""

from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import HistorialServicio, Servicio


class DatosServicioInvalidos(Exception):
    """Los datos del servicio incumplen reglas del catálogo."""


class ServicioNoEncontrado(Exception):
    """No existe el servicio solicitado."""


def _normalizar(datos):
    normalizados = dict(datos)
    for campo in ("codigo", "nombre", "categoria", "unidad"):
        normalizados[campo] = normalizados.get(campo, "").strip()
        if not normalizados[campo]:
            raise DatosServicioInvalidos(f"El campo {campo} es obligatorio.")
    if "descripcion" in normalizados:
        normalizados["descripcion"] = normalizados["descripcion"].strip()
    tarifa = normalizados.get("tarifa_base")
    if tarifa is not None:
        if not isinstance(tarifa, Decimal):
            try:
                # Se convierte desde texto para no heredar imprecisión de float.
                tarifa = Decimal(str(tarifa))
            except (InvalidOperation, ValueError) as exc:
                raise DatosServicioInvalidos("La tarifa debe ser decimal.") from exc
        if not tarifa.is_finite() or tarifa < Decimal(0):
            raise DatosServicioInvalidos("La tarifa debe ser un valor no negativo.")
        if tarifa.quantize(Decimal("0.01")) != tarifa:
            raise DatosServicioInvalidos("La tarifa admite como máximo dos decimales.")
        normalizados["tarifa_base"] = tarifa
    return normalizados


def _validar_activacion(datos):
    if (
        datos.get("activo")
        and datos.get("tarifa_base") is None
        and not datos.get("requiere_valoracion", False)
    ):
        raise DatosServicioInvalidos(
            "No se puede activar: configura una tarifa o indica que requiere "
            "valoración manual. La tarifa sigue pendiente."
        )


def _instantanea(servicio):
    return {
        "codigo": servicio.codigo,
        "nombre": servicio.nombre,
        "categoria": servicio.categoria,
        "descripcion": servicio.descripcion,
        "unidad": servicio.unidad,
        "tarifa_base": (
            str(servicio.tarifa_base) if servicio.tarifa_base is not None else None
        ),
        "requiere_valoracion": servicio.requiere_valoracion,
        "activo": servicio.activo,
    }


@transaction.atomic
def crear_servicio(datos, usuario):
    datos = _normalizar(datos)
    _validar_activacion(datos)
    servicio = Servicio.objects.create(creado_por=usuario, **datos)
    HistorialServicio.objects.create(
        servicio=servicio,
        accion="CREADO",
        datos=_instantanea(servicio),
        usuario=usuario,
    )
    return servicio


@transaction.atomic
def editar_servicio(servicio_id, datos, usuario):
    servicio = Servicio.objects.select_for_update().filter(pk=servicio_id).first()
    if servicio is None:
        raise ServicioNoEncontrado
    cambios = _normalizar({**_instantanea(servicio), **datos})
    _validar_activacion(cambios)
    anterior = _instantanea(servicio)
    for campo in datos:
        setattr(servicio, campo, cambios[campo])
    servicio.save(update_fields=[*datos.keys(), "actualizado_en"])
    HistorialServicio.objects.create(
        servicio=servicio,
        accion="ACTUALIZADO",
        datos={"anterior": anterior, "nuevo": _instantanea(servicio)},
        usuario=usuario,
    )
    return servicio


def listar_servicios():
    return Servicio.objects.all()


def listar_servicios_cotizables():
    """Servicios activos con tarifa: los únicos que se pueden agregar a un pedido."""
    return Servicio.objects.filter(activo=True, tarifa_base__isnull=False)


def obtener_servicio(servicio_id):
    servicio = Servicio.objects.filter(pk=servicio_id).first()
    if servicio is None:
        raise ServicioNoEncontrado
    return servicio


def listar_historial(servicio_id):
    if not Servicio.objects.filter(pk=servicio_id).exists():
        raise ServicioNoEncontrado
    return HistorialServicio.objects.filter(servicio_id=servicio_id).select_related(
        "usuario"
    )
