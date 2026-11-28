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
    message = "No tienes permiso para cambiar el estado del pedido."

    def has_permission(self, request, view):
        # La recepcionista solo marca «Entregado»; services.py valida la transición.
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None)
            in {"administradora", "recepcionista", "costurera"}
        )
