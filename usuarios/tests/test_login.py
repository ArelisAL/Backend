"""
Pruebas del endpoint POST /api/v1/auth/login/ (2.3, 2.6, SEG-02).

Criterios:
- Dado que no soy autenticado, cuando envío credenciales válidas, entonces
  recibo tokens de acceso y refresh (200).
- Dado credenciales inválidas, entonces 401 con formato {"error", "detalle"}.
- Dado más de 5 intentos por minuto, entonces 429 (SEG-02).
"""

import logging

import pytest
from django.test import override_settings

from .conftest import PASSWORD_TEST, crear_usuario


class TestAuthEndpoints:
    @pytest.mark.django_db
    def test_login_ok(self, client, usuario_recepcionista):
        respuesta = client.post(
            "/api/v1/auth/login/",
            data={"email": usuario_recepcionista.email, "password": PASSWORD_TEST},
            format="json",
        )
        assert respuesta.status_code == 200
        datos = respuesta.json()
        assert datos["access"]
        assert datos["refresh"]

    @pytest.mark.django_db
    def test_login_credenciales_invalidas_401(self, client, usuario_recepcionista):
        respuesta = client.post(
            "/api/v1/auth/login/",
            data={"email": usuario_recepcionista.email, "password": "wrong-password"},
            format="json",
        )
        assert respuesta.status_code == 401
        assert set(respuesta.json()) == {"error", "detalle"}
        assert respuesta.json()["error"] == "credenciales_invalidas"

    @pytest.mark.django_db
    @override_settings(GOOGLE_OAUTH_CLIENT_ID="fran-web-client-id")
    def test_login_google_entrega_tokens_a_cuenta_existente(
        self, client, usuario_recepcionista, monkeypatch
    ):
        from usuarios import services

        monkeypatch.setattr(
            services.id_token,
            "verify_oauth2_token",
            lambda credential, request, audience: {
                "email": usuario_recepcionista.email,
                "email_verified": True,
            },
        )
        respuesta = client.post(
            "/api/v1/auth/google/", {"credential": "token-ficticio"}, format="json"
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["access"]
        assert respuesta.json()["refresh"]

    @pytest.mark.django_db
    @override_settings(GOOGLE_OAUTH_CLIENT_ID="fran-web-client-id")
    def test_login_google_rechaza_cuenta_no_registrada(self, client, monkeypatch):
        from usuarios import services

        monkeypatch.setattr(
            services.id_token,
            "verify_oauth2_token",
            lambda *args, **kwargs: {
                "email": "no-registrada@example.com",
                "email_verified": True,
            },
        )
        respuesta = client.post(
            "/api/v1/auth/google/", {"credential": "token-ficticio"}, format="json"
        )
        assert respuesta.status_code == 401
        assert respuesta.json()["error"] == "credenciales_invalidas"

    @pytest.mark.django_db
    @override_settings(GOOGLE_OAUTH_CLIENT_ID="fran-web-client-id")
    def test_login_google_rechaza_correo_no_verificado(
        self, client, usuario_recepcionista, monkeypatch
    ):
        from usuarios import services

        monkeypatch.setattr(
            services.id_token,
            "verify_oauth2_token",
            lambda *args, **kwargs: {
                "email": usuario_recepcionista.email,
                "email_verified": False,
            },
        )
        respuesta = client.post(
            "/api/v1/auth/google/", {"credential": "token-ficticio"}, format="json"
        )
        assert respuesta.status_code == 401

    @pytest.mark.django_db
    @override_settings(GOOGLE_OAUTH_CLIENT_ID="")
    def test_login_google_sin_configuracion_devuelve_503(self, client):
        respuesta = client.post(
            "/api/v1/auth/google/", {"credential": "token-ficticio"}, format="json"
        )
        assert respuesta.status_code == 503
        assert respuesta.json()["error"] == "proveedor_no_disponible"

    @pytest.mark.django_db
    @override_settings(GOOGLE_OAUTH_CLIENT_ID="fran-web-client-id")
    def test_login_google_rechaza_token_invalido(self, client, monkeypatch):
        from usuarios import services

        def token_invalido(*args, **kwargs):
            raise ValueError("detalle privado que no se expone")

        monkeypatch.setattr(services.id_token, "verify_oauth2_token", token_invalido)
        respuesta = client.post(
            "/api/v1/auth/google/", {"credential": "token-ficticio"}, format="json"
        )
        assert respuesta.status_code == 401
        assert "detalle privado" not in respuesta.content.decode()

    @pytest.mark.django_db
    def test_login_email_inexistente_401(self, client):
        respuesta = client.post(
            "/api/v1/auth/login/",
            data={"email": "nadie@fran-costuras.com", "password": PASSWORD_TEST},
            format="json",
        )
        assert respuesta.status_code == 401
        assert respuesta.json()["error"] == "credenciales_invalidas"

    @pytest.mark.django_db
    def test_login_sin_campos_400(self, client):
        respuesta = client.post("/api/v1/auth/login/", data={}, format="json")
        assert respuesta.status_code == 400
        assert respuesta.json()["error"] == "datos_invalidos"

    @pytest.mark.django_db
    def test_login_throttled_429(self, client, usuario_recepcionista):
        # 5 intentos por minuto permitidos (SEG-02).
        for _ in range(5):
            respuesta = client.post(
                "/api/v1/auth/login/",
                data={"email": usuario_recepcionista.email, "password": PASSWORD_TEST},
                format="json",
            )
            assert respuesta.status_code == 200
        respuesta = client.post(
            "/api/v1/auth/login/",
            data={"email": usuario_recepcionista.email, "password": PASSWORD_TEST},
            format="json",
        )
        assert respuesta.status_code == 429
        assert respuesta.json()["error"] == "throttled"

    @pytest.mark.django_db
    def test_throttle_por_ip_con_correos_distintos_429(self, client):
        # Misma IP, 6 correos distintos: el límite por IP corta el sexto (SEG-02).
        for i in range(5):
            respuesta = client.post(
                "/api/v1/auth/login/",
                data={"email": f"n{i}@fran-costuras.com", "password": "x"},
                format="json",
                REMOTE_ADDR="10.0.0.1",
            )
            assert respuesta.status_code == 401
        respuesta = client.post(
            "/api/v1/auth/login/",
            data={"email": "n9@fran-costuras.com", "password": "x"},
            format="json",
            REMOTE_ADDR="10.0.0.1",
        )
        assert respuesta.status_code == 429
        assert set(respuesta.json()) == {"error", "detalle"}

    @pytest.mark.django_db
    def test_throttle_por_usuario_desde_ips_distintas_429(
        self, client, usuario_recepcionista
    ):
        # Mismo usuario desde 6 IPs distintas: el límite por usuario corta (SEG-02).
        for i in range(5):
            respuesta = client.post(
                "/api/v1/auth/login/",
                data={"email": usuario_recepcionista.email, "password": "mala"},
                format="json",
                REMOTE_ADDR=f"10.0.1.{i}",
            )
            assert respuesta.status_code == 401
        respuesta = client.post(
            "/api/v1/auth/login/",
            data={"email": usuario_recepcionista.email.upper(), "password": "mala"},
            format="json",
            REMOTE_ADDR="10.0.1.99",
        )
        assert respuesta.status_code == 429

    @pytest.mark.django_db
    def test_login_fallido_se_registra_sin_datos_personales(
        self, client, usuario_recepcionista, caplog, monkeypatch
    ):
        # El logger "usuarios" no propaga (settings.LOGGING); caplog escucha en raíz.
        monkeypatch.setattr(logging.getLogger("usuarios"), "propagate", True)
        with caplog.at_level("INFO", logger="usuarios"):
            client.post(
                "/api/v1/auth/login/",
                data={"email": usuario_recepcionista.email, "password": "mala-clave"},
                format="json",
            )
        mensajes = " ".join(r.getMessage() for r in caplog.records)
        assert "Inicio de sesión fallido" in mensajes
        assert usuario_recepcionista.email not in mensajes
        assert "mala-clave" not in mensajes

    @pytest.mark.django_db
    def test_usuario_desactivado_no_inicia_sesion(self, client):
        usuario = crear_usuario("baja@fran-costuras.com", activo=False)
        respuesta = client.post(
            "/api/v1/auth/login/",
            data={"email": usuario.email, "password": PASSWORD_TEST},
            format="json",
        )
        assert respuesta.status_code == 401
