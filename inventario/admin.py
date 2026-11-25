from django.contrib import admin

from .models import Tela, UsoTela


@admin.register(Tela)
class TelaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "color",
        "metros_disponibles",
        "precio_metro",
        "proveedor",
        "stock_minimo",
    )
    search_fields = ("nombre", "color", "proveedor")


@admin.register(UsoTela)
class UsoTelaAdmin(admin.ModelAdmin):
    list_display = ("pedido", "tela", "metros_usados", "fecha")
    list_filter = ("fecha",)
    search_fields = ("pedido__codigo", "tela__nombre")
    readonly_fields = ("pedido", "tela", "metros_usados", "fecha")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
