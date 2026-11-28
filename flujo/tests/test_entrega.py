"""Entrega del pedido: quién la marca y bloqueo por saldo (auditoría C2 y C3).

Decisiones de la cliente (27/11/2026):
- La costurera solo avanza PENDIENTE → EN_PROCESO → TERMINADO.
- «Entregado» lo marca la recepcionista.
- La entrega se bloquea si queda saldo pendiente.
"""

from decimal import Decimal

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from flujo.models import HistorialEstado
from pagos.models import Pago
from pedidos.models import Pedido
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
    return {
        "blusa": catalogo["blusa"],
        "cliente": crear_cliente("Clienta Ficticia"),
        "costurera": crear_usuario("cost-entrega@fran-costuras.test", "costurera"),
        "recepcion": crear_usuario("recep-entrega@fran-costuras.test", "recepcionista"),
        "admin": crear_usuario("admin-entrega@fran-costuras.test", "administradora"),
    }


def _pedido(datos, estado=Pedido.TERMINADO, total="0.00"):
    return crear_pedido(
        "FC-0001",
        datos["cliente"],
        datos["blusa"],
        total=total,
        costurera=datos["costurera"],
        estado=estado,
    )


def _avanzar(usuario, codigo="FC-0001"):
    cliente = ClientSeguro()
    cliente.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(usuario).access_token}"
    )
    return cliente.post(
        f"/api/v1/pedidos/{codigo}/estado/", {"confirmar": True}, format="json"
    )


def test_recepcionista_marca_entregado_sin_saldo(datos):
    _pedido(datos)
    respuesta = _avanzar(datos["recepcion"])
    assert respuesta.status_code == 200
    assert respuesta.json()["estado_nuevo"] == "ENTREGADO"
    pedido = Pedido.objects.get(codigo="FC-0001")
    assert pedido.estado == Pedido.ENTREGADO
    assert pedido.entregado_en is not None


def test_costurera_no_puede_marcar_entregado(datos):
    _pedido(datos)
    respuesta = _avanzar(datos["costurera"])
    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "sin_permiso"
    assert Pedido.objects.get(codigo="FC-0001").estado == Pedido.TERMINADO
    assert not HistorialEstado.objects.exists()


def test_costurera_sigue_avanzando_hasta_terminado(datos):
    _pedido(datos, estado=Pedido.EN_PROCESO)
    respuesta = _avanzar(datos["costurera"])
    assert respuesta.status_code == 200
    assert respuesta.json()["estado_nuevo"] == "TERMINADO"


def test_recepcionista_no_cambia_otros_estados(datos):
    _pedido(datos, estado=Pedido.EN_PROCESO)
    respuesta = _avanzar(datos["recepcion"])
    assert respuesta.status_code == 403
    assert Pedido.objects.get(codigo="FC-0001").estado == Pedido.EN_PROCESO


def test_entrega_bloqueada_con_saldo_pendiente(datos):
    pedido = _pedido(datos, total="85.00")
    Pago.objects.create(
        pedido=pedido, monto=Decimal("50.00"), registrado_por=datos["recepcion"]
    )
    respuesta = _avanzar(datos["recepcion"])
    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "saldo_pendiente"
    assert "35.00" in respuesta.json()["detalle"]
    assert Pedido.objects.get(codigo="FC-0001").estado == Pedido.TERMINADO
    assert not HistorialEstado.objects.exists()


def test_entrega_permitida_con_saldo_cero(datos):
    pedido = _pedido(datos, total="85.00")
    Pago.objects.create(
        pedido=pedido, monto=Decimal("85.00"), registrado_por=datos["recepcion"]
    )
    assert _avanzar(datos["recepcion"]).status_code == 200


def test_pago_anulado_no_cuenta_para_entregar(datos):
    pedido = _pedido(datos, total="85.00")
    Pago.objects.create(
        pedido=pedido,
        monto=Decimal("85.00"),
        registrado_por=datos["recepcion"],
        anulado=True,
    )
    assert _avanzar(datos["recepcion"]).status_code == 409


def test_administradora_conserva_la_entrega(datos):
    _pedido(datos)
    assert _avanzar(datos["admin"]).status_code == 200
