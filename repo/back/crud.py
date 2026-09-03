import asyncio
import logging
import os
import secrets
from datetime import datetime, timedelta

from fastapi_mail import FastMail, MessageSchema, MessageType
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from email_config import conf
from models import Usuario


logger = logging.getLogger(__name__)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception as error:
        logger.error(
            "[login] Error al verificar la contraseña: %s",
            type(error).__name__
        )
        return False


def crear_usuario(db: Session, usuario):
    usuario_existente = (
        db.query(Usuario)
        .filter(Usuario.correo == usuario.correo)
        .first()
    )

    if usuario_existente:
        raise ValueError(
            "Ya existe un usuario registrado con ese correo"
        )

    nuevo_usuario = Usuario(
        nombre=usuario.nombre,
        telefono=usuario.telefono,
        correo=usuario.correo,
        contrasena_hash=hashear_password(usuario.contrasena_hash),
        id_rol=usuario.id_rol,
        activo=usuario.activo,
        fecha_creacion=datetime.utcnow(),
        id_copropiedad=usuario.id_copropiedad
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


def obtener_usuarios(db: Session):
    return db.query(Usuario).all()


async def enviar_recuperacion(db: Session, correo: str):
    """
    Genera un token de recuperación, lo guarda en la base de datos
    e intenta enviar el correo.

    Retorna:
    {
        "link": enlace generado o None,
        "enviado": True o False,
        "error": mensaje interno o None
    }
    """

    correo_limpio = correo.strip()

    usuario = (
        db.query(Usuario)
        .filter(Usuario.correo == correo_limpio)
        .first()
    )

    if not usuario:
        logger.info(
            "[recuperacion] Solicitud para un correo no registrado"
        )

        return {
            "link": None,
            "enviado": False,
            "error": None
        }

    frontend_url = os.getenv("FRONTEND_URL", "").strip()

    if not frontend_url:
        logger.error(
            "[recuperacion] Falta configurar FRONTEND_URL"
        )

        return {
            "link": None,
            "enviado": False,
            "error": "Falta configurar FRONTEND_URL"
        }

    token = secrets.token_urlsafe(32)

    usuario.token_recuperacion = token
    usuario.expira_token = datetime.utcnow() + timedelta(minutes=30)

    db.commit()

    link = f"{frontend_url.rstrip('/')}/restablecer/{token}"

    mensaje = MessageSchema(
        subject="Recuperación de contraseña - MultiAdmin",
        recipients=[correo_limpio],
        body=f"""
Hola {usuario.nombre},

Se solicitó recuperar tu contraseña.

Utiliza el siguiente enlace para establecer una nueva contraseña:

{link}

Este enlace expirará en 30 minutos.

Si no solicitaste este cambio, puedes ignorar este correo.

Equipo MultiAdmin.
""",
        subtype=MessageType.plain
    )

    try:
        fast_mail = FastMail(conf)

        await asyncio.wait_for(
            fast_mail.send_message(mensaje),
            timeout=30
        )

        logger.info(
            "[recuperacion] Correo enviado correctamente"
        )

        return {
            "link": link,
            "enviado": True,
            "error": None
        }

    except asyncio.TimeoutError:
        logger.error(
            "[recuperacion] Tiempo agotado al enviar el correo"
        )

        return {
            "link": link,
            "enviado": False,
            "error": "Tiempo agotado al conectar con el servidor de correo"
        }

    except Exception as error:
        logger.exception(
            "[recuperacion] Error al enviar el correo"
        )

        return {
            "link": link,
            "enviado": False,
            "error": f"{type(error).__name__}: {error}"
        }


def cambiar_password(
    db: Session,
    token: str,
    nueva_password: str
):
    usuario = (
        db.query(Usuario)
        .filter(Usuario.token_recuperacion == token)
        .first()
    )

    if not usuario:
        return False

    if not usuario.expira_token:
        return False

    if usuario.expira_token < datetime.utcnow():
        return False

    usuario.contrasena_hash = hashear_password(nueva_password)
    usuario.token_recuperacion = None
    usuario.expira_token = None

    db.commit()

    return True


def login_usuario(
    db: Session,
    correo: str,
    password: str
):
    usuario = (
        db.query(Usuario)
        .filter(Usuario.correo == correo.strip())
        .first()
    )

    if not usuario:
        return None

    if not verificar_password(
        password,
        usuario.contrasena_hash
    ):
        return None

    return usuario
