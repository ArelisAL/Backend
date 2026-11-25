"""Rutas REST del módulo pedidos bajo /api/v1/."""

from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("pedidos/", views.PedidoListView.as_view(), name="pedido_list"),
    path("mis-pedidos/", views.MisPedidosView.as_view(), name="mis_pedidos"),
    path(
        "pedidos/<str:codigo>/notas/",
        views.PedidoNotaView.as_view(),
        name="pedido_notas",
    ),
    path(
        "pedidos/<str:codigo>/",
        views.PedidoDetailView.as_view(),
        name="pedido_detail",
    ),
]
