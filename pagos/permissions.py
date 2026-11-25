"""Permisos por rol del módulo pagos."""

from rest_framework.permissions import BasePermission


class PuedeRegistrarPago(BasePermission):
    message = "Solo administradora o recepcionista puede registrar pagos."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None)
            in {"administradora", "recepcionista"}
        )


class EsAdministradora(BasePermission):
    message = "Solo la administradora puede anular pagos."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None) == "administradora"
        )
