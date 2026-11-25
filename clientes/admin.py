from django.contrib import admin

from .models import Cliente, Medida


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "correo")
    search_fields = ("nombre", "telefono", "correo")


@admin.register(Medida)
class MedidaAdmin(admin.ModelAdmin):
    list_display = ("cliente", "categoria", "prenda", "fecha", "tomada_por")
    list_filter = ("categoria", "fecha")
    search_fields = ("cliente__nombre", "cliente__correo", "cliente__telefono")
    readonly_fields = ("fecha",)
