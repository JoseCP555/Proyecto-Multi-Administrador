"""Gestión financiera: conceptos y movimientos."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.models import ConceptoFinanciero, MovimientoFinanciero, Propiedad, Usuario
from app.database import get_db
from app.deps import require_permiso
from app.redis_client import cache_get, cache_set, cache_del
from app.chatbot import responder

router = APIRouter(prefix="/finanzas", tags=["Finanzas"], dependencies=[Depends(require_permiso("finanzas.ver"))])


@router.get("/conceptos", response_model=list[schemas.ConceptoResponse])
def listar_conceptos(db: Session = Depends(get_db)):
    return db.query(ConceptoFinanciero).all()


def _serializar(m: MovimientoFinanciero, db: Session) -> dict:
    concepto = db.query(ConceptoFinanciero).get(m.concepto_id)
    prop = None
    if m.propiedad_id:
        prop = db.query(Propiedad).get(m.propiedad_id)
    prop_desc = f"{prop.apartamento}" if prop else None
    return {
        "id": m.id, "propiedad_id": m.propiedad_id, "propiedad_desc": prop_desc,
        "concepto_id": m.concepto_id,
        "concepto_nombre": concepto.nombre if concepto else "",
        "monto": float(m.monto), "fecha_vencimiento": m.fecha_vencimiento,
        "fecha_pago": m.fecha_pago, "estado": m.estado, "numero_recibo": m.numero_recibo,
        "metodo_pago": m.metodo_pago, "referencia": m.referencia, "notas": m.notas,
        "fecha_creacion": m.fecha_creacion,
    }


@router.get("", response_model=list[schemas.MovimientoResponse])
def listar_movimientos(estado: str = None, db: Session = Depends(get_db)):
    q = db.query(MovimientoFinanciero)
    if estado:
        q = q.filter(MovimientoFinanciero.estado == estado)
    movs = q.order_by(MovimientoFinanciero.fecha_vencimiento.desc()).all()
    return [_serializar(m, db) for m in movs]


@router.post("", response_model=schemas.MovimientoResponse, status_code=201, dependencies=[Depends(require_permiso("finanzas.crear"))])
def crear(data: schemas.MovimientoCreate, db: Session = Depends(get_db)):
    m = MovimientoFinanciero(
        propiedad_id=data.propiedad_id, concepto_id=data.concepto_id, monto=data.monto,
        fecha_vencimiento=data.fecha_vencimiento, fecha_pago=data.fecha_pago,
        estado=data.estado, numero_recibo=data.numero_recibo, metodo_pago=data.metodo_pago,
        referencia=data.referencia, notas=data.notas,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    cache_del("dashboard_stats")
    return _serializar(m, db)


@router.put("/{movimiento_id}", response_model=schemas.MovimientoResponse, dependencies=[Depends(require_permiso("finanzas.editar"))])
def actualizar(movimiento_id: int, data: schemas.MovimientoCreate, db: Session = Depends(get_db)):
    m = db.query(MovimientoFinanciero).get(movimiento_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")
    for campo in ("propiedad_id", "concepto_id", "monto", "fecha_vencimiento", "fecha_pago",
                  "estado", "numero_recibo", "metodo_pago", "referencia", "notas"):
        setattr(m, campo, getattr(data, campo))
    db.commit()
    db.refresh(m)
    cache_del("dashboard_stats")
    return _serializar(m, db)


@router.delete("/{movimiento_id}", status_code=204, dependencies=[Depends(require_permiso("finanzas.eliminar"))])
def eliminar(movimiento_id: int, db: Session = Depends(get_db)):
    m = db.query(MovimientoFinanciero).get(movimiento_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")
    db.delete(m)
    db.commit()
    cache_del("dashboard_stats")
    return None


@router.get("/resumen")
def resumen_financiero(db: Session = Depends(get_db)):
    """Resumen de ingresos/gastos/pendientes (cacheado en Redis 60s)."""
    cacheado = cache_get("finanzas_resumen")
    if cacheado:
        return cacheado
    concepto = {c.id: c for c in db.query(ConceptoFinanciero).all()}
    ingresos = gastos = 0.0
    pendiente = 0.0
    pagados = 0
    pend_count = 0
    for m in db.query(MovimientoFinanciero).all():
        c = concepto.get(m.concepto_id)
        tipo = c.tipo if c else "gasto"
        if m.estado == "pagado":
            if tipo == "ingreso":
                ingresos += float(m.monto)
            else:
                gastos += float(m.monto)
            pagados += 1
        elif m.estado in ("pendiente", "vencido"):
            pendiente += float(m.monto)
            pend_count += 1
    resultado = {
        "ingresos": round(ingresos, 2), "gastos": round(gastos, 2),
        "saldo": round(ingresos - gastos, 2), "pendiente": round(pendiente, 2),
        "movimientos_pagados": pagados, "movimientos_pendientes": pend_count,
    }
    cache_set("finanzas_resumen", resultado, ttl=60)
    return resultado
