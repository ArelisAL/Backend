"""Clientes y tomas de medidas (DERCAS RF-01/RF-02, AGENTS.md §4.4 y §5)."""

import pytest

from clientes import services
from clientes.models import Medida
from pedidos.tests.fabricas import (
    crear_catalogo,
    crear_cliente,
    crear_pedido,
    crear_usuario,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogo():
    return crear_catalogo()


@pytest.fixture
def recepcion():
    return crear_usuario("rec-clientes@fran-costuras.test", "recepcionista")


# --- Clientes ------------------------------------------------------------


def test_crear_cliente_normaliza_contacto():
    cliente = services.crear_cliente(
        {
            "nombre": "  Ana Ficticia ",
            "telefono": " 0990000001 ",
            "correo": "ANA@X.TEST",
        }
    )
    assert cliente.nombre == "Ana Ficticia"
    assert cliente.telefono == "0990000001"
    assert cliente.correo == "ana@x.test"


def test_contacto_vacio_se_guarda_como_nulo():
    cliente = services.crear_cliente({"nombre": "Sin contacto", "telefono": "  "})
    assert cliente.telefono is None
    assert cliente.correo is None


def test_nombre_vacio_se_rechaza():
    with pytest.raises(services.DatosClienteInvalidos):
        services.crear_cliente({"nombre": "   "})


def test_telefono_duplicado_se_rechaza():
    services.crear_cliente({"nombre": "Uno", "telefono": "0990000002"})
    with pytest.raises(services.ClienteDuplicado):
        services.crear_cliente({"nombre": "Dos", "telefono": "0990000002"})


def test_correo_duplicado_sin_importar_mayusculas():
    services.crear_cliente({"nombre": "Uno", "correo": "uno@x.test"})
    with pytest.raises(services.ClienteDuplicado):
        services.crear_cliente({"nombre": "Dos", "correo": "UNO@X.TEST"})


def test_listar_y_buscar_clientes():
    services.crear_cliente({"nombre": "Beatriz", "telefono": "0991111111"})
    services.crear_cliente({"nombre": "Ana", "correo": "ana@x.test"})
    assert [c.nombre for c in services.listar_clientes()] == ["Ana", "Beatriz"]
    assert [c.nombre for c in services.listar_clientes("09911")] == ["Beatriz"]
    assert [c.nombre for c in services.listar_clientes("ANA@")] == ["Ana"]


def test_obtener_cliente_inexistente():
    with pytest.raises(services.ClienteNoEncontrado):
        services.obtener_cliente(999)


# --- Medidas -------------------------------------------------------------


def test_registrar_medida_de_prenda(catalogo, recepcion):
    cliente = crear_cliente()
    medida = services.registrar_medida(
        cliente,
        "MUJER",
        {"contorno_busto": "88.5"},
        recepcion,
        prenda_id=catalogo["blusa"].pk,
    )
    assert medida.valores_cm == {"contorno_busto": 88.5}


def test_cada_toma_es_un_registro_nuevo(catalogo, recepcion):
    cliente = crear_cliente()
    for valor in (88, 90):
        services.registrar_medida(
            cliente,
            "MUJER",
            {"contorno_busto": valor},
            recepcion,
            prenda_id=catalogo["blusa"].pk,
        )
    assert Medida.objects.filter(cliente=cliente).count() == 2
    ultima = services.ultima_medida(cliente.pk, catalogo["blusa"].pk)
    assert ultima.valores_cm == {"contorno_busto": 90.0}


@pytest.mark.parametrize(
    "valores, mensaje",
    [
        ({}, "obligatoria"),
        ({"contorno_busto": 0}, "mayor que 0"),
        ({"contorno_busto": "-3"}, "mayor que 0"),
        ({"contorno_busto": "88.55"}, "un decimal"),
        ({"contorno_busto": "abc"}, "número"),
        ({"contorno_busto": True}, "número"),
        ({"contorno_busto": 88, "largo_total": 50}, "no corresponde"),
    ],
)
def test_medidas_invalidas(catalogo, recepcion, valores, mensaje):
    with pytest.raises(services.DatosDeMedidaInvalidos, match=mensaje):
        services.registrar_medida(
            crear_cliente(),
            "MUJER",
            valores,
            recepcion,
            prenda_id=catalogo["blusa"].pk,
        )


def test_valores_deben_ser_objeto(catalogo, recepcion):
    with pytest.raises(services.DatosDeMedidaInvalidos, match="objeto"):
        services.registrar_medida(
            crear_cliente(),
            "MUJER",
            ["88"],
            recepcion,
            prenda_id=catalogo["blusa"].pk,
        )


def test_categoria_inexistente(catalogo, recepcion):
    with pytest.raises(services.DatosDeMedidaInvalidos, match="categoría no existe"):
        services.registrar_medida(crear_cliente(), "GIGANTE", {}, recepcion)


def test_prenda_inexistente(catalogo, recepcion):
    with pytest.raises(services.DatosDeMedidaInvalidos, match="prenda no existe"):
        services.registrar_medida(
            crear_cliente(), "MUJER", {}, recepcion, prenda_id=9999
        )


def test_prenda_de_otra_categoria(catalogo, recepcion):
    with pytest.raises(services.DatosDeMedidaInvalidos, match="no pertenece"):
        services.registrar_medida(
            crear_cliente(), "MUJER", {}, recepcion, prenda_id=catalogo["camisa"].pk
        )


def test_sin_prenda_solo_para_bebe(catalogo, recepcion):
    with pytest.raises(services.DatosDeMedidaInvalidos, match="Selecciona una prenda"):
        services.registrar_medida(crear_cliente(), "MUJER", {}, recepcion)
    medida = services.registrar_medida(
        crear_cliente(), "BEBE", {"largo_total": 55}, recepcion
    )
    assert medida.prenda is None


def test_listar_medidas_cliente_inexistente():
    with pytest.raises(services.ClienteNoEncontrado):
        services.listar_medidas(999)


def test_costurera_solo_ve_medidas_de_sus_prendas(catalogo, recepcion):
    cliente = crear_cliente()
    costurera = crear_usuario("cost-medidas@fran-costuras.test", "costurera")
    services.registrar_medida(
        cliente,
        "MUJER",
        {"contorno_busto": 88},
        recepcion,
        prenda_id=catalogo["blusa"].pk,
    )
    services.registrar_medida(cliente, "BEBE", {"largo_total": 50}, recepcion)
    assert services.listar_medidas(cliente.pk, costurera).count() == 0
    crear_pedido("FC-0001", cliente, catalogo["blusa"], costurera=costurera)
    visibles = services.listar_medidas(cliente.pk, costurera)
    assert [m.prenda_id for m in visibles] == [catalogo["blusa"].pk]
    assert services.listar_medidas(cliente.pk).count() == 2
