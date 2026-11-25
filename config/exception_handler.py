"""
Manejador global de excepciones — contrato DERCAS §7.2.

Todo error de la API devuelve {"error": codigo, "detalle": mensaje} sin trazas
internas; códigos: no_autenticado (401), sin_permiso (403), credenciales_invalidas
(401), datos_invalidos (400), no_encontrado (404), error_interno (500).
Referencia: AGENTS.md §4.1, DERCAS §7.2.
"""

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.views import exception_handler as manejador_drf

CODIGOS = [
    (Http404, "no_encontrado"),
    (DjangoPermissionDenied, "sin_permiso"),
    (NotAuthenticated, "no_autenticado"),
    (AuthenticationFailed, "credenciales_invalidas"),
    (PermissionDenied, "sin_permiso"),
    (NotFound, "no_encontrado"),
    (ValidationError, "datos_invalidos"),
    (Throttled, "throttled"),
    (APIException, "error_api"),
]


def _codigo_de(exc: Exception) -> str:
    for clase, codigo in CODIGOS:
        if isinstance(exc, clase):
            return codigo
    return type(exc).__name__.lower()


def _texto(data):
    """Vuelve a una lista de cadenas de detalle a partir de data del response."""
    partes: list[str] = []
    if isinstance(data, dict):
        if "detail" in data:
            return [str(data["detail"])]
        for valor in data.values():
            partes.extend(_texto(valor))
    elif isinstance(data, (list, tuple)):
        for valor in data:
            partes.extend(_texto(valor))
    elif data is not None:
        partes.append(str(data))
    return partes


def manejador_errores_personalizado(exc, context):
    """Adapta errores de DRF al formato {"error", "detalle"} del contrato."""
    response = manejador_drf(exc, context)
    if response is None:
        return None
    detalle = "; ".join(_texto(response.data)) or "Error en la solicitud."
    response.data = {"error": _codigo_de(exc), "detalle": detalle}
    return response
