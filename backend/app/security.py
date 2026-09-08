"""Utilidades de seguridad: hashing de contraseñas con bcrypt (directo).

Se usa la librería `bcrypt` directamente en lugar de `passlib`, porque es más
robusta y evita incompatibilidades de versiones.
"""
import logging
import bcrypt

logger = logging.getLogger(__name__)


def hashear_password(password: str) -> str:
    """Hash de una contraseña (bcrypt)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    """Verifica una contraseña contra su hash, sin filtrar errores internos."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception as error:
        logger.error("[login] Error al verificar la contraseña: %s", type(error).__name__)
        return False
