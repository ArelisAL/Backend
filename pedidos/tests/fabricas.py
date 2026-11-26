"""Datos ficticios compartidos por las pruebas de pedidos, clientes, pagos y
asignación (AGENTS.md §10.1: nunca datos reales)."""

from datetime import date, timedelta
from decimal import Decimal

from catalogo.models import CategoriaMedida, Prenda, PrendaMedida, TipoMedida
from clientes.models import Cliente
from pedidos.models import Pedido
from usuarios.models import Usuario

CONTRASENA = "Hilo-Morado-2026"


def crear_usuario(email: str, rol: str, **extra) -> Usuario:
    datos = {"nombre": rol.capitalize(), "debe_cambiar_contraseña": False}
    datos.update(extra)
    return Usuario.objects.create_user(
        email=email, password=CONTRASENA, rol=rol, **datos
    )


def crear_catalogo() -> dict:
    """Categoría MUJER con una prenda (1 obligatoria + 1 opcional) y BEBE."""
    mujer = CategoriaMedida.objects.create(nombre="MUJER")
    busto = TipoMedida.objects.create(
        codigo="contorno_busto",
        nombre="Contorno de busto",
        como_se_toma="Alrededor del busto.",
        categoria=mujer,
    )
    cintura = TipoMedida.objects.create(
        codigo="contorno_cintura",
        nombre="Contorno de cintura",
        como_se_toma="Alrededor de la cintura.",
        categoria=mujer,
    )
    blusa = Prenda.objects.create(codigo="blusas", nombre="Blusa", categoria=mujer)
    PrendaMedida.objects.create(prenda=blusa, tipo_medida=busto, opcional=False)
    PrendaMedida.objects.create(prenda=blusa, tipo_medida=cintura, opcional=True)

    hombre = CategoriaMedida.objects.create(nombre="HOMBRE")
    camisa = Prenda.objects.create(codigo="camisas", nombre="Camisa", categoria=hombre)

    bebe = CategoriaMedida.objects.create(nombre="BEBE")
    TipoMedida.objects.create(
        codigo="largo_total",
        nombre="Largo total",
        como_se_toma="De la cabeza a los pies.",
        categoria=bebe,
    )
    return {"mujer": mujer, "blusa": blusa, "camisa": camisa, "bebe": bebe}


def crear_cliente(nombre="Cliente ficticio", **extra) -> Cliente:
    return Cliente.objects.create(nombre=nombre, **extra)


def crear_pedido(codigo, cliente, prenda, total="0.00", **extra) -> Pedido:
    return Pedido.objects.create(
        codigo=codigo,
        cliente=cliente,
        prenda=prenda,
        fecha_entrega=date.today() + timedelta(days=7),
        total=Decimal(total),
        **extra,
    )
