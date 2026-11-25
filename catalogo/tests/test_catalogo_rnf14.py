"""
RNF-14 — El catálogo de medidas cargado coincide con MEDIDAS.md (versión 2).

Se lee MEDIDAS.md directamente (secciones 1 a 4) y se compara con lo que
queda en la base tras `loaddata catalogo_medidas`. La sección 5 (resumen
rápido) no se carga (AGENTS.md §4.4). BEBE no tiene prendas (decisión A8
abierta: la guía no las define).
"""

from pathlib import Path

import pytest
from django.core.management import call_command

from catalogo.models import CategoriaMedida, Prenda, PrendaMedida, TipoMedida

BACKEND = Path(__file__).resolve().parents[2]
MEDIDAS = BACKEND / "MEDIDAS.md"
MEDIDAS_RAIZ = BACKEND.parent / "MEDIDAS.md"

CODIGOS_CATEGORIA = {
    "(`MUJER`)": "MUJER",
    "(`HOMBRE`)": "HOMBRE",
    "(`NINO`)": "NINO",
    "(`BEBE`)": "BEBE",
}


def _codigo(texto: str) -> str:
    """Devuelve el contenido del primer `...` de un texto."""
    return texto.split("`")[1]


def leer_guia() -> dict:
    """Interpreta MEDIDAS.md: {categoria: {"tipos": {...}, "prendas": {...}}}."""
    guia: dict = {}
    categoria = None
    en_prendas = False
    prenda = None
    for linea in MEDIDAS.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            categoria = next(
                (c for marca, c in CODIGOS_CATEGORIA.items() if marca in linea), None
            )
            if categoria:
                guia[categoria] = {"tipos": {}, "prendas": {}}
            en_prendas = False
            prenda = None
            continue
        if categoria is None:
            continue
        if linea.startswith("### B."):
            en_prendas = True
            continue
        if not en_prendas and linea.startswith("|"):
            celdas = [c.strip() for c in linea.strip("|").split("|")]
            if len(celdas) == 4 and celdas[0].isdigit():
                nombre = celdas[1].replace("*(agregada)*", "").strip()
                guia[categoria]["tipos"][_codigo(celdas[2])] = (nombre, celdas[3])
        elif en_prendas and linea.startswith("**"):
            nombre = linea.split("**")[1]
            prenda = _codigo(linea.split("**")[2])
            guia[categoria]["prendas"][prenda] = {"nombre": nombre, "medidas": {}}
        elif en_prendas and linea.startswith("- ") and prenda:
            etiqueta, codigo = linea[2:].rsplit(" — ", 1)
            guia[categoria]["prendas"][prenda]["medidas"][_codigo(codigo)] = (
                "(opcional" in etiqueta
            )
    return guia


@pytest.fixture
def catalogo_cargado(db):
    call_command("loaddata", "catalogo_medidas", verbosity=0)


@pytest.fixture(scope="module")
def guia():
    return leer_guia()


def test_guia_interpretada_tiene_las_cuatro_categorias(guia):
    assert list(guia) == ["MUJER", "HOMBRE", "NINO", "BEBE"]
    # Totales del DERCAS Anexo A.
    assert {c: len(g["tipos"]) for c, g in guia.items()} == {
        "MUJER": 32,
        "HOMBRE": 26,
        "NINO": 27,
        "BEBE": 14,
    }


def test_categorias_cargadas(catalogo_cargado):
    nombres = set(CategoriaMedida.objects.values_list("nombre", flat=True))
    assert nombres == {"MUJER", "HOMBRE", "NINO", "BEBE"}


def test_tipos_de_medida_coinciden_con_la_guia(catalogo_cargado, guia):
    for categoria, datos in guia.items():
        en_bd = {
            t.codigo: (t.nombre, t.como_se_toma)
            for t in TipoMedida.objects.filter(categoria__nombre=categoria)
        }
        assert en_bd == datos["tipos"], categoria


def test_prendas_y_sus_medidas_coinciden_con_la_guia(catalogo_cargado, guia):
    for categoria, datos in guia.items():
        prendas_bd = Prenda.objects.filter(categoria__nombre=categoria)
        assert {p.codigo for p in prendas_bd} == set(datos["prendas"]), categoria
        for prenda in prendas_bd:
            esperado = datos["prendas"][prenda.codigo]
            assert prenda.nombre == esperado["nombre"]
            medidas_bd = {
                pm.tipo_medida.codigo: pm.opcional
                for pm in prenda.medidas_requeridas.select_related("tipo_medida")
            }
            assert medidas_bd == esperado["medidas"], f"{categoria}:{prenda.codigo}"


def test_opcionales_marcados_segun_la_guia(catalogo_cargado):
    opcionales = {
        (pm.prenda.categoria.nombre, pm.prenda.codigo, pm.tipo_medida.codigo)
        for pm in PrendaMedida.objects.filter(opcional=True).select_related(
            "prenda__categoria", "tipo_medida"
        )
    }
    assert opcionales == {
        ("MUJER", "faldas", "largo_abertura"),
        ("NINO", "vestidos", "separacion_busto"),
    }


def test_cada_prenda_usa_solo_medidas_de_su_categoria(catalogo_cargado):
    for pm in PrendaMedida.objects.select_related("prenda", "tipo_medida"):
        assert pm.tipo_medida.categoria_id == pm.prenda.categoria_id


def test_bebe_sin_prendas_y_con_tabla_completa(catalogo_cargado):
    bebe = CategoriaMedida.objects.get(nombre="BEBE")
    assert bebe.prendas.count() == 0
    assert bebe.tipos_medida.count() == 14


def test_resumen_rapido_seccion_5_no_se_carga(catalogo_cargado):
    nombres = {n.lower() for n in Prenda.objects.values_list("nombre", flat=True)}
    for excluida in ("ropa deportiva", "ropa interior", "abrigo"):
        assert excluida not in nombres


@pytest.mark.skipif(not MEDIDAS_RAIZ.exists(), reason="sin MEDIDAS.md en la raíz")
def test_copia_de_medidas_igual_a_la_guia_oficial():
    assert MEDIDAS.read_bytes() == MEDIDAS_RAIZ.read_bytes()
