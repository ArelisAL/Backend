from django.contrib import admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """Registro del modelo Usuario en el panel de Django (Backend/§4.1)."""

    list_display = (
        "email",
        "nombre",
        "rol",
        "activo",
        "debe_cambiar_contraseña",
        "date_joined",
    )
    search_fields = ("email", "nombre")
    list_filter = ("rol", "activo", "debe_cambiar_contraseña")
