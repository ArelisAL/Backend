"""
Serializers del módulo usuarios (2.3): forma del JSON y validación de
formato — sin reglas de negocio (todo lo de reglas de negocio está en
usuarios/services.py). Nunca exponen el hash ni la contraseña (RF-M0-02).
"""

from rest_framework import serializers

from .models import ROL_CHOICES, Usuario


class ErrorSerializer(serializers.Serializer):
    """Formato de error del contrato (DERCAS §7.2)."""

    error = serializers.CharField()
    detalle = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    """Formato de POST /api/v1/auth/login/."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginGoogleSerializer(serializers.Serializer):
    """Formato de POST /api/v1/auth/google/: token de identidad, no OAuth code."""

    credential = serializers.CharField(
        write_only=True, trim_whitespace=True, max_length=8192
    )


class LoginResponseSerializer(serializers.Serializer):
    """Respuesta con el par de tokens (login, refresh, cambio de contraseña)."""

    access = serializers.CharField()
    refresh = serializers.CharField()


class RefreshSerializer(serializers.Serializer):
    """Formato de POST /api/v1/auth/refresh/."""

    refresh = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    """Formato de POST /api/v1/auth/logout/."""

    refresh = serializers.CharField(write_only=True)


class CambiarContrasenaSerializer(serializers.Serializer):
    """Formato de POST /api/v1/auth/cambiar-contraseña/ (C3)."""

    contrasena_actual = serializers.CharField(write_only=True)
    nueva_contrasena = serializers.CharField(write_only=True)


class UsuarioSerializer(serializers.ModelSerializer):
    """Datos públicos del usuario (solo lectura; sin hash ni contraseña)."""

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "rol", "activo", "debe_cambiar_contraseña"]
        read_only_fields = fields


class FiltroUsuariosSerializer(serializers.Serializer):
    """Parámetros de GET /api/v1/usuarios/ (RF-M0-02)."""

    rol = serializers.ChoiceField(choices=ROL_CHOICES, required=False)


class CrearUsuarioSerializer(serializers.Serializer):
    """Formato de POST /api/v1/usuarios/ (reglas de negocio en services)."""

    nombre = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    rol = serializers.ChoiceField(choices=ROL_CHOICES)
    password = serializers.CharField(write_only=True)


class EditarUsuarioSerializer(serializers.Serializer):
    """Formato de PUT/PATCH /api/v1/usuarios/{id}/ (RF-M0-03)."""

    nombre = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    rol = serializers.ChoiceField(choices=ROL_CHOICES, required=False)
