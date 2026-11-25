"""Rutas del módulo clientes y medidas bajo /api/v1/."""

from django.urls import path

from . import views

app_name = "clientes"

urlpatterns = [
    path("clientes/", views.ClienteListView.as_view(), name="cliente_list"),
    path(
        "clientes/<int:cliente_id>/",
        views.ClienteDetailView.as_view(),
        name="cliente_detail",
    ),
    path(
        "clientes/<int:cliente_id>/medidas/",
        views.ClienteMedidasView.as_view(),
        name="cliente_medidas",
    ),
]
