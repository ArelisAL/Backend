"""Rutas REST del catálogo administrable de servicios."""

from django.urls import path

from . import views

app_name = "servicios"

urlpatterns = [
    path("servicios/", views.ServicioListView.as_view(), name="servicio_list"),
    path(
        "servicios/cotizables/",
        views.ServicioCotizableListView.as_view(),
        name="servicio_cotizables",
    ),
    path(
        "servicios/<int:servicio_id>/",
        views.ServicioDetailView.as_view(),
        name="servicio_detail",
    ),
    path(
        "servicios/<int:servicio_id>/historial/",
        views.ServicioHistorialView.as_view(),
        name="servicio_historial",
    ),
]
