"""
Reglas de negocio del módulo usuarios (AGENTS.md §4.1, DERCAS §2 y §5.1).

Todo lo de reglas de negocio está aquí: vistas y serializers solo validan el
formato. Funciones (2.2): login, refresh, logout, cambiar contraseña
temporal, crear usuario, listar, editar, desactivar.

Referencias:
- DERCAS §2 (usuarios y roles), DERCAS §5.1 (SEG-01..07).
- Plan M0 §1: C3 (cambio obligatorio) y C4 (RF-M0-01..05).
- AGENTS.md §4.1 (capas), AGENTS.md §10.2 (Backend).
"""

import logging

from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as ValidationErrorDjango
from django.db import IntegrityError, transaction
from google.auth.exceptions import TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework_simplejwt.settings import api_settings as simplejwt_settings
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ROL_ADMINISTRADORA, Usuario

logger = logging.getLogger("usuarios")


class CredencialesInvalidas(Exception):
    """Usuario inexistente, inactivo o contraseña incorrecta (401)."""


class ProveedorGoogleNoDisponible(Exception):
    """La verificación Google no está configurada o no responde (503)."""


class ContrasenaNoObligatoria(Exception):
    """El usuario ya cambió su contraseña; no puede llamar al endpoint (400)."""


class DatosInvalidos(Exception):
    """Datos inválidos para una regla de negocio (400)."""


class CorreoDuplicado(Exception):
    """Ya existe un usuario con ese correo (409, RF-M0-01)."""


class AutoCambioRol(Exception):
    """La administradora intenta cambiarse el rol a sí misma (403, RF-M0-03)."""


class UltimaAdministradora(Exception):
    """Se intenta desactivar a la única administradora activa (409, RF-M0-04)."""


class UsuarioYaInactivo(Exception):
    """El usuario ya estaba desactivado (409)."""


class TokenAjeno(Exception):
    """El refresh enviado pertenece a otro usuario (403, SEG-04)."""


def _normalizar_email(email: str | None) -> str:
    """Normaliza el email a minúsculas para búsquedas y unicidad (DERCAS §2)."""
    return (email or "").strip().lower()


def _buscar_usuario(email: str) -> Usuario | None:
    return Usuario.objects.filter(email=_normalizar_email(email)).first()


def _contrasena_correcta(usuario: Usuario, password: str | None) -> bool:
    return bool(password) and usuario.check_password(password)


def _validar_contrasena_nueva(usuario: Usuario, nueva_contrasena: str | None) -> None:
    """Valida la contraseña por los validadores de Django (SEG-03).

    Longitud mínima 10 + validadores configurados en settings.
    """
    contrasena = nueva_contrasena or ""
    if len(contrasena) < 10:
        raise DatosInvalidos("La contraseña debe tener al menos 10 caracteres")
    try:
        password_validation.validate_password(contrasena, user=usuario)
    except ValidationErrorDjango as exc:
        raise DatosInvalidos("; ".join(exc.messages)) from exc


def _emitir_tokens(usuario: Usuario) -> dict:
    refresh_token = RefreshToken.for_user(usuario)
    return {"access": str(refresh_token.access_token), "refresh": str(refresh_token)}


def _invalidar_refresh_del_usuario(usuario: Usuario) -> None:
    """Pone en blacklist todos los refresh emitidos al usuario (SEG-01)."""
    for pendiente in OutstandingToken.objects.filter(user=usuario):
        BlacklistedToken.objects.get_or_create(token=pendiente)


def login(email: str, password: str | None) -> dict:
    """Autentica al usuario y devuelve los tokens {access, refresh} (2.2, 2.4).

    - Rechaza si el usuario no existe, no está activo o la contraseña es
      incorrecta → CredencialesInvalidas (401).
    - Registra en el log los inicios de sesión fallidos sin datos personales
      (SEG-07).
    """
    usuario = _buscar_usuario(email)
    if (
        usuario is None
        or not usuario.activo
        or not _contrasena_correcta(usuario, password)
    ):
        logger.info("Inicio de sesión fallido: credenciales inválidas")
        raise CredencialesInvalidas("Credenciales inválidas")
    return _emitir_tokens(usuario)


