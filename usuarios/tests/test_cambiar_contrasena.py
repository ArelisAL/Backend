"""
Pruebas del endpoint POST /api/v1/auth/cambiar-contraseña/ (C3, RF-M0-05, SEG-03).

Criterios:
- Dado que inicio sesión con contraseña temporal, cuando envío la actual y
  una nueva válida, entonces debe_cambiar_contraseña=False, recibo un par de
  tokens nuevo (rotación) y puedo usar el sistema.
- Contraseña actual incorrecta → 401; nueva corta o común → 400.
- El refresh anterior al cambio queda invalidado (rotación).
- Sin token → 401 (RNF-02).
"""

import pytest

from .conftest import PASSWORD_TEST, crear_usuario, login_tokens

URL = "/api/v1/auth/cambiar-contrasena/"
URL_ANTERIOR = "/api/v1/auth/cambiar-contraseña/"
NUEVA = "Hilo-Morado-2026"


def _cambiar(client, tokens, actual=PASSWORD_TEST, nueva=NUEVA):
    return client.post(
        URL,
        data={"contrasena_actual": actual, "nueva_contrasena": nueva},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )


@pytest.fixture
def usuario_temporal():
    return crear_usuario("pendiente@fran-costuras.com", debe_cambiar_contraseña=True)


@pytest.mark.django_db
def test_cambio_ok_desbloquea_y_rota_tokens(client, usuario_temporal):
    tokens = login_tokens(client, usuario_temporal)
    respuesta = _cambiar(client, tokens)
    assert respuesta.status_code == 200
    nuevos = respuesta.json()
    assert set(nuevos) == {"access", "refresh"}
    usuario_temporal.refresh_from_db()
    assert usuario_temporal.debe_cambiar_contraseña is False
    assert usuario_temporal.check_password(NUEVA)

    respuesta = client.get(
        "/api/v1/auth/yo/", HTTP_AUTHORIZATION=f"Bearer {nuevos['access']}"
    )
    assert respuesta.status_code == 200

    # El refresh previo al cambio quedó invalidado.
    respuesta = client.post(
        "/api/v1/auth/refresh/", data={"refresh": tokens["refresh"]}, format="json"
    )
    assert respuesta.status_code == 401
    # El nuevo sí funciona.
    respuesta = client.post(
        "/api/v1/auth/refresh/", data={"refresh": nuevos["refresh"]}, format="json"
    )
    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_contrasena_actual_incorrecta_401(client, usuario_temporal):
    tokens = login_tokens(client, usuario_temporal)
    respuesta = _cambiar(client, tokens, actual="otra-cosa-1234")
    assert respuesta.status_code == 401
    assert respuesta.json()["error"] == "credenciales_invalidas"
    usuario_temporal.refresh_from_db()
    assert usuario_temporal.debe_cambiar_contraseña is True


@pytest.mark.django_db
def test_contrasena_corta_400(client, usuario_temporal):
    tokens = login_tokens(client, usuario_temporal)
    respuesta = _cambiar(client, tokens, nueva="123")
    assert respuesta.status_code == 400
    assert set(respuesta.json()) == {"error", "detalle"}
    assert respuesta.json()["error"] == "datos_invalidos"


@pytest.mark.django_db
def test_falta_contrasena_actual_400(client, usuario_temporal):
    tokens = login_tokens(client, usuario_temporal)
    respuesta = client.post(
        URL,
        data={"nueva_contrasena": NUEVA},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"] == "datos_invalidos"


@pytest.mark.django_db
def test_sin_cambio_pendiente_400(client, usuario_recepcionista):
    tokens = login_tokens(client, usuario_recepcionista)
    respuesta = _cambiar(client, tokens)
    assert respuesta.status_code == 400
    assert respuesta.json()["error"] == "contrasena_no_obligatoria"


@pytest.mark.django_db
def test_sin_token_401(client):
    respuesta = client.post(
        URL,
        data={"contrasena_actual": PASSWORD_TEST, "nueva_contrasena": NUEVA},
        format="json",
    )
    assert respuesta.status_code == 401
    assert respuesta.json()["error"] == "no_autenticado"


@pytest.mark.django_db
def test_ruta_anterior_con_ene_sigue_funcionando(client, usuario_temporal):
    tokens = login_tokens(client, usuario_temporal)
    respuesta = client.post(
        URL_ANTERIOR,
        data={"contrasena_actual": PASSWORD_TEST, "nueva_contrasena": NUEVA},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )
    assert respuesta.status_code == 200
