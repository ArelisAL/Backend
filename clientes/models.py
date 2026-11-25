"""Clientes y registros históricos de medidas (DERCAS §1.5, §4 RF-01/02, §7.1)."""

from django.conf import settings
from django.db import models


class Cliente(models.Model):
    """Persona que encarga prendas; teléfono y correo no se repiten."""

    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=30, unique=True, blank=True, null=True)
    correo = models.EmailField(unique=True, blank=True, null=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nombre", "id"]

    def __str__(self) -> str:
        return self.nombre


class Medida(models.Model):
    """Una toma inmutable de medidas corporales registrada en centímetros."""

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="medidas"
    )
    categoria = models.ForeignKey(
        "catalogo.CategoriaMedida",
        on_delete=models.PROTECT,
        related_name="tomas_medida",
    )
    prenda = models.ForeignKey(
        "catalogo.Prenda",
        on_delete=models.PROTECT,
        related_name="tomas_medida",
        blank=True,
        null=True,
    )
    valores_cm = models.JSONField(default=dict)
    fecha = models.DateTimeField(auto_now_add=True)
    tomada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="medidas_tomadas",
    )

    class Meta:
        verbose_name = "toma de medidas"
        verbose_name_plural = "tomas de medidas"
        ordering = ["-fecha", "-id"]

    def __str__(self) -> str:
        prenda = f" · {self.prenda}" if self.prenda_id else ""
        fecha = self.fecha.strftime("%Y-%m-%d") if self.fecha else "sin fecha"
        return f"Medidas de {self.cliente}{prenda} ({fecha})"
