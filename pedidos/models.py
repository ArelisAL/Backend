"""Entidad Pedido y estados de trabajo (DERCAS §4 RF-04, §7.1)."""

from django.conf import settings
from django.db import models


class Pedido(models.Model):
    """Encargo de una prenda a un cliente."""

    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    TERMINADO = "TERMINADO"
    ENTREGADO = "ENTREGADO"
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (EN_PROCESO, "En Proceso"),
        (TERMINADO, "Terminado"),
        (ENTREGADO, "Entregado"),
    ]

    codigo = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.PROTECT, related_name="pedidos"
    )
    prenda = models.ForeignKey(
        "catalogo.Prenda", on_delete=models.PROTECT, related_name="pedidos"
    )
    descripcion = models.TextField(blank=True)
    fecha_entrega = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)
    costurera = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos_asignados",
        blank=True,
        null=True,
    )
    nota_interna = models.TextField(blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    entregado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["fecha_entrega", "id"]

    def __str__(self) -> str:
        return self.codigo
