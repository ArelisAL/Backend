"""
Vistas del módulo usuarios (2.3): token + permiso + llamar al servicio +
responder JSON. Sin lógica de negocio (todo lo de negocio está en services.py).

OpenAPI (2.6): documentación drf-spectacular en /api/docs/ con ejemplos de
error 400/401/403/404/409/429 en formato {"error", "detalle"}.
"""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from . import services
from .models import ROL_CHOICES
from .permissions import EsAdministradora
from .serializers import (
    CambiarContrasenaSerializer,
    CrearUsuarioSerializer,
    EditarUsuarioSerializer,
    ErrorSerializer,
    FiltroUsuariosSerializer,
    LoginGoogleSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
    UsuarioSerializer,
)
from .throttles import LoginPorIPThrottle, LoginPorUsuarioThrottle

# --- Respuestas de error documentadas (OpenAPI) -----------------------------


def _doc_error(descripcion: str, codigo: str, detalle: str) -> OpenApiResponse:
    return OpenApiResponse(
        response=ErrorSerializer,
        description=descripcion,
        examples=[
            OpenApiExample(codigo, value={"error": codigo, "detalle": detalle}),
        ],
    )


ERROR_400 = _doc_error("Datos inválidos", "datos_invalidos", "Este campo es requerido.")
ERROR_401 = _doc_error(
    "Sin token válido",
    "no_autenticado",
    "Las credenciales de autenticación no se proveyeron.",
)
ERROR_403 = _doc_error(
    "Sin permiso o cambio de contraseña pendiente",
    "sin_permiso",
    "Solo la administradora puede realizar esta acción.",
)
ERROR_404 = _doc_error("No existe", "no_encontrado", "No encontrado.")
ERROR_409_CORREO = _doc_error(
    "Correo duplicado", "correo_duplicado", "Ya existe un usuario con ese correo"
)
ERROR_429 = _doc_error(
    "Límite de intentos de inicio de sesión (5 por minuto)",
    "throttled",
    "Solicitud fue regulada (throttled). Expected available in 60 seconds.",
)


def _error(codigo: str, exc: Exception, estado: int) -> Response:
    return Response({"error": codigo, "detalle": str(exc)}, status=estado)


# --- Autenticación ----------------------------------------------------------


class LoginView(APIView):
    """POST /api/v1/auth/login/ — tokens de acceso y refresh (DERCAS §7.2)."""

    authentication_classes = []
    permission_classes = []
    throttle_classes = [LoginPorUsuarioThrottle, LoginPorIPThrottle]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: LoginResponseSerializer,
            400: ERROR_400,
            401: _doc_error(
                "Credenciales inválidas",
                "credenciales_invalidas",
                "Credenciales inválidas",
            ),
            429: ERROR_429,
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = services.login(**serializer.validated_data)
        except services.CredencialesInvalidas as exc:
            return _error("credenciales_invalidas", exc, status.HTTP_401_UNAUTHORIZED)
        return Response(tokens, status=status.HTTP_200_OK)


