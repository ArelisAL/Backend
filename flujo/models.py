"""Historial de transiciones de estado de pedidos (DERCAS RF-09/RF-10, §7.1)."""

from django.conf import settings
from django.db import models


class HistorialEstado(models.Model):
    """Registra cada cambio de estado de un pedido y el usuario responsable."""

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("EN_PROCESO", "En Proceso"),
        ("TERMINADO", "Terminado"),
        ("ENTREGADO", "Entregado"),
    ]

    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.PROTECT,
        related_name="historial_estados",
    )
    estado_anterior = models.CharField(max_length=20, choices=ESTADOS)
    estado_nuevo = models.CharField(max_length=20, choices=ESTADOS)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cambios_estado_pedido",
    )

    class Meta:
        verbose_name = "historial de estado"
        verbose_name_plural = "historiales de estado"
        ordering = ["fecha_hora", "id"]

    def __str__(self) -> str:
        return f"{self.pedido.codigo}: {self.estado_anterior or 'Inicio'} → {self.estado_nuevo}"
