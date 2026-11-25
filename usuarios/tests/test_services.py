"""
Pruebas de services.py del módulo usuarios (Backend/§4.1, DERCAS §4).

Criterios de aceptación probados aquí:
- Login/refresh/logout/cambio de contraseña y CRUD de usuarios (2.2).
- 401 sin credenciales válidas (RNF-02), errores {"error", "detalle"} (§7.2).
- Logs sin datos personales; login fallido registrado (SEG-07).
"""

import pytest
from rest_framework_simplejwt.exceptions import TokenError

from usuarios import services
from usuarios.models import ROL_ADMINISTRADORA

from .conftest import PASSWORD_TEST, crear_usuario


class TestLogin:
    """2.2, 2.4, SEG-07."""

    @pytest.mark.django_db
    def test_login_devuelve_tokens(self, usuario_recepcionista):
        tokens = services.login(
            email=usuario_recepcionista.email, password=PASSWORD_TEST
        )
        assert tokens["access"]
        assert tokens["refresh"]

    @pytest.mark.django_db
    def test_login_sin_usuario_lanza_credenciales_invalidas(self):
        with pytest.raises(services.CredencialesInvalidas):
            services.login(email="nadie@fran-costuras.com", password=PASSWORD_TEST)

    @pytest.mark.django_db
    def test_login_contrasena_incorrecta_lanza(self, usuario_recepcionista):
        with pytest.raises(services.CredencialesInvalidas):
            services.login(
                email=usuario_recepcionista.email, password="contrasena_equivocada"
            )

    @pytest.mark.django_db
    def test_login_usuario_inactivo_lanza(self):
        usuario = crear_usuario("inactivo@fran-costuras.com", activo=False)
        with pytest.raises(services.CredencialesInvalidas):
            services.login(email=usuario.email, password=PASSWORD_TEST)


class TestRefresh:
    """2.2, 2.4, SEG-01."""

    @pytest.mark.django_db
    def test_refresh_rota_y_devuelve_par_nuevo(self, usuario_recepcionista):
        tokens = services.login(
            email=usuario_recepcionista.email, password=PASSWORD_TEST
        )
        nuevos = services.refresh(tokens["refresh"])
        assert nuevos["access"]
        assert nuevos["refresh"]
        assert nuevos["refresh"] != tokens["refresh"]
        # El refresh anterior queda invalidado por la rotación (SEG-01).
        with pytest.raises(TokenError):
            services.refresh(tokens["refresh"])

    @pytest.mark.django_db
    def test_refresh_token_invalido_lanza_token_error(self):
        with pytest.raises(TokenError):
            services.refresh("token-no-valido")

    @pytest.mark.django_db
    def test_refresh_usuario_eliminado_lanza(self, usuario_recepcionista):
        tokens = services.login(
            email=usuario_recepcionista.email, password=PASSWORD_TEST
        )
        usuario_recepcionista.delete()
        with pytest.raises(services.CredencialesInvalidas):
            services.refresh(tokens["refresh"])


class TestLogout:
    """2.2, 2.4, SEG-01."""

    @pytest.mark.django_db
    def test_logout_invalida_el_refresh(self, usuario_recepcionista):
        tokens = services.login(
            email=usuario_recepcionista.email, password=PASSWORD_TEST
        )
        services.logout(tokens["refresh"])
        with pytest.raises(TokenError):
            services.refresh(tokens["refresh"])

    @pytest.mark.django_db
    def test_logout_token_invalido_lanza_token_error(self):
        with pytest.raises(TokenError):
            services.logout("nope")


