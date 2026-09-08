"""Configuración SMTP para el envío de correos reales (recuperación de contraseña)."""
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

EMAIL_USER = os.getenv("EMAIL_USER", "").strip()
# Las contraseñas de aplicación de Gmail se muestran con espacios: se aceptan y se limpian.
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "").replace(" ", "").strip()
MAIL_SERVER = os.getenv("MAIL_SERVER", "").strip()
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
# fastapi-mail exige un remitente válido; se usa un placeholder cuando no hay SMTP.
MAIL_FROM = os.getenv("MAIL_FROM", "").strip() or EMAIL_USER or "no-reply@multiadmin.com"

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_USER,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


def resumen_smtp() -> str:
    """Texto para el log de arranque: indica si el envío real de correos está activo."""
    if mail_configurado():
        return f"SMTP configurado: {EMAIL_USER} via {MAIL_SERVER}:{MAIL_PORT}"
    return ("SMTP NO configurado: los correos de verificación/recuperación NO se enviarán. "
            "Define EMAIL_USER, EMAIL_PASSWORD y MAIL_SERVER en backend/.env")


def mail_configurado() -> bool:
    """True si hay credenciales SMTP reales configuradas."""
    return bool(EMAIL_USER and EMAIL_PASSWORD and MAIL_SERVER)
