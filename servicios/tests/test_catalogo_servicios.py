from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from servicios.models import HistorialServicio, Servicio
from usuarios.models import Usuario


@pytest.fixture
def admin():
    return Usuario.objects.create_user(
        email="admin-servicios@fran-costuras.test",
        password="Password_2026x",
        nombre="Admin prueba",
        rol="administradora",
        debe_cambiar_contraseña=False,
    )


@pytest.fixture
def recepcionista():
    return Usuario.objects.create_user(
        email="recepcion-servicios@fran-costuras.test",
        password="Password_2026x",
        nombre="Recepción prueba",
        rol="recepcionista",
        debe_cambiar_contraseña=False,
    )


@pytest.fixture
def costurera():
    return Usuario.objects.create_user(
        email="costurera-servicios@fran-costuras.test",
        password="Password_2026x",
        nombre="Costurera prueba",
        rol="costurera",
        debe_cambiar_contraseña=False,
    )


@pytest.fixture
def cliente_api():
    return APIClient()


def datos_servicio(**cambios):
    return {
        "codigo": "ARR-TEST-001",
        "nombre": "Arreglo de prueba",
        "categoria": "Arreglos",
        "descripcion": "Servicio ficticio para pruebas.",
        "unidad": "prenda",
        **cambios,
    }


@pytest.mark.django_db
def test_sin_token_no_consulta_catalogo(cliente_api):
    respuesta = cliente_api.get("/api/v1/servicios/", secure=True)
    assert respuesta.status_code == 401
    assert respuesta.json()["error"] == "no_autenticado"


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["recepcionista", "costurera"])
def test_otros_roles_no_consultan_ni_modifican_catalogo(cliente_api, rol):
    usuario = Usuario.objects.create_user(
        email=f"{rol}@fran-costuras.test",
        password="Password_2026x",
        nombre=rol,
        rol=rol,
        debe_cambiar_contraseña=False,
    )
    cliente_api.force_authenticate(usuario)
    lista = cliente_api.get("/api/v1/servicios/", secure=True)
    creacion = cliente_api.post(
        "/api/v1/servicios/", datos_servicio(), format="json", secure=True
    )
    assert lista.status_code == 403
    assert lista.json() == {
        "error": "sin_permiso",
        "detalle": "Solo la administradora puede consultar o modificar el catálogo.",
    }
    assert creacion.status_code == 403
    assert Servicio.objects.count() == 0


@pytest.mark.django_db
def test_admin_crea_servicio_sin_precio_sin_asignar_cero_ni_activarlo(
    cliente_api, admin
):
    cliente_api.force_authenticate(admin)
    respuesta = cliente_api.post(
        "/api/v1/servicios/", datos_servicio(), format="json", secure=True
    )
    assert respuesta.status_code == 201, respuesta.json()
    assert respuesta.json()["tarifa_base"] is None
    assert respuesta.json()["configuracion_pendiente"] is True
    assert respuesta.json()["activo"] is False
    assert HistorialServicio.objects.filter(
        servicio_id=respuesta.json()["id"], accion="CREADO", usuario=admin
    ).exists()


@pytest.mark.django_db
def test_no_activa_servicio_sin_tarifa_o_valoracion_manual(cliente_api, admin):
    cliente_api.force_authenticate(admin)
    respuesta = cliente_api.post(
        "/api/v1/servicios/",
        datos_servicio(activo=True),
        format="json",
        secure=True,
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"] == "datos_invalidos"
    assert "tarifa sigue pendiente" in respuesta.json()["detalle"]
    assert Servicio.objects.count() == 0


@pytest.mark.django_db
def test_activa_con_tarifa_explicita_y_audita_cambios(cliente_api, admin):
    cliente_api.force_authenticate(admin)
    creada = cliente_api.post(
        "/api/v1/servicios/", datos_servicio(), format="json", secure=True
    )
    servicio_id = creada.json()["id"]
    respuesta = cliente_api.patch(
        f"/api/v1/servicios/{servicio_id}/",
        {"tarifa_base": "18.25", "activo": True},
        format="json",
        secure=True,
    )
    assert respuesta.status_code == 200, respuesta.json()
    assert respuesta.json()["tarifa_base"] == "18.25"
    assert respuesta.json()["activo"] is True
    eventos = list(HistorialServicio.objects.filter(servicio_id=servicio_id))
    assert len(eventos) == 2
    assert eventos[0].datos["anterior"]["tarifa_base"] is None
    assert eventos[0].datos["nuevo"]["tarifa_base"] == "18.25"
    listado = cliente_api.get("/api/v1/servicios/", secure=True)
    assert listado.status_code == 200
    assert listado.json()["count"] == 1
    assert Decimal(listado.json()["results"][0]["tarifa_base"]) == Decimal("18.25")


@pytest.mark.django_db
def test_admin_puede_editar_registro_enviando_su_codigo_actual(cliente_api, admin):
    cliente_api.force_authenticate(admin)
    creada = cliente_api.post(
        "/api/v1/servicios/", datos_servicio(), format="json", secure=True
    )
    servicio_id = creada.json()["id"]
    respuesta = cliente_api.patch(
        f"/api/v1/servicios/{servicio_id}/",
        datos_servicio(nombre="Nombre actualizado", tarifa_base="3.75"),
        format="json",
        secure=True,
    )
    assert respuesta.status_code == 200, respuesta.json()
    assert respuesta.json()["codigo"] == "ARR-TEST-001"
    assert respuesta.json()["nombre"] == "Nombre actualizado"
    assert respuesta.json()["tarifa_base"] == "3.75"


@pytest.mark.django_db
def test_valoracion_manual_se_puede_marcar_sin_inventar_tarifa(cliente_api, admin):
    cliente_api.force_authenticate(admin)
    respuesta = cliente_api.post(
        "/api/v1/servicios/",
        datos_servicio(requiere_valoracion=True, activo=True),
        format="json",
        secure=True,
    )
    assert respuesta.status_code == 201, respuesta.json()
    assert respuesta.json()["tarifa_base"] is None
    assert respuesta.json()["requiere_valoracion"] is True
    assert respuesta.json()["configuracion_pendiente"] is False


@pytest.mark.django_db
def test_rechaza_tarifa_con_mas_de_dos_decimales(cliente_api, admin):
    cliente_api.force_authenticate(admin)
    respuesta = cliente_api.post(
        "/api/v1/servicios/",
        datos_servicio(tarifa_base="4.125"),
        format="json",
        secure=True,
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"] == "datos_invalidos"
    assert Servicio.objects.count() == 0


@pytest.mark.django_db
def test_historial_paginado_solo_admin_y_no_hay_borrado_fisico(cliente_api, admin):
    cliente_api.force_authenticate(admin)
    creada = cliente_api.post(
        "/api/v1/servicios/", datos_servicio(), format="json", secure=True
    )
    servicio_id = creada.json()["id"]
    historial = cliente_api.get(
        f"/api/v1/servicios/{servicio_id}/historial/", secure=True
    )
    borrado = cliente_api.delete(f"/api/v1/servicios/{servicio_id}/", secure=True)
    assert historial.status_code == 200
    assert historial.json()["count"] == 1
    assert historial.json()["results"][0]["usuario_nombre"] == admin.nombre
    assert borrado.status_code == 405
    assert Servicio.objects.filter(pk=servicio_id).exists()