def login_con_google(credential: str) -> dict:
    """Verifica un ID token Google y autentica una cuenta ya creada.

    Nunca crea cuentas públicas. La firma, audiencia y expiración se verifican
    con la biblioteca oficial; además se exige correo verificado y usuario activo.
    """
    client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    if not client_id:
        raise ProveedorGoogleNoDisponible("El acceso con Google no está configurado")
    solicitud = google_requests.Request()

    def solicitud_limitada(url, method="GET", body=None, headers=None):
        return solicitud(url, method=method, body=body, headers=headers, timeout=5)

    try:
        datos = id_token.verify_oauth2_token(
            credential, solicitud_limitada, audience=client_id
        )
    except TransportError as exc:
        logger.warning("No se pudo contactar al verificador de Google")
        raise ProveedorGoogleNoDisponible(
            "El acceso con Google no está disponible temporalmente"
        ) from exc
    except ValueError as exc:
        logger.info("Inicio de sesión Google fallido: credencial inválida")
        raise CredencialesInvalidas("Credenciales inválidas") from exc

    if datos.get("email_verified") is not True or not datos.get("email"):
        logger.info("Inicio de sesión Google fallido: correo no verificado")
        raise CredencialesInvalidas("Credenciales inválidas")
    usuario = _buscar_usuario(datos["email"])
    if usuario is None or not usuario.activo:
        logger.info("Inicio de sesión Google fallido: cuenta no disponible")
        raise CredencialesInvalidas("Credenciales inválidas")
    return _emitir_tokens(usuario)


def refresh(refresh_token: str) -> dict:
    """Intercambia el refresh por un nuevo par de tokens (2.2, 2.4, SEG-01).

    - Token inválido, vencido o en blacklist → TokenError → 401 (SEG-01).
    - Rota el refresh (ROTATE_REFRESH_TOKENS) y invalida el anterior.
    """
    token = RefreshToken(refresh_token)
    usuario_id = token.get(simplejwt_settings.USER_ID_CLAIM)
    usuario = Usuario.objects.filter(pk=usuario_id).first() if usuario_id else None
    if usuario is None or not usuario.activo:
        raise CredencialesInvalidas("Usuario no activo")

    access_token = str(token.access_token)
    if simplejwt_settings.ROTATE_REFRESH_TOKENS:
        if simplejwt_settings.BLACKLIST_AFTER_ROTATION:
            token.blacklist()
        token.set_jti()
        token.set_exp()
        token.set_iat()
        token.outstand()
        return {"access": access_token, "refresh": str(token)}
    return {"access": access_token, "refresh": str(refresh_token)}  # pragma: no cover


def logout(refresh_token: str, usuario: Usuario | None = None) -> None:
    """Invalida el refresh (blacklist) sin borrar datos (2.2, 2.4, SEG-01).

    - Token inválido o ya invalidado → TokenError → 401.
    - Si se indica el usuario, el refresh debe ser suyo → TokenAjeno (SEG-04).
    """
    token = RefreshToken(refresh_token)
    if usuario is not None:
        dueno_id = token.get(simplejwt_settings.USER_ID_CLAIM)
        if str(dueno_id) != str(usuario.pk):
            raise TokenAjeno("El token de refresco no pertenece a tu sesión")
    token.blacklist()


def cambiar_contrasena_temporal(
    usuario: Usuario, contrasena_actual: str | None, nueva_contrasena: str | None
) -> dict:
    """Cambia la contraseña temporal del primer ingreso (2.2, SEG-03, C3).

    - Requiere que debe_cambiar_contraseña esté activo (ContrasenaNoObligatoria).
    - Exige la contraseña actual (CredencialesInvalidas si no coincide).
    - Valida la nueva con los validadores de Django (mínimo 10).
    - Marca debe_cambiar_contraseña=False, invalida los refresh anteriores y
      devuelve un par de tokens nuevo (rotación del refresh).
    """
    if not usuario.debe_cambiar_contraseña:
        raise ContrasenaNoObligatoria(
            "Ya cambiaste tu contraseña; no hay nada pendiente de cambiar"
        )
    if not _contrasena_correcta(usuario, contrasena_actual):
        logger.info("Cambio de contraseña rechazado: contraseña actual incorrecta")
        raise CredencialesInvalidas("La contraseña actual no es correcta")
    if contrasena_actual == nueva_contrasena:
        raise DatosInvalidos("La contraseña nueva debe ser distinta de la temporal")
    _validar_contrasena_nueva(usuario, nueva_contrasena)
    with transaction.atomic():
        usuario.set_password(nueva_contrasena)
        usuario.debe_cambiar_contraseña = False
        usuario.save(update_fields=["password", "debe_cambiar_contraseña"])
        _invalidar_refresh_del_usuario(usuario)
        return _emitir_tokens(usuario)


