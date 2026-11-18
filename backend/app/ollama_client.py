"""Cliente HTTP para Ollama (compatible con Ollama v0.40+ / API nativa).

Se comunica directamente con la API nativa de Ollama usando `httpx` (sin
dependencias externas adicionales):

* `GET  /api/version` -> versión instalada del servidor Ollama
* `GET  /api/tags`    -> modelos descargados localmente
* `POST /api/chat`    -> conversación multi-turno con contexto del conjunto
* `POST /api/pull`    -> descarga bajo demanda de un modelo (opcional)

Diseñado para ser tolerante a fallos: si Ollama no está encendido, está
descargando el modelo o supera el tiempo de espera, devuelve `None` (con
registro claro en logs) para que el chatbot responda con el motor local de
respaldo sin romper la experiencia del usuario.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

import httpx

logger = logging.getLogger("app.ollama")

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
DEFAULT_OLLAMA_TIMEOUT = 120.0
DEFAULT_OLLAMA_KEEP_ALIVE = "10m"

_RE_THINK = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)

# Familias de modelos con modo de razonamiento ("thinking") en Ollama v0.24+/v0.40+.
_PREFIJOS_THINKING = ("qwen3", "deepseek-r1", "gemma4", "qwq", "gpt-oss")


def ollama_base_url() -> str:
    url = (
        os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OLLAMA_HOST")
        or DEFAULT_OLLAMA_URL
    ).strip().rstrip("/")
    # Si se usa el .env de Docker (http://ollama:11434) fuera de un contenedor,
    # redirige automáticamente al Ollama local en localhost:11434.
    if url.startswith("http://ollama:") and not os.path.exists("/.dockerenv"):
        puerto = url.split(":", 2)[2]
        return f"http://localhost:{puerto}"
    return url


def ollama_modelo_defecto() -> str:
    return (os.getenv("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL).strip()


def ollama_timeout() -> float:
    try:
        return max(5.0, float(os.getenv("OLLAMA_TIMEOUT", str(DEFAULT_OLLAMA_TIMEOUT))))
    except ValueError:
        return DEFAULT_OLLAMA_TIMEOUT


def ollama_keep_alive() -> str:
    return (os.getenv("OLLAMA_KEEP_ALIVE") or DEFAULT_OLLAMA_KEEP_ALIVE).strip()


def _es_modelo_thinking(modelo: str) -> bool:
    nombre = (modelo or "").strip().lower()
    return any(nombre.startswith(p) for p in _PREFIJOS_THINKING)


def _limpiar_respuesta(texto: str) -> str:
    """Elimina bloques `<think>...</think>` si un modelo razonador los emite."""
    limpio = _RE_THINK.sub("", texto or "").strip()
    return limpio


def _modelo_coincide(solicitado: str, disponibles: list[str]) -> bool:
    """Compara nombres de modelo tolerando el tag implícito `:latest`."""
    req = (solicitado or "").strip().lower()
    if not req:
        return False
    req_con_latest = req if ":" in req else f"{req}:latest"
    for d in disponibles:
        dn = d.strip().lower()
        if dn == req or dn == req_con_latest:
            return True
    return False


def estado_ollama(modelo: Optional[str] = None, timeout: float = 3.0) -> dict[str, Any]:
    """Consulta la disponibilidad, versión y modelos instalados en Ollama."""
    base = ollama_base_url()
    modelo_obj = (modelo or ollama_modelo_defecto()).strip()
    res: dict[str, Any] = {
        "disponible": False,
        "version": None,
        "url": base,
        "modelo": modelo_obj,
        "modelo_instalado": False,
        "modelos_disponibles": [],
        "detalle": "Ollama no está conectado.",
    }
    try:
        with httpx.Client(base_url=base, timeout=timeout) as client:
            r_ver = client.get("/api/version")
            if r_ver.status_code == 200:
                res["version"] = r_ver.json().get("version")

            r_tags = client.get("/api/tags")
            r_tags.raise_for_status()
            modelos = [
                m.get("name", "")
                for m in (r_tags.json().get("models") or [])
                if isinstance(m, dict) and m.get("name")
            ]
            res["disponible"] = True
            res["modelos_disponibles"] = modelos
            res["modelo_instalado"] = _modelo_coincide(modelo_obj, modelos)

            ver_txt = f" v{res['version']}" if res["version"] else ""
            if res["modelo_instalado"]:
                res["detalle"] = f"Conectado a Ollama{ver_txt} ({modelo_obj})"
            else:
                res["detalle"] = (
                    f"Ollama{ver_txt} activo, pero el modelo '{modelo_obj}' aún no está "
                    f"descargado (ejecuta: ollama pull {modelo_obj})."
                )
    except Exception as exc:  # noqa: BLE001
        res["detalle"] = f"No se pudo conectar con Ollama en {base}: {exc.__class__.__name__}"
    return res


def chatear_ollama(
    mensajes: list[dict[str, str]],
    *,
    modelo: Optional[str] = None,
    temperatura: float = 0.3,
    timeout: Optional[float] = None,
) -> Optional[str]:
    """Envía una conversación a `POST /api/chat` de Ollama y devuelve el texto.

    Devuelve `None` si Ollama no responde, si el modelo no existe o si falla la
    petición, permitiendo al llamador hacer fallback limpio al motor local.
    """
    base = ollama_base_url()
    modelo_obj = (modelo or ollama_modelo_defecto()).strip()
    t_espera = timeout if timeout is not None else ollama_timeout()

    payload: dict[str, Any] = {
        "model": modelo_obj,
        "messages": mensajes,
        "stream": False,
        "keep_alive": ollama_keep_alive(),
        "options": {
            "temperature": temperatura,
            "num_predict": 512,
        },
    }
    # En Ollama v0.24+/v0.40+, los modelos con razonamiento activan `think` por
    # defecto y pueden tardar mucho en CPU. Desactivarlo acelera el chatbot.
    if _es_modelo_thinking(modelo_obj):
        payload["think"] = False

    try:
        with httpx.Client(base_url=base, timeout=t_espera) as client:
            r = client.post("/api/chat", json=payload)
            # Compatibilidad defensiva: si un modelo/versión rechaza `think`, reintentar sin él.
            if r.status_code == 400 and "think" in payload:
                payload.pop("think", None)
                r = client.post("/api/chat", json=payload)
            if r.status_code == 404:
                logger.warning(
                    "[ollama] Modelo '%s' no encontrado en %s. Descárgalo con: ollama pull %s",
                    modelo_obj,
                    base,
                    modelo_obj,
                )
                return None
            r.raise_for_status()
            datos = r.json()
            contenido = (datos.get("message") or {}).get("content") or ""
            texto = _limpiar_respuesta(contenido)
            if not texto:
                logger.warning("[ollama] Respuesta vacía del modelo '%s'.", modelo_obj)
                return None
            return texto
    except httpx.TimeoutException:
        logger.warning("[ollama] Tiempo de espera agotado (%.0fs) consultando '%s'.", t_espera, modelo_obj)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ollama] Error comunicando con %s (%s): %s", base, modelo_obj, exc)
        return None
