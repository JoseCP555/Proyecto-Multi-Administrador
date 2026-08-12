"""
Rate limiting simple en memoria (por IP) para endpoints sensibles.
NOTA: esto es un mitigante básico para un solo proceso/instancia.
Para producción con múltiples workers/instancias, usar Redis
(p. ej. slowapi + redis) en vez de este diccionario en memoria.
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException

_intentos = defaultdict(list)


def limitar(request: Request, clave: str, max_intentos: int = 5, ventana_segundos: int = 60):
    ip = request.client.host if request.client else "desconocido"
    llave = f"{clave}:{ip}"
    ahora = time.time()

    _intentos[llave] = [t for t in _intentos[llave] if ahora - t < ventana_segundos]

    if len(_intentos[llave]) >= max_intentos:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos. Intenta de nuevo en un momento."
        )

    _intentos[llave].append(ahora)
