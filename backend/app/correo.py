"""Envío de correos transaccionales (verificación de cuenta y recuperación de contraseña).

Construye el mensaje con la librería estándar (`EmailMessage`) y lo envía con
aiosmtplib, para controlar todas las cabeceras que influyen en la entregabilidad
(From con nombre, Reply-To, Message-ID propio del dominio, Date, Auto-Submitted,
multipart/alternative texto+HTML). Si no hay SMTP configurado o el envío falla,
se registra el error y se informa (nunca se expone el enlace).
"""
import asyncio
from contextvars import ContextVar
import logging
import os
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from urllib.parse import urlparse

import aiosmtplib

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
    MAIL_TIMEOUT,
    mail_configurado,
)

logger = logging.getLogger(__name__)

APP = "Multi-Administrador"
AZUL = "#2563EB"

# Origen real detectado desde las peticiones HTTP del navegador (permite que los
# correos abran la app aunque FRONTEND_URL siga en localhost y se use LAN/túnel).
_origen_peticion_actual: ContextVar[str] = ContextVar("ma_origen_frontend", default="")
_ultimo_origen_publico: str = ""


def _normalizar_origen(url: str | None) -> str:
    crudo = (url or "").strip()
    if not crudo:
        return ""
    parsed = urlparse(crudo)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def es_url_local(url: str | None) -> bool:
    parsed = urlparse((url or "").strip())
    host = (parsed.hostname or "").lower()
    return host in ("", "localhost", "127.0.0.1", "0.0.0.0", "::1")


def registrar_origen_frontend(url: str | None):
    """Guarda el origen del navegador durante la petición actual y recuerda
    el último origen accesible desde red/Internet (IP LAN o dominio HTTPS)."""
    global _ultimo_origen_publico
    limpio = _normalizar_origen(url)
    token = _origen_peticion_actual.set(limpio)
    if limpio and not es_url_local(limpio):
        _ultimo_origen_publico = limpio
    return token


def restaurar_origen_frontend(token) -> None:
    try:
        _origen_peticion_actual.reset(token)
    except Exception:  # noqa: BLE001
        pass


def frontend_url() -> str:
    """Devuelve la URL base del frontend para los enlaces de correo.

    Prioridad:
    1. `FRONTEND_URL` si apunta a una dirección real (IP de red o dominio HTTPS).
    2. Origen real del navegador en la petición actual (ej. `http://192.168.1.34:3000`
       o `https://xxx.trycloudflare.com`).
    3. Último origen público/LAN conocido (útil para avisos en segundo plano).
    4. Origen local de la petición actual (ej. `http://localhost:5173`).
    5. `FRONTEND_URL` configurado o `http://localhost:3000`.
    """
    env_url = _normalizar_origen(os.getenv("FRONTEND_URL", "http://localhost:3000"))
    if env_url and not es_url_local(env_url):
        return env_url
    actual = _origen_peticion_actual.get()
    if actual and not es_url_local(actual):
        return actual
    if _ultimo_origen_publico:
        return _ultimo_origen_publico
    if actual:
        return actual
    return env_url or "http://localhost:3000"


def _bloque_codigo(codigo: str) -> str:
    return f"""
          <p style="margin:0 0 6px;font-size:13px;color:#6b7280;">Tu código:</p>
          <div style="display:inline-block;padding:14px 26px;border-radius:12px;background:#eff6ff;border:1px dashed {AZUL};
                      font-size:30px;font-weight:800;letter-spacing:10px;color:{AZUL};font-family:Consolas,Menlo,monospace;">{codigo}</div>
          <p style="margin:6px 0 0;font-size:12px;color:#9ca3af;">Escríbelo en la aplicación, o usa el botón de abajo.</p>"""