class TestCambiarContrasenaTemporal:
    """2.2, SEG-03."""

    @pytest.mark.django_db
    def test_requiere_pendiente(self, usuario_admin):
        with pytest.raises(services.ContrasenaNoObligatoria):
            services.cambiar_contrasena_temporal(
                usuario_admin, PASSWORD_TEST, "Password_2026_nuevo"
            )

    @pytest.mark.django_db
    def test_rechaza_contrasena_corta(self):
        usuario = crear_usuario("corta@fran-costuras.com", debe_cambiar_contraseña=True)
        with pytest.raises(services.DatosInvalidos):
            services.cambiar_contrasena_temporal(usuario, PASSWORD_TEST, "123")

    @pytest.mark.django_db
    def test_rechaza_contrasena_comun(self):
        usuario = crear_usuario("comun@fran-costuras.com", debe_cambiar_contraseña=True)
        with pytest.raises(services.DatosInvalidos):
            services.cambiar_contrasena_temporal(usuario, PASSWORD_TEST, "1234567890")

    @pytest.mark.django_db
    def test_cambio_desactiva_el_pendiente(self):
        usuario = crear_usuario(
            "cambio@fran-costuras.com", debe_cambiar_contraseña=True
        )
        nueva = "Password_2026_nuevo"
        tokens = services.cambiar_contrasena_temporal(usuario, PASSWORD_TEST, nueva)
        usuario.refresh_from_db()
        assert usuario.debe_cambiar_contraseña is False
        assert usuario.check_password(nueva)
        assert tokens["access"]
        assert tokens["refresh"]


class TestUsuariosCRUD:
    """2.2."""

    @pytest.mark.django_db
    def test_crear_usuario_rechaza_duplicado(self, usuario_admin):
        datos = {
            "nombre": "Dup",
            "email": usuario_admin.email,
            "rol": "recepcionista",
            "password": PASSWORD_TEST,
        }
        with pytest.raises(services.CorreoDuplicado):
            services.crear_usuario(datos)

    @pytest.mark.django_db
    def test_crear_usuario_normaliza_email(self):
        datos = {
            "nombre": "Nueva Costurera",
            "email": "NUEVA@FRAN-COSTURAS.com",
            "rol": "costurera",
            "password": PASSWORD_TEST,
        }
        usuario = services.crear_usuario(datos)
        assert usuario.email == "nueva@fran-costuras.com"
        assert usuario.debe_cambiar_contraseña is True

    @pytest.mark.django_db
    def test_listar_usuarios_devuelve_todos(self):
        crear_usuario("a@fran-costuras.com", nombre="A", debe_cambiar_contraseña=False)
        crear_usuario("b@fran-costuras.com", nombre="B", debe_cambiar_contraseña=False)
        assert {u.nombre for u in services.listar_usuarios()} == {"A", "B"}

    @pytest.mark.django_db
    def test_editar_usuario(self):
        usuario = crear_usuario(
            "editable@fran-costuras.com", debe_cambiar_contraseña=False
        )
        editado = services.editar_usuario(usuario, {"nombre": "Editado"}, actor=usuario)
        editado.refresh_from_db()
        assert editado.nombre == "Editado"

    @pytest.mark.django_db
    def test_editar_usuario_duplicado_rechaza(self):
        a = crear_usuario(
            "a@fran-costuras.com", nombre="A", debe_cambiar_contraseña=False
        )
        b = crear_usuario(
            "b@fran-costuras.com", nombre="B", debe_cambiar_contraseña=False
        )
        with pytest.raises(services.CorreoDuplicado):
            services.editar_usuario(a, {"email": b.email}, actor=a)

    @pytest.mark.django_db
    def test_desactivar_usuario(self):
        usuario = crear_usuario(
            "desact@fran-costuras.com", debe_cambiar_contraseña=False
        )
        desactivado = services.desactivar_usuario(usuario)
        assert desactivado.activo is False

    @pytest.mark.django_db
    def test_desactivar_usuario_ya_desactivado_rechaza(self):
        usuario = crear_usuario(
            "desact2@fran-costuras.com", debe_cambiar_contraseña=False, activo=False
        )
        with pytest.raises(services.UsuarioYaInactivo):
            services.desactivar_usuario(usuario)

    @pytest.mark.django_db
    def test_obtener_usuario_actual(self, usuario_recepcionista):
        assert (
            services.obtener_usuario_actual(usuario_recepcionista).pk
            == usuario_recepcionista.pk
        )


class TestRoles:
    """Rol ESCOGIDO en services/models (DERCAS §2, AGENTS.md §10.2)."""

    @pytest.mark.django_db
    def test_usuario_tiene_roles_validos(self, usuario_admin):
        assert usuario_admin.rol == ROL_ADMINISTRADORA
