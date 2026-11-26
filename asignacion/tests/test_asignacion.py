"""Asignación de pedidos a costureras (DERCAS RF-11)."""

import pytest

from asignacion import services
from pedidos.tests.fabricas import (
    crear_catalogo,
    crear_cliente,
    crear_pedido,
    crear_usuario,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def datos():
    catalogo = crear_catalogo()
    pedido = crear_pedido("FC-0001", crear_cliente(), catalogo["blusa"])
    costurera = crear_usuario("costurera-asig@fran-costuras.test", "costurera")
    return {"pedido": pedido, "costurera": costurera}


def test_asigna_costurera_activa(datos):
    pedido = services.asignar_pedido("FC-0001", datos["costurera"].pk)
    assert pedido.costurera == datos["costurera"]


def test_no_reasigna_pedido_ya_asignado(datos):
    services.asignar_pedido("FC-0001", datos["costurera"].pk)
    otra = crear_usuario("otra-costurera@fran-costuras.test", "costurera")
    with pytest.raises(services.AsignacionInvalidas, match="ya tiene"):
        services.asignar_pedido("FC-0001", otra.pk)


def test_costurera_inactiva_se_rechaza(datos):
    inactiva = crear_usuario("inactiva@fran-costuras.test", "costurera", activo=False)
    with pytest.raises(services.AsignacionInvalidas, match="costurera activa"):
        services.asignar_pedido("FC-0001", inactiva.pk)


def test_usuario_que_no_es_costurera_se_rechaza(datos):
    recepcion = crear_usuario("rec-asig@fran-costuras.test", "recepcionista")
    with pytest.raises(services.AsignacionInvalidas):
        services.asignar_pedido("FC-0001", recepcion.pk)


def test_pedido_inexistente(datos):
    with pytest.raises(services.AsignacionInvalidas, match="no existe"):
        services.asignar_pedido("FC-9999", datos["costurera"].pk)
