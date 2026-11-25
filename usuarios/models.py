"""
Entidad Usuario — módulo M0 (DERCAS §2, §7.1).

Glosario del DERCAS §1.5: Usuario, rol, debe_cambiar_contraseña, activo.
Nombre en código en español, usando el glosario del DERCAS (AGENTS.md §1.1).
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

ROL_ADMINISTRADORA = "administradora"
ROL_RECEPCIONISTA = "recepcionista"
ROL_COSTURERA = "costurera"

ROL_CHOICES = [
    (ROL_ADMINISTRADORA, "Administradora"),
    (ROL_RECEPCIONISTA, "Recepcionista"),
    (ROL_COSTURERA, "Costurera"),
]


class UsuarioManager(BaseUserManager):
    """Manager del Usuario: email como USERNAME_FIELD (DERCAS §7.1)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError(_("El correo es obligatorio"))
        email = self.normalize_email(email).lower()
        extra.setdefault("debe_cambiar_contraseña", True)
        extra.setdefault("activo", True)
        usuario = self.model(email=email, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("rol", ROL_ADMINISTRADORA)
        return self._create_user(email, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuario del taller (DERCAS §2, §7.1): nombre, correo, contraseña, rol."""

    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    debe_cambiar_contraseña = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "rol"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return f"{self.nombre} ({self.email})" if self.nombre else self.email

    @property
    def is_active(self):
        """Mapeo para Django/SimpleJWT; el campo canónico es activo (DERCAS)."""
        return self.activo
