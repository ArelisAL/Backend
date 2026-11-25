"""
URLs raíz del Backend — contrato DERCAS §7.2 (rutas bajo /api/v1/).

- Documentación OpenAPI en /api/docs/ (drf-spectacular).
- Esquema expuesto en /api/esquema/ (drf-spectacular).
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("usuarios.urls")),
    path("api/v1/", include("clientes.urls")),
    path("api/v1/", include("pedidos.urls")),
    path("api/v1/", include("flujo.urls")),
    path("api/v1/", include("asignacion.urls")),
    path("api/v1/", include("inventario.urls")),
    path("api/v1/", include("pagos.urls")),
    path("api/v1/", include("servicios.urls")),
    path("api/v1/catalogo/", include("catalogo.urls")),
    path("api/esquema/", SpectacularAPIView.as_view(), name="esquema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="esquema"),
        name="api_docs",
    ),
]
