"""Prendas del pedido desde el catálogo y cierre del total (auditoría C1).

Decisiones de la cliente (27/11/2026):
- El total se fija cuando la clienta ya no tiene más prendas que añadir.
- Lo cierra la recepcionista.
- El precio de cada prenda sale del catálogo de servicios.
"""

from decimal import Decimal

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from pagos.models import Pago
from pedidos.models import Pedido, ServicioPedido
from pedidos.tests.fabricas import (
    crear_catalogo,
    crear_cliente,
    crear_pedido,
    crear_usuario,
)
from servicios.models import Servicio
from usuarios.tests.conftest import ClientSeguro

pytestmark = pytest.mark.django_db

BASE = "/api/v1/pedidos/FC-0001"


@pytest.fixture
def datos():
    catalogo = crear_catalogo()
    admin = crear_usuario("admin-total@fran-costuras.test", "administradora")
    recepcion = crear_usuario("recep-total2@fran-costuras.test", "recepcionista")
    costurera = crear_usuario("cost-total@fran-costuras.test", "costurera")
    pedido = crear_pedido(
        "FC-0001", crear_cliente(), catalogo["blusa"], costurera=costurera
    )

    def servicio(codigo, tarifa, activo=True, valoracion=False):
        return Servicio.objects.create(
            codigo=codigo,
            nombre=codigo.capitalize(),
            categoria="Arreglos",
            unidad="prenda",
            tarifa_base=tarifa,
            requiere_valoracion=valoracion,
            activo=activo,
            creado_por=admin,
        )

    return {
        "admin": admin,
        "recepcion": recepcion,
        "costurera": costurera,
        "pedido": pedido,
        "basta": servicio("basta", Decimal("5.00")),
        "vestido": servicio("vestido", Decimal("40.00")),
        "inactivo": servicio("inactivo", Decimal("9.00"), activo=False),
        "sin_tarifa": servicio("valorar", None, valoracion=True),
    }


def _api(usuario):
    cliente = ClientSeguro()
    token = RefreshToken.for_user(usuario).access_token
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return cliente


def _agregar(usuario, servicio, cantidad=1):
    return _api(usuario).post(
        f"{BASE}/servicios/",
        {"servicio": servicio.pk, "cantidad": cantidad, "detalle": " Ruedo "},
        format="json",
    )


def test_recepcion_agrega_prendas_y_cierra_el_total(datos):
    assert _agregar(datos["recepcion"], datos["basta"], cantidad=2).status_code == 201
    respuesta = _agregar(datos["admin"], datos["vestido"])
    assert respuesta.status_code == 201
    assert respuesta.json()["precio_unitario"] == "40.00"
    assert respuesta.json()["subtotal"] == "40.00"

    listado = _api(datos["recepcion"]).get(f"{BASE}/servicios/").json()
    assert [linea["subtotal"] for linea in listado] == ["10.00", "40.00"]
    assert listado[0]["detalle"] == "Ruedo"

    cierre = _api(datos["recepcion"]).post(f"{BASE}/cerrar-total/")
    assert cierre.status_code == 200
    assert cierre.json()["total"] == "50.00"
    assert cierre.json()["total_cerrado_en"] is not None
    pedido = Pedido.objects.get(codigo="FC-0001")
    assert pedido.total == Decimal("50.00")
    assert pedido.total_cerrado_por == datos["recepcion"]


def test_precio_copiado_no_cambia_si_cambia_la_tarifa(datos):
    _agregar(datos["recepcion"], datos["basta"])
    datos["basta"].tarifa_base = Decimal("8.00")
    datos["basta"].save()
    cierre = _api(datos["recepcion"]).post(f"{BASE}/cerrar-total/")
    assert cierre.json()["total"] == "5.00"


def test_solo_la_recepcionista_cierra_el_total(datos):
    _agregar(datos["recepcion"], datos["basta"])
    for rol in ("admin", "costurera"):
        respuesta = _api(datos[rol]).post(f"{BASE}/cerrar-total/")
        assert respuesta.status_code == 403
    assert Pedido.objects.get(codigo="FC-0001").total_cerrado_en is None


