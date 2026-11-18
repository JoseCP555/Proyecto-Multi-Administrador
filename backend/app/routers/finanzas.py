"""Gestión financiera: conceptos y movimientos."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.models import ConceptoFinanciero, Conjunto, MovimientoFinanciero, Propiedad, Usuario
from app.database import get_db
from app.deps import get_current_user, require_permiso
from app.auditoria import registrar_seguro
from app.redis_client import cache_get, cache_set, cache_del, cache_del_prefix
from app.conjunto_ctx import conjunto_activo, filtrar
from app.chatbot import responder

router = APIRouter(prefix="/finanzas", tags=["Finanzas"], dependencies=[Depends(require_permiso("finanzas.ver"))])


def _invalidar_cache_financiero() -> None:
    """Invalida las cachés de balances y estadísticas para reflejar cambios en tiempo real (UH-05)."""
    cache_del("dashboard_stats")
    cache_del_prefix("dashboard_stats:", "finanzas_resumen:", "finanzas_por_mes:")


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
def listar_movimientos(estado: str = None, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    q = filtrar(db.query(MovimientoFinanciero), MovimientoFinanciero, cid)
    if estado:
        q = q.filter(MovimientoFinanciero.estado == estado)
    movs = q.order_by(MovimientoFinanciero.fecha_vencimiento.desc()).all()
    return [_serializar(m, db) for m in movs]


@router.post("", response_model=schemas.MovimientoResponse, status_code=201, dependencies=[Depends(require_permiso("finanzas.crear"))])
def crear(data: schemas.MovimientoCreate, db: Session = Depends(get_db),
          cid: int = Depends(conjunto_activo), usuario: Usuario = Depends(get_current_user)):
    m = MovimientoFinanciero(
        propiedad_id=data.propiedad_id, concepto_id=data.concepto_id, monto=data.monto,
        fecha_vencimiento=data.fecha_vencimiento, fecha_pago=data.fecha_pago,
        estado=data.estado, numero_recibo=data.numero_recibo, metodo_pago=data.metodo_pago,
        referencia=data.referencia, notas=data.notas, id_conjunto=cid,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="pago", autor_id=usuario.id,
        titulo="Nuevo movimiento financiero",
        mensaje=f"Se registró un movimiento por ${float(m.monto or 0):,.0f} (estado: {m.estado}).",
        clave=f"creado:{m.id}", fecha=m.fecha_vencimiento,
        severidad="alta" if m.estado == "vencido" else "media",
    )
    _alertar_si_supera_umbral(db, m, cid, usuario)
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Finanzas",
                     entidad="movimiento", entidad_id=m.id, id_conjunto=cid,
                     detalle=f"Registró un movimiento por ${float(m.monto or 0):,.0f} ({m.estado})")
    _invalidar_cache_financiero()
    return _serializar(m, db)


def _alertar_si_supera_umbral(db: Session, m: MovimientoFinanciero, cid: int | None, usuario: Usuario) -> None:
    """UH-26: avisa al consejo cuando un gasto supera el umbral configurado.

    La alerta incluye monto, categoría (concepto) y el administrador que
    registró el movimiento.
    """
    concepto = db.query(ConceptoFinanciero).get(m.concepto_id)
    if not concepto or concepto.tipo != "gasto":
        return
    conjunto = db.query(Conjunto).get(cid) if cid else None
    umbral = float(getattr(conjunto, "umbral_gasto", 0) or 0)
    if umbral <= 0 or float(m.monto or 0) <= umbral:
        return
    from app.permisos import ADMIN, CONSEJO, SUPER_ADMIN

    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="alerta_gasto", autor_id=usuario.id,
        titulo="Gasto superior al umbral configurado",
        mensaje=(
            f"Se registró un gasto de ${float(m.monto):,.0f} en la categoría «{concepto.nombre}» "
            f"(umbral: ${umbral:,.0f}). Registrado por {usuario.nombre}."
        ),
        clave=f"umbral:{m.id}", severidad="alta", url="/dashboard/finanzas",
        solo_roles=[CONSEJO, ADMIN, SUPER_ADMIN],
    )


@router.put("/{movimiento_id}", response_model=schemas.MovimientoResponse, dependencies=[Depends(require_permiso("finanzas.editar"))])
def actualizar(movimiento_id: int, data: schemas.MovimientoCreate, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    m = db.query(MovimientoFinanciero).get(movimiento_id)
    if not m or (cid is not None and m.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")
    for campo in ("propiedad_id", "concepto_id", "monto", "fecha_vencimiento", "fecha_pago",
                  "estado", "numero_recibo", "metodo_pago", "referencia", "notas"):
        setattr(m, campo, getattr(data, campo))
    db.commit()
    db.refresh(m)
    _invalidar_cache_financiero()
    return _serializar(m, db)


@router.delete("/{movimiento_id}", status_code=204, dependencies=[Depends(require_permiso("finanzas.eliminar"))])
def eliminar(movimiento_id: int, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    m = db.query(MovimientoFinanciero).get(movimiento_id)
    if not m or (cid is not None and m.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")
    db.delete(m)
    db.commit()
    _invalidar_cache_financiero()
    return None


@router.get("/resumen")
def resumen_financiero(
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
    desde: date | None = Query(None, description="Fecha inicial del período (UH-23)"),
    hasta: date | None = Query(None, description="Fecha final del período (UH-23)"),
):
    """Resumen de ingresos/gastos/pendientes, filtrable por período (UH-23).

    Cacheado en Redis 60 s; la clave incluye el período consultado.
    """
    clave_cache = f"finanzas_resumen:{cid}:{desde}:{hasta}"
    cacheado = cache_get(clave_cache)
    if cacheado:
        return cacheado
    concepto = {c.id: c for c in db.query(ConceptoFinanciero).all()}
    ingresos = gastos = 0.0
    pendiente = 0.0
    pagados = 0
    pend_count = 0
    consulta = filtrar(db.query(MovimientoFinanciero), MovimientoFinanciero, cid)
    if desde:
        consulta = consulta.filter(MovimientoFinanciero.fecha_vencimiento >= desde)
    if hasta:
        consulta = consulta.filter(MovimientoFinanciero.fecha_vencimiento <= hasta)
    for m in consulta.all():
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
    cache_set(clave_cache, resultado, ttl=60)
    return resultado
