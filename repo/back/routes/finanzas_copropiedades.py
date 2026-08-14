from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel
 
from database import SessionLocal
from routes.finanzas import Movimiento, MovimientoResponse
 
router = APIRouter(prefix="/finanzas/copropiedades", tags=["Finanzas por Copropiedad"])
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 

# ESQUEMAS

 
class ResumenCopropiedad(BaseModel):
    copropiedad: str
    total_gastado: float
 
 
class ProveedorResumen(BaseModel):
    proveedor: str
    monto: float
 
 
class DetalleCopropiedad(BaseModel):
    copropiedad: str
    total_gastado: float
    proveedores: list[ProveedorResumen]
    movimientos: list[MovimientoResponse]
 
 

# RUTAS

 
@router.get("", response_model=list[ResumenCopropiedad])
def listar_copropiedades(db: Session = Depends(get_db)):
    """
    Lista las copropiedades que tienen movimientos registrados,
    con el total gastado en cada una. Sirve para llenar el
    <select> de copropiedades del frontend.
    """
    resultados = (
        db.query(
            Movimiento.copropiedad,
            func.sum(Movimiento.monto).label("total_gastado")
        )
        .group_by(Movimiento.copropiedad)
        .all()
    )
 
    return [
        {"copropiedad": r.copropiedad, "total_gastado": r.total_gastado}
        for r in resultados
    ]
 
 
@router.get("/{copropiedad}", response_model=DetalleCopropiedad)
def detalle_copropiedad(copropiedad: str, db: Session = Depends(get_db)):
    """
    Detalle financiero de una copropiedad: total gastado,
    desglose por proveedor y el listado completo de movimientos.
    """
    movimientos = (
        db.query(Movimiento)
        .filter(Movimiento.copropiedad == copropiedad)
        .order_by(Movimiento.fecha.desc())
        .all()
    )
 
    if not movimientos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay movimientos registrados para esta copropiedad."
        )
 
    total_gastado = sum(m.monto for m in movimientos)
 
    proveedores_dict: dict[str, float] = {}
    for m in movimientos:
        if m.proveedor:
            proveedores_dict[m.proveedor] = proveedores_dict.get(m.proveedor, 0) + m.monto
 
    proveedores = [
        {"proveedor": nombre, "monto": monto}
        for nombre, monto in proveedores_dict.items()
    ]
 
    return {
        "copropiedad": copropiedad,
        "total_gastado": total_gastado,
        "proveedores": proveedores,
        "movimientos": movimientos
    }
 