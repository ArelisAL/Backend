"""
Esqueleto del Backend (Fase 1, tarea 1.5): CORS (RNF-10) y rutas /api/v1/.

Datos ficticios; las peticiones van por https para no recibir el 301 de
SECURE_SSL_REDIRECT.
"""

import pytest
from django.conf import settings
from django.urls import resolve


@pytest.mark.parametrize("origen", ["http://localhost:5173", "http://localhost:5174"])
def test_cors_permite_frontend_y_adminweb(client, origen):
    respuesta = client.options(
        "/api/v1/auth/login/",
        HTTP_ORIGIN=origen,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        secure=True,
    )
    assert respuesta.headers.get("Access-Control-Allow-Origin") == origen


def test_cors_rechaza_otro_origen(client):
    respuesta = client.options(
        "/api/v1/auth/login/",
        HTTP_ORIGIN="http://sitio-ajeno.example",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        secure=True,
    )
    assert "Access-Control-Allow-Origin" not in respuesta.headers


def test_cors_por_defecto_solo_5173_y_5174():
    assert settings.CORS_ALLOWED_ORIGINS == [
        "http://localhost:5173",
        "http://localhost:5174",
    ]
    assert not getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False)


def test_rutas_de_la_api_bajo_api_v1():
    assert resolve("/api/v1/auth/login/")
    assert resolve("/api/docs/")


def test_base_de_datos_de_desarrollo_es_sqlite():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
