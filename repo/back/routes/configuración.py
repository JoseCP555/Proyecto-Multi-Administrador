from fastapi import APIRouter, Depends
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Session
from pydantic import BaseModel
 
from database import Base, SessionLocal
from models import Usuario
from routes.perfil import get_usuario_actual
 
router = APIRouter(prefix="/configuracion", tags=["Configuración"])
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 

# MODELO (tabla nueva, no existía antes)

 
class Configuracion(Base):
    __tablename__ = "configuraciones"
 
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
 
    notif_admin = Column(Boolean, default=True)
    notif_res = Column(Boolean, default=True)
    notif_vig = Column(Boolean, default=False)
 
    brightness = Column(Integer, default=70)
    daltonismo = Column(String, nullable=True)   
    tema = Column(String, default="Siguiendo")    
 
 

# ESQUEMAS

 
class ConfiguracionUpdate(BaseModel):
    notif_admin: bool | None = None
    notif_res: bool | None = None
    notif_vig: bool | None = None
    brightness: int | None = None
    daltonismo: str | None = None
    tema: str | None = None
 
 
class ConfiguracionResponse(BaseModel):
    notif_admin: bool
    notif_res: bool
    notif_vig: bool
    brightness: int
    daltonismo: str | None = None
    tema: str
 
    class Config:
        from_attributes = True
 
 
VALORES_POR_DEFECTO = {
    "notif_admin": True,
    "notif_res": True,
    "notif_vig": False,
    "brightness": 70,
    "daltonismo": None,
    "tema": "Siguiendo",
}
 
 

# RUTAS

 
@router.get("", response_model=ConfiguracionResponse)
def obtener_configuracion(
    usuario_actual: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db)
):
    config = db.query(Configuracion).filter(
        Configuracion.usuario_id == usuario_actual.id
    ).first()
 
    if not config:

        return VALORES_POR_DEFECTO
 
    return config
 
 
@router.put("", response_model=ConfiguracionResponse)
def actualizar_configuracion(
    datos: ConfiguracionUpdate,
    usuario_actual: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db)
):
    config = db.query(Configuracion).filter(
        Configuracion.usuario_id == usuario_actual.id
    ).first()
 
    if not config:

        config = Configuracion(usuario_id=usuario_actual.id, **VALORES_POR_DEFECTO)
        db.add(config)
 
    if datos.notif_admin is not None:
        config.notif_admin = datos.notif_admin
    if datos.notif_res is not None:
        config.notif_res = datos.notif_res
    if datos.notif_vig is not None:
        config.notif_vig = datos.notif_vig
    if datos.brightness is not None:
        config.brightness = datos.brightness
    if datos.daltonismo is not None:
        config.daltonismo = datos.daltonismo
    if datos.tema is not None:
        config.tema = datos.tema
 
    db.commit()
    db.refresh(config)
 
    return config
 
 
@router.put("/restablecer", response_model=ConfiguracionResponse)
def restablecer_configuracion(
    usuario_actual: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db)
):
    config = db.query(Configuracion).filter(
        Configuracion.usuario_id == usuario_actual.id
    ).first()
 
    if not config:
        config = Configuracion(usuario_id=usuario_actual.id, **VALORES_POR_DEFECTO)
        db.add(config)
    else:
        for campo, valor in VALORES_POR_DEFECTO.items():
            setattr(config, campo, valor)
 
    db.commit()
    db.refresh(config)
 
    return config
 