"""Zonas comunes y reservas (UH-10 · UH-14).

* El administrador crea/edita las zonas comunes y puede aprobar, rechazar o
  cancelar cualquier reserva (UH-10).
* El residente consulta la disponibilidad, reserva una zona desde el celular o
  el computador y ve su historial personal (UH-14).
* **Nunca** se aceptan dos reservas que se solapen en la misma zona y fecha:
  el backend lo valida antes de guardar (criterio de aceptación de UH-10).
"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.auditoria import registrar_seguro
from app.conjunto_ctx import conjunto_activo, filtrar
from app.database import get_db
from app.deps import get_current_user, require_permiso, require_alguno, usuario_tiene_permiso
from app.models import ReservaZona, Usuario, ZonaComun

router = APIRouter(prefix="/reservas", tags=["Reservas y zonas comunes"])

ESTADOS_OCUPAN = ("pendiente", "aprobada")


def _minutos(hhmm: str) -> int:
    h, m = (hhmm or "00:00").split(":")[:2]
    return int(h) * 60 + int(m)


def _serializar(db: Session, r: ReservaZona) -> dict:
    zona = db.query(ZonaComun).get(r.zona_id)
    usuario = db.query(Usuario).get(r.usuario_id) if r.usuario_id else None
    return {
        "id": r.id,
        "zona_id": r.zona_id,
        "zona_nombre": zona.nombre if zona else None,
        "usuario_id": r.usuario_id,
        "solicitante": usuario.nombre if usuario else None,
        "fecha": r.fecha,
        "hora_inicio": r.hora_inicio,
        "hora_fin": r.hora_fin,
        "motivo": r.motivo,
        "asistentes": r.asistentes,
        "estado": r.estado,
        "motivo_decision": r.motivo_decision,
        "fecha_decision": r.fecha_decision,
        "fecha_creacion": r.fecha_creacion,
    }


def _hay_conflicto(db: Session, zona_id: int, fecha: date, inicio: str, fin: str,
                   excluir_id: int | None = None) -> ReservaZona | None:
    """¿Existe otra reserva vigente que se crucele con este horario?"""
    q = db.query(ReservaZona).filter(
        ReservaZona.zona_id == zona_id,
        ReservaZona.fecha == fecha,
        ReservaZona.estado.in_(ESTADOS_OCUPAN),
    )
    if excluir_id is not None:
        q = q.filter(ReservaZona.id != excluir_id)
    a1, a2 = _minutos(inicio), _minutos(fin)
    for r in q.all():
        b1, b2 = _minutos(r.hora_inicio), _minutos(r.hora_fin)
        if a1 < b2 and b1 < a2:
            return r
    return None


# ---------------------------------------------------------------------------
# ZONAS COMUNES
# ---------------------------------------------------------------------------
@router.get("/zonas", response_model=list[schemas.ZonaComunResponse], dependencies=[Depends(require_permiso("zonas.ver"))])
def listar_zonas(db: Session = Depends(get_db), cid: int | None = Depends(conjunto_activo)):
    return (
        filtrar(db.query(ZonaComun), ZonaComun, cid)
        .order_by(ZonaComun.nombre)
        .all()
    )


@router.post("/zonas", response_model=schemas.ZonaComunResponse, status_code=201, dependencies=[Depends(require_permiso("zonas.crear"))])
def crear_zona(data: schemas.ZonaComunCreate, db: Session = Depends(get_db),
               usuario: Usuario = Depends(get_current_user), cid: int | None = Depends(conjunto_activo)):
    if _minutos(data.hora_cierre) <= _minutos(data.hora_apertura):
        raise HTTPException(status_code=400, detail="La hora de cierre debe ser posterior a la de apertura.")
    z = ZonaComun(**data.model_dump(), id_conjunto=cid)
    db.add(z)
    db.commit()
    db.refresh(z)
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Zonas comunes",
                     entidad="zona_comun", entidad_id=z.id, id_conjunto=cid,
                     detalle=f"Creó la zona común «{z.nombre}»")
    return z


@router.put("/zonas/{zona_id}", response_model=schemas.ZonaComunResponse, dependencies=[Depends(require_permiso("zonas.editar"))])
def editar_zona(zona_id: int, data: schemas.ZonaComunCreate, db: Session = Depends(get_db),
                usuario: Usuario = Depends(get_current_user), cid: int | None = Depends(conjunto_activo)):
    z = db.query(ZonaComun).get(zona_id)
    if not z or (cid is not None and z.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Zona común no encontrada.")
    for campo, valor in data.model_dump().items():
        setattr(z, campo, valor)
    db.commit()
    db.refresh(z)
    registrar_seguro(db=db, usuario=usuario, accion="editar", modulo="Zonas comunes",
                     entidad="zona_comun", entidad_id=z.id, id_conjunto=cid,
                     detalle=f"Editó la zona común «{z.nombre}»")
    return z


@router.delete("/zonas/{zona_id}", status_code=204, dependencies=[Depends(require_permiso("zonas.eliminar"))])
def eliminar_zona(zona_id: int, db: Session = Depends(get_db),
                  usuario: Usuario = Depends(get_current_user), cid: int | None = Depends(conjunto_activo)):
    z = db.query(ZonaComun).get(zona_id)
    if not z or (cid is not None and z.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Zona común no encontrada.")
    nombre = z.nombre
    db.query(ReservaZona).filter(ReservaZona.zona_id == zona_id).delete(synchronize_session=False)
    db.delete(z)
    db.commit()
    registrar_seguro(db=db, usuario=usuario, accion="eliminar", modulo="Zonas comunes",
                     entidad="zona_comun", entidad_id=zona_id, id_conjunto=cid,
                     detalle=f"Eliminó la zona común «{nombre}»")
    return None


# ---------------------------------------------------------------------------
# DISPONIBILIDAD
# ---------------------------------------------------------------------------
@router.get("/disponibilidad", dependencies=[Depends(require_permiso("reservas.ver"))])
def disponibilidad(
    zona_id: int,
    fecha: date,
    db: Session = Depends(get_db),
    cid: int | None = Depends(conjunto_activo),
):
    """Franjas ocupadas de una zona en una fecha (para pintar el selector)."""
    zona = db.query(ZonaComun).get(zona_id)
    if not zona or (cid is not None and zona.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Zona común no encontrada.")
    ocupadas = (
        db.query(ReservaZona)
        .filter(ReservaZona.zona_id == zona_id, ReservaZona.fecha == fecha,
                ReservaZona.estado.in_(ESTADOS_OCUPAN))
        .order_by(ReservaZona.hora_inicio)
        .all()
    )
    return {
        "zona_id": zona_id,
        "fecha": fecha,
        "hora_apertura": zona.hora_apertura,
        "hora_cierre": zona.hora_cierre,
        "ocupadas": [
            {"hora_inicio": r.hora_inicio, "hora_fin": r.hora_fin, "estado": r.estado}
            for r in ocupadas
        ],
        "disponible": len(ocupadas) == 0,
    }


# ---------------------------------------------------------------------------
# RESERVAS
# ---------------------------------------------------------------------------
@router.get("", response_model=list[schemas.ReservaResponse], dependencies=[Depends(require_permiso("reservas.ver"))])
def listar_reservas(
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """El residente ve su historial personal; la administración ve todas."""
    from app.permisos import CONSEJO

    q = filtrar(db.query(ReservaZona), ReservaZona, cid)
    # El consejo supervisa todas las reservas del conjunto aunque no las gestione.
    if not usuario_tiene_permiso(db, usuario, "reservas.gestionar") and usuario.rol_id != CONSEJO:
        q = q.filter(ReservaZona.usuario_id == usuario.id)
    if estado:
        q = q.filter(ReservaZona.estado == estado)
    if desde:
        q = q.filter(ReservaZona.fecha >= desde)
    if hasta:
        q = q.filter(ReservaZona.fecha <= hasta)
    filas = q.order_by(ReservaZona.fecha.desc(), ReservaZona.hora_inicio).all()
    return [_serializar(db, r) for r in filas]


@router.post("", response_model=schemas.ReservaResponse, status_code=201, dependencies=[Depends(require_permiso("reservas.crear"))])
def crear_reserva(
    data: schemas.ReservaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    zona = db.query(ZonaComun).get(data.zona_id)
    if not zona or (cid is not None and zona.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Zona común no encontrada.")
    if not zona.activo:
        raise HTTPException(status_code=400, detail="La zona común no está disponible.")

    inicio, fin = _minutos(data.hora_inicio), _minutos(data.hora_fin)
    if fin <= inicio:
        raise HTTPException(status_code=400, detail="La hora final debe ser posterior a la inicial.")
    if inicio < _minutos(zona.hora_apertura) or fin > _minutos(zona.hora_cierre):
        raise HTTPException(
            status_code=400,
            detail=f"La zona se puede reservar entre {zona.hora_apertura} y {zona.hora_cierre}.",
        )
    if data.fecha < date.today():
        raise HTTPException(status_code=400, detail="No se pueden reservar fechas pasadas.")
    if data.asistentes and zona.capacidad and data.asistentes > zona.capacidad:
        raise HTTPException(status_code=400, detail=f"La zona admite máximo {zona.capacidad} personas.")

    conflicto = _hay_conflicto(db, zona.id, data.fecha, data.hora_inicio, data.hora_fin)
    if conflicto:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Ya existe una reserva de {zona.nombre} el {data.fecha:%d/%m/%Y} "
                f"de {conflicto.hora_inicio} a {conflicto.hora_fin}. Elige otro horario."
            ),
        )

    estado = "pendiente" if zona.requiere_aprobacion else "aprobada"
    r = ReservaZona(
        zona_id=zona.id, usuario_id=usuario.id, fecha=data.fecha,
        hora_inicio=data.hora_inicio, hora_fin=data.hora_fin,
        motivo=data.motivo, asistentes=data.asistentes, estado=estado,
        id_conjunto=cid,
    )
    db.add(r)
    db.commit()
    db.refresh(r)

    if estado == "pendiente":
        notif.notificar_seguro(
            db=db, id_conjunto=cid, tipo="reserva", autor_id=usuario.id,
            titulo="Nueva reserva por aprobar",
            mensaje=f"{usuario.nombre} solicitó {zona.nombre} el {data.fecha:%d/%m/%Y} de {data.hora_inicio} a {data.hora_fin}.",
            clave=f"creado:{r.id}", severidad="media",
            url="/dashboard/reservas",
        )
    else:
        notif.notificar_seguro(
            db=db, id_conjunto=cid, tipo="reserva", autor_id=usuario.id,
            titulo="Reserva confirmada",
            mensaje=f"Tu reserva de {zona.nombre} quedó confirmada para el {data.fecha:%d/%m/%Y} de {data.hora_inicio} a {data.hora_fin}.",
            clave=f"confirmada:{r.id}", severidad="baja",
            url="/dashboard/reservas", solo_usuario_id=usuario.id,
        )
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Reservas",
                     entidad="reserva", entidad_id=r.id, id_conjunto=cid,
                     detalle=f"Reservó {zona.nombre} el {data.fecha} de {data.hora_inicio} a {data.hora_fin}")
    return _serializar(db, r)


@router.put("/{reserva_id}/decidir", response_model=schemas.ReservaResponse, dependencies=[Depends(require_permiso("reservas.gestionar"))])
def decidir_reserva(
    reserva_id: int,
    datos: dict,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Aprobar, rechazar o cancelar una reserva (UH-10)."""
    estado = str(datos.get("estado", "")).lower()
    if estado not in {"aprobada", "rechazada", "cancelada"}:
        raise HTTPException(status_code=400, detail="Estado inválido: aprobada, rechazada o cancelada.")
    r = db.query(ReservaZona).get(reserva_id)
    if not r or (cid is not None and r.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    if estado == "aprobada":
        conflicto = _hay_conflicto(db, r.zona_id, r.fecha, r.hora_inicio, r.hora_fin, excluir_id=r.id)
        if conflicto:
            raise HTTPException(
                status_code=409,
                detail=f"No se puede aprobar: hay otra reserva en ese horario (de {conflicto.hora_inicio} a {conflicto.hora_fin}).",
            )
    r.estado = estado
    r.motivo_decision = datos.get("motivo_decision")
    r.decidido_por = usuario.id
    r.fecha_decision = datetime.utcnow()
    db.commit()
    db.refresh(r)
    zona = db.query(ZonaComun).get(r.zona_id)
    if r.usuario_id:
        notif.notificar_seguro(
            db=db, id_conjunto=cid, tipo="reserva", autor_id=usuario.id,
            titulo=f"Reserva {estado}",
            mensaje=f"Tu reserva de {zona.nombre if zona else 'zona común'} el {r.fecha:%d/%m/%Y} quedó {estado}."
                    + (f" Motivo: {r.motivo_decision}" if r.motivo_decision else ""),
            clave=f"decision:{r.id}:{estado}", severidad="media",
            url="/dashboard/reservas", solo_usuario_id=r.usuario_id,
        )
    registrar_seguro(db=db, usuario=usuario, accion="editar", modulo="Reservas",
                     entidad="reserva", entidad_id=r.id, id_conjunto=cid,
                     detalle=f"Marcó la reserva {r.id} como {estado}")
    return _serializar(db, r)


@router.delete("/{reserva_id}", status_code=204, dependencies=[Depends(require_alguno("reservas.crear", "reservas.gestionar"))])
def eliminar_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """El residente cancela su propia reserva; la administración puede borrar cualquiera."""
    r = db.query(ReservaZona).get(reserva_id)
    if not r or (cid is not None and r.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    if not usuario_tiene_permiso(db, usuario, "reservas.gestionar") and r.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Sólo puedes cancelar tus propias reservas.")
    db.delete(r)
    db.commit()
    registrar_seguro(db=db, usuario=usuario, accion="eliminar", modulo="Reservas",
                     entidad="reserva", entidad_id=reserva_id, id_conjunto=cid,
                     detalle=f"Eliminó/canceló la reserva {reserva_id}")
    return None
