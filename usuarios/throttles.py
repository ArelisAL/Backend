"""
Throttling del endpoint de login (2.6, DERCAS §5.1, SEG-02).

Máximo 5 intentos de inicio de sesión por minuto por usuario y por IP → 429.
"""

from collections.abc import Mapping

from rest_framework.exceptions import ParseError
from rest_framework.throttling import SimpleRateThrottle


class LoginPorUsuarioThrottle(SimpleRateThrottle):
    """Throttle 5/min por usuario (email de la petición)."""

    scope = "login_por_usuario"

    def get_cache_key(self, request, view):
        try:
            datos = request.data
        except ParseError:
            # Cuerpo ilegible: no hay usuario que limitar (sí se limita por IP).
            return None
        email = ""
        if isinstance(datos, Mapping):
            email = str(datos.get("email") or "").strip().lower()
        if not email:
            return None
        ident = f"usuario:{email}"
        return self.cache_format % {"scope": self.scope, "ident": ident}


class LoginPorIPThrottle(SimpleRateThrottle):
    """Throttle 5/min por IP (REMOTE_ADDR / X-Forwarded-For)."""

    scope = "login_por_ip"

    def get_cache_key(self, request, view):
        ident = f"ip:{self.get_ident(request)}"
        return self.cache_format % {"scope": self.scope, "ident": ident}
