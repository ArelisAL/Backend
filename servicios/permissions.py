"""Permisos por rol para la configuración comercial del catálogo."""

from rest_framework.permissions import BasePermission


class EsAdministradora(BasePermission):
    message = "Solo la administradora puede consultar o modificar el catálogo."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None) == "administradora"
        )
