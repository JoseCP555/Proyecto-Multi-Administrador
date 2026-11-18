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
from email.utils import formatdate, make_msgid
from html import escape

from app.correo import APP, DOMINIOS_SIN_ENVIO, frontend_url
from app.email_config import (
    EMAIL_PASSWORD,
    EMAIL_USER,
    MAIL_AUTH,
    MAIL_FROM,
    MAIL_FROM_NAME,
    MAIL_PORT,
    MAIL_SERVER,
    MAIL_SSL_CERTS,
    MAIL_SSL_TLS,
    MAIL_STARTTLS,
    mail_configurado,
)

logger = logging.getLogger(__name__)

# Además de los dominios de prueba, las cuentas de demostración no deben
# generar rebotes en el remitente real (lista compartida con correo.py).
DOMINIOS_SIN_CORREO = DOMINIOS_SIN_ENVIO


def canal_habilitado() -> bool:
    """Interruptor global para no inundar de correos en entornos de prueba."""
    return os.getenv("NOTIFICACIONES_CORREO", "true").strip().lower() not in ("0", "false", "no")


def construir_url_notificacion(ruta: str | None = None, id_conjunto: int | None = None) -> str:
    """Construye la URL completa para abrir la notificación en el navegador."""
    destino = (ruta or "/dashboard/inicio").strip()
    if destino.startswith("http://") or destino.startswith("https://"):
        url = destino
    else:
        if not destino.startswith("/"):
            destino = "/" + destino
        url = f"{frontend_url()}{destino}"
    if id_conjunto is not None:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}conjunto={id_conjunto}"
    return url


def _html(nombre: str, titulo: str, mensaje: str, url: str) -> str:
    url_segura = escape(url, quote=True)
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
      <table cellpadding="0" cellspacing="0" role="presentation"><tr><td style="border-radius:999px;background:#2563eb;">
        <a href="{url_segura}" target="_blank" rel="noopener noreferrer" style="display:inline-block;padding:14px 28px;background:#2563eb;color:#ffffff;text-decoration:none;font-weight:700;font-size:15px;border-radius:999px;">Ver en la aplicación</a>
      </td></tr></table>
      <p style="margin:20px 0 0;font-size:12px;color:#6b7280;line-height:1.5;">
        Si el botón no abre la aplicación automáticamente, copia o toca este enlace en tu navegador:<br>
        <a href="{url_segura}" target="_blank" rel="noopener noreferrer" style="color:#2563eb;word-break:break-all;">{url_segura}</a>
      </p>
      <p style="margin:20px 0 0;font-size:12px;color:#9ca3af;">
        Recibes este aviso porque tienes una cuenta en {APP}.
        Puedes desactivar los avisos por correo desde la campana de notificaciones.
      </p>
    </td></tr>
  </table>
</td></tr></table></body></html>"""


def enviar_correo_notificacion(
    destinatario: str,
    nombre: str,
    titulo: str,
    mensaje: str,
    ruta: str | None = None,
    id_conjunto: int | None = None,
) -> dict:
    """Envía el aviso por SMTP. Nunca lanza excepción: devuelve el resultado."""
    url = construir_url_notificacion(ruta, id_conjunto=id_conjunto)
    dominio = (destinatario or "").rsplit("@", 1)[-1].lower()
    if dominio in DOMINIOS_SIN_CORREO:
        logger.info("[correo-notif] omitido (dominio de prueba): %s", destinatario)
        return {"enviado": True, "omitido": True, "url": url}
    if not canal_habilitado():
        return {"enviado": False, "error": "canal desactivado", "url": url}
    if not mail_configurado():
        return {"enviado": False, "error": "SMTP no configurado", "url": url}

    mensaje_obj = MIMEMultipart("alternative")
    mensaje_obj["Subject"] = f"[{APP}] {titulo}"
    # Nombre visible + cabeceras que favorecen la entrega en la bandeja de entrada.
    mensaje_obj["From"] = f"{MAIL_FROM_NAME} <{MAIL_FROM or EMAIL_USER}>"
    mensaje_obj["To"] = destinatario
    mensaje_obj["Reply-To"] = MAIL_FROM or EMAIL_USER
    mensaje_obj["Message-ID"] = make_msgid(domain=(MAIL_FROM or EMAIL_USER).split("@")[-1])
    mensaje_obj["Date"] = formatdate(localtime=True)
    mensaje_obj["X-Mailer"] = f"{APP} (SMTP)"
    mensaje_obj["Auto-Submitted"] = "auto-generated"
    mensaje_obj["X-Auto-Response-Suppress"] = "All"
    # Los proveedores (Gmail/Yahoo) valoran que un aviso se pueda "des-suscribir".
    mensaje_obj["List-Unsubscribe"] = f"<mailto:{MAIL_FROM or EMAIL_USER}?subject=unsubscribe>"
    mensaje_obj["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    texto = f"Hola {nombre},\n\n{titulo}\n\n{mensaje}\n\nAbre la aplicación: {url}"
    mensaje_obj.attach(MIMEText(texto, "plain", "utf-8"))
    mensaje_obj.attach(MIMEText(_html(nombre or "", titulo, mensaje or "", url), "html", "utf-8"))

    try:
        contexto = ssl.create_default_context()
        if not MAIL_SSL_CERTS:
            contexto.check_hostname = False
            contexto.verify_mode = ssl.CERT_NONE
        if MAIL_SSL_TLS:
            cliente = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, timeout=20, context=contexto)
        else:
            cliente = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=20)
        with cliente as smtp:
            smtp.ehlo()
            if MAIL_STARTTLS and not MAIL_SSL_TLS:
                smtp.starttls(context=contexto)
                smtp.ehlo()
            if MAIL_AUTH:
                smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.send_message(mensaje_obj)
        logger.info("[correo-notif] enviado a %s: %s (%s)", destinatario, titulo, url)
        return {"enviado": True, "url": url}
    except Exception as exc:  # noqa: BLE001 - un fallo de correo no tumba la notificación
        logger.exception("[correo-notif] error al enviar a %s", destinatario)
        return {"enviado": False, "error": f"{type(exc).__name__}: {exc}", "url": url}
