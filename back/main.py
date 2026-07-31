from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import Base, engine, SessionLocal
import models
import schemas
import crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Administrador API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://detail-uninvited-gotten.ngrok-free.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.post("/crear_usuarios")
def crear_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db)
):
    return crud.crear_usuario(db, usuario)


@app.get("/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db)
):
    return crud.obtener_usuarios(db)

@app.post("/login")
def login(
    datos: schemas.Login,
    db: Session = Depends(get_db)
):

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

    return {
        "ok": True,
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
    datos: RecuperarPassword,
    db: Session = Depends(get_db)
):

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