class LoginGoogleView(APIView):
    """POST /api/v1/auth/google/ — verifica Google y entrega JWT propio."""

    authentication_classes = []
    permission_classes = []
    throttle_classes = [LoginPorIPThrottle]

    @extend_schema(
        request=LoginGoogleSerializer,
        responses={
            200: LoginResponseSerializer,
            400: ERROR_400,
            401: _doc_error(
                "Credencial Google inválida o cuenta no habilitada",
                "credenciales_invalidas",
                "Credenciales inválidas",
            ),
            429: ERROR_429,
            503: _doc_error(
                "Verificación de Google no configurada o temporalmente indisponible",
                "proveedor_no_disponible",
                "El acceso con Google no está disponible temporalmente",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginGoogleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = services.login_con_google(serializer.validated_data["credential"])
        except services.CredencialesInvalidas as exc:
            return _error("credenciales_invalidas", exc, status.HTTP_401_UNAUTHORIZED)
        except services.ProveedorGoogleNoDisponible:
            return Response(
                {
                    "error": "proveedor_no_disponible",
                    "detalle": "El acceso con Google no está disponible temporalmente",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(tokens, status=status.HTTP_200_OK)


class RefreshView(APIView):
    """POST /api/v1/auth/refresh/ (2.2, 2.4, SEG-01)."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=RefreshSerializer,
        responses={
            200: LoginResponseSerializer,
            400: ERROR_400,
            401: _doc_error(
                "Refresh inválido, reutilizado o de sesión cerrada",
                "token_invalido",
                "El token está en la lista negra",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = services.refresh(serializer.validated_data["refresh"])
        except TokenError as exc:
            return _error("token_invalido", exc, status.HTTP_401_UNAUTHORIZED)
        except services.CredencialesInvalidas as exc:
            return _error("credenciales_invalidas", exc, status.HTTP_401_UNAUTHORIZED)
        return Response(tokens, status=status.HTTP_200_OK)


class YoView(APIView):
    """GET /api/v1/auth/yo/ (2.2): datos del usuario autenticado."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: UsuarioSerializer,
            401: ERROR_401,
            403: _doc_error(
                "Cambio de contraseña pendiente",
                "cambio_contraseña_requerido",
                "Debes cambiar tu contraseña temporal antes de continuar.",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        usuario = services.obtener_usuario_actual(request.user)
        return Response(UsuarioSerializer(usuario).data)


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ (2.2, 2.4, SEG-01): invalida el refresh."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={
            204: OpenApiResponse(description="Sesión cerrada"),
            400: ERROR_400,
            401: ERROR_401,
            403: _doc_error(
                "El refresh es de otro usuario",
                "token_ajeno",
                "El token de refresco no pertenece a tu sesión",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.logout(serializer.validated_data["refresh"], request.user)
        except TokenError as exc:
            return _error("token_invalido", exc, status.HTTP_401_UNAUTHORIZED)
        except services.TokenAjeno as exc:
            return _error("token_ajeno", exc, status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CambiarContrasenaView(APIView):
    """POST /api/v1/auth/cambiar-contraseña/ (2.2, SEG-03, RF-M0-05)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CambiarContrasenaSerializer,
        responses={
            200: OpenApiResponse(
                response=LoginResponseSerializer,
                description="Contraseña cambiada; par de tokens nuevo (rotación).",
            ),
            400: _doc_error(
                "Contraseña nueva inválida o sin cambio pendiente",
                "datos_invalidos",
                "La contraseña debe tener al menos 10 caracteres",
            ),
            401: _doc_error(
                "Sin token o contraseña actual incorrecta",
                "credenciales_invalidas",
                "La contraseña actual no es correcta",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = CambiarContrasenaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = services.cambiar_contrasena_temporal(
                request.user, **serializer.validated_data
            )
        except services.CredencialesInvalidas as exc:
            return _error("credenciales_invalidas", exc, status.HTTP_401_UNAUTHORIZED)
        except services.ContrasenaNoObligatoria as exc:
            return _error("contrasena_no_obligatoria", exc, status.HTTP_400_BAD_REQUEST)
        except services.DatosInvalidos as exc:
            return _error("datos_invalidos", exc, status.HTTP_400_BAD_REQUEST)
        return Response(tokens, status=status.HTTP_200_OK)


# --- Gestión de usuarios (solo administradora) ------------------------------


class UsuarioListView(APIView):
    """GET y POST /api/v1/usuarios/ (RF-M0-01, RF-M0-02)."""

    permission_classes = [IsAuthenticated, EsAdministradora]

    @extend_schema(
        parameters=[
            OpenApiParameter("rol", str, enum=[valor for valor, _ in ROL_CHOICES]),
            OpenApiParameter("page", int),
        ],
        responses={
            200: UsuarioSerializer(many=True),
            400: ERROR_400,
            401: ERROR_401,
            403: ERROR_403,
        },
    )
    def get(self, request, *args, **kwargs):
        filtro = FiltroUsuariosSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        usuarios = services.listar_usuarios(**filtro.validated_data)
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(usuarios, request, view=self)
        return paginador.get_paginated_response(
            UsuarioSerializer(pagina, many=True).data
        )

    @extend_schema(
        request=CrearUsuarioSerializer,
        responses={
            201: UsuarioSerializer,
            400: ERROR_400,
            401: ERROR_401,
            403: ERROR_403,
            409: ERROR_409_CORREO,
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = CrearUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            usuario = services.crear_usuario(serializer.validated_data)
        except services.CorreoDuplicado as exc:
            return _error("correo_duplicado", exc, status.HTTP_409_CONFLICT)
        except services.DatosInvalidos as exc:
            return _error("datos_invalidos", exc, status.HTTP_400_BAD_REQUEST)
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)


class UsuarioDetailView(APIView):
    """GET/PUT/PATCH/DELETE /api/v1/usuarios/{id}/ (RF-M0-03, RF-M0-04).

    DELETE desactiva (activo=False); nunca borra el registro.
    """

    permission_classes = [IsAuthenticated, EsAdministradora]

    def _obtener(self, pk):
        return get_object_or_404(services.listar_usuarios(), pk=pk)

    @extend_schema(
        responses={
            200: UsuarioSerializer,
            401: ERROR_401,
            403: ERROR_403,
            404: ERROR_404,
        }
    )
    def get(self, request, pk, *args, **kwargs):
        return Response(UsuarioSerializer(self._obtener(pk)).data)

    @extend_schema(
        request=EditarUsuarioSerializer,
        responses={
            200: UsuarioSerializer,
            400: ERROR_400,
            401: ERROR_401,
            403: _doc_error(
                "Sin permiso o intento de cambiar el propio rol",
                "auto_cambio_rol",
                "No puedes cambiar tu propio rol",
            ),
            404: ERROR_404,
            409: ERROR_409_CORREO,
        },
    )
    def patch(self, request, pk, *args, **kwargs):
        usuario = self._obtener(pk)
        serializer = EditarUsuarioSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            usuario = services.editar_usuario(
                usuario, serializer.validated_data, actor=request.user
            )
        except services.AutoCambioRol as exc:
            return _error("auto_cambio_rol", exc, status.HTTP_403_FORBIDDEN)
        except services.CorreoDuplicado as exc:
            return _error("correo_duplicado", exc, status.HTTP_409_CONFLICT)
        return Response(UsuarioSerializer(usuario).data)

    @extend_schema(
        request=EditarUsuarioSerializer,
        responses={
            200: UsuarioSerializer,
            400: ERROR_400,
            401: ERROR_401,
            403: ERROR_403,
            404: ERROR_404,
            409: ERROR_409_CORREO,
        },
    )
    def put(self, request, pk, *args, **kwargs):
        return self.patch(request, pk, *args, **kwargs)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Usuario desactivado (no se borra)"),
            401: ERROR_401,
            403: ERROR_403,
            404: ERROR_404,
            409: _doc_error(
                "Única administradora activa o usuario ya inactivo",
                "ultima_administradora",
                "No se puede desactivar a la única administradora activa",
            ),
        },
    )
    def delete(self, request, pk, *args, **kwargs):
        usuario = self._obtener(pk)
        try:
            services.desactivar_usuario(usuario)
        except services.UltimaAdministradora as exc:
            return _error("ultima_administradora", exc, status.HTTP_409_CONFLICT)
        except services.UsuarioYaInactivo as exc:
            return _error("usuario_inactivo", exc, status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)
