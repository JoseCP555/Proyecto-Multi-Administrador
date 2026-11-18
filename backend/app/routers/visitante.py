"""Registro y control de acceso de visitantes (UH-12).

El personal de vigilancia (o el administrador) registra nombre, documento,
apartamento visitado y hora de ingreso. La salida se marca con un clic y el
historial es consultable con filtros de fecha, apartamento y estado.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import schemas
from app.auditoria import registrar_seguro
from app.conjunto_ctx import conjunto_activo, filtrar
from app.database import get_db
from app.deps import get_current_user, require_permiso
from app.models import Usuario, Visitante

router = APIRouter(prefix="/visitantes", tags=["Visitantes"])


def _serializar(db: Session, v: Visitante) -> dict:
    u = db.query(Usuario).get(v.registrado_por) if v.registrado_por else None
    return {
        "id": v.id,
        "nombre": v.nombre,
        "documento": v.documento,
        "telefono": v.telefono,
        "apartamento": v.apartamento,
        "residente_id": v.residente_id,
        "motivo": v.motivo,
        "observaciones": v.observaciones,
        "hora_ingreso": v.hora_ingreso,
        "hora_salida": v.hora_salida,
        "estado": v.estado,
        "registrado_por": v.registrado_por,
        "registrado_por_nombre": u.nombre if u else None,
    }


@router.get("", response_model=list[schemas.VisitanteResponse], dependencies=[Depends(require_permiso("visitantes.ver"))])
def listar(
    desde: date | None = None,
    hasta: date | None = None,
    estado: str | None = None,
    apartamento: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    cid: int | None = Depends(conjunto_activo),
):
    consulta = filtrar(db.query(Visitante), Visitante, cid)
    if desde:
        consulta = consulta.filter(Visitante.hora_ingreso >= datetime.combine(desde, datetime.min.time()))
    if hasta:
        consulta = consulta.filter(Visitante.hora_ingreso < datetime.combine(hasta + timedelta(days=1), datetime.min.time()))
    if estado:
        consulta = consulta.filter(Visitante.estado == estado)
    if apartamento:
        consulta = consulta.filter(Visitante.apartamento == apartamento)
    if q:
        patron = f"%{q.strip()}%"
        consulta = consulta.filter(
            (Visitante.nombre.ilike(patron)) | (Visitante.documento.ilike(patron))
        )
    filas = consulta.order_by(Visitante.hora_ingreso.desc()).limit(500).all()
    return [_serializar(db, v) for v in filas]


@router.get("/dentro", response_model=list[schemas.VisitanteResponse], dependencies=[Depends(require_permiso("visitantes.ver"))])
def visitantes_dentro(db: Session = Depends(get_db), cid: int | None = Depends(conjunto_activo)):
    """Visitantes que aún no han registrado la salida (vista de portería)."""
    filas = (
        filtrar(db.query(Visitante).filter(Visitante.estado == "dentro"), Visitante, cid)
        .order_by(Visitante.hora_ingreso.desc())
        .all()
    )
    return [_serializar(db, v) for v in filas]


@router.post("", response_model=schemas.VisitanteResponse, status_code=201, dependencies=[Depends(require_permiso("visitantes.crear"))])
def registrar(
    data: schemas.VisitanteCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Registra el ingreso con nombre, documento, apartamento y hora (UH-12)."""
    v = Visitante(
        nombre=data.nombre.strip(),
        documento=data.documento.strip(),
        telefono=data.telefono,
        apartamento=data.apartamento.strip(),
        residente_id=data.residente_id,
        motivo=data.motivo,
        observaciones=data.observaciones,
        hora_ingreso=datetime.utcnow(),
        estado="dentro",
        registrado_por=usuario.id,
        id_conjunto=cid,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Visitantes",
                     entidad="visitante", entidad_id=v.id, id_conjunto=cid,
                     detalle=f"Registró el ingreso de {v.nombre} ({v.documento}) al {v.apartamento}")
    return _serializar(db, v)


@router.put("/{visitante_id}/salida", response_model=schemas.VisitanteResponse, dependencies=[Depends(require_permiso("visitantes.editar"))])
def registrar_salida(
    visitante_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    v = db.query(Visitante).get(visitante_id)
    if not v or (cid is not None and v.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Registro de visitante no encontrado.")
    if v.estado == "salio":
        raise HTTPException(status_code=400, detail="La salida de este visitante ya fue registrada.")
    v.hora_salida = datetime.utcnow()
    v.estado = "salio"
    db.commit()
    db.refresh(v)
    registrar_seguro(db=db, usuario=usuario, accion="editar", modulo="Visitantes",
                     entidad="visitante", entidad_id=v.id, id_conjunto=cid,
                     detalle=f"Registró la salida de {v.nombre}")
    return _serializar(db, v)


@router.put("/{visitante_id}", response_model=schemas.VisitanteResponse, dependencies=[Depends(require_permiso("visitantes.editar"))])
def editar(
    visitante_id: int,
    data: schemas.VisitanteCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    v = db.query(Visitante).get(visitante_id)
    if not v or (cid is not None and v.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Registro de visitante no encontrado.")
    for campo, valor in data.model_dump().items():
        setattr(v, campo, valor)
    db.commit()
    db.refresh(v)
    registrar_seguro(db=db, usuario=usuario, accion="editar", modulo="Visitantes",
                     entidad="visitante", entidad_id=v.id, id_conjunto=cid,
                     detalle=f"Editó el registro del visitante {v.nombre}")
    return _serializar(db, v)


@router.delete("/{visitante_id}", status_code=204, dependencies=[Depends(require_permiso("visitantes.eliminar"))])
def eliminar(
    visitante_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    v = db.query(Visitante).get(visitante_id)
    if not v or (cid is not None and v.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Registro de visitante no encontrado.")
    db.delete(v)
    db.commit()
    registrar_seguro(db=db, usuario=usuario, accion="eliminar", modulo="Visitantes",
                     entidad="visitante", entidad_id=visitante_id, id_conjunto=cid,
                     detalle=f"Eliminó el registro del visitante {visitante_id}")
    return None


@router.get("/exportar.xlsx", dependencies=[Depends(require_permiso("visitantes.ver"))])
def exportar(
    desde: date | None = None,
    hasta: date | None = None,
    db: Session = Depends(get_db),
    cid: int | None = Depends(conjunto_activo),
):
    """Historial descargable (Excel) del control de acceso."""
    from app import exportar as exp

    contenido = exp.visitantes_xlsx(db, cid, desde, hasta)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="visitantes.xlsx"'},
    )
