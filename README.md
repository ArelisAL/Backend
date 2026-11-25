# Fran-Costuras — Backend (API REST)

API REST del taller de costura **Fran-Costuras**: usuarios y roles, clientes y
medidas, pedidos y su flujo de estados, asignación a costureras, inventario de
telas, pagos y reportes. La usan `Frontend`, `AdminWeb` y `AppMovil`.

- Stack: Python 3.12, Django 5 + Django REST Framework, JWT (simplejwt),
  drf-spectacular, django-cors-headers. SQLite en desarrollo.
- Especificación: `DERCAS_Fran-Costuras.pdf`. Reglas de trabajo: `AGENTS.md`.
  Catálogo de medidas: `MEDIDAS.md` (versión 2).

## Instalar

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt   # producción: solo requirements.txt
```

## Variables de entorno

Se definen en el sistema o en la plataforma de despliegue (nunca en el código
ni en commits).

| Variable | Desarrollo | Producción |
|---|---|---|
| `DEBUG` | `True` | `False` (valor por defecto) |
| `SECRET_KEY` | opcional (hay una clave solo de desarrollo) | **obligatoria** |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` (+ IP de la PC para AppMovil) | dominio de la API |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:5174` (por defecto) | dominios de Frontend y AdminWeb |
| `GOOGLE_OAUTH_CLIENT_ID` | vacío (Google deshabilitado) | Client ID web usado por Frontend/AdminWeb para verificar credenciales Google |

Con `DEBUG=False` y sin `SECRET_KEY` la API no arranca a propósito.

Para habilitar el login Google, configura el mismo Client ID web en Backend,
Frontend y AdminWeb. El endpoint `/api/v1/auth/google/` valida la credencial,
correo verificado y estado activo; solo inicia sesión en cuentas creadas por la
administración. No hay registro público. Sin el Client ID del Backend responde
503 y los clientes muestran la opción deshabilitada.

## Correr en local

```bash
set DEBUG=True                      # PowerShell: $env:DEBUG="True"
python manage.py migrate
python manage.py loaddata catalogo_medidas   # catálogo desde MEDIDAS.md
python manage.py runserver
```

- API: <http://localhost:8000/api/v1/>
- Documentación OpenAPI: <http://localhost:8000/api/docs/>

## Probar y revisar calidad

```bash
ruff check . --fix && ruff format .
pytest -q
pytest --cov=. --cov-report=term-missing
pip-audit -r requirements.txt
```

Las pruebas usan `config/settings_pruebas.py` (definido en `pytest.ini`) y
solo datos ficticios.

## Ampliación de alcance

El proyecto también contempla la ampliación aprobada por la cliente en `DERCAS_Fran-Costuras_v1.5-ampliacion.docx` y `.pdf` (§14). La captura de consumos por recepción/administración y la confirmación de «En proceso» por administradora/costurera asignada están implementadas y verificadas en Backend, Frontend, AdminWeb y AppMovil como primera entrega de la Fase A. El resto se entrega por fases según `docs/plan/AMPLIACION-DERCAS-1.5.md`; las decisiones de negocio pendientes siguen bloqueando las funciones dependientes. El DERCAS describe el alcance, no certifica las funciones pendientes.
