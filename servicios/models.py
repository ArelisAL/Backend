"""Catálogo administrable de servicios (DERCAS v1.5 §14.1 y §14.2)."""

from django.conf import settings
from django.db import models


class Servicio(models.Model):
    """Servicio tarifable; una tarifa nula significa que sigue sin configurarse."""

    codigo = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=120)
    categoria = models.CharField(max_length=80)
    descripcion = models.TextField(blank=True)
    unidad = models.CharField(max_length=40)
    tarifa_base = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    requiere_valoracion = models.BooleanField(default=False)
    activo = models.BooleanField(default=False)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="servicios_creados",
    )
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["categoria", "nombre", "id"]
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self) -> str:
        return f"{self.codigo} — {self.nombre}"

    @property
    def configuracion_pendiente(self) -> bool:
        return self.tarifa_base is None and not self.requiere_valoracion


class HistorialServicio(models.Model):
    """Instantánea auditable de creación y cambios administrativos del catálogo."""

    servicio = models.ForeignKey(
        Servicio, on_delete=models.PROTECT, related_name="historial"
    )
    accion = models.CharField(max_length=20)
    datos = models.JSONField()
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="historial_servicios",
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_hora", "-id"]
        verbose_name = "cambio de catálogo"
        verbose_name_plural = "historial del catálogo"
