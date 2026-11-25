"""Rutas de asignación bajo /api/v1/."""

from django.urls import path

from . import views

app_name = "asignacion"

urlpatterns = [
    path(
        "pedidos/<str:codigo>/asignar/",
        views.AsignacionPedidoView.as_view(),
        name="pedido_asignacion",
    ),
]
