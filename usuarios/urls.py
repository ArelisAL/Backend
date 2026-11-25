"""
URLs del módulo usuarios (2.3, DERCAS §7.2): rutas bajo /api/v1/.
"""

from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("auth/login/", views.LoginView.as_view(), name="auth_login"),
    path("auth/google/", views.LoginGoogleView.as_view(), name="auth_google"),
    path("auth/refresh/", views.RefreshView.as_view(), name="auth_refresh"),
    path("auth/yo/", views.YoView.as_view(), name="auth_yo"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth_logout"),
    path(
        "auth/cambiar-contrasena/",
        views.CambiarContrasenaView.as_view(),
        name="auth_cambiar_contrasena_ascii",
    ),
    path(
        "auth/cambiar-contraseña/",
        views.CambiarContrasenaView.as_view(),
        name="auth_cambiar_contrasena_legacy",
    ),
    path("usuarios/", views.UsuarioListView.as_view(), name="usuario_list"),
    path(
        "usuarios/<int:pk>/",
        views.UsuarioDetailView.as_view(),
        name="usuario_detail",
    ),
]
