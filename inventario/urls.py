"""Rutas de tela del módulo de inventario."""

from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("telas/", views.TelaListView.as_view(), name="tela_list"),
    path(
        "telas/opciones-consumo/",
        views.TelaOpcionesConsumoView.as_view(),
        name="tela_opciones_consumo",
    ),
    path(
        "telas/stock-bajo/", views.TelaStockBajoView.as_view(), name="tela_stock_bajo"
    ),
    path("telas/<int:tela_id>/", views.TelaDetailView.as_view(), name="tela_detail"),
    path(
        "pedidos/<str:codigo>/consumos/",
        views.PedidoConsumosView.as_view(),
        name="pedido_consumos",
    ),
]
