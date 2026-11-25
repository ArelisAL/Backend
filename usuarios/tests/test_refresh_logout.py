"""
Pruebas de los endpoints POST /api/v1/auth/refresh/ y POST /api/v1/auth/logout/.

Criterios (SEG-01):
- Dado un refresh válido, cuando lo uso, entonces recibo un par nuevo.
- El refresh anterior está invalidado (401).
- Dado un refresh de una sesión cerrada, cuando lo uso, entonces 401.
"""

import pytest

from .conftest import login_tokens


class TestRefreshEndpoint:
    @pytest.mark.django_db
    def test_refresh_rota_y_devuelve_par_nuevo(self, client, usuario_recepcionista):
        tokens = login_tokens(client, usuario_recepcionista)
        respuesta = client.post(
            "/api/v1/auth/refresh/", data={"refresh": tokens["refresh"]}, format="json"
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()
        assert datos["access"]
        assert datos["refresh"]
        assert datos["refresh"] != tokens["refresh"]

    @pytest.mark.django_db
    def test_refresh_viejo_da_401_seg01(self, client, usuario_recepcionista):
        tokens = login_tokens(client, usuario_recepcionista)
        respuesta = client.post(
            "/api/v1/auth/refresh/", data={"refresh": tokens["refresh"]}, format="json"
        )
        assert respuesta.status_code == 200
        # El refresh usado queda en blacklist → 401 (SEG-01).
        respuesta = client.post(
            "/api/v1/auth/refresh/", data={"refresh": tokens["refresh"]}, format="json"
        )
        assert respuesta.status_code == 401
        assert set(respuesta.json()) == {"error", "detalle"}

    @pytest.mark.django_db
    def test_refresh_token_invalido_401(self, client):
        respuesta = client.post(
            "/api/v1/auth/refresh/", data={"refresh": "no-es-un-token"}, format="json"
        )
        assert respuesta.status_code == 401


class TestLogoutEndpoint:
    @pytest.mark.django_db
    def test_logout_invalida_refresh(self, client, usuario_recepcionista):
        tokens = login_tokens(client, usuario_recepcionista)
        respuesta = client.post(
            "/api/v1/auth/logout/",
            data={"refresh": tokens["refresh"]},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        assert respuesta.status_code == 204
        respuesta = client.post(
            "/api/v1/auth/refresh/", data={"refresh": tokens["refresh"]}, format="json"
        )
        assert respuesta.status_code == 401

    @pytest.mark.django_db
    def test_logout_sin_token_401(self, client):
        respuesta = client.post("/api/v1/auth/logout/", data={}, format="json")
        assert respuesta.status_code == 401
