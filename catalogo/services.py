"""Consultas del catálogo oficial de medidas (DERCAS §4.2, §7.1 y §7.2)."""

from .models import CategoriaMedida, Prenda, PrendaMedida, TipoMedida


class PrendaNoEncontrada(Exception):
    """La prenda consultada no existe en el catálogo."""


def listar_categorias():
    return CategoriaMedida.objects.prefetch_related("tipos_medida").all()


def obtener_categoria(codigo: str):
    return CategoriaMedida.objects.filter(nombre=codigo).first()


def obtener_tipos_categoria(codigo: str):
    return TipoMedida.objects.filter(categoria__nombre=codigo).select_related(
        "categoria"
    )


def listar_prendas(categoria: str | None = None):
    prendas = Prenda.objects.select_related("categoria").all()
    if categoria:
        prendas = prendas.filter(categoria__nombre=categoria)
    return prendas


def obtener_prenda(prenda_id: int):
    prenda = Prenda.objects.select_related("categoria").filter(pk=prenda_id).first()
    if prenda is None:
        raise PrendaNoEncontrada
    return prenda


def listar_medidas_prenda(prenda_id: int):
    if not Prenda.objects.filter(pk=prenda_id).exists():
        raise PrendaNoEncontrada
    return PrendaMedida.objects.filter(prenda_id=prenda_id).select_related(
        "tipo_medida"
    )
