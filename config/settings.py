"""
Django settings — Fran-Costuras Backend (v1.4).

Fuente de verdad: DERCAS (§5.1, §7) y AGENTS.md §10.2.
Stack: Django 5.x + DRF + djangorestframework-simplejwt (JWT 15 min / 1 día,
rotación y blacklist) + drf-spectacular + django-cors-headers.
Secretos solo por variables de entorno (§10.1); nunca leemos ni modificamos
.env.
"""

import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.environ.get(name, "")
    items = [part.strip() for part in raw.split(",")]
    return [item for item in items if item] or list(default or [])


def _env_int(name: str, default: int | None = None) -> int | None:
    raw = os.environ.get(name)
    if not raw:
        return default
    return int(raw)


DEBUG = _env_bool("DEBUG", default=False)

# SECRET_KEY solo por variable de entorno (AGENTS.md §10.1). La clave de
# respaldo sirve únicamente en desarrollo (DEBUG=True); con DEBUG=False
# (producción) la API no arranca sin SECRET_KEY.
_CLAVE_SOLO_DESARROLLO = (
    "solo-desarrollo-no-usar-en-produccion-fran-costuras-0123456789abcdef"
)
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "Falta la variable de entorno SECRET_KEY (obligatoria con DEBUG=False)."
        )
    SECRET_KEY = _CLAVE_SOLO_DESARROLLO

# AGENTS.md §3 y §10.2: la variable se llama DJANGO_ALLOWED_HOSTS.
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "usuarios",
    "catalogo",
    "clientes",
    "pedidos",
    "flujo",
    "asignacion",
    "inventario",
    "pagos",
    "servicios",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # RNF-10: CORS solo para Frontend y AdminWeb (debe ir antes de CommonMiddleware).
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.BloqueoContrasenaTemporalMiddleware",
]

AUTH_USER_MODEL = "usuarios.Usuario"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

_DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if _DATABASE_URL:
    _database = urlparse(_DATABASE_URL)
    if _database.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL debe usar PostgreSQL.")
    _database_options = parse_qs(_database.query)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(_database.path.lstrip("/")),
            "USER": unquote(_database.username or ""),
            "PASSWORD": unquote(_database.password or ""),
            "HOST": _database.hostname or "",
            "PORT": str(_database.port or ""),
            "CONN_MAX_AGE": 0,
            "OPTIONS": {
                "sslmode": _database_options.get("sslmode", ["require"])[0],
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.environ.get("DB_NAME", "db.sqlite3"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# --- Seguridad (DERCAS §5.1, SEG-01..07) -----------------------------------
# Por defecto activos (producción). Solo con DEBUG=True (desarrollo local con
# runserver sobre http) se desactivan si no se indica otra cosa.
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_HSTS_SECONDS = _env_int("SECURE_HSTS_SECONDS", default=0 if DEBUG else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", default=not DEBUG)

# --- DRF / JWT / OpenAPI ---------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "login_por_usuario": "5/min",
        "login_por_ip": "5/min",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "config.exception_handler.manejador_errores_personalizado",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API Fran-Costuras",
    "DESCRIPTION": "API REST del taller Fran-Costuras (v1.4) — DERCAS §7.2.",
    "VERSION": "1.0.0",
    # Pedido.estado e HistorialEstado comparten el mismo conjunto de estados.
    "ENUM_NAME_OVERRIDES": {"EstadoPedidoEnum": "pedidos.models.Pedido.ESTADOS"},
}

CORS_ALLOWED_ORIGINS = _env_list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
)

# --- Idioma / localización --------------------------------------------------
LANGUAGE_CODE = "es-ES"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Logging ----------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "usuarios": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "pagos": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
