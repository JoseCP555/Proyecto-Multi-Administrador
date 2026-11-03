"""Gestión de eventos / agenda del conjunto."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.models import Evento
from app.database import get_db
from app.deps import require_permiso
from app.conjunto_ctx import conjunto_activo, filtrar

router = APIRouter(prefix="/eventos", tags=["Eventos"], dependencies=[Depends(require_permiso("eventos.ver"))])


@router.get("", response_model=list[schemas.EventoResponse])
def listar(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    q = filtrar(db.query(Evento), Evento, cid)
    return q.order_by(Evento.fecha.asc()).all()


def _validar_fecha_futura(fecha: date) -> None:
    """Los eventos solo pueden programarse a partir de mañana (después del día actual)."""
    if fecha <= date.today():
        raise HTTPException(
            status_code=400,
            detail="La fecha del evento debe ser posterior al día de hoy.",
        )


@router.post("", response_model=schemas.EventoResponse, status_code=201, dependencies=[Depends(require_permiso("eventos.crear"))])
def crear(data: schemas.EventoCreate, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    _validar_fecha_futura(data.fecha)
    e = Evento(titulo=data.titulo, descripcion=data.descripcion, fecha=data.fecha,
               lugar=data.lugar, id_conjunto=cid)
    db.add(e)
    db.commit()
    db.refresh(e)
    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="evento",
        titulo="Nuevo evento programado",
        mensaje=f"{e.titulo} — {e.fecha.strftime('%d/%m/%Y')}" + (f" en {e.lugar}" if e.lugar else ""),
        clave=f"creado:{e.id}", fecha=e.fecha,
    )
    return e


@router.put("/{evento_id}", response_model=schemas.EventoResponse, dependencies=[Depends(require_permiso("eventos.editar"))])
def actualizar(evento_id: int, data: schemas.EventoCreate, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    e = db.query(Evento).get(evento_id)
    if not e or (cid is not None and e.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Evento no encontrado.")
    # Solo se valida si la fecha cambia: editar título/lugar de un evento ya pasado sigue permitido.
    if data.fecha != e.fecha:
        _validar_fecha_futura(data.fecha)
    e.titulo = data.titulo
    e.descripcion = data.descripcion
    e.fecha = data.fecha
    e.lugar = data.lugar
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{evento_id}", status_code=204, dependencies=[Depends(require_permiso("eventos.eliminar"))])
def eliminar(evento_id: int, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    e = db.query(Evento).get(evento_id)
    if not e or (cid is not None and e.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Evento no encontrado.")
    db.delete(e)
    db.commit()
    return None
