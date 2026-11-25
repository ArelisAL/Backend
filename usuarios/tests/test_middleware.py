"""
Pruebas del middleware BloqueoContrasenaTemporalMiddleware (C3, RF-M0-05, SEG-03).

Criterios:
- Dado un usuario con debe_cambiar_contraseña=True, cuando accedo a cualquier
  otro endpoint, entonces 403 {"error": "cambio_contraseña_requerido", ...}.
- Exentos: auth/yo/, auth/cambiar-contraseña/, auth/refresh/, auth/logout/.
- Dado debe_cambiar_contraseña=False, entonces acceso normal (200).
- Sin token → 401 (RNF-02); token inválido no se trata como bloqueo.
"""

import pytest

from .conftest import PASSWORD_TEST, crear_usuario, login_tokens


@pytest.mark.django_db
@pytest.mark.parametrize("ruta", ["/api/v1/usuarios/"])
def test_bloquea_endpoints_no_exentos(client, ruta):
    usuario = crear_usuario(
        "bloqueo@fran-costuras.com",
        debe_cambiar_contraseña=True,
        rol="administradora",
    )
    tokens = login_tokens(client, usuario)
    respuesta = client.get(ruta, HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "cambio_contraseña_requerido"
    assert set(respuesta.json()) == {"error", "detalle"}


@pytest.mark.django_db
def test_usuario_temporal_puede_consultar_su_estado_de_cuenta(client):
    usuario = crear_usuario("temporal@fran-costuras.com", debe_cambiar_contraseña=True)
    tokens = login_tokens(client, usuario)
    respuesta = client.get(
        "/api/v1/auth/yo/", HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["debe_cambiar_contraseña"] is True


@pytest.mark.django_db
def test_endpoints_exentos_no_bloqueados(client):
    usuario = crear_usuario("exento@fran-costuras.com", debe_cambiar_contraseña=True)
    tokens = login_tokens(client, usuario)

    respuesta = client.post(
        "/api/v1/auth/refresh/", data={"refresh": tokens["refresh"]}, format="json"
    )
    assert respuesta.status_code == 200
    rotados = respuesta.json()

    respuesta = client.post(
        "/api/v1/auth/logout/",
        data={"refresh": rotados["refresh"]},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {rotados['access']}",
    )
    assert respuesta.status_code == 204

    tokens = login_tokens(client, usuario)
    respuesta = client.post(
        "/api/v1/auth/cambiar-contrasena/",
        data={
            "contrasena_actual": PASSWORD_TEST,
            "nueva_contrasena": "Hilo-Morado-2026",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )
    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_sin_cambio_pendiente_no_bloqueado(client, usuario_recepcionista):
    tokens = login_tokens(client, usuario_recepcionista)
    respuesta = client.get(
        "/api/v1/auth/yo/", HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
    )
    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_anonimo_no_bloqueado(client):
    respuesta = client.get("/api/v1/auth/yo/")
    assert respuesta.status_code == 401
    assert respuesta.json()["error"] == "no_autenticado"


@pytest.mark.django_db
def test_token_invalido_da_401_no_403(client):
    respuesta = client.get(
        "/api/v1/auth/yo/", HTTP_AUTHORIZATION="Bearer no-es-un-token"
    )
    assert respuesta.status_code == 401
    assert set(respuesta.json()) == {"error", "detalle"}
