"""Gestión de mantenimiento / órdenes de trabajo."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.models import TareaMantenimiento, Propiedad
from app.redis_client import cache_del
from app.database import get_db
from app.deps import require_permiso
from app.conjunto_ctx import conjunto_activo, filtrar

router = APIRouter(prefix="/mantenimiento", tags=["Mantenimiento"], dependencies=[Depends(require_permiso("mantenimiento.ver"))])


def _serializar(t: TareaMantenimiento, db: Session) -> dict:
    prop_desc = None
    if t.propiedad_id:
        p = db.query(Propiedad).get(t.propiedad_id)
        prop_desc = p.apartamento if p else None
    return {
        "id": t.id, "propiedad_id": t.propiedad_id, "residente_id": t.residente_id,
        "titulo": t.titulo, "descripcion": t.descripcion, "prioridad": t.prioridad,
        "estado": t.estado, "asignado_a": t.asignado_a, "costo_estimado": float(t.costo_estimado) if t.costo_estimado else None,
        "fecha_programada": t.fecha_programada, "fecha_completada": t.fecha_completada,
        "fecha_creacion": t.fecha_creacion, "propiedad_desc": prop_desc,
    }


@router.get("", response_model=list[schemas.TareaResponse])
def listar(estado: str = None, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    q = filtrar(db.query(TareaMantenimiento), TareaMantenimiento, cid)
    if estado:
        q = q.filter(TareaMantenimiento.estado == estado)
    return [_serializar(t, db) for t in q.order_by(TareaMantenimiento.fecha_creacion.desc()).all()]


@router.post("", response_model=schemas.TareaResponse, status_code=201, dependencies=[Depends(require_permiso("mantenimiento.crear"))])
def crear(data: schemas.TareaCreate, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    t = TareaMantenimiento(
        propiedad_id=data.propiedad_id, residente_id=data.residente_id,
        titulo=data.titulo, descripcion=data.descripcion, prioridad=data.prioridad,
        estado=data.estado, asignado_a=data.asignado_a, costo_estimado=data.costo_estimado,
        fecha_programada=data.fecha_programada, id_conjunto=cid,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="mantenimiento",
        titulo="Nueva solicitud de mantenimiento",
        mensaje=f"{t.titulo} (prioridad {t.prioridad}, estado {t.estado}).",
        clave=f"creado:{t.id}",
        severidad="alta" if t.prioridad == "critica" else "media",
    )
    cache_del("dashboard_stats")
    return _serializar(t, db)


@router.put("/{tarea_id}", response_model=schemas.TareaResponse, dependencies=[Depends(require_permiso("mantenimiento.editar"))])
def actualizar(tarea_id: int, data: schemas.TareaCreate, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    t = db.query(TareaMantenimiento).get(tarea_id)
    if not t or (cid is not None and t.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    t.propiedad_id = data.propiedad_id
    t.residente_id = data.residente_id
    t.titulo = data.titulo
    t.descripcion = data.descripcion
    t.prioridad = data.prioridad
    t.estado = data.estado
    t.asignado_a = data.asignado_a
    t.costo_estimado = data.costo_estimado
    t.fecha_programada = data.fecha_programada
    if data.estado == "completada":
        t.fecha_completada = datetime.utcnow()
    db.commit()
    db.refresh(t)
    cache_del("dashboard_stats")
    return _serializar(t, db)


@router.delete("/{tarea_id}", status_code=204, dependencies=[Depends(require_permiso("mantenimiento.eliminar"))])
def eliminar(tarea_id: int, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    t = db.query(TareaMantenimiento).get(tarea_id)
    if not t or (cid is not None and t.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    db.delete(t)
    db.commit()
    cache_del("dashboard_stats")
    return None