def test_costurera_no_ve_ni_agrega_prendas_con_precio(datos):
    assert _api(datos["costurera"]).get(f"{BASE}/servicios/").status_code == 403
    assert _agregar(datos["costurera"], datos["basta"]).status_code == 403


def test_no_se_cierra_sin_prendas(datos):
    respuesta = _api(datos["recepcion"]).post(f"{BASE}/cerrar-total/")
    assert respuesta.status_code == 400
    assert respuesta.json()["error"] == "datos_invalidos"


def test_servicios_inactivos_o_sin_tarifa_se_rechazan(datos):
    for clave in ("inactivo", "sin_tarifa"):
        respuesta = _agregar(datos["recepcion"], datos[clave])
        assert respuesta.status_code == 400
        assert respuesta.json()["error"] == "datos_invalidos"
    respuesta = _api(datos["recepcion"]).post(
        f"{BASE}/servicios/", {"servicio": 9999}, format="json"
    )
    assert respuesta.status_code == 400
    respuesta = _api(datos["recepcion"]).post(
        f"{BASE}/servicios/",
        {"servicio": datos["basta"].pk, "cantidad": 0},
        format="json",
    )
    assert respuesta.status_code == 400
    assert not ServicioPedido.objects.exists()


def test_quitar_prenda_antes_de_cerrar(datos):
    linea = _agregar(datos["recepcion"], datos["basta"]).json()
    respuesta = _api(datos["recepcion"]).delete(f"{BASE}/servicios/{linea['id']}/")
    assert respuesta.status_code == 204
    assert not ServicioPedido.objects.exists()
    respuesta = _api(datos["recepcion"]).delete(f"{BASE}/servicios/{linea['id']}/")
    assert respuesta.status_code == 400


def test_total_cerrado_no_admite_cambios(datos):
    linea = _agregar(datos["recepcion"], datos["basta"]).json()
    _api(datos["recepcion"]).post(f"{BASE}/cerrar-total/")
    assert _agregar(datos["recepcion"], datos["vestido"]).status_code == 409
    respuesta = _api(datos["recepcion"]).delete(f"{BASE}/servicios/{linea['id']}/")
    assert respuesta.status_code == 409
    respuesta = _api(datos["recepcion"]).post(f"{BASE}/cerrar-total/")
    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "total_cerrado"


def test_pedido_inexistente(datos):
    api = _api(datos["recepcion"])
    assert api.get("/api/v1/pedidos/FC-9999/servicios/").status_code == 404
    respuesta = api.post(
        "/api/v1/pedidos/FC-9999/servicios/",
        {"servicio": datos["basta"].pk},
        format="json",
    )
    assert respuesta.status_code == 404
    assert api.delete("/api/v1/pedidos/FC-9999/servicios/1/").status_code == 404
    assert api.post("/api/v1/pedidos/FC-9999/cerrar-total/").status_code == 404


def test_abono_exige_total_cerrado_y_luego_respeta_saldo(datos):
    api = _api(datos["recepcion"])
    sin_cerrar = api.post(f"{BASE}/pagos/", {"monto": "5.00"}, format="json")
    assert sin_cerrar.status_code == 400
    assert "no está cerrado" in sin_cerrar.json()["detalle"]

    _agregar(datos["recepcion"], datos["basta"])
    api.post(f"{BASE}/cerrar-total/")
    assert (
        api.post(f"{BASE}/pagos/", {"monto": "5.00"}, format="json").status_code == 201
    )
    assert Pago.objects.count() == 1


def test_recepcion_lista_solo_servicios_cotizables(datos):
    respuesta = _api(datos["recepcion"]).get("/api/v1/servicios/cotizables/")
    assert respuesta.status_code == 200
    codigos = [s["codigo"] for s in respuesta.json()["results"]]
    assert codigos == ["basta", "vestido"]
    assert set(respuesta.json()["results"][0]) == {
        "id",
        "codigo",
        "nombre",
        "categoria",
        "unidad",
        "tarifa_base",
    }
    assert (
        _api(datos["costurera"]).get("/api/v1/servicios/cotizables/").status_code == 403
    )
    # El catálogo completo sigue siendo solo de la administradora.
    assert _api(datos["recepcion"]).get("/api/v1/servicios/").status_code == 403
