"""Reglas de clientes y tomas de medidas (DERCAS RF-01/RF-02)."""

from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.db.models import Q

from catalogo import services as catalogo_services

from .models import Cliente, Medida


class ClienteDuplicado(Exception):
    """El teléfono o el correo ya pertenece a otro cliente."""


class ClienteNoEncontrado(Exception):
    """No existe el cliente solicitado."""


class DatosClienteInvalidos(Exception):
    """Los datos del cliente no cumplen el contrato de registro."""


class DatosDeMedidaInvalidos(Exception):
    """La categoría, prenda o valores no coinciden con el catálogo."""


def _normalizar_contacto(valor: str | None) -> str | None:
    limpio = (valor or "").strip()
    return limpio or None


def crear_cliente(datos: dict) -> Cliente:
    nombre = datos["nombre"].strip()
    if not nombre:
        raise DatosClienteInvalidos("El nombre del cliente es obligatorio.")
    telefono = _normalizar_contacto(datos.get("telefono"))
    correo = _normalizar_contacto(datos.get("correo"))
    if correo:
        correo = correo.lower()

    if telefono and Cliente.objects.filter(telefono=telefono).exists():
        raise ClienteDuplicado("Cliente ya registrado")
    if correo and Cliente.objects.filter(correo__iexact=correo).exists():
        raise ClienteDuplicado("Cliente ya registrado")

    try:
        with transaction.atomic():
            return Cliente.objects.create(
                nombre=nombre,
                telefono=telefono,
                correo=correo,
            )
    except IntegrityError as exc:
        # También cubre una colisión concurrente protegida por UNIQUE en BD.
        if (telefono and Cliente.objects.filter(telefono=telefono).exists()) or (
            correo and Cliente.objects.filter(correo__iexact=correo).exists()
        ):
            raise ClienteDuplicado("Cliente ya registrado") from exc
        raise


def listar_clientes(busqueda: str | None = None):
    clientes = Cliente.objects.all()
    termino = (busqueda or "").strip()
    if termino:
        clientes = clientes.filter(
            Q(nombre__icontains=termino)
            | Q(telefono__icontains=termino)
            | Q(correo__icontains=termino)
        )
    return clientes.order_by("nombre", "id")


def obtener_cliente(cliente_id: int) -> Cliente:
    cliente = Cliente.objects.filter(pk=cliente_id).first()
    if cliente is None:
        raise ClienteNoEncontrado
    return cliente


def listar_medidas(cliente_id: int, costurera=None):
    if not Cliente.objects.filter(pk=cliente_id).exists():
        raise ClienteNoEncontrado
    medidas = Medida.objects.filter(cliente_id=cliente_id)
    if costurera is not None:
        from pedidos import services as pedidos_services

        asignadas = pedidos_services.prendas_asignadas_de_cliente(costurera, cliente_id)
        ids_prendas = [prenda_id for prenda_id, _ in asignadas]
        consulta = Q(prenda_id__in=ids_prendas)
        if any(categoria == "BEBE" for _, categoria in asignadas):
            consulta |= Q(categoria__nombre="BEBE", prenda__isnull=True)
        medidas = medidas.filter(consulta)
    return medidas.select_related("categoria", "prenda", "tomada_por")


def ultima_medida(cliente_id: int, prenda_id: int):
    return (
        Medida.objects.filter(cliente_id=cliente_id, prenda_id=prenda_id)
        .select_related("categoria")
        .order_by("-fecha", "-id")
        .first()
    )


def _normalizar_valor_cm(codigo: str, valor) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (str, int, float, Decimal)):
        raise DatosDeMedidaInvalidos(
            f"La medida {codigo} debe ser un número mayor que 0 con hasta un decimal."
        )
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise DatosDeMedidaInvalidos(
            f"La medida {codigo} debe ser un número mayor que 0 con hasta un decimal."
        ) from None
    if not numero.is_finite() or numero <= 0 or (numero * 10) % 1:
        raise DatosDeMedidaInvalidos(
            f"La medida {codigo} debe ser mayor que 0 y tener hasta un decimal."
        )
    return float(numero)


def registrar_medida(
    cliente: Cliente,
    categoria_codigo: str,
    valores_cm: dict,
    tomada_por,
    prenda_id: int | None = None,
) -> Medida:
    categoria = catalogo_services.obtener_categoria(categoria_codigo)
    if categoria is None:
        raise DatosDeMedidaInvalidos("La categoría no existe en el catálogo.")

    prenda = None
    if prenda_id is not None:
        try:
            prenda = catalogo_services.obtener_prenda(prenda_id)
        except catalogo_services.PrendaNoEncontrada:
            raise DatosDeMedidaInvalidos(
                "La prenda no existe en el catálogo."
            ) from None
        if prenda.categoria_id != categoria.id:
            raise DatosDeMedidaInvalidos(
                "La prenda no pertenece a la categoría seleccionada."
            )
        requeridas = catalogo_services.listar_medidas_prenda(prenda.id)
        permitidas = {item.tipo_medida.codigo: item for item in requeridas}
        obligatorias = {
            item.tipo_medida.codigo for item in requeridas if not item.opcional
        }
    else:
        if categoria_codigo != "BEBE":
            raise DatosDeMedidaInvalidos("Selecciona una prenda para esta categoría.")
        permitidas = {
            tipo.codigo: tipo
            for tipo in catalogo_services.obtener_tipos_categoria(categoria_codigo)
        }
        obligatorias = set(permitidas)

    if not isinstance(valores_cm, dict):
        raise DatosDeMedidaInvalidos("Envía las medidas como un objeto por código.")
    recibidas = set(valores_cm)
    desconocidas = recibidas - set(permitidas)
    if desconocidas:
        codigo = min(str(item) for item in desconocidas)
        raise DatosDeMedidaInvalidos(
            f"La medida {codigo} no corresponde a la prenda y categoría seleccionadas."
        )
    faltantes = obligatorias - recibidas
    if faltantes:
        codigo = min(faltantes)
        raise DatosDeMedidaInvalidos(f"La medida {codigo} es obligatoria.")

    valores_normalizados = {
        codigo: _normalizar_valor_cm(codigo, valor)
        for codigo, valor in valores_cm.items()
    }
    with transaction.atomic():
        return Medida.objects.create(
            cliente=cliente,
            categoria=categoria,
            prenda=prenda,
            valores_cm=valores_normalizados,
            tomada_por=tomada_por,
        )
