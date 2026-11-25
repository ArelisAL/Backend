"""Permiso exclusivo de la administradora para inventario."""

from rest_framework.permissions import BasePermission


class EsAdministradora(BasePermission):
    message = "Solo la administradora puede gestionar el inventario."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None) == "administradora"
        )


class EsPersonalTaller(BasePermission):
    message = "No tienes permiso para consultar las opciones de consumo."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None)
            in {"administradora", "recepcionista", "costurera"}
        )


class PuedeRegistrarConsumos(BasePermission):
    message = "Solo administración o recepción puede registrar consumos."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "rol", None)
            in {"administradora", "recepcionista"}
        )
