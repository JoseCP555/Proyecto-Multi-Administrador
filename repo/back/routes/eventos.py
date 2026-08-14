from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from pydantic import BaseModel
 
from database import Base, SessionLocal
 
router = APIRouter(prefix="/eventos", tags=["Inicio / Eventos"])
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 

# MODELO (tabla nueva, no existía antes)

 
class Evento(Base):
    __tablename__ = "eventos"
 
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    fecha = Column(String, nullable=False)   
    tipo = Column(String, nullable=False, default="evento")  
 
 

# ESQUEMAS

 
class EventoCreate(BaseModel):
    titulo: str
    fecha: str
    tipo: str = "evento"
 
 
class EventoUpdate(BaseModel):
    titulo: str | None = None
    fecha: str | None = None
    tipo: str | None = None
 
 
class EventoResponse(BaseModel):
    id: int
    titulo: str
    fecha: str
    tipo: str
 
    class Config:
        from_attributes = True
 
 

# RUTAS

 
@router.get("", response_model=list[EventoResponse])
def listar_eventos(
    mes: int | None = None,
    anio: int | None = None,
    db: Session = Depends(get_db)
):
    """
    Lista los eventos. Si se pasan mes y año (ej: ?mes=8&anio=2026),
    filtra solo los eventos de ese mes, para el calendario del frontend.
    """
    query = db.query(Evento)
 
    if mes and anio:
        prefijo = f"{anio}-{str(mes).zfill(2)}"
        query = query.filter(Evento.fecha.like(f"{prefijo}%"))
 
    return query.order_by(Evento.fecha.asc()).all()
 
 
@router.post("", response_model=EventoResponse, status_code=status.HTTP_201_CREATED)
def crear_evento(datos: EventoCreate, db: Session = Depends(get_db)):
    nuevo = Evento(
        titulo=datos.titulo,
        fecha=datos.fecha,
        tipo=datos.tipo
    )
 
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
 
    return nuevo
 
 
@router.put("/{evento_id}", response_model=EventoResponse)
def actualizar_evento(evento_id: int, datos: EventoUpdate, db: Session = Depends(get_db)):
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
 
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado."
        )
 
    if datos.titulo is not None:
        evento.titulo = datos.titulo
    if datos.fecha is not None:
        evento.fecha = datos.fecha
    if datos.tipo is not None:
        evento.tipo = datos.tipo
 
    db.commit()
    db.refresh(evento)
 
    return evento
 
 
@router.delete("/{evento_id}", status_code=status.HTTP_200_OK)
def eliminar_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
 
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado."
        )
 
    db.delete(evento)
    db.commit()
 
    return {"mensaje": "Evento eliminado correctamente."}
 