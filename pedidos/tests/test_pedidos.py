"""Registro, búsqueda y permisos de pedidos (DERCAS RF-04..08, AGENTS.md §5)."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from pedidos import services
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
    cliente = crear_cliente("María Ficticia")
    costurera = crear_usuario("cost-pedidos@fran-costuras.test", "costurera")
    otra = crear_usuario("otra-pedidos@fran-costuras.test", "costurera")
    return {
        "blusa": catalogo["blusa"],
        "cliente": cliente,
        "costurera": costurera,
        "otra": otra,
    }


def _entrada(datos, dias=3, **extra):
    base = {
        "cliente": datos["cliente"].pk,
        "prenda": datos["blusa"].pk,
        "fecha_entrega": timezone.localdate() + timedelta(days=dias),
        "descripcion": "  Blusa con encaje  ",
    }
    base.update(extra)
    return base


def test_codigos_unicos_consecutivos(datos):
    primero = services.crear_pedido(_entrada(datos))
    segundo = services.crear_pedido(_entrada(datos))
    assert (primero.codigo, segundo.codigo) == ("FC-0001", "FC-0002")
    assert primero.estado == Pedido.PENDIENTE
    assert primero.descripcion == "Blusa con encaje"


def test_codigo_ignora_sufijos_no_numericos(datos):
    crear_pedido("FC-ABC", datos["cliente"], datos["blusa"])
    crear_pedido("FC-0007", datos["cliente"], datos["blusa"])
    assert services.crear_pedido(_entrada(datos)).codigo == "FC-0008"


def test_fecha_pasada_se_rechaza(datos):
    with pytest.raises(services.DatosPedidoInvalidos, match="anterior a hoy"):
        services.crear_pedido(_entrada(datos, dias=-1))


def test_cliente_o_prenda_inexistentes(datos):
    with pytest.raises(services.DatosPedidoInvalidos, match="cliente"):
        services.crear_pedido(_entrada(datos, cliente=999))
    with pytest.raises(services.DatosPedidoInvalidos, match="prenda"):
        services.crear_pedido(_entrada(datos, prenda=999))


def test_listado_filtra_por_rol_estado_y_busqueda(datos):
    mio = crear_pedido(
        "FC-0001", datos["cliente"], datos["blusa"], costurera=datos["costurera"]
    )
    crear_pedido("FC-0002", datos["cliente"], datos["blusa"], costurera=datos["otra"])
    crear_pedido(
        "FC-0003", crear_cliente("Otro"), datos["blusa"], estado=Pedido.ENTREGADO
    )
    admin = crear_usuario("admin-pedidos@fran-costuras.test", "administradora")

    assert list(services.listar_pedidos(datos["costurera"])) == [mio]
    assert services.listar_pedidos(admin).count() == 2
    assert services.listar_pedidos(admin, incluir_entregados=True).count() == 3
    assert (
        services.listar_pedidos(
            admin, incluir_entregados=True, estado=Pedido.ENTREGADO
        ).count()
        == 1
    )
    assert services.listar_pedidos(admin, busqueda="fc-0002").count() == 1
    assert services.listar_pedidos(admin, busqueda="maría").count() == 2


def test_costurera_no_ve_pedido_ajeno(datos):
    crear_pedido("FC-0001", datos["cliente"], datos["blusa"], costurera=datos["otra"])
    with pytest.raises(PermissionError):
        services.obtener_pedido_por_codigo("FC-0001", datos["costurera"])
    with pytest.raises(services.PedidoNoEncontrado):
        services.obtener_pedido_por_codigo("FC-9999", datos["costurera"])


def test_permisos_de_medidas_de_la_costurera(datos):
    crear_pedido(
        "FC-0001", datos["cliente"], datos["blusa"], costurera=datos["costurera"]
    )
    cid = datos["cliente"].pk
    assert services.puede_trabajar_con_medidas(datos["costurera"], cid, None)
    assert services.puede_trabajar_con_medidas(
        datos["costurera"], cid, datos["blusa"].pk
    )
    assert not services.puede_trabajar_con_medidas(datos["otra"], cid, None)
    assert services.prendas_asignadas_de_cliente(datos["costurera"], cid) == [
        (datos["blusa"].pk, "MUJER")
    ]


def test_cambiar_fecha_y_nota(datos):
    pedido = crear_pedido("FC-0001", datos["cliente"], datos["blusa"])
    nueva = timezone.localdate() + timedelta(days=10)
    assert services.cambiar_fecha_entrega(pedido, nueva).fecha_entrega == nueva
    with pytest.raises(services.DatosPedidoInvalidos):
        services.cambiar_fecha_entrega(pedido, timezone.localdate() - timedelta(1))
    assert services.cambiar_nota_interna(pedido, "  urgente ").nota_interna == (
        "urgente"
    )


def test_estados_y_entrega(datos):
    pedido = crear_pedido("FC-0001", datos["cliente"], datos["blusa"])
    assert services.siguiente_estado(Pedido.PENDIENTE) == Pedido.EN_PROCESO
    assert services.siguiente_estado(Pedido.EN_PROCESO) == Pedido.TERMINADO
    assert services.siguiente_estado(Pedido.TERMINADO) == Pedido.ENTREGADO
    assert services.siguiente_estado(Pedido.ENTREGADO) is None
    services.guardar_estado(pedido, Pedido.ENTREGADO)
    pedido.refresh_from_db()
    assert pedido.entregado_en is not None


def test_bloqueado_por_codigo_inexistente(datos):
    with pytest.raises(services.PedidoNoEncontrado):
        services.obtener_pedido_bloqueado_por_codigo("FC-9999")


def test_ultimas_medidas_sin_tomas(datos):
    pedido = crear_pedido("FC-0001", datos["cliente"], datos["blusa"])
    assert services.ultimas_medidas(pedido) is None


# --- API -----------------------------------------------------------------


def _cliente_con_token(usuario):
    cliente = ClientSeguro()
    cliente.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(usuario).access_token}"
    )
    return cliente


def test_api_sin_token_401():
    assert ClientSeguro().get("/api/v1/pedidos/").status_code == 401


def test_api_pedido_ajeno_403(datos):
    crear_pedido("FC-0001", datos["cliente"], datos["blusa"], costurera=datos["otra"])
    respuesta = _cliente_con_token(datos["costurera"]).get("/api/v1/pedidos/FC-0001/")
    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "sin_permiso"


def test_api_mis_pedidos_solo_los_propios(datos):
    crear_pedido(
        "FC-0001", datos["cliente"], datos["blusa"], costurera=datos["costurera"]
    )
    crear_pedido("FC-0002", datos["cliente"], datos["blusa"], costurera=datos["otra"])
    respuesta = _cliente_con_token(datos["costurera"]).get("/api/v1/mis-pedidos/")
    assert respuesta.status_code == 200
    codigos = [p["codigo"] for p in respuesta.json()["results"]]
    assert codigos == ["FC-0001"]
