"""Operaciones de autenticación, usuarios y recuperación de contraseña."""
import logging
import os
import secrets
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import correo as correo_svc
from app.models import Usuario, Rol, Permiso, RolPermiso
from app.security import hashear_password, verificar_password

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# USUARIOS
# ---------------------------------------------------------------------------
VERIFICACION_HORAS = 24


def generar_codigo() -> str:
    """Código numérico de 6 dígitos (criptográficamente aleatorio)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def buscar_por_correo(db: Session, correo: str | None):
    """Busca un usuario por correo sin distinguir mayúsculas ni espacios."""
    limpio = (correo or "").strip().lower()
    if not limpio:
        return None
    return db.query(Usuario).filter(func.lower(Usuario.correo) == limpio).first()


def crear_usuario(db: Session, datos, verificado: bool = False) -> Usuario:
    """Crea el usuario. Si `verificado` es False se genera un token de
    verificación de correo y la cuenta no podrá iniciar sesión hasta confirmarlo."""
    existe = buscar_por_correo(db, datos.correo)
    if existe:
        raise ValueError("Ya existe un usuario registrado con ese correo.")

    nuevo = Usuario(
        nombre=datos.nombre,
        telefono=datos.telefono or "",
        correo=datos.correo.strip().lower(),
        contrasena_hash=hashear_password(datos.contrasena),
        rol_id=datos.rol_id,
        activo=True,
        fecha_creacion=datetime.utcnow(),
        id_copropiedad=datos.id_copropiedad,
        correo_verificado=verificado,
        token_verificacion=None if verificado else secrets.token_urlsafe(32),
        codigo_verificacion=None if verificado else generar_codigo(),
        expira_verificacion=None if verificado else datetime.utcnow() + timedelta(hours=VERIFICACION_HORAS),
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_rol(db: Session, rol_id: int):
    return db.query(Rol).filter(Rol.id == rol_id).first()


def obtener_permisos_rol(db: Session, rol_id: int) -> list[str]:
    """Devuelve la lista de códigos de permiso asignados al rol desde la BD."""
    filas = (
        db.query(Permiso.codigo)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .filter(RolPermiso.rol_id == rol_id)
        .all()
    )
    return [fila[0] for fila in filas]


def listar_usuarios(db: Session):
    return db.query(Usuario).all()


def obtener_usuario_por_id(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def actualizar_usuario(db: Session, usuario: Usuario, datos) -> Usuario:
    if datos.nombre is not None:
        usuario.nombre = datos.nombre
    if datos.telefono is not None:
        usuario.telefono = datos.telefono
    if datos.correo is not None:
        usuario.correo = datos.correo
    if datos.rol_id is not None:
        usuario.rol_id = datos.rol_id
    if datos.activo is not None:
        usuario.activo = datos.activo
    db.commit()
    db.refresh(usuario)
    return usuario


def eliminar_usuario(db: Session, usuario: Usuario) -> None:
    """Elimina el usuario; desvincula residentes y sesiones de chat asociados."""
    from app.models import (
        Residente, SesionChat, MovimientoFinanciero, TareaMantenimiento, Documento, Evento,
    )
    uid = usuario.id
    db.query(Residente).filter(Residente.usuario_id == uid).update({"usuario_id": None})
    db.query(SesionChat).filter(SesionChat.usuario_id == uid).update({"usuario_id": None})
    db.query(MovimientoFinanciero).filter(MovimientoFinanciero.creado_por == uid).update({"creado_por": None})
    db.query(TareaMantenimiento).filter(TareaMantenimiento.asignado_a == uid).update({"asignado_a": None})
    db.query(Documento).filter(Documento.subido_por == uid).update({"subido_por": None})
    db.query(Evento).filter(Evento.creado_por == uid).update({"creado_por": None})
    db.delete(usuario)
    db.commit()


def serializar_usuario(u: Usuario, db: Session) -> dict:
    rol = obtener_rol(db, u.rol_id)
    return {
        "id": u.id,
        "nombre": u.nombre,
        "telefono": u.telefono,
        "correo": u.correo,
        "rol_id": u.rol_id,
        "nombre_rol": rol.nombre if rol else "sin rol",
        "activo": u.activo,
        "id_copropiedad": u.id_copropiedad,
        "correo_verificado": bool(u.correo_verificado),
        "permisos": obtener_permisos_rol(db, u.rol_id),
    }


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
class CorreoNoVerificado(Exception):
    """Credenciales correctas pero el correo aún no fue confirmado."""


def login_usuario(db: Session, correo: str, password: str):
    usuario = buscar_por_correo(db, correo)
    if not usuario:
        return None
    if not usuario.activo:
        return None
    if not verificar_password(password, usuario.contrasena_hash):
        return None
    if not usuario.correo_verificado:
        raise CorreoNoVerificado()
    usuario.ultimo_acceso = datetime.utcnow()
    db.commit()
    return usuario


# ---------------------------------------------------------------------------
# VERIFICACIÓN DE CORREO
# ---------------------------------------------------------------------------
async def enviar_verificacion(db: Session, usuario: Usuario) -> dict:
    """(Re)genera el token de verificación y envía el correo."""
    usuario.token_verificacion = secrets.token_urlsafe(32)
    usuario.codigo_verificacion = generar_codigo()
    usuario.expira_verificacion = datetime.utcnow() + timedelta(hours=VERIFICACION_HORAS)
    db.commit()
    return await correo_svc.enviar_verificacion(
        usuario.correo, usuario.nombre, usuario.token_verificacion, usuario.codigo_verificacion
    )


def verificar_correo(db: Session, token: str) -> str:
    """Devuelve 'ok', 'expirado' o 'invalido'."""
    if not token:
        return "invalido"
    usuario = db.query(Usuario).filter(Usuario.token_verificacion == token).first()
    if not usuario:
        return "invalido"
    # Idempotente: si el enlace ya se usó (doble clic, StrictMode, escáner de enlaces
    # del proveedor de correo), se responde 'ok' en lugar de 'invalido'.
    if usuario.correo_verificado:
        return "ok"
    if usuario.expira_verificacion and usuario.expira_verificacion < datetime.utcnow():
        return "expirado"
    usuario.correo_verificado = True
    usuario.codigo_verificacion = None
    # El token se conserva (ya no otorga nada nuevo) para que reabrir el enlace siga mostrando 'ok'.
    db.commit()
    return "ok"


def verificar_codigo_correo(db: Session, correo: str, codigo: str) -> str:
    """Verifica la cuenta con el código de 6 dígitos. Devuelve 'ok', 'expirado' o 'invalido'."""
    codigo = (codigo or "").strip()
    usuario = buscar_por_correo(db, correo)
    if not usuario:
        return "invalido"
    if usuario.correo_verificado:
        return "ok"
    if not usuario.codigo_verificacion or not secrets.compare_digest(usuario.codigo_verificacion, codigo):
        return "invalido"
    if usuario.expira_verificacion and usuario.expira_verificacion < datetime.utcnow():
        return "expirado"
    usuario.correo_verificado = True
    usuario.codigo_verificacion = None
    db.commit()
    return "ok"


# ---------------------------------------------------------------------------
# RECUPERACIÓN DE CONTRASEÑA (envía correo real vía SMTP)
# ---------------------------------------------------------------------------
async def enviar_recuperacion(db: Session, correo: str) -> dict:
    """Genera token (30 min), lo guarda en BD y envía el correo con el enlace."""
    correo_limpio = correo.strip()
    usuario = buscar_por_correo(db, correo_limpio)
    if not usuario:
        logger.info("[recuperacion] Solicitud para un correo no registrado")
        return {"enviado": False, "error": None}

    token = secrets.token_urlsafe(32)
    codigo = generar_codigo()
    usuario.token_recuperacion = token
    usuario.codigo_recuperacion = codigo
    usuario.expira_token = datetime.utcnow() + timedelta(minutes=30)
    db.commit()
    return await correo_svc.enviar_recuperacion(usuario.correo, usuario.nombre, token, codigo)


def validar_codigo_recuperacion(db: Session, correo: str, codigo: str) -> str | None:
    """Si el código de 6 dígitos es correcto y vigente, devuelve el token para
    restablecer la contraseña (el mismo que viaja en el enlace del correo)."""
    codigo = (codigo or "").strip()
    usuario = buscar_por_correo(db, correo)
    if not usuario or not usuario.codigo_recuperacion or not usuario.token_recuperacion:
        return None
    if not secrets.compare_digest(usuario.codigo_recuperacion, codigo):
        return None
    if not usuario.expira_token or usuario.expira_token < datetime.utcnow():
        return None
    return usuario.token_recuperacion


def cambiar_password(db: Session, token: str, nueva_password: str) -> bool:
    usuario = db.query(Usuario).filter(Usuario.token_recuperacion == token).first()
    if not usuario:
        return False
    if not usuario.expira_token:
        return False
    if usuario.expira_token < datetime.utcnow():
        return False
    usuario.contrasena_hash = hashear_password(nueva_password)
    usuario.token_recuperacion = None
    usuario.codigo_recuperacion = None
    usuario.expira_token = None
    db.commit()
    return True
