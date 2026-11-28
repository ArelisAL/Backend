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
    total_cerrado_en = models.DateTimeField(blank=True, null=True)
    total_cerrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos_total_cerrado",
        blank=True,
        null=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    entregado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["fecha_entrega", "id"]

    def __str__(self) -> str:
        return self.codigo


class ServicioPedido(models.Model):
    """Prenda de confección o arreglo del pedido, cotizada con el catálogo.

    Decisión de la cliente (27/11/2026, auditoría C1): el precio sale del
    catálogo de servicios y la recepcionista cierra el total cuando la clienta
    ya no tiene más prendas que añadir. El precio se copia al registrar la línea
    para que un cambio posterior de tarifa no altere pedidos ya cotizados.
    """

    pedido = models.ForeignKey(
        Pedido, on_delete=models.PROTECT, related_name="servicios"
    )
    servicio = models.ForeignKey(
        "servicios.Servicio", on_delete=models.PROTECT, related_name="lineas_pedido"
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    detalle = models.CharField(max_length=200, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="servicios_pedido_registrados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado_en", "id"]
        verbose_name = "servicio del pedido"
        verbose_name_plural = "servicios del pedido"

    def __str__(self) -> str:
        return f"{self.pedido.codigo} · {self.servicio.nombre} × {self.cantidad}"
