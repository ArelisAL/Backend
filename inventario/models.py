"""Telas y consumo por pedido (DERCAS RF-13/RF-14, §7.1)."""

from django.db import models


class Tela(models.Model):
    """Tela disponible para la confección de pedidos, medida en metros."""

    nombre = models.CharField(max_length=120)
    color = models.CharField(max_length=80)
    metros_disponibles = models.DecimalField(max_digits=10, decimal_places=2)
    precio_metro = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.CharField(max_length=150)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=5)

    class Meta:
        verbose_name = "tela"
        verbose_name_plural = "telas"
        ordering = ["nombre", "id"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.color})"


class UsoTela(models.Model):
    """Consumo capturado y posteriormente confirmado al descontar stock."""

    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.PROTECT,
        related_name="usos_tela",
    )
    tela = models.ForeignKey(
        Tela,
        on_delete=models.PROTECT,
        related_name="usos",
    )
    metros_usados = models.DecimalField(max_digits=10, decimal_places=2)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="consumos_tela_registrados",
        blank=True,
        null=True,
    )
    confirmado = models.BooleanField(default=False)
    vigente = models.BooleanField(default=True)
    reemplazado_en = models.DateTimeField(blank=True, null=True)
    reemplazado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="consumos_tela_reemplazados",
        blank=True,
        null=True,
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "uso de tela"
        verbose_name_plural = "usos de tela"
        ordering = ["fecha", "id"]

    def __str__(self) -> str:
        return f"{self.pedido.codigo}: {self.metros_usados} m de {self.tela}"
