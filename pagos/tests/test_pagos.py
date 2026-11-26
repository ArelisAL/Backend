"""Pagos parciales, saldo y anulación (DERCAS RF-18, AGENTS.md §5)."""

from decimal import Decimal

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from pagos import services
from pagos.models import Pago
from pedidos import services as pedidos_services
from pedidos.tests.fabricas import (
    crear_catalogo,
    crear_cliente,
    crear_pedido,
    crear_usuario,
)
from usuarios.tests.conftest import ClientSeguro

pytestmark = pytest.mark.django_db


@pytest.fixture
def datos():
    catalogo = crear_catalogo()
    admin = crear_usuario("admin-pagos@fran-costuras.test", "administradora")
    recepcion = crear_usuario("recepcion-pagos@fran-costuras.test", "recepcionista")
    costurera = crear_usuario("costurera-pagos@fran-costuras.test", "costurera")
    pedido = crear_pedido("FC-0001", crear_cliente(), catalogo["blusa"], total="50.00")
    return {
        "admin": admin,
        "recepcion": recepcion,
        "costurera": costurera,
        "pedido": pedido,
    }


def _cliente_con_token(usuario):
    cliente = ClientSeguro()
    token = RefreshToken.for_user(usuario).access_token
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return cliente


# --- Servicios -----------------------------------------------------------


def test_pago_parcial_reduce_saldo(datos):
    pago, saldo = services.registrar_pago("FC-0001", "20.00", datos["recepcion"])
    assert pago.monto == Decimal("20.00")
    assert saldo == Decimal("30.00")
    assert services.saldo_pedido(datos["pedido"]) == Decimal("30.00")


def test_codigo_sin_distinguir_mayusculas(datos):
    _, saldo = services.registrar_pago("fc-0001", 10, datos["admin"])
    assert saldo == Decimal("40.00")


def test_pago_que_salda_deja_saldo_cero(datos):
    _, saldo = services.registrar_pago("FC-0001", "50.00", datos["recepcion"])
    assert saldo == Decimal("0.00")


@pytest.mark.parametrize(
    "monto", [0, "-5", "10.001", "abc", True, "NaN", "Infinity", None]
)
def test_monto_invalido_se_rechaza(datos, monto):
    with pytest.raises(services.PagoInvalido):
        services.registrar_pago("FC-0001", monto, datos["recepcion"])
    assert Pago.objects.count() == 0


def test_monto_mayor_al_saldo_se_rechaza(datos):
    with pytest.raises(services.PagoInvalido, match="supera el saldo"):
        services.registrar_pago("FC-0001", "50.01", datos["recepcion"])


def test_sin_saldo_pendiente_se_rechaza(datos):
    services.registrar_pago("FC-0001", "50.00", datos["recepcion"])
    with pytest.raises(services.PagoInvalido, match="no tiene saldo"):
        services.registrar_pago("FC-0001", "1.00", datos["recepcion"])


def test_pedido_inexistente(datos):
    with pytest.raises(pedidos_services.PedidoNoEncontrado):
        services.registrar_pago("FC-9999", "1.00", datos["recepcion"])


def test_anular_pago_lo_conserva_y_recupera_saldo(datos):
    pago, _ = services.registrar_pago("FC-0001", "20.00", datos["recepcion"])
    anulado, saldo = services.anular_pago(pago.pk, datos["admin"])
    assert anulado.anulado is True
    assert anulado.anulado_por == datos["admin"]
    assert saldo == Decimal("50.00")
    assert Pago.objects.filter(pk=pago.pk).exists()


def test_anular_dos_veces_se_rechaza(datos):
    pago, _ = services.registrar_pago("FC-0001", "20.00", datos["recepcion"])
    services.anular_pago(pago.pk, datos["admin"])
    with pytest.raises(services.PagoInvalido, match="ya está anulado"):
        services.anular_pago(pago.pk, datos["admin"])


def test_anular_pago_inexistente(datos):
    with pytest.raises(services.PagoNoEncontrado):
        services.anular_pago(999, datos["admin"])


def test_listar_pagos_incluye_anulados(datos):
    pago, _ = services.registrar_pago("FC-0001", "10.00", datos["recepcion"])
    services.registrar_pago("FC-0001", "5.00", datos["recepcion"])
    services.anular_pago(pago.pk, datos["admin"])
    pagos = list(services.listar_pagos("FC-0001", datos["admin"]))
    assert len(pagos) == 2
    assert services.saldo_pedido(datos["pedido"]) == Decimal("45.00")


# --- API: 401 / 403 ------------------------------------------------------


def test_api_sin_token_401(datos):
    respuesta = ClientSeguro().get("/api/v1/pedidos/FC-0001/pagos/")
    assert respuesta.status_code == 401


def test_api_recepcionista_registra_pago(datos):
    respuesta = _cliente_con_token(datos["recepcion"]).post(
        "/api/v1/pedidos/FC-0001/pagos/", {"monto": "12.50"}, format="json"
    )
    assert respuesta.status_code == 201, respuesta.json()
    assert respuesta.json()["saldo"] == "37.50"


def test_api_costurera_no_ve_pagos_403(datos):
    respuesta = _cliente_con_token(datos["costurera"]).get(
        "/api/v1/pedidos/FC-0001/pagos/"
    )
    assert respuesta.status_code == 403


def test_api_monto_excesivo_formato_error(datos):
    respuesta = _cliente_con_token(datos["admin"]).post(
        "/api/v1/pedidos/FC-0001/pagos/", {"monto": "80.00"}, format="json"
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"] == "pago_invalido"


def test_api_solo_administradora_anula(datos):
    pago, _ = services.registrar_pago("FC-0001", "10.00", datos["recepcion"])
    url = f"/api/v1/pagos/{pago.pk}/anular/"
    assert _cliente_con_token(datos["recepcion"]).post(url).status_code == 403
    respuesta = _cliente_con_token(datos["admin"]).post(url)
    assert respuesta.status_code == 200
    assert respuesta.json()["saldo"] == "50.00"
