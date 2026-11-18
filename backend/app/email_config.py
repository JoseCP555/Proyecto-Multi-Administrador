"""Configuración SMTP para el envío de correos reales (verificación, recuperación y avisos).

Variables de entorno (backend/.env):

    EMAIL_USER      correo remitente (p. ej. micuenta@gmail.com)
    EMAIL_PASSWORD  contraseña de APLICACIÓN del proveedor (Gmail: 16 caracteres)
    MAIL_SERVER     servidor SMTP (smtp.gmail.com, smtp-mail.outlook.com, smtp.resend.com…)
    MAIL_PORT       587 (STARTTLS) o 465 (SSL/TLS)
    MAIL_FROM       remitente visible (por defecto, EMAIL_USER)
    MAIL_FROM_NAME  nombre visible del remitente (por defecto, "Multi-Administrador")
    MAIL_STARTTLS   true/false — por defecto true en el puerto 587 y false en el 465
    MAIL_SSL_TLS    true/false — por defecto true en el puerto 465
    MAIL_SSL_CERTS  true/false — validación del certificado (déjalo en true)
    MAIL_AUTH       true/false — autenticar con usuario/contraseña (false en servidores
                    locales de pruebas como MailHog, Mailpit o aiosmtpd)
    MAIL_TIMEOUT    segundos de espera por operación SMTP (por defecto 30)

Con puerto 25 (servidores locales tipo MailHog/Mailpit/aiosmtpd) no se usa TLS
automáticamente, así que no hay que tocar nada más.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig

# Carga las variables sin depender del directorio desde el que se lance uvicorn:
# 1) backend/.env  2) .env en la raíz del proyecto  3) .env del cwd (por compatibilidad).
_BACKEND_DIR = Path(__file__).resolve().parents[1]
for _ruta in (_BACKEND_DIR / ".env", _BACKEND_DIR.parent / ".env"):
    if _ruta.is_file():
        load_dotenv(_ruta, override=False)
load_dotenv(override=False)


def _flag(nombre: str, por_defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None or valor.strip() == "":
        return por_defecto
    return valor.strip().lower() in ("1", "true", "yes", "si", "sí", "on")


EMAIL_USER = os.getenv("EMAIL_USER", "").strip()
# Las contraseñas de aplicación de Gmail se muestran con espacios: se aceptan y se limpian.
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "").replace(" ", "").strip()
MAIL_SERVER = os.getenv("MAIL_SERVER", "").strip()
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
# fastapi-mail exige un remitente válido; se usa un placeholder cuando no hay SMTP.
MAIL_FROM = os.getenv("MAIL_FROM", "").strip() or EMAIL_USER or "no-reply@multiadmin.com"
# Nombre visible en la bandeja ("Multi-Administrador <correo@dominio>"). Un nombre
# reconocible reduce la probabilidad de que el correo se marque como spam.
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "").strip() or "Multi-Administrador"
MAIL_TIMEOUT = int(os.getenv("MAIL_TIMEOUT", "30"))

# 465 => SSL directo; 587/25 => STARTTLS (en el 25 se desactiva por defecto).
_SSL_POR_DEFECTO = MAIL_PORT == 465
_STARTTLS_POR_DEFECTO = MAIL_PORT not in (25, 465)
MAIL_SSL_TLS = _flag("MAIL_SSL_TLS", _SSL_POR_DEFECTO)
MAIL_STARTTLS = _flag("MAIL_STARTTLS", _STARTTLS_POR_DEFECTO and not MAIL_SSL_TLS)
MAIL_SSL_CERTS = _flag("MAIL_SSL_CERTS", True)
# Servidores locales de pruebas (MailHog/Mailpit/aiosmtpd) no piden autenticación.
MAIL_AUTH = _flag("MAIL_AUTH", True)

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_USER,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_STARTTLS=MAIL_STARTTLS,
    MAIL_SSL_TLS=MAIL_SSL_TLS,
    USE_CREDENTIALS=MAIL_AUTH,
    VALIDATE_CERTS=MAIL_SSL_CERTS,
    TIMEOUT=MAIL_TIMEOUT,
)


def mail_configurado() -> bool:
    """True si hay un servidor SMTP utilizable configurado.

    Con autenticación hacen falta usuario y contraseña; en un servidor local de
    pruebas (MAIL_AUTH=false) basta con el servidor y un remitente.
    """
    if not MAIL_SERVER:
        return False
    if not MAIL_AUTH:
        return bool(EMAIL_USER or MAIL_FROM)
    return bool(EMAIL_USER and EMAIL_PASSWORD)


def modo_seguridad() -> str:
    """Texto corto con el modo de cifrado efectivo (para logs y /health)."""
    if MAIL_SSL_TLS:
        return "SSL/TLS"
    if MAIL_STARTTLS:
        return "STARTTLS"
    return "sin cifrado (servidor local)"


def resumen_smtp() -> str:
    """Texto para el log de arranque: indica si el envío real de correos está activo."""
    if mail_configurado():
        return (f"SMTP configurado: {MAIL_FROM_NAME} <{EMAIL_USER}> via "
                f"{MAIL_SERVER}:{MAIL_PORT} ({modo_seguridad()})")
    return ("SMTP NO configurado: los correos de verificación/recuperación NO se enviarán. "
            "Define EMAIL_USER, EMAIL_PASSWORD y MAIL_SERVER en backend/.env "
            "(ver README → Correo de verificación y recuperación).")


def advertencia_enlaces() -> str | None:
    """Aviso si los enlaces de los correos apuntan a un host local.

    Un enlace a `localhost` no le sirve al destinatario y los filtros antispam lo
    tratan como sospechoso; en producción define FRONTEND_URL con la URL pública.
    """
    url = (os.getenv("FRONTEND_URL", "") or "").strip().lower()
    if url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
        return ("FRONTEND_URL apunta a localhost: los enlaces de los correos solo funcionarán "
                "en tu equipo. Para producción usa la URL pública (https://tu-dominio.com).")
    return None


def diagnostico() -> dict:
    """Datos de configuración sin exponer la contraseña (usado por /health y el CLI)."""
    return {
        "configurado": mail_configurado(),
        "remitente": EMAIL_USER or None,
        "remitente_visible": f"{MAIL_FROM_NAME} <{MAIL_FROM}>",
        "servidor": MAIL_SERVER or None,
        "puerto": MAIL_PORT,
        "seguridad": modo_seguridad(),
        "autenticacion": MAIL_AUTH,
        "password_definida": bool(EMAIL_PASSWORD),
        "password_longitud": len(EMAIL_PASSWORD),
        "timeout": MAIL_TIMEOUT,
    }