def crear_usuario(datos: dict) -> Usuario:
    """Crea un usuario por la administradora (2.2, RF-M0-01).

    - Correo único → CorreoDuplicado (409).
    - Contraseña temporal válida según SEG-03 → DatosInvalidos (400).
    - Queda con debe_cambiar_contraseña=True.
    """
    email = _normalizar_email(datos["email"])
    if Usuario.objects.filter(email=email).exists():
        raise CorreoDuplicado("Ya existe un usuario con ese correo")
    candidato = Usuario(email=email, nombre=datos["nombre"], rol=datos["rol"])
    _validar_contrasena_nueva(candidato, datos["password"])
    try:
        with transaction.atomic():
            return Usuario.objects.create_user(
                email=email,
                password=datos["password"],
                nombre=datos["nombre"],
                rol=datos["rol"],
                debe_cambiar_contraseña=True,
            )
    except IntegrityError as exc:
        # La restricción única también debe traducir colisiones simultáneas
        # al contrato funcional 409 y no dejar escapar un 500.
        if Usuario.objects.filter(email=email).exists():
            raise CorreoDuplicado("Ya existe un usuario con ese correo") from exc
        raise


def listar_usuarios(rol: str | None = None):
    """Lista los usuarios (2.2, RF-M0-02); paginado en la vista, filtro por rol."""
    usuarios = Usuario.objects.all().order_by("nombre", "pk")
    if rol:
        usuarios = usuarios.filter(rol=rol)
    return usuarios


def obtener_costurera_activa(usuario_id: int) -> Usuario | None:
    return Usuario.objects.filter(pk=usuario_id, rol="costurera", activo=True).first()


def editar_usuario(usuario: Usuario, datos: dict, actor: Usuario) -> Usuario:
    """Edita nombre, correo o rol (2.2, RF-M0-03).

    - La administradora no puede cambiarse su propio rol → AutoCambioRol (403).
    - Correo de otro usuario → CorreoDuplicado (409).
    - La desactivación va por desactivar_usuario (RF-M0-04), no por aquí.
    """
    campos_editables = ("nombre", "email", "rol")
    actualizados = {c: v for c, v in datos.items() if c in campos_editables}
    nuevo_rol = actualizados.get("rol")
    if usuario.pk == actor.pk and nuevo_rol and nuevo_rol != usuario.rol:
        raise AutoCambioRol("No puedes cambiar tu propio rol")
    if "email" in actualizados:
        actualizados["email"] = _normalizar_email(actualizados["email"])
        duplicado = Usuario.objects.filter(email=actualizados["email"]).exclude(
            pk=usuario.pk
        )
        if duplicado.exists():
            raise CorreoDuplicado("Ya existe un usuario con ese correo")
    if actualizados:
        try:
            with transaction.atomic():
                for campo, valor in actualizados.items():
                    setattr(usuario, campo, valor)
                usuario.save(update_fields=list(actualizados))
        except IntegrityError as exc:
            if (
                "email" in actualizados
                and Usuario.objects.filter(email=actualizados["email"])
                .exclude(pk=usuario.pk)
                .exists()
            ):
                usuario.refresh_from_db()
                raise CorreoDuplicado("Ya existe un usuario con ese correo") from exc
            raise
    return usuario


def desactivar_usuario(usuario: Usuario) -> Usuario:
    """Desactiva un usuario sin borrarlo (2.2, RF-M0-04).

    - Ya inactivo → UsuarioYaInactivo (409).
    - Única administradora activa → UltimaAdministradora (409).
    - Invalida sus refresh; sus access dejan de valer porque está inactivo.
    """
    if not usuario.activo:
        raise UsuarioYaInactivo("El usuario ya está desactivado")
    with transaction.atomic():
        if usuario.rol == ROL_ADMINISTRADORA:
            otras_activas = (
                Usuario.objects.select_for_update()
                .filter(rol=ROL_ADMINISTRADORA, activo=True)
                .exclude(pk=usuario.pk)
            )
            if not otras_activas.exists():
                raise UltimaAdministradora(
                    "No se puede desactivar a la única administradora activa"
                )
        usuario.activo = False
        usuario.save(update_fields=["activo"])
        _invalidar_refresh_del_usuario(usuario)
    return usuario


def obtener_usuario_actual(usuario: Usuario) -> Usuario:
    """Devuelve el usuario autenticado (auth/yo/; 2.2)."""
    return usuario
