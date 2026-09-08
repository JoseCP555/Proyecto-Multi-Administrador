"""Cliente de Redis: caché de API, sesiones, rate limiting y estado del chatbot."""
import os
import json
import logging
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _get_client() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=True)


# Instancia única (perezosa). En Docker siempre hay Redis disponible.
_redis = None


def redis():
    global _redis
    if _redis is None:
        try:
            _redis = _get_client()
            _redis.ping()
            logger.info("conectado a Redis OK")
        except RedisError as e:
            logger.warning("Redis no disponible, se usará caché en memoria: %s", e)
            _redis = None
    return _redis


# ---- Caché genérica de JSON ------------------------------------------------
def cache_get(key: str):
    r = redis()
    if not r:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val is not None else None
    except Exception:
        return None


def cache_set(key: str, value, ttl: int = 300) -> None:
    r = redis()
    if not r:
        return
    try:
        r.set(key, json.dumps(value), ex=ttl)
    except Exception:
        pass


def cache_del(*keys) -> None:
    r = redis()
    if not r:
        return
    try:
        r.delete(*keys)
    except Exception:
        pass


# ---- Rate limiting ---------------------------------------------------------
def exponer_intento(clave: str, max_intentos: int, ventana_segundos: int):
    """Incrementa un contador y devuelve (bloqueado, intentos)."""
    r = redis()
    if not r:
        return False, 0
    try:
        llave = f"rl:{clave}"
        cont = r.incr(llave)
        if cont == 1:
            r.expire(llave, ventana_segundos)
        return cont > max_intentos, cont
    except Exception:
        return False, 0


def limpiar_intentos(clave: str) -> None:
    r = redis()
    if not r:
        return
    try:
        r.delete(f"rl:{clave}")
    except Exception:
        pass


# ---- Lista negra de tokens JWT (revocación de sesiones) --------------------
def revocar_token(token: str, ttl: int) -> None:
    """Introduce un token en la lista negra con TTL (expira cuando el propio token)."""
    r = redis()
    if not r:
        return
    try:
        r.set(f"blacklist:{token}", "1", ex=max(ttl, 1))
    except Exception:
        pass


def token_revocado(token: str) -> bool:
    """True si el token está en la lista negra (sesión cerrada)."""
    r = redis()
    if not r:
        return False
    try:
        return r.get(f"blacklist:{token}") is not None
    except Exception:
        return False


# ---- Contador de usuarios conectados / métricas simples --------------------
def incr_metrico(clave: str, delta: int = 1, ttl: int = 300) -> int:
    """Contador con expiración; útil para métricas de uso del sistema."""
    r = redis()
    if not r:
        return 0
    try:
        llave = f"metric:{clave}"
        cont = r.incrby(llave, delta)
        if cont == delta:
            r.expire(llave, ttl)
        return int(cont)
    except Exception:
        return 0

