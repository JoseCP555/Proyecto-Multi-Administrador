"""Rate limiting simple apoyado en Redis (con respaldo en memoria)."""
import os
import time
from fastapi import Request
from app.redis_client import exponer_intento, limpiar_intentos

# Respaldo en memoria si Redis no está disponible (por ejemplo en local).
_mem: dict[str, list[float]] = {}


def _clave(request: Request, tipo: str) -> str:
    ip = request.client.host if request.client else "desconocido"
    ruta = request.url.path
    return f"{ip}:{tipo}:{ruta}"


def limitar(request: Request, tipo: str, max_intentos: int, ventana_segundos: int) -> None:
    """Lanza HTTPException 429 si se excede el límite de intentos.

    Se usa en login y recuperación de contraseña para prevenir fuerza bruta.
    """
    from fastapi import HTTPException

    clave = _clave(request, tipo)

    bloqueado, intentos = exponer_intento(clave, max_intentos, ventana_segundos)

    if not bloqueado:
        # Aunque Redis esté activo, mantenemos la base en memoria como fallback.
        ahora = time.time()
        _mem.setdefault(clave, []).append(ahora)
        _mem[clave] = [t for t in _mem[clave] if t > ahora - ventana_segundos]
        if len(_mem[clave]) > max_intentos:
            HTTPException(status_code=429, detail="Demasiados intentos. Intenta más tarde.")

    if bloqueado:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos. Intenta de nuevo en unos minutos.",
        )


def resetear(request: Request, tipo: str) -> None:
    clave = _clave(request, tipo)
    limpiar_intentos(clave)
    _mem.pop(clave, None)
