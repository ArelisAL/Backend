from django.contrib import admin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        "pedido",
        "monto",
        "fecha",
        "registrado_por",
        "anulado",
        "anulado_por",
    )
    list_filter = ("anulado", "fecha")
    search_fields = (
        "pedido__codigo",
        "registrado_por__email",
        "anulado_por__email",
    )
    readonly_fields = (
        "pedido",
        "monto",
        "fecha",
        "registrado_por",
        "anulado",
        "anulado_por",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
