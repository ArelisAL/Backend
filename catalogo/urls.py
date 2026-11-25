"""Rutas de consulta del catálogo bajo /api/v1/catalogo/."""

from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("categorias/", views.CategoriaListView.as_view(), name="categorias"),
    path("prendas/", views.PrendaListView.as_view(), name="prendas"),
    path(
        "prendas/<int:prenda_id>/medidas/",
        views.PrendaMedidaListView.as_view(),
        name="prenda_medidas",
    ),
]
