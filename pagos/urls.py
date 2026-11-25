"""Rutas del módulo de pagos según DERCAS §7.2."""

from django.urls import path

from .views import AnularPagoView, PagosPedidoView

urlpatterns = [
    path("pedidos/<str:codigo>/pagos/", PagosPedidoView.as_view(), name="pagos-pedido"),
    path("pagos/<int:pago_id>/anular/", AnularPagoView.as_view(), name="anular-pago"),
]
