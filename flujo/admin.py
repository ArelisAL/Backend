from django.contrib import admin

from .models import HistorialEstado


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = (
        "pedido",
        "estado_anterior",
        "estado_nuevo",
        "fecha_hora",
        "usuario",
    )
    list_filter = ("estado_anterior", "estado_nuevo", "fecha_hora")
    search_fields = ("pedido__codigo", "usuario__email")
    readonly_fields = (
        "pedido",
        "estado_anterior",
        "estado_nuevo",
        "fecha_hora",
        "usuario",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
