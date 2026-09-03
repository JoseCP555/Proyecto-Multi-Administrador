from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

import crud
import schemas

from auth_jwt import crear_token
from database import SessionLocal
from rate_limit import limitar


router = APIRouter(
    prefix="",
    tags=["Usuarios"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


class RecuperarPassword(BaseModel):
    correo: str


class NuevaPassword(BaseModel):
    token: str
    nueva_password: str


@router.post(
    "/crear_usuarios",
    response_model=schemas.UsuarioResponse
)
def crear_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db)
):
    return crud.crear_usuario(db, usuario)


@router.get(
    "/usuarios",
    response_model=list[schemas.UsuarioResponse]
)
def listar_usuarios(
    db: Session = Depends(get_db)
):
    return crud.obtener_usuarios(db)


@router.post("/login")
def login(
    request: Request,
    datos: schemas.Login,
    db: Session = Depends(get_db)
):
    limitar(
        request,
        "login",
        max_intentos=5,
        ventana_segundos=60
    )

    usuario = crud.login_usuario(
        db,
        datos.correo,
        datos.password
    )

    if not usuario:
        return {
            "ok": False,
            "mensaje": "Correo o contraseña incorrectos."
        }

    token = crear_token(
        {
            "sub": str(usuario.id),
            "rol": usuario.id_rol
        }
    )

    return {
        "ok": True,
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "rol": usuario.id_rol
        }
    }


@router.post("/recuperar-password")
async def recuperar_password(
    request: Request,
    datos: RecuperarPassword,
    db: Session = Depends(get_db)
):
    limitar(
        request,
        "recuperar-password",
        max_intentos=3,
        ventana_segundos=300
    )

    resultado = await crud.enviar_recuperacion(
        db,
        datos.correo
    )

    # No revela si el correo existe o no.
    return {
        "mensaje": (
            "Si el correo existe, se envió un enlace "
            "de recuperación."
        )
    }


@router.post("/restablecer-password")
def restablecer_password(
    datos: NuevaPassword,
    db: Session = Depends(get_db)
):
    resultado = crud.cambiar_password(
        db,
        datos.token,
        datos.nueva_password
    )

    if resultado:
        return {
            "mensaje": "Contraseña actualizada correctamente."
        }

    return {
        "mensaje": "El enlace es inválido o ya expiró."
    }
