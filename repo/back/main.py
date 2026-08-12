import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import Base, engine, SessionLocal
import models
import schemas
import crud
from auth_jwt import crear_token
from rate_limit import limitar

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Administrador API")

# ALLOWED_ORIGINS en .env, separados por coma. Ej:
# ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
_origenes_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origenes_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"mensaje": "Backend funcionando con PostgreSQL"}


# ==========================
# USUARIOS
# ==========================

@app.post("/crear_usuarios", response_model=schemas.UsuarioResponse)
def crear_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db)
):
    return crud.crear_usuario(db, usuario)


@app.get("/usuarios", response_model=list[schemas.UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db)
):
    return crud.obtener_usuarios(db)

@app.post("/login")
def login(
    request: Request,
    datos: schemas.Login,
    db: Session = Depends(get_db)
):
    limitar(request, "login", max_intentos=5, ventana_segundos=60)

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

    token = crear_token({"sub": str(usuario.id), "rol": usuario.id_rol})

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
    
# ==========================
# MODELOS PARA RECUPERACIÓN
# ==========================

class RecuperarPassword(BaseModel):
    correo: str


class NuevaPassword(BaseModel):
    token: str
    nueva_password: str


# ==========================
# RECUPERAR CONTRASEÑA
# =================
# =========

@app.post("/recuperar-password")
async def recuperar_password(
    request: Request,
    datos: RecuperarPassword,
    db: Session = Depends(get_db)
):
    limitar(request, "recuperar-password", max_intentos=3, ventana_segundos=300)

    await crud.enviar_recuperacion(
        db,
        datos.correo
    )

    return {
        "mensaje": "Si el correo existe, se envió un enlace de recuperación."
    }


@app.post("/restablecer-password")
def restablecer_password(
    datos: NuevaPassword,
    db: Session = Depends(get_db)
):

    ok = crud.cambiar_password(
        db,
        datos.token,
        datos.nueva_password
    )

    if ok:
        return {
            "mensaje": "Contraseña actualizada correctamente."
        }

    return {
        "mensaje": "El enlace es inválido o ya expiró."
    }