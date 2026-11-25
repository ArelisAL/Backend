"""
Settings solo para pytest (pytest.ini).

Reutiliza config/settings.py tal cual (DEBUG=False, como en producción) y
solo aporta una SECRET_KEY ficticia si no viene por variable de entorno,
para que las pruebas corran sin `.env`. Nunca se usa fuera de las pruebas.
"""

import os

os.environ.setdefault(
    "SECRET_KEY", "solo-pruebas-no-usar-en-produccion-fran-costuras-abcdef0123456789"
)

from config.settings import *
