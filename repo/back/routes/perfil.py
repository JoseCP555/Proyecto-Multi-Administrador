from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
 
from database import SessionLocal
import schemas
import crud
from models import Usuario
from auth_jwt import verificar_token
 
router = APIRouter(prefix="/perfil", tags=["Perfil"])
 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 
def get_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    payload = verificar_token(token)
 
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado."
        )
 
    usuario = db.query(Usuario).filter(
        Usuario.id == int(payload.get("sub"))
    ).first()
 
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
 
    return usuario
 
 

# MODELO PARA ACTUALIZAR PERFIL

 
class PerfilUpdate(BaseModel):
    nombre: str | None = None
    telefono: str | None = None
    correo: EmailStr | None = None
    nueva_password: str | None = None
 
    @field_validator("nueva_password")
    @classmethod
    def validar_password(cls, v: str | None) -> str | None:
        if v is not None and len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v
 
 

# PERFIL

 
@router.get("", response_model=schemas.UsuarioResponse)
def obtener_perfil(
    usuario_actual: Usuario = Depends(get_usuario_actual)
):
    return usuario_actual
 
 
@router.put("", response_model=schemas.UsuarioResponse)
def actualizar_perfil(
    datos: PerfilUpdate,
    usuario_actual: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db)
):
    if datos.nombre is not None:
        usuario_actual.nombre = datos.nombre
 
    if datos.telefono is not None:
        usuario_actual.telefono = datos.telefono
 
    if datos.correo is not None:
        usuario_actual.correo = datos.correo
 
    if datos.nueva_password is not None:
        usuario_actual.contrasena_hash = crud.hashear_password(datos.nueva_password)
 
    db.commit()
    db.refresh(usuario_actual)
 
    return usuario_actual
