"""Emisión y validación de tokens JWT para autenticación."""
import os
import uuid
from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 horas

if not SECRET_KEY:
    raise Exception("❌ SECRET_KEY no cargada. Revisa tu archivo .env")


def crear_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """Genera un token JWT firmado con los datos del usuario.

    Se añade un `jti` (identificador único) para que cada login produzca un
    token distinto: al cerrar sesión solo se revoca ese token y no los demás
    tokens de otros logins del mismo usuario (evita el "logout cruzado").
    """
    to_encode = data.copy()
    expira = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({
        "exp": expira,
        "iat": int(datetime.utcnow().timestamp()),
        "jti": uuid.uuid4().hex,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str):
    """Decodifica y valida un token. Retorna el payload o None si es inválido."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def segundos_restantes(token: str) -> int:
    """Segundos hasta que expire un token válido (para la lista negra)."""
    payload = verificar_token(token)
    if not payload:
        return 0
    exp = payload.get("exp")
    if not exp:
        return 0
    return max(0, int(exp - datetime.utcnow().timestamp()))
