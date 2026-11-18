"""Historial de auditoría (UH-29).

Sólo lectura: no hay endpoints para editar ni borrar el historial, de modo que
ningún usuario común puede alterar la trazabilidad de las acciones.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import schemas
from app.conjunto_ctx import conjunto_activo, filtrar
from app.database import get_db
from app.deps import require_permiso
from app.models import Auditoria

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("", response_model=list[schemas.AuditoriaResponse], dependencies=[Depends(require_permiso("auditoria.ver"))])
def listar(
    modulo: str | None = None,
    accion: str | None = None,
    usuario_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    q: str | None = None,
    limite: int = 300,
    db: Session = Depends(get_db),
    cid: int | None = Depends(conjunto_activo),
):
    """Historial con filtros por módulo, acción, usuario, texto y fechas."""
    consulta = filtrar(db.query(Auditoria), Auditoria, cid)
    if modulo:
        consulta = consulta.filter(Auditoria.modulo == modulo)
    if accion:
        consulta = consulta.filter(Auditoria.accion == accion)
    if usuario_id:
        consulta = consulta.filter(Auditoria.usuario_id == usuario_id)
    if desde:
        consulta = consulta.filter(Auditoria.fecha_creacion >= datetime.combine(desde, datetime.min.time()))
    if hasta:
        consulta = consulta.filter(
            Auditoria.fecha_creacion < datetime.combine(hasta + timedelta(days=1), datetime.min.time())
        )
    if q:
        patron = f"%{q.strip()}%"
        consulta = consulta.filter(
            (Auditoria.detalle.ilike(patron))
            | (Auditoria.usuario_nombre.ilike(patron))
            | (Auditoria.ruta.ilike(patron))
        )
    limite = max(1, min(limite, 2000))
    return consulta.order_by(Auditoria.fecha_creacion.desc()).limit(limite).all()


@router.get("/resumen", dependencies=[Depends(require_permiso("auditoria.ver"))])
def resumen(db: Session = Depends(get_db), cid: int | None = Depends(conjunto_activo)):
    """Contadores rápidos por acción y módulo para el panel de auditoría."""
    filas = filtrar(db.query(Auditoria), Auditoria, cid).all()
    por_accion: dict[str, int] = {}
    por_modulo: dict[str, int] = {}
    for f in filas:
        por_accion[f.accion] = por_accion.get(f.accion, 0) + 1
        por_modulo[f.modulo] = por_modulo.get(f.modulo, 0) + 1
    return {
        "total": len(filas),
        "por_accion": por_accion,
        "por_modulo": dict(sorted(por_modulo.items(), key=lambda x: -x[1])[:10]),
    }


@router.get("/exportar.xlsx", dependencies=[Depends(require_permiso("auditoria.ver"))])
def exportar(db: Session = Depends(get_db), cid: int | None = Depends(conjunto_activo)):
    from app import exportar as exp

    contenido = exp.auditoria_xlsx(db, cid)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="auditoria.xlsx"'},
    )
