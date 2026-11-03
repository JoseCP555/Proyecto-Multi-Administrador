"""Configuración compartida de pytest.

El rate-limit (HTTP 429) es correcto en producción, pero las suites disparan
muchas peticiones públicas (/register, /login, /recuperar-password) desde la
misma IP. Antes de cada prueba se limpian los contadores `rl:*` en Redis.
"""
import os

import pytest
from dotenv import dotenv_values

# `test_unit.py` sobrescribe DATABASE_URL con SQLite a nivel de módulo durante
# la recolección. conftest se importa ANTES, así que guardamos la URL real de
# PostgreSQL para las pruebas de integración que consultan la BD por SQL
# directo (verificación de correo, recuperación...).
_cfg = dotenv_values(os.path.join(os.path.dirname(__file__), "..", ".env"))
os.environ["MULTIADMIN_TEST_DB_URL"] = (
    os.getenv("DATABASE_URL") or _cfg.get("DATABASE_URL") or ""
)
# Lo mismo con Redis: test_unit.py lo cambia a un puerto inexistente (6399),
# lo que impedía limpiar los contadores de rate-limit y provocaba 429 falsos.
os.environ["MULTIADMIN_TEST_REDIS_URL"] = (
    os.getenv("REDIS_URL") or _cfg.get("REDIS_URL") or "redis://localhost:6379/0"
)


@pytest.fixture(autouse=True)
def _limpiar_rate_limit():
    try:
        from dotenv import dotenv_values
        from redis import Redis
        valores = dotenv_values(os.path.join(os.path.dirname(__file__), "..", ".env"))
        r = Redis.from_url(
            os.environ.get("MULTIADMIN_TEST_REDIS_URL")
            or valores.get("REDIS_URL")
            or "redis://localhost:6379/0"
        )
        keys = list(r.scan_iter("rl:*"))
        if keys:
            r.delete(*keys)
    except Exception:  # noqa: BLE001 - sin Redis no hay contadores persistentes que limpiar
        pass
    yield
