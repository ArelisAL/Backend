"""Rutas de estados e historial bajo /api/v1/."""

from django.urls import path

from . import views

app_name = "flujo"

urlpatterns = [
    path(
        "pedidos/<str:codigo>/estado/",
        views.PedidoEstadoView.as_view(),
        name="pedido_estado",
    ),
    path(
        "pedidos/<str:codigo>/historial/",
        views.PedidoHistorialView.as_view(),
        name="pedido_historial",
    ),
]
