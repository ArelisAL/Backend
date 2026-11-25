"""Middleware de Fran-Costuras Backend.

Módulo M0 usuarios (2.5): mientras el usuario debe cambiar su contraseña
(debe_cambiar_contraseña=True) se bloquean todos los endpoints salvo
``auth/cambiar-contraseña/``, ``auth/refresh/`` y ``auth/logout/`` → HTTP 403.

Referencia: DERCAS §2 y AGENTS.md §10.2 (SEG-03).
"""

from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

EXENTOS_2_5 = (
    # Los clientes consultan este endpoint tras el login para decidir si deben
    # mostrar el cambio obligatorio de contraseña. Solo expone el perfil propio.
    "/api/v1/auth/yo/",
    "/api/v1/auth/cambiar-contrasena/",
    # Alias anterior; Vercel puede no resolver de forma consistente rutas con ñ.
    "/api/v1/auth/cambiar-contraseña/",
    "/api/v1/auth/refresh/",
    "/api/v1/auth/logout/",
)


class BloqueoContrasenaTemporalMiddleware:
    """Bloquea endpoints salvo los de auth mientras cambio_contrasena pendiente."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._requiere_cambio_contrasena(request):
            return JsonResponse(
                {
                    "error": "cambio_contraseña_requerido",
                    "detalle": (
                        "Debes cambiar tu contraseña temporal antes de continuar. "
                        "Usa POST /api/v1/auth/cambiar-contraseña/."
                    ),
                },
                status=403,
            )
        return self.get_response(request)

    def _requiere_cambio_contrasena(self, request):
        if any(self._igual(request.path, exento) for exento in EXENTOS_2_5):
            return False
        usuario = getattr(request, "user", None)
        if not getattr(usuario, "is_authenticated", False):
            usuario = self._usuario_jwt(request)
        if not getattr(usuario, "is_authenticated", False):
            return False
        return bool(getattr(usuario, "debe_cambiar_contraseña", False))

    @staticmethod
    def _igual(path_a: str, path_b: str) -> bool:
        return path_a.rstrip("/") == path_b.rstrip("/")

    @staticmethod
    def _usuario_jwt(request):
        try:
            autenticado = JWTAuthentication().authenticate(request)
        except AuthenticationFailed:
            # Token inválido, vencido o de usuario inactivo: la vista responde 401.
            return None
        return autenticado[0] if autenticado else None
