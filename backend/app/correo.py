"""Envío de correos transaccionales (verificación de cuenta y recuperación de contraseña).

Usa fastapi-mail con las credenciales SMTP del .env. Si no hay SMTP configurado
o el envío falla, se registra el error y se informa (nunca se expone el enlace).
"""
import asyncio
import logging
import os
from datetime import datetime

from fastapi_mail import FastMail, MessageSchema, MessageType

from app.email_config import conf, mail_configurado

logger = logging.getLogger(__name__)

APP = "Multi-Administrador"
AZUL = "#2563EB"


def frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3000").strip().rstrip("/")


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
          <a href="{link}" style="display:inline-block;padding:14px 28px;color:#fff;text-decoration:none;font-weight:700;font-size:15px;border-radius:999px;">{boton}</a>
        </td></tr></table>
        <p style="margin:24px 0 0;font-size:12px;color:#6B7280;line-height:1.5;">
          Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
          <a href="{link}" style="color:{AZUL};word-break:break-all;">{link}</a>
        </p>
        <p style="margin:20px 0 0;font-size:12px;color:#9CA3AF;">{pie}</p>
      </td></tr>
      <tr><td style="padding:16px 32px;background:#F9FAFB;font-size:11px;color:#9CA3AF;text-align:center;">
        © {datetime.now().year} {APP} · Gestión de copropiedades
      </td></tr>
    </table>
  </td></tr>
</table></body></html>"""


# Dominios reservados para pruebas automáticas: no se envían (evita rebotes en la cuenta remitente).
DOMINIOS_PRUEBA = {"x.com", "test.com", "example.com", "example.org", "localhost"}


async def _enviar(destinatario: str, asunto: str, html: str, texto: str) -> dict:
    if destinatario.rsplit("@", 1)[-1].lower() in DOMINIOS_PRUEBA:
        logger.info("[correo] '%s' a %s omitido (dominio de prueba)", asunto, destinatario)
        return {"enviado": True, "omitido": True}
    if not mail_configurado():
        logger.error("[correo] SMTP no configurado; no se envió '%s'. Configura EMAIL_USER/EMAIL_PASSWORD.", asunto)
        return {"enviado": False, "error": "SMTP no configurado"}
    mensaje = MessageSchema(
        subject=asunto,
        recipients=[destinatario],
        body=html,
        alternative_body=texto,
        subtype=MessageType.html,
    )
    try:
        await asyncio.wait_for(FastMail(conf).send_message(mensaje), timeout=30)
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
