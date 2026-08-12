from sqlalchemy.orm import Session
from models import Usuario
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, MessageType
from email_config import conf
from passlib.context import CryptContext
import secrets
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False


def crear_usuario(db: Session, usuario):
    nuevo = Usuario(
        nombre=usuario.nombre,
        telefono=usuario.telefono,
        correo=usuario.correo,
        contrasena_hash=hashear_password(usuario.contrasena_hash),
        id_rol=usuario.id_rol,
        activo=usuario.activo,
        fecha_creacion=datetime.utcnow(),
        id_copropiedad=usuario.id_copropiedad
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo


def obtener_usuarios(db: Session):
    return db.query(Usuario).all()


async def enviar_recuperacion(db: Session, correo: str):

    usuario = db.query(Usuario).filter(
        Usuario.correo == correo
    ).first()

    if not usuario:
        return False

    token = secrets.token_urlsafe(32)

    usuario.token_recuperacion = token
    usuario.expira_token = datetime.utcnow() + timedelta(minutes=30)

    db.commit()

    link = f"{os.getenv('FRONTEND_URL')}/restablecer/{token}"
    mensaje = MessageSchema(
        subject="Recuperación de contraseña - MultiAdmin",
        recipients=[correo],
        body=f"""
Hola {usuario.nombre},

Se solicitó recuperar tu contraseña.

Haz clic en este enlace:

{link}

Este enlace expirará en 30 minutos.

Si no solicitaste este cambio puedes ignorar este correo.

Equipo MultiAdmin.
""",
        subtype=MessageType.plain
    )

    fm = FastMail(conf)

    await fm.send_message(mensaje)

    return True


def cambiar_password(db: Session, token: str, nueva_password: str):

    usuario = db.query(Usuario).filter(
        Usuario.token_recuperacion == token
    ).first()

    if not usuario:
        return False

    if usuario.expira_token < datetime.utcnow():
        return False

    usuario.contrasena_hash = hashear_password(nueva_password)

    usuario.token_recuperacion = None
    usuario.expira_token = None

    db.commit()

    return True

def login_usuario(db: Session, correo: str, password: str):

    usuario = db.query(Usuario).filter(
        Usuario.correo == correo
    ).first()

    if not usuario:
        return None

    if not verificar_password(password, usuario.contrasena_hash):
        return None

    return usuario