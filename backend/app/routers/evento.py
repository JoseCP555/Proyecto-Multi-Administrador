"""Gestión de eventos / agenda del conjunto."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.models import Evento
from app.database import get_db
from app.deps import get_current_user, require_permiso
from app.auditoria import registrar_seguro
from app.conjunto_ctx import conjunto_activo, filtrar

router = APIRouter(prefix="/eventos", tags=["Eventos"], dependencies=[Depends(require_permiso("eventos.ver"))])


@router.get("", response_model=list[schemas.EventoResponse])
def listar(
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
    tipo: str | None = Query(None, description="Filtra por tipo: actividad, asamblea, reunion o mantenimiento (UH-15)"),
):
    """Calendario general del conjunto (UH-15).

    El residente ve todos los eventos publicados y puede filtrar por tipo de
    evento; el detalle de cada uno está en el propio registro devuelto.
    """
    q = filtrar(db.query(Evento), Evento, cid)
    if tipo and tipo.strip().lower() not in ("todos", "todo", "all"):
        q = q.filter(func.lower(Evento.tipo) == tipo.strip().lower())
    return q.order_by(Evento.fecha.asc(), Evento.hora.asc()).all()


def _validar_fecha_futura(fecha: date) -> None:
    """Los eventos solo pueden programarse a partir de mañana (después del día actual)."""
    if fecha <= date.today():
        raise HTTPException(
            status_code=400,
            detail="La fecha del evento debe ser posterior al día de hoy.",
        )


@router.post("", response_model=schemas.EventoResponse, status_code=201, dependencies=[Depends(require_permiso("eventos.crear"))])
def crear(data: schemas.EventoCreate, db: Session = Depends(get_db), cid: int = Depends(conjunto_activo),
          usuario=Depends(get_current_user)):
    """Programa una reunión / asamblea con fecha, hora, lugar y descripción.

    Al guardar se notifica automáticamente a los residentes (UH-04) y, si es una
    asamblea o reunión, el aviso se refuerza 48 horas antes (UH-01, a cargo del
    programador en segundo plano).
    """
    _validar_fecha_futura(data.fecha)
    e = Evento(titulo=data.titulo, descripcion=data.descripcion, fecha=data.fecha,
               hora=data.hora, tipo=data.tipo, lugar=data.lugar, id_conjunto=cid,
               creado_por=usuario.id)
    db.add(e)
    db.commit()
    db.refresh(e)

    es_asamblea = (e.tipo or "").lower() in ("asamblea", "reunion", "reunión")
    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="asamblea" if es_asamblea else "evento",
        titulo=("Nueva asamblea programada" if es_asamblea else "Nuevo evento programado"),
        mensaje=f"{e.titulo} — {e.fecha.strftime('%d/%m/%Y')}"
                + (f" a las {e.hora}" if e.hora else "")
                + (f" en {e.lugar}" if e.lugar else ""),
        clave=f"creado:{e.id}", fecha=e.fecha,
        severidad="alta" if es_asamblea else "media",
        url="/dashboard/eventos",
    )
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Eventos",
                     entidad="evento", entidad_id=e.id, id_conjunto=cid,
                     detalle=f"Programó «{e.titulo}» para el {e.fecha}")
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
    e.hora = data.hora
    e.tipo = data.tipo
    e.lugar = data.lugar
    # Si cambia la fecha, el recordatorio de 48 h vuelve a evaluarse.
    e.notificado_48h = False
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
