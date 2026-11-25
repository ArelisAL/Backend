"""Permisos del flujo de pedidos."""

from rest_framework.permissions import BasePermission


class EsPersonalTaller(BasePermission):
    message = "No tienes permiso para consultar el flujo de pedidos."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None)
            in {"administradora", "recepcionista", "costurera"}
        )


class PuedeCambiarEstado(BasePermission):
    message = "Solo la administradora o la costurera puede cambiar el estado."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None) in {"administradora", "costurera"}
        )
