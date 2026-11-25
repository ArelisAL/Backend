"""
Pruebas del contrato OpenAPI (2.7): /api/docs/ con drf-spectacular.

Criterios:
- GET /api/docs/ → 200 (Swagger UI visible).
- GET /api/esquema/ → 200 y contiene los paths de los endpoints de M0
  (auth/login/, auth/refresh/, auth/yo/, auth/logout/, auth/cambiar-contraseña/,
  usuarios/).
"""


class TestOpenAPI:
    def test_docs_visible(self, client):
        respuesta = client.get("/api/docs/")
        assert respuesta.status_code == 200

    def test_esquema_contiene_endpoints(self, client):
        respuesta = client.get("/api/esquema/")
        assert respuesta.status_code == 200
        contenido = respuesta.content.decode()
        assert "/api/v1/auth/login/" in contenido
        assert "/api/v1/auth/google/" in contenido
        assert "/api/v1/auth/refresh/" in contenido
        assert "/api/v1/auth/yo/" in contenido
        assert "/api/v1/auth/logout/" in contenido
        assert "/api/v1/auth/cambiar-contraseña/" in contenido
        assert "/api/v1/auth/cambiar-contrasena/" in contenido
        assert "/api/v1/usuarios/" in contenido
