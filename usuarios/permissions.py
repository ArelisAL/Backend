"""
Permisos del módulo usuarios (2.3, DERCAS §5.1, SEG-04).

Cada endpoint exige JWT (RNF-02); sin token → 401 (sin permiso → 403).
Todo endpoint comprueba rol **y dueño del dato**.
"""

from rest_framework.permissions import BasePermission

from .models import ROL_ADMINISTRADORA


class EsAdministradora(BasePermission):
    """Permiso de rol: solo la administradora (AdminWeb; DERCAS §2)."""

    message = "Solo la administradora puede realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and getattr(usuario, "rol", None) == ROL_ADMINISTRADORA
        )


class EsDueñoUsuario(BasePermission):
    """Permiso de dueño del dato (SEG-04): ver tu propio usuario."""

    message = "Solo puedes acceder a tu propio usuario."

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated and obj.pk == usuario.pk)


class DueñoOAdministradora(BasePermission):
    """Dueño del dato o administradora (edición de usuarios)."""

    message = "Solo puedes editar tu propio usuario o debes ser administradora."

    def has_object_permission(self, request, view, obj):
        if EsAdministradora().has_permission(request, view):
            return True
        return EsDueñoUsuario().has_object_permission(request, view, obj)
