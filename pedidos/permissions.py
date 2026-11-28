"""Permisos por rol para pedidos."""

from rest_framework.permissions import BasePermission


class EsPersonalTaller(BasePermission):
    message = "No tienes permiso para consultar pedidos."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None)
            in {"administradora", "recepcionista", "costurera"}
        )


class EsAdministradoraORecepcionista(BasePermission):
    message = "Solo administradora o recepcionista pueden registrar pedidos."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None)
            in {"administradora", "recepcionista"}
        )


class EsAdministradora(BasePermission):
    message = "Solo la administradora puede modificar esta fecha."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None) == "administradora"
        )


class EsCosturera(BasePermission):
    message = "Solo la costurera puede consultar Mis pedidos."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None) == "costurera"
        )


class EsRecepcionista(BasePermission):
    message = "Solo la recepcionista puede cerrar el total del pedido."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None) == "recepcionista"
        )
