"""Configuración compartida de pytest.

El rate-limit (HTTP 429) es correcto en producción, pero las suites disparan
muchas peticiones públicas (/register, /login, /recuperar-password) desde la
misma IP. Antes de cada prueba se limpian los contadores `rl:*` en Redis.
"""
import os

import pytest


@pytest.fixture(autouse=True)
def _limpiar_rate_limit():
    try:
        from dotenv import dotenv_values
        from redis import Redis
        valores = dotenv_values(os.path.join(os.path.dirname(__file__), "..", ".env"))
        r = Redis.from_url(valores.get("REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        keys = list(r.scan_iter("rl:*"))
        if keys:
            r.delete(*keys)
    except Exception:  # noqa: BLE001 - sin Redis no hay contadores persistentes que limpiar
        pass
    yield
