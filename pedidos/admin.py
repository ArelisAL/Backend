from django.contrib import admin

from .models import Pedido


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "cliente", "prenda", "estado", "fecha_entrega")
    list_filter = ("estado", "fecha_entrega")
    search_fields = ("codigo", "cliente__nombre")
    readonly_fields = (
        "codigo",
        "estado",
        "costurera",
        "nota_interna",
        "creado_en",
        "entregado_en",
    )
