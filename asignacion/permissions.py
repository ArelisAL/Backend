"""Permisos del módulo de asignación."""

from rest_framework.permissions import BasePermission


class EsAdministradora(BasePermission):
    message = "Solo la administradora puede asignar pedidos."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None) == "administradora"
        )
