"""Autenticación: registro, login, recuperación y restablecimiento de contraseña."""
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth_jwt import crear_token, segundos_restantes
from app.database import get_db
from app.rate_limit import limitar, resetear
from app.models import Rol
from app.deps import get_current_user, usuario_tiene_permiso
from app.models import Usuario
from app.auth_jwt import verificar_token
from app.permisos import RESIDENTE
from app.redis_client import revocar_token
from app import correo as correo_svc

router = APIRouter(tags=["Autenticación"])


class LoginRequest(BaseModel):
    correo: str
    password: str


@router.get("/roles")
def listar_roles(db: Session = Depends(get_db)):
    return [{"id": r.id, "nombre": r.nombre} for r in db.query(Rol).all()]


def _usuario_opcional(authorization: str | None, db: Session) -> Usuario | None:
    """Devuelve el usuario autenticado si viene un Bearer válido; None si no."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    payload = verificar_token(authorization.split(" ", 1)[1].strip())
    if not payload or payload.get("sub") is None:
        return None
    u = db.query(Usuario).get(int(payload["sub"]))
    return u if u and u.activo else None


@router.post("/register")
async def registrar(
    request: Request,
    usuario: schemas.UsuarioCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Registro público: siempre crea un *residente* y envía un correo de
    verificación; la cuenta no puede iniciar sesión hasta confirmarlo.
    Solo un usuario autenticado con `usuarios.crear` puede asignar otro rol
    (y únicamente el super_admin puede crear otros super_admin); las cuentas
    creadas por un administrador quedan verificadas de inmediato."""
    actual = _usuario_opcional(authorization, db)
    # Anti-abuso solo para el registro público (los administradores no se limitan).
    if not actual:
        limitar(request, "register", max_intentos=10, ventana_segundos=300)
    if usuario.rol_id != RESIDENTE:
        if not actual or not usuario_tiene_permiso(db, actual, "usuarios.crear"):
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para crear usuarios con ese rol.",
            )
        if usuario.rol_id == 1 and actual.rol_id != 1:
            raise HTTPException(
                status_code=403,
                detail="Solo un super administrador puede crear otro super administrador.",
            )
    creado_por_admin = bool(actual and usuario_tiene_permiso(db, actual, "usuarios.crear"))
    try:
        nuevo = crud.crear_usuario(db, usuario, verificado=creado_por_admin)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    respuesta = crud.serializar_usuario(nuevo, db)
    if not creado_por_admin:
        envio = await correo_svc.enviar_verificacion(nuevo.correo, nuevo.nombre, nuevo.token_verificacion, nuevo.codigo_verificacion)
        respuesta["verificacion"] = {
            "requerida": True,
            "enviado": bool(envio.get("enviado")),
            "mensaje": (
                "Te enviamos un correo para verificar tu cuenta. Revisa tu bandeja de entrada (y el spam)."
                if envio.get("enviado")
                else (
                    "El servidor no tiene correo configurado (EMAIL_USER / EMAIL_PASSWORD en backend/.env). "
                    "Configúralo y usa 'Reenviar verificación' desde el inicio de sesión."
                    if envio.get("error") == "SMTP no configurado"
                    else "No se pudo enviar el correo de verificación (revisa el log del servidor). "
                         "Usa la opción 'Reenviar verificación' desde el inicio de sesión."
                )
            ),
        }
    return respuesta


@router.get("/verificar-correo/{token}")
def verificar_correo(token: str, db: Session = Depends(get_db)):
    """Confirma el correo a partir del token enviado por email."""
    estado = crud.verificar_correo(db, token)
    mensajes = {
        "ok": "¡Correo verificado! Ya puedes iniciar sesión.",
        "expirado": "El enlace de verificación expiró. Solicita uno nuevo.",
        "invalido": "El enlace de verificación es inválido o ya fue utilizado.",
    }
    return {"ok": estado == "ok", "estado": estado, "mensaje": mensajes[estado]}


