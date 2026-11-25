"""Abonos y registro de anulaciones (DERCAS RF-18, §7.1)."""

from django.conf import settings
from django.db import models


class Pago(models.Model):
    """Abono asociado a un pedido, conservado aunque se anule."""

    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.PROTECT,
        related_name="pagos",
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pagos_registrados",
    )
    anulado = models.BooleanField(default=False)
    anulado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pagos_anulados",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "pago"
        verbose_name_plural = "pagos"
        ordering = ["fecha", "id"]

    def __str__(self) -> str:
        return f"{self.pedido.codigo}: {self.monto}"
