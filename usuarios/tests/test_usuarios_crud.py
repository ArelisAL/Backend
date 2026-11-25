"""
Pruebas de GET/POST /api/v1/usuarios/, GET/PUT/PATCH/DELETE /api/v1/usuarios/{id}/
(2.2, 2.3, SEG-04: 401 sin token, 403 sin permiso o dato ajeno).
"""

import pytest


def _headers(tokens):
    return {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}


class TestUsuarioListView:
    @pytest.mark.django_db
    def test_listar_requiere_token(self, client):
        respuesta = client.get("/api/v1/usuarios/")
        assert respuesta.status_code == 401
        assert respuesta.json()["error"] == "no_autenticado"

    @pytest.mark.django_db
    def test_listar_como_administradora(
        self, client, usuario_admin, usuario_recepcionista, tokens_admin
    ):
        respuesta = client.get("/api/v1/usuarios/", **_headers(tokens_admin))
        assert respuesta.status_code == 200
        datos = respuesta.json()["results"]
        assert any(u["email"] == usuario_recepcionista.email for u in datos)

    @pytest.mark.django_db
    def test_listar_como_recepcionista_403(self, client, tokens_recepcionista):
        respuesta = client.get("/api/v1/usuarios/", **_headers(tokens_recepcionista))
        assert respuesta.status_code == 403
        assert respuesta.json()["error"] == "sin_permiso"

    @pytest.mark.django_db
    def test_crear_usuario(self, client, usuario_admin, tokens_admin):
        respuesta = client.post(
            "/api/v1/usuarios/",
            data={
                "nombre": "Costurera Nueva",
                "email": "costurera@fran-costuras.com",
                "rol": "costurera",
                "password": "Password_2026x",
            },
            format="json",
            **_headers(tokens_admin),
        )
        assert respuesta.status_code == 201
        datos = respuesta.json()
        assert datos["nombre"] == "Costurera Nueva"
        assert datos["debe_cambiar_contraseña"] is True

    @pytest.mark.django_db
    def test_crear_duplicado_409(self, client, usuario_admin, tokens_admin):
        respuesta = client.post(
            "/api/v1/usuarios/",
            data={
                "nombre": "Dup",
                "email": usuario_admin.email,
                "rol": "recepcionista",
                "password": "Password_2026x",
            },
            format="json",
            **_headers(tokens_admin),
        )
        assert respuesta.status_code == 409
        assert respuesta.json()["error"] == "correo_duplicado"

    @pytest.mark.django_db
    def test_crear_como_recepcionista_403(self, client, tokens_recepcionista):
        respuesta = client.post(
            "/api/v1/usuarios/",
            data={
                "nombre": "Otro",
                "email": "otro@fran-costuras.com",
                "rol": "costurera",
                "password": "Password_2026x",
            },
            format="json",
            **_headers(tokens_recepcionista),
        )
        assert respuesta.status_code == 403


class TestUsuarioDetailView:
    @pytest.mark.django_db
    def test_get_404_formato_error(self, client, tokens_admin):
        respuesta = client.get("/api/v1/usuarios/9999/", **_headers(tokens_admin))
        assert respuesta.status_code == 404
        assert respuesta.json()["error"] == "no_encontrado"

    @pytest.mark.django_db
    def test_recepcionista_no_puede_ver_usuarios(
        self, client, usuario_recepcionista, tokens_recepcionista
    ):
        respuesta = client.get(
            f"/api/v1/usuarios/{usuario_recepcionista.pk}/",
            **_headers(tokens_recepcionista),
        )
        assert respuesta.status_code == 403
        assert respuesta.json()["error"] == "sin_permiso"

    @pytest.mark.django_db
    def test_dueño_no_puede_ver_ajenos_403(
        self, client, usuario_admin, tokens_recepcionista
    ):
        respuesta = client.get(
            f"/api/v1/usuarios/{usuario_admin.pk}/", **_headers(tokens_recepcionista)
        )
        assert respuesta.status_code == 403

    @pytest.mark.django_db
    def test_recepcionista_no_puede_editar_usuarios(
        self, client, usuario_recepcionista, tokens_recepcionista
    ):
        respuesta = client.patch(
            f"/api/v1/usuarios/{usuario_recepcionista.pk}/",
            data={"nombre": "Nombre Nuevo"},
            format="json",
            **_headers(tokens_recepcionista),
        )
        assert respuesta.status_code == 403
        usuario_recepcionista.refresh_from_db()
        assert usuario_recepcionista.nombre == "Recepcionista"

    @pytest.mark.django_db
    def test_desactivar_por_administradora(
        self, client, usuario_recepcionista, tokens_admin
    ):
        respuesta = client.delete(
            f"/api/v1/usuarios/{usuario_recepcionista.pk}/", **_headers(tokens_admin)
        )
        assert respuesta.status_code == 204
        usuario_recepcionista.refresh_from_db()
        assert usuario_recepcionista.activo is False

    @pytest.mark.django_db
    def test_desactivar_por_dueño_403(
        self, client, usuario_recepcionista, tokens_recepcionista
    ):
        respuesta = client.delete(
            f"/api/v1/usuarios/{usuario_recepcionista.pk}/",
            **_headers(tokens_recepcionista),
        )
        assert respuesta.status_code == 403
        usuario_recepcionista.refresh_from_db()
        assert usuario_recepcionista.activo is True