@router.post("/verificar-codigo")
def verificar_codigo(request: Request, datos: schemas.CodigoCorreo, db: Session = Depends(get_db)):
    """Confirma la cuenta con el código de 6 dígitos recibido por correo."""
    limitar(request, "verificar-codigo", max_intentos=10, ventana_segundos=300)
    estado = crud.verificar_codigo_correo(db, datos.correo, datos.codigo)
    mensajes = {
        "ok": "¡Correo verificado! Ya puedes iniciar sesión.",
        "expirado": "El código expiró. Solicita uno nuevo.",
        "invalido": "El código es incorrecto.",
    }
    return {"ok": estado == "ok", "estado": estado, "mensaje": mensajes[estado]}


@router.post("/reenviar-verificacion")
async def reenviar_verificacion(
    request: Request,
    datos: schemas.ReenviarVerificacion,
    db: Session = Depends(get_db),
):
    """Reenvía el correo de verificación. No revela si el correo existe."""
    limitar(request, "reenviar-verificacion", max_intentos=10, ventana_segundos=600)
    respuesta = {"mensaje": "Si el correo está registrado y pendiente de verificación, te enviamos un nuevo código."}
    usuario = crud.buscar_por_correo(db, datos.correo)
    if usuario and not usuario.correo_verificado:
        await crud.enviar_verificacion(db, usuario)
    return respuesta


@router.post("/login")
def login(request: Request, datos: LoginRequest, db: Session = Depends(get_db)):
    limitar(request, "login", max_intentos=5, ventana_segundos=60)

    try:
        usuario = crud.login_usuario(db, datos.correo, datos.password)
    except crud.CorreoNoVerificado:
        return {
            "ok": False,
            "codigo": "correo_no_verificado",
            "mensaje": "Debes verificar tu correo antes de iniciar sesión. Revisa tu bandeja de entrada.",
        }
    if not usuario:
        return {"ok": False, "mensaje": "Correo o contraseña incorrectos."}

    resetear(request, "login")

    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol_id})
    return {
        "ok": True,
        "access_token": token,
        "token_type": "bearer",
        "usuario": crud.serializar_usuario(usuario, db),
    }


@router.get("/me", response_model=schemas.UsuarioResponse)
def perfil_actual(
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Devuelve el usuario autenticado con su listado de permisos (RBAC)."""
    return crud.serializar_usuario(usuario, db)


@router.post("/logout")
def logout(
    authorization: str = Header(None),
    usuario=Depends(get_current_user),
):
    """Cierra la sesión revocando el JWT vigente en Redis (lista negra)."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        revocar_token(token, segundos_restantes(token))
    return {"ok": True, "mensaje": "Sesión cerrada correctamente."}


@router.post("/recuperar-password")
async def recuperar_password(
    request: Request,
    datos: schemas.RecuperarPassword,
    db: Session = Depends(get_db),
):
    limitar(request, "recuperar-password", max_intentos=10, ventana_segundos=600)
    await crud.enviar_recuperacion(db, datos.correo)
    # No se revela si el correo existe (anti-enumeración) y nunca se expone el enlace.
    return {"mensaje": "Si el correo existe, te enviamos un código de recuperación."}


@router.post("/validar-codigo-recuperacion")
def validar_codigo_recuperacion(request: Request, datos: schemas.CodigoCorreo, db: Session = Depends(get_db)):
    """Valida el código de 6 dígitos y devuelve el token para restablecer la contraseña."""
    limitar(request, "validar-codigo-recuperacion", max_intentos=10, ventana_segundos=300)
    token = crud.validar_codigo_recuperacion(db, datos.correo, datos.codigo)
    if not token:
        return {"valido": False, "mensaje": "El código es incorrecto o ya expiró."}
    return {"valido": True, "token": token}


@router.get("/validar-token-recuperacion/{token}")
def validar_token_recuperacion(token: str, db: Session = Depends(get_db)):
    """Permite al frontend saber si el enlace sigue vigente antes de mostrar el formulario."""
    from datetime import datetime
    u = db.query(Usuario).filter(Usuario.token_recuperacion == token).first()
    valido = bool(u and u.expira_token and u.expira_token >= datetime.utcnow())
    return {"valido": valido}


@router.post("/restablecer-password")
def restablecer_password(
    datos: schemas.NuevaPassword,
    db: Session = Depends(get_db),
):
    ok = crud.cambiar_password(db, datos.token, datos.nueva_password)
    return {
        "ok": ok,
        "mensaje": "Contraseña actualizada correctamente." if ok else "El enlace es inválido o ya expiró.",
    }
