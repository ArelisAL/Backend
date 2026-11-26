"""Consultas del catálogo de medidas (DERCAS §4.2, AGENTS.md §4.4)."""

import pytest

from catalogo import services
from pedidos.tests.fabricas import crear_catalogo

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogo():
    return crear_catalogo()


def test_listar_categorias(catalogo):
    nombres = {c.nombre for c in services.listar_categorias()}
    assert nombres == {"MUJER", "HOMBRE", "BEBE"}


def test_listar_prendas_por_categoria(catalogo):
    assert services.listar_prendas().count() == 2
    assert [p.codigo for p in services.listar_prendas("MUJER")] == ["blusas"]


def test_medidas_de_prenda_con_opcionales(catalogo):
    medidas = {
        m.tipo_medida.codigo: m.opcional
        for m in services.listar_medidas_prenda(catalogo["blusa"].pk)
    }
    assert medidas == {"contorno_busto": False, "contorno_cintura": True}


def test_prenda_inexistente(catalogo):
    with pytest.raises(services.PrendaNoEncontrada):
        services.obtener_prenda(9999)
    with pytest.raises(services.PrendaNoEncontrada):
        services.listar_medidas_prenda(9999)


def test_tipos_de_categoria_bebe(catalogo):
    assert [t.codigo for t in services.obtener_tipos_categoria("BEBE")] == [
        "largo_total"
    ]
    assert services.obtener_categoria("NADA") is None
