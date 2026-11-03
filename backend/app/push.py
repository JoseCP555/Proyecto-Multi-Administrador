"""Notificaciones push del navegador mediante Web Push / VAPID.

El navegador se suscribe con `PushManager.subscribe()` y envía su
`suscripcion` al backend. Cuando nace una notificación se llama a
`enviar_push()`, que usa `pywebpush` para entregar el mensaje al servicio de
push del navegador (Chrome/Firefox/Edge). El service worker `public/sw.js`
lo muestra incluso con la pestaña en segundo plano.

Las claves VAPID se leen de `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` en el
`.env`. Si faltan, se puede generar un par con:

    python backend/generar_vapid.py
"""
from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

# Carga .env sin depender del directorio desde el que se lance uvicorn.
_BACKEND_DIR = Path(__file__).resolve().parents[1]
for _ruta in (_BACKEND_DIR / ".env", _BACKEND_DIR.parent / ".env"):
    if _ruta.is_file():
        load_dotenv(_ruta, override=False)
load_dotenv(override=False)

logger = logging.getLogger(__name__)


def _b64url(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def generar_claves_vapid() -> tuple[str, str]:
    """Devuelve (clave_publica, clave_privada) en base64url sin padding."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    clave = ec.generate_private_key(ec.SECP256R1())
    privada = _b64url(clave.private_numbers().private_value.to_bytes(32, "big"))
    publica = _b64url(
        clave.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )
    )
    return publica, privada


def clave_publica() -> str:
    return os.getenv("VAPID_PUBLIC_KEY", "").strip()


def clave_privada() -> str:
    return os.getenv("VAPID_PRIVATE_KEY", "").strip()


def subject() -> str:
    return os.getenv("VAPID_SUBJECT", "mailto:multiadmin0@gmail.com").strip()


def configurado() -> bool:
    return bool(clave_publica() and clave_privada())


def enviar_push(
    db: Session,
    usuario_id: int,
    titulo: str,
    mensaje: str,
    url: str | None,
    notificacion_id: int,
) -> int:
    """Entrega el aviso a todas las suscripciones activas del usuario.

    Devuelve el número de envíos aceptados. Nunca lanza: un fallo de push
    no puede impedir que la notificación quede guardada.
    """
    if not configurado():
        return 0

    from app.models import PushSuscripcion

    suscripciones = (
        db.query(PushSuscripcion)
        .filter(PushSuscripcion.usuario_id == usuario_id, PushSuscripcion.activa.is_(True))
        .all()
    )
    if not suscripciones:
        return 0

    datos = json.dumps({
        "id": notificacion_id,
        "titulo": titulo,
        "mensaje": mensaje or "",
        "url": url or "/dashboard/inicio",
    })
    enviados = 0
    for sus in suscripciones:
        info = {"endpoint": sus.endpoint, "keys": {"p256dh": sus.p256dh, "auth": sus.auth}}
        try:
            webpush(
                subscription_info=info,
                data=datos,
                vapid_private_key=clave_privada(),
                vapid_claims={"sub": subject()},
                timeout=15,
            )
            enviados += 1
        except WebPushException as exc:
            # 404/410 = suscripción caducada: se desactiva para no reintentar.
            codigo = getattr(getattr(exc, "response", None), "status_code", None)
            if codigo in (404, 410):
                sus.activa = False
                logger.info("[push] suscripción caducada, desactivada")
            else:
                logger.warning("[push] no se pudo entregar: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[push] error inesperado: %s", exc)
    # No se hace commit aquí: lo hace el servicio de notificaciones, que
    # además guarda la marca `enviada_push` en la misma transacción.
    return enviados
