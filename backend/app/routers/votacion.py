"""Votaciones del consejo de administración (UH-25).

El administrador (o el propio consejo) crea la votación con sus opciones y un
plazo. Cada miembro vota **una sola vez** y, al llegar la fecha de cierre, el
sistema muestra los resultados (el cierre también se aplica solo, desde el
programador en segundo plano).
"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.auditoria import registrar_seguro
from app.conjunto_ctx import conjunto_activo, filtrar
from app.database import get_db
from app.deps import get_current_user, require_permiso
from app.models import Usuario, Votacion, VotacionOpcion, Voto

router = APIRouter(prefix="/votaciones", tags=["Votaciones"])


def _serializar(db: Session, v: Votacion, usuario: Usuario | None = None) -> dict:
    opciones = (
        db.query(VotacionOpcion)
        .filter(VotacionOpcion.votacion_id == v.id)
        .order_by(VotacionOpcion.orden, VotacionOpcion.id)
        .all()
    )
    votos = db.query(Voto).filter(Voto.votacion_id == v.id).all()
    conteo = {o.id: 0 for o in opciones}
    for voto in votos:
        conteo[voto.opcion_id] = conteo.get(voto.opcion_id, 0) + 1
    total = len(votos)
    mi_voto = None
    if usuario is not None:
        propio = next((x for x in votos if x.usuario_id == usuario.id), None)
        mi_voto = propio.opcion_id if propio else None

    return {
        "id": v.id,
        "titulo": v.titulo,
        "descripcion": v.descripcion,
        "fecha_cierre": v.fecha_cierre,
        "estado": v.estado,
        "creado_por": v.creado_por,
        "fecha_creacion": v.fecha_creacion,
        "opciones": [
            {"id": o.id, "texto": o.texto, "votos": conteo.get(o.id, 0),
             "porcentaje": round(conteo.get(o.id, 0) * 100 / total, 1) if total else 0.0}
            for o in opciones
        ],
        "total_votos": total,
        "mi_voto": mi_voto,
        "puede_votar": v.estado == "abierta" and v.fecha_cierre >= date.today() and mi_voto is None,
        "resultados": [
            {"opcion_id": o.id, "texto": o.texto, "votos": conteo.get(o.id, 0)}
            for o in opciones
        ],
    }


def _cerrar(db: Session, v: Votacion, notificar: bool = True) -> None:
    v.estado = "cerrada"
    db.commit()
    if not notificar:
        return
    datos = _serializar(db, v)
    ganadora = max(datos["opciones"], key=lambda o: o["votos"], default=None)
    notif.notificar_seguro(
        db=db, id_conjunto=v.id_conjunto, tipo="votacion",
        titulo=f"Resultados de la votación «{v.titulo}»",
        mensaje=(
            f"Votación cerrada con {datos['total_votos']} voto(s). "
            + (f"Opción más votada: «{ganadora['texto']}»." if ganadora and ganadora["votos"] else "Sin votos registrados.")
        ),
        clave=f"resultados:{v.id}", severidad="media", url="/dashboard/votaciones",
    )


@router.get("", response_model=list[schemas.VotacionResponse], dependencies=[Depends(require_permiso("votaciones.ver"))])
def listar(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    # Cierre perezoso: si venció el plazo, se cierra antes de responder.
    abiertas = filtrar(db.query(Votacion).filter(Votacion.estado == "abierta"), Votacion, cid).all()
    for v in abiertas:
        if v.fecha_cierre < date.today():
            v.estado = "cerrada"
    db.commit()

    filas = (
        filtrar(db.query(Votacion), Votacion, cid)
        .order_by(Votacion.estado.desc(), Votacion.fecha_cierre.desc())
        .all()
    )
    return [_serializar(db, v, usuario) for v in filas]


@router.get("/{votacion_id}", response_model=schemas.VotacionResponse, dependencies=[Depends(require_permiso("votaciones.ver"))])
def detalle(
    votacion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    v = db.query(Votacion).get(votacion_id)
    if not v or (cid is not None and v.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Votación no encontrada.")
    return _serializar(db, v, usuario)


@router.post("", response_model=schemas.VotacionResponse, status_code=201, dependencies=[Depends(require_permiso("votaciones.crear"))])
def crear(
    data: schemas.VotacionCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    opciones = [o.strip() for o in data.opciones if o and o.strip()]
    if len(opciones) < 2:
        raise HTTPException(status_code=400, detail="La votación necesita al menos dos opciones.")
    if data.fecha_cierre < date.today():
        raise HTTPException(status_code=400, detail="La fecha de cierre no puede ser pasada.")

    v = Votacion(
        titulo=data.titulo.strip(), descripcion=data.descripcion,
        fecha_cierre=data.fecha_cierre, estado="abierta",
        creado_por=usuario.id, id_conjunto=cid,
    )
    db.add(v)
    db.flush()
    for i, texto in enumerate(opciones):
        db.add(VotacionOpcion(votacion_id=v.id, texto=texto[:200], orden=i))
    db.commit()
    db.refresh(v)

    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="votacion", autor_id=usuario.id,
        titulo=f"Nueva votación: {v.titulo}",
        mensaje=f"Votación abierta hasta el {v.fecha_cierre:%d/%m/%Y}. Opciones: {', '.join(opciones)}.",
        clave=f"creada:{v.id}", severidad="alta", url="/dashboard/votaciones",
    )
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Votaciones",
                     entidad="votacion", entidad_id=v.id, id_conjunto=cid,
                     detalle=f"Creó la votación «{v.titulo}» con {len(opciones)} opciones")
    return _serializar(db, v, usuario)


@router.post("/{votacion_id}/voto", response_model=schemas.VotacionResponse, dependencies=[Depends(require_permiso("votaciones.votar"))])
def votar(
    votacion_id: int,
    data: schemas.VotoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Registra el voto. Un miembro sólo puede votar una vez (UH-25)."""
    v = db.query(Votacion).get(votacion_id)
    if not v or (cid is not None and v.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Votación no encontrada.")
    if v.estado != "abierta" or v.fecha_cierre < date.today():
        raise HTTPException(status_code=400, detail="La votación ya está cerrada.")

    opcion = db.query(VotacionOpcion).get(data.opcion_id)
    if not opcion or opcion.votacion_id != v.id:
        raise HTTPException(status_code=400, detail="La opción no pertenece a esta votación.")

    if db.query(Voto).filter(Voto.votacion_id == v.id, Voto.usuario_id == usuario.id).first():
        raise HTTPException(status_code=409, detail="Ya votaste en esta votación: sólo se permite un voto.")

    try:
        db.add(Voto(votacion_id=v.id, opcion_id=opcion.id, usuario_id=usuario.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya votaste en esta votación: sólo se permite un voto.")

    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Votaciones",
                     entidad="voto", entidad_id=v.id, id_conjunto=cid,
                     detalle=f"Votó «{opcion.texto}» en la votación «{v.titulo}»")
    db.refresh(v)
    return _serializar(db, v, usuario)


@router.put("/{votacion_id}/cerrar", response_model=schemas.VotacionResponse, dependencies=[Depends(require_permiso("votaciones.cerrar"))])
def cerrar(
    votacion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    v = db.query(Votacion).get(votacion_id)
    if not v or (cid is not None and v.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Votación no encontrada.")
    if v.estado == "cerrada":
        raise HTTPException(status_code=400, detail="La votación ya está cerrada.")
    _cerrar(db, v)
    registrar_seguro(db=db, usuario=usuario, accion="editar", modulo="Votaciones",
                     entidad="votacion", entidad_id=v.id, id_conjunto=cid,
                     detalle=f"Cerró la votación «{v.titulo}»")
    return _serializar(db, v, usuario)


@router.delete("/{votacion_id}", status_code=204, dependencies=[Depends(require_permiso("votaciones.crear"))])
def eliminar(
    votacion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    v = db.query(Votacion).get(votacion_id)
    if not v or (cid is not None and v.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Votación no encontrada.")
    db.query(Voto).filter(Voto.votacion_id == v.id).delete(synchronize_session=False)
    db.query(VotacionOpcion).filter(VotacionOpcion.votacion_id == v.id).delete(synchronize_session=False)
    db.delete(v)
    db.commit()
    registrar_seguro(db=db, usuario=usuario, accion="eliminar", modulo="Votaciones",
                     entidad="votacion", entidad_id=votacion_id, id_conjunto=cid,
                     detalle=f"Eliminó la votación {votacion_id}")
    return None
