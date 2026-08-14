from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from pydantic import BaseModel
 
from database import Base, SessionLocal
 
router = APIRouter(prefix="/residentes", tags=["Residentes"])
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 

# MODELO (tabla nueva, no existía antes)

 
class Residente(Base):
    __tablename__ = "residentes"
 
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    conjunto = Column(String, nullable=False)
    telefono = Column(String, nullable=True)
    correo = Column(String, nullable=True)
    unidad = Column(String, nullable=True)
 
 

# ESQUEMAS

 
class ResidenteCreate(BaseModel):
    nombre: str
    conjunto: str
    telefono: str | None = None
    correo: str | None = None
    unidad: str | None = None
 
 
class ResidenteUpdate(BaseModel):
    nombre: str | None = None
    conjunto: str | None = None
    telefono: str | None = None
    correo: str | None = None
    unidad: str | None = None
 
 
class ResidenteResponse(BaseModel):
    id: int
    nombre: str
    conjunto: str
    telefono: str | None = None
    correo: str | None = None
    unidad: str | None = None
 
    class Config:
        from_attributes = True
 
 

# RUTAS

 
@router.get("", response_model=list[ResidenteResponse])
def listar_residentes(db: Session = Depends(get_db)):
    return db.query(Residente).all()
 
 
@router.get("/{residente_id}", response_model=ResidenteResponse)
def obtener_residente(residente_id: int, db: Session = Depends(get_db)):
    residente = db.query(Residente).filter(Residente.id == residente_id).first()
 
    if not residente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Residente no encontrado."
        )
 
    return residente
 
 
@router.post("", response_model=ResidenteResponse, status_code=status.HTTP_201_CREATED)
def crear_residente(datos: ResidenteCreate, db: Session = Depends(get_db)):
    nuevo = Residente(
        nombre=datos.nombre,
        conjunto=datos.conjunto,
        telefono=datos.telefono,
        correo=datos.correo,
        unidad=datos.unidad
    )
 
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
 
    return nuevo
 
 
@router.put("/{residente_id}", response_model=ResidenteResponse)
def actualizar_residente(residente_id: int, datos: ResidenteUpdate, db: Session = Depends(get_db)):
    residente = db.query(Residente).filter(Residente.id == residente_id).first()
 
    if not residente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Residente no encontrado."
        )
 
    if datos.nombre is not None:
        residente.nombre = datos.nombre
    if datos.conjunto is not None:
        residente.conjunto = datos.conjunto
    if datos.telefono is not None:
        residente.telefono = datos.telefono
    if datos.correo is not None:
        residente.correo = datos.correo
    if datos.unidad is not None:
        residente.unidad = datos.unidad
 
    db.commit()
    db.refresh(residente)
 
    return residente
 
 
@router.delete("/{residente_id}", status_code=status.HTTP_200_OK)
def eliminar_residente(residente_id: int, db: Session = Depends(get_db)):
    residente = db.query(Residente).filter(Residente.id == residente_id).first()
 
    if not residente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Residente no encontrado."
        )
 
    db.delete(residente)
    db.commit()
 
    return {"mensaje": "Residente eliminado correctamente."}
 