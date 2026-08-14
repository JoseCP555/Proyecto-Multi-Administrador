from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
 
from database import Base, SessionLocal
 
router = APIRouter(prefix="/mantenimiento", tags=["Mantenimiento"])
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 

# MODELO (tabla nueva, no existía antes)

 
class Tarea(Base):
    __tablename__ = "tareas_mantenimiento"
 
    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String, nullable=False) 
    texto = Column(String, nullable=False)
    estado = Column(String, nullable=False, default="pendiente")  
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
 
 

# ESQUEMAS

 
class TareaCreate(BaseModel):
    categoria: str
    texto: str
    estado: str = "pendiente"
 
 
class TareaUpdate(BaseModel):
    categoria: str | None = None
    texto: str | None = None
    estado: str | None = None
 
 
class TareaResponse(BaseModel):
    id: int
    categoria: str
    texto: str
    estado: str
    fecha_creacion: datetime
 
    class Config:
        from_attributes = True
 
 

# RUTAS

 
@router.get("", response_model=list[TareaResponse])
def listar_tareas(
    categoria: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Tarea)
 
    if categoria:
        query = query.filter(Tarea.categoria == categoria)
 
    return query.order_by(Tarea.fecha_creacion.desc()).all()
 
 
@router.get("/{tarea_id}", response_model=TareaResponse)
def obtener_tarea(tarea_id: int, db: Session = Depends(get_db)):
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
 
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada."
        )
 
    return tarea
 
 
@router.post("", response_model=TareaResponse, status_code=status.HTTP_201_CREATED)
def crear_tarea(datos: TareaCreate, db: Session = Depends(get_db)):
    nueva = Tarea(
        categoria=datos.categoria,
        texto=datos.texto,
        estado=datos.estado,
        fecha_creacion=datetime.utcnow()
    )
 
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
 
    return nueva
 
 
@router.put("/{tarea_id}", response_model=TareaResponse)
def actualizar_tarea(tarea_id: int, datos: TareaUpdate, db: Session = Depends(get_db)):
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
 
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada."
        )
 
    if datos.categoria is not None:
        tarea.categoria = datos.categoria
    if datos.texto is not None:
        tarea.texto = datos.texto
    if datos.estado is not None:
        tarea.estado = datos.estado
 
    db.commit()
    db.refresh(tarea)
 
    return tarea
 
 
@router.delete("/{tarea_id}", status_code=status.HTTP_200_OK)
def eliminar_tarea(tarea_id: int, db: Session = Depends(get_db)):
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
 
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada."
        )
 
    db.delete(tarea)
    db.commit()
 
    return {"mensaje": "Tarea eliminada correctamente."}
 