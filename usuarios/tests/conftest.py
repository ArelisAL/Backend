"""
Fixtures y helpers para las pruebas del módulo usuarios (Backend/§4.1).

Datos ficticios (AGENTS.md §10.1): en desarrollo y pruebas se usan datos
ficticios, nunca datos reales de clientes.
"""

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from usuarios.models import ROL_ADMINISTRADORA, ROL_RECEPCIONISTA, Usuario

PASSWORD_TEST = "Password_2026x"


def crear_usuario(
    email, password=PASSWORD_TEST, nombre="Usuario", rol=ROL_RECEPCIONISTA, **extra
):
    """Crea un Usuario para las pruebas."""
    defaults = {"debe_cambiar_contraseña": False, "activo": True}
    defaults.update(extra)
    return Usuario.objects.create_user(
        email=email, password=password, nombre=nombre, rol=rol, **defaults
    )


def login_tokens(client, usuario, password=PASSWORD_TEST):
    """Llama a POST /api/v1/auth/login/ y devuelve JSON {access, refresh}."""
    respuesta = client.post(
        "/api/v1/auth/login/",
        data={"email": usuario.email, "password": password},
        format="json",
    )
    assert respuesta.status_code == 200, respuesta.json()
    return respuesta.json()


class ClientSeguro(APIClient):
    """APIClient que realiza peticiones https.

    Evita el 301 por SECURE_SSL_REDIRECT (config/settings.py) para que las
    pruebas puedan asertar códigos de respuesta directamente.
    """

    @staticmethod
    def _forzar_seguro(kwargs):
        kwargs["secure"] = True
        return kwargs

    def get(self, *args, **kwargs):
        return super().get(*args, **self._forzar_seguro(kwargs))

    def post(self, *args, **kwargs):
        return super().post(*args, **self._forzar_seguro(kwargs))

    def put(self, *args, **kwargs):
        return super().put(*args, **self._forzar_seguro(kwargs))

    def patch(self, *args, **kwargs):
        return super().patch(*args, **self._forzar_seguro(kwargs))

    def delete(self, *args, **kwargs):
        return super().delete(*args, **self._forzar_seguro(kwargs))


@pytest.fixture(autouse=True)
def limpiar_throttle():
    """Limpia el caché de throttling entre pruebas (SEG-02)."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return ClientSeguro()


@pytest.fixture
def usuario_admin():
    return crear_usuario(
        "admin@fran-costuras.com", nombre="Administradora", rol=ROL_ADMINISTRADORA
    )


@pytest.fixture
def usuario_recepcionista():
    return crear_usuario(
        "rec@fran-costuras.com", nombre="Recepcionista", rol=ROL_RECEPCIONISTA
    )


@pytest.fixture
def tokens_admin(client, usuario_admin):
    return login_tokens(client, usuario_admin)


@pytest.fixture
def tokens_recepcionista(client, usuario_recepcionista):
    return login_tokens(client, usuario_recepcionista)
