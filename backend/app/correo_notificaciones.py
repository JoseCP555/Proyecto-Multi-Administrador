"""Envío de correo para las notificaciones del sistema.

Es independiente (y síncrono) de `correo.py`: los endpoints que generan
notificaciones son `def` y se ejecutan en el threadpool de FastAPI, así que
aquí se usa `smtplib` directamente en vez de `fastapi-mail` (que es async).
No se toca el flujo de verificación / recuperación de contraseña.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from app.correo import APP, DOMINIOS_PRUEBA, frontend_url
from app.email_config import (
    EMAIL_PASSWORD,
    EMAIL_USER,
    MAIL_FROM,
    MAIL_PORT,
    MAIL_SERVER,
    mail_configurado,
)

logger = logging.getLogger(__name__)

# Además de los dominios de prueba, las cuentas de demostración no deben
# generar rebotes en el remitente real.
DOMINIOS_SIN_CORREO = set(DOMINIOS_PRUEBA) | {"multiadmin.com"}


def canal_habilitado() -> bool:
    """Interruptor global para no inundar de correos en entornos de prueba."""
    return os.getenv("NOTIFICACIONES_CORREO", "true").strip().lower() not in ("0", "false", "no")


def _html(nombre: str, titulo: str, mensaje: str, url: str) -> str:
    return f"""\
<!doctype html><html lang="es"><body style="margin:0;padding:0;background:#EEF0F7;font-family:Inter,Segoe UI,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 12px;"><tr><td align="center">
  <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#fff;border-radius:24px;overflow:hidden;">
    <tr><td style="background:#111;padding:20px 32px;color:#fff;font-size:18px;font-weight:800;">{APP}</td></tr>
    <tr><td style="padding:32px;">
      <p style="margin:0 0 18px;font-size:12px;font-weight:700;letter-spacing:1px;color:#6b7280;text-transform:uppercase;">Nueva notificación</p>
      <h1 style="margin:0 0 12px;font-size:22px;color:#111827;">{escape(titulo)}</h1>
      <p style="margin:0 0 8px;font-size:15px;color:#374151;">Hola {escape(nombre)},</p>
      <p style="margin:0 0 24px;font-size:15px;color:#374151;line-height:1.55;">{escape(mensaje)}</p>
      <a href="{escape(url)}" style="display:inline-block;padding:14px 28px;background:#2563eb;color:#fff;text-decoration:none;font-weight:700;border-radius:999px;">Ver en la aplicación</a>
      <p style="margin:24px 0 0;font-size:12px;color:#9ca3af;">Puedes desactivar estos avisos desde la campana de notificaciones.</p>
    </td></tr>
  </table>
</td></tr></table></body></html>"""


def enviar_correo_notificacion(
    destinatario: str,
    nombre: str,
    titulo: str,
    mensaje: str,
    ruta: str | None = None,
) -> dict:
    """Envía el aviso por SMTP. Nunca lanza excepción: devuelve el resultado."""
    dominio = (destinatario or "").rsplit("@", 1)[-1].lower()
    if dominio in DOMINIOS_SIN_CORREO:
        logger.info("[correo-notif] omitido (dominio de prueba): %s", destinatario)
        return {"enviado": True, "omitido": True}
    if not canal_habilitado():
        return {"enviado": False, "error": "canal desactivado"}
    if not mail_configurado():
        return {"enviado": False, "error": "SMTP no configurado"}

    url = f"{frontend_url()}{(ruta or '/dashboard/inicio')}"
    mensaje_obj = MIMEMultipart("alternative")
    mensaje_obj["Subject"] = f"[{APP}] {titulo}"
    mensaje_obj["From"] = MAIL_FROM or EMAIL_USER
    mensaje_obj["To"] = destinatario
    texto = f"Hola {nombre},\n\n{titulo}\n\n{mensaje}\n\nAbre la aplicación: {url}"
    mensaje_obj.attach(MIMEText(texto, "plain", "utf-8"))
    mensaje_obj.attach(MIMEText(_html(nombre or "", titulo, mensaje or "", url), "html", "utf-8"))

    try:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.send_message(mensaje_obj)
        logger.info("[correo-notif] enviado a %s: %s", destinatario, titulo)
        return {"enviado": True}
    except Exception as exc:  # noqa: BLE001 - un fallo de correo no tumba la notificación
        logger.exception("[correo-notif] error al enviar a %s", destinatario)
        return {"enviado": False, "error": f"{type(exc).__name__}: {exc}"}