def _plantilla(titulo: str, saludo: str, cuerpo: str, boton: str, link: str, pie: str, codigo: str = "") -> str:
    """Plantilla HTML sencilla y compatible con Gmail/Outlook."""
    return f"""\
<!doctype html><html lang="es"><body style="margin:0;padding:0;background:#EEF0F7;font-family:Inter,Segoe UI,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#EEF0F7;padding:32px 12px;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:24px;overflow:hidden;box-shadow:0 10px 30px rgba(37,99,235,.10);">
      <tr><td style="background:#111111;padding:22px 32px;color:#fff;font-size:18px;font-weight:800;letter-spacing:.2px;">
        {APP}
      </td></tr>
      <tr><td style="padding:32px;">
        <h1 style="margin:0 0 12px;font-size:22px;color:#111827;">{titulo}</h1>
        <p style="margin:0 0 8px;font-size:15px;color:#374151;">{saludo}</p>
        <p style="margin:0 0 24px;font-size:15px;color:#374151;line-height:1.55;">{cuerpo}</p>
        {_bloque_codigo(codigo) if codigo else ""}
        <table cellpadding="0" cellspacing="0" style="margin-top:22px;"><tr><td style="border-radius:999px;background:{AZUL};">
          <a href="{link}" target="_blank" rel="noopener noreferrer" style="display:inline-block;padding:14px 28px;color:#fff;text-decoration:none;font-weight:700;font-size:15px;border-radius:999px;">{boton}</a>
        </td></tr></table>
        <p style="margin:24px 0 0;font-size:12px;color:#6B7280;line-height:1.5;">
          Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
          <a href="{link}" target="_blank" rel="noopener noreferrer" style="color:{AZUL};word-break:break-all;">{link}</a>
        </p>
        <p style="margin:20px 0 0;font-size:12px;color:#9CA3AF;">{pie}</p>
        <p style="margin:8px 0 0;font-size:11px;color:#B0B7C3;line-height:1.5;">
          Recibes este mensaje porque tienes una cuenta en {APP}. Si no reconoces esta
          actividad, ignóralo o escríbenos respondiendo a este correo.
        </p>
      </td></tr>
      <tr><td style="padding:16px 32px;background:#F9FAFB;font-size:11px;color:#9CA3AF;text-align:center;">
        © {datetime.now().year} {APP} · Gestión de copropiedades
      </td></tr>
    </table>
  </td></tr>
</table></body></html>"""


# Dominios reservados para pruebas automáticas: no se envían (evita rebotes en la cuenta remitente).
DOMINIOS_PRUEBA = {
    "x.com", "test.com", "example.com", "example.org", "localhost",
    # Variantes en español que también se usan para probar el registro.
    "ejemplo.com", "ejemplo.es", "prueba.com", "correo.com",
}


# Dominios que nunca reciben correo: los de prueba y el de las cuentas demo del
# seed (`residente@multiadmin.com`), para no generar rebotes en la cuenta remitente.
DOMINIOS_SIN_ENVIO = set(DOMINIOS_PRUEBA) | {"multiadmin.com"}


def envio_deshabilitado() -> bool:
    """Interruptor para pruebas automatizadas: no se envía ningún correo real."""
    return os.getenv("CORREO_DESHABILITADO", "").strip().lower() in ("1", "true", "yes", "si", "sí")


