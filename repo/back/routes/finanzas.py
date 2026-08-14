from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
 
from database import Base, SessionLocal
 
router = APIRouter(prefix="/finanzas", tags=["Finanzas"])
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 

# MODELO (tabla nueva, no existía antes)

 
class Movimiento(Base):
    __tablename__ = "movimientos_financieros"
 
    id = Column(Integer, primary_key=True, index=True)
    copropiedad = Column(String, nullable=False)     
    concepto = Column(String, nullable=False)         
    proveedor = Column(String, nullable=True)        
    banco = Column(String, nullable=True)               
    monto = Column(Float, nullable=False)
    tipo = Column(String, nullable=False, default="pago") 
    fecha = Column(DateTime, default=datetime.utcnow)
 
 

# ESQUEMAS

 
class MovimientoCreate(BaseModel):
    copropiedad: str
    concepto: str
    proveedor: str | None = None
    banco: str | None = None
    monto: float
    tipo: str = "pago"
 
 
class MovimientoUpdate(BaseModel):
    copropiedad: str | None = None
    concepto: str | None = None
    proveedor: str | None = None
    banco: str | None = None
    monto: float | None = None
    tipo: str | None = None
 
 
class MovimientoResponse(BaseModel):
    id: int
    copropiedad: str
    concepto: str
    proveedor: str | None = None
    banco: str | None = None
    monto: float
    tipo: str
    fecha: datetime
 
    class Config:
        from_attributes = True
 
 

# RUTAS

 
@router.get("", response_model=list[MovimientoResponse])
def listar_movimientos(
    copropiedad: str | None = None,
    concepto: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Movimiento)
 
    if copropiedad:
        query = query.filter(Movimiento.copropiedad == copropiedad)
    if concepto:
        query = query.filter(Movimiento.concepto == concepto)
 
    return query.order_by(Movimiento.fecha.desc()).all()
 
 
@router.get("/{movimiento_id}", response_model=MovimientoResponse)
def obtener_movimiento(movimiento_id: int, db: Session = Depends(get_db)):
    movimiento = db.query(Movimiento).filter(Movimiento.id == movimiento_id).first()
 
    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado."
        )
 
    return movimiento
 
 
@router.post("", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def crear_movimiento(datos: MovimientoCreate, db: Session = Depends(get_db)):
    nuevo = Movimiento(
        copropiedad=datos.copropiedad,
        concepto=datos.concepto,
        proveedor=datos.proveedor,
        banco=datos.banco,
        monto=datos.monto,
        tipo=datos.tipo,
        fecha=datetime.utcnow()
    )
 
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
 
    return nuevo
 
 
@router.put("/{movimiento_id}", response_model=MovimientoResponse)
def actualizar_movimiento(movimiento_id: int, datos: MovimientoUpdate, db: Session = Depends(get_db)):
    movimiento = db.query(Movimiento).filter(Movimiento.id == movimiento_id).first()
 
    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado."
        )
 
    if datos.copropiedad is not None:
        movimiento.copropiedad = datos.copropiedad
    if datos.concepto is not None:
        movimiento.concepto = datos.concepto
    if datos.proveedor is not None:
        movimiento.proveedor = datos.proveedor
    if datos.banco is not None:
        movimiento.banco = datos.banco
    if datos.monto is not None:
        movimiento.monto = datos.monto
    if datos.tipo is not None:
        movimiento.tipo = datos.tipo
 
    db.commit()
    db.refresh(movimiento)
 
    return movimiento
 
 
@router.delete("/{movimiento_id}", status_code=status.HTTP_200_OK)
def eliminar_movimiento(movimiento_id: int, db: Session = Depends(get_db)):
    movimiento = db.query(Movimiento).filter(Movimiento.id == movimiento_id).first()
 
    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado."
        )
 
    db.delete(movimiento)
    db.commit()
 
    return {"mensaje": "Movimiento eliminado correctamente."}
 