async def _enviar(destinatario: str, asunto: str, html: str, texto: str) -> dict:
    dominio = destinatario.rsplit("@", 1)[-1].lower()
    if dominio in DOMINIOS_SIN_ENVIO:
        logger.info("[correo] '%s' a %s omitido (dominio sin envío: %s)", asunto, destinatario, dominio)
        return {"enviado": False, "omitido": True}
    if envio_deshabilitado():
        logger.info("[correo] '%s' a %s omitido (CORREO_DESHABILITADO)", asunto, destinatario)
        return {"enviado": False, "omitido": True}
    if not mail_configurado():
        logger.error("[correo] SMTP no configurado; no se envió '%s'. Configura EMAIL_USER/EMAIL_PASSWORD.", asunto)
        return {"enviado": False, "error": "SMTP no configurado"}
    # Mensaje MIME con texto plano + HTML y todas las cabeceras que revisan los
    # filtros antispam: From con nombre visible, Reply-To real, Message-ID propio
    # del dominio del remitente, Date y Auto-Submitted (evita respuestas
    # automáticas). Un mensaje bien formado reduce la probabilidad de spam.
    dominio_remitente = (MAIL_FROM.split("@")[-1] or "multiadmin.local").strip("> ")
    mensaje = EmailMessage()
    mensaje["From"] = formataddr((MAIL_FROM_NAME, MAIL_FROM))
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje["Date"] = formatdate(localtime=True)
    mensaje["Message-ID"] = make_msgid(domain=dominio_remitente)
    mensaje["Reply-To"] = formataddr((MAIL_FROM_NAME, MAIL_FROM))
    mensaje["X-Mailer"] = f"{APP} (SMTP)"
    mensaje["Auto-Submitted"] = "auto-generated"
    mensaje["X-Auto-Response-Suppress"] = "All"
    mensaje.set_content(texto, subtype="plain", charset="utf-8")
    mensaje.add_alternative(html, subtype="html", charset="utf-8")

    contexto = ssl.create_default_context()
    if not MAIL_SSL_CERTS:
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
    parametros = dict(
        hostname=MAIL_SERVER,
        port=MAIL_PORT,
        timeout=MAIL_TIMEOUT,
        tls_context=contexto,
        validate_certs=MAIL_SSL_CERTS,
    )
    if MAIL_SSL_TLS:
        parametros["use_tls"] = True
    else:
        parametros["start_tls"] = MAIL_STARTTLS
    if MAIL_AUTH:
        parametros["username"] = EMAIL_USER
        parametros["password"] = EMAIL_PASSWORD

    try:
        await asyncio.wait_for(aiosmtplib.send(mensaje, **parametros), timeout=MAIL_TIMEOUT + 10)
        logger.info("[correo] '%s' enviado a %s", asunto, destinatario)
        return {"enviado": True}
    except Exception as error:  # noqa: BLE001
        logger.exception("[correo] Error al enviar '%s'", asunto)
        return {"enviado": False, "error": f"{type(error).__name__}: {error}"}


async def enviar_verificacion(destinatario: str, nombre: str, token: str, codigo: str = "") -> dict:
    link = f"{frontend_url()}/verificar/{token}"
    html = _plantilla(
        titulo="Confirma tu correo electrónico",
        saludo=f"Hola {nombre},",
        cuerpo=(f"Gracias por registrarte en {APP}. Para activar tu cuenta y poder iniciar sesión, "
                "confirma que este correo te pertenece haciendo clic en el botón."),
        boton="Verificar mi correo",
        link=link,
        pie="El código y el enlace expiran en 24 horas. Si no creaste una cuenta, ignora este mensaje.",
        codigo=codigo,
    )
    texto = (f"Hola {nombre},\n\nTu código de verificación en {APP} es: {codigo}\n\n"
             f"También puedes confirmar tu correo abriendo este enlace:\n{link}\n\n"
             "El enlace expira en 24 horas. Si no creaste una cuenta, ignora este mensaje.")
    r = await _enviar(destinatario, f"Verifica tu correo - {APP}", html, texto)
    return r


async def enviar_recuperacion(destinatario: str, nombre: str, token: str, codigo: str = "") -> dict:
    link = f"{frontend_url()}/restablecer/{token}"
    html = _plantilla(
        titulo="Restablece tu contraseña",
        saludo=f"Hola {nombre},",
        cuerpo=("Recibimos una solicitud para restablecer la contraseña de tu cuenta. "
                "Haz clic en el botón para elegir una nueva contraseña."),
        boton="Restablecer contraseña",
        link=link,
        codigo=codigo,
        pie="El código y el enlace expiran en 30 minutos. Si no solicitaste este cambio, puedes ignorar este correo; tu contraseña no cambiará.",
    )
    texto = (f"Hola {nombre},\n\nTu código para restablecer la contraseña en {APP} es: {codigo}\n\n"
             f"También puedes abrir este enlace:\n{link}\n\n"
             "El enlace expira en 30 minutos. Si no lo solicitaste, ignora este correo.")
    r = await _enviar(destinatario, f"Recuperación de contraseña - {APP}", html, texto)
    return r
