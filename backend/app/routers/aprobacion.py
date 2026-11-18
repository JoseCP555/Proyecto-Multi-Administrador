"""Solicitudes del administrador que aprueba el consejo (UH-24).

El administrador envía una solicitud (gasto, contrato, presupuesto…), el
consejo la ve en su panel y decide aprobar o rechazar. La decisión queda
registrada con **fecha, hora y el miembro que la tomó**.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.auditoria import registrar_seguro
from app.conjunto_ctx import conjunto_activo, filtrar
from app.database import get_db
from app.deps import get_current_user, require_permiso, usuario_tiene_permiso
from app.models import SolicitudAprobacion, Usuario
from app.permisos import CONSEJO

router = APIRouter(prefix="/aprobaciones", tags=["Aprobaciones del consejo"])

CATEGORIAS = {"gasto", "contrato", "presupuesto", "otro"}


def _serializar(db: Session, s: SolicitudAprobacion) -> dict:
    creador = db.query(Usuario).get(s.creado_por) if s.creado_por else None
    decidio = db.query(Usuario).get(s.decidido_por) if s.decidido_por else None
    return {
        "id": s.id,
        "titulo": s.titulo,
        "descripcion": s.descripcion,
        "monto": float(s.monto or 0),
        "categoria": s.categoria,
        "estado": s.estado,
        "creado_por": s.creado_por,
        "creado_por_nombre": creador.nombre if creador else None,
        "decidido_por": s.decidido_por,
        "decidido_por_nombre": decidio.nombre if decidio else None,
        "fecha_decision": s.fecha_decision,
        "motivo_decision": s.motivo_decision,
        "fecha_creacion": s.fecha_creacion,
    }


@router.get("", response_model=list[schemas.AprobacionResponse], dependencies=[Depends(require_permiso("aprobaciones.ver"))])
def listar(
    estado: str | None = None,
    db: Session = Depends(get_db),
    cid: int | None = Depends(conjunto_activo),
):
    q = filtrar(db.query(SolicitudAprobacion), SolicitudAprobacion, cid)
    if estado:
        q = q.filter(SolicitudAprobacion.estado == estado)
    filas = q.order_by(SolicitudAprobacion.estado.desc(), SolicitudAprobacion.fecha_creacion.desc()).all()
    return [_serializar(db, s) for s in filas]


@router.post("", response_model=schemas.AprobacionResponse, status_code=201, dependencies=[Depends(require_permiso("aprobaciones.crear"))])
def crear(
    data: schemas.AprobacionCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    if data.categoria not in CATEGORIAS:
        raise HTTPException(status_code=400, detail=f"Categoría inválida. Usa: {', '.join(sorted(CATEGORIAS))}.")
    s = SolicitudAprobacion(
        titulo=data.titulo.strip(), descripcion=data.descripcion.strip(),
        monto=data.monto, categoria=data.categoria, estado="pendiente",
        creado_por=usuario.id, id_conjunto=cid,
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="aprobacion", autor_id=usuario.id,
        titulo="Solicitud pendiente de aprobación del consejo",
        mensaje=f"{s.titulo} — ${float(s.monto):,.0f} ({s.categoria}). Enviada por {usuario.nombre}.",
        clave=f"creada:{s.id}", severidad="alta", url="/dashboard/aprobaciones",
        solo_roles=[CONSEJO],
    )
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Aprobaciones del consejo",
                     entidad="solicitud", entidad_id=s.id, id_conjunto=cid,
                     detalle=f"Envió la solicitud «{s.titulo}» por ${float(s.monto):,.0f}")
    return _serializar(db, s)


@router.put("/{solicitud_id}/decidir", response_model=schemas.AprobacionResponse, dependencies=[Depends(require_permiso("aprobaciones.decidir"))])
def decidir(
    solicitud_id: int,
    data: schemas.AprobacionDecision,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Aprueba o rechaza dejando fecha, hora y responsable (UH-24)."""
    if data.estado not in {"aprobada", "rechazada"}:
        raise HTTPException(status_code=400, detail="Estado inválido: aprobada o rechazada.")
    s = db.query(SolicitudAprobacion).get(solicitud_id)
    if not s or (cid is not None and s.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    if s.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta solicitud ya fue decidida.")

    s.estado = data.estado
    s.motivo_decision = data.motivo_decision
    s.decidido_por = usuario.id
    s.fecha_decision = datetime.utcnow()
    db.commit()
    db.refresh(s)

    if s.creado_por:
        notif.notificar_seguro(
            db=db, id_conjunto=cid, tipo="aprobacion_decision", autor_id=usuario.id,
            titulo=f"Solicitud {s.estado} por el consejo",
            mensaje=f"«{s.titulo}» fue {s.estado} por {usuario.nombre}."
                    + (f" Motivo: {s.motivo_decision}" if s.motivo_decision else ""),
            clave=f"decision:{s.id}:{s.estado}", severidad="alta",
            url="/dashboard/aprobaciones", solo_usuario_id=s.creado_por,
        )
    registrar_seguro(db=db, usuario=usuario, accion="editar", modulo="Aprobaciones del consejo",
                     entidad="solicitud", entidad_id=s.id, id_conjunto=cid,
                     detalle=f"{data.estado.capitalize()} la solicitud «{s.titulo}»")
    return _serializar(db, s)


@router.delete("/{solicitud_id}", status_code=204, dependencies=[Depends(require_permiso("aprobaciones.crear"))])
def eliminar(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    s = db.query(SolicitudAprobacion).get(solicitud_id)
    if not s or (cid is not None and s.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    if s.estado != "pendiente" and not usuario_tiene_permiso(db, usuario, "aprobaciones.decidir"):
        raise HTTPException(status_code=400, detail="No se puede eliminar una solicitud ya decidida.")
    db.delete(s)
    db.commit()
    registrar_seguro(db=db, usuario=usuario, accion="eliminar", modulo="Aprobaciones del consejo",
                     entidad="solicitud", entidad_id=solicitud_id, id_conjunto=cid,
                     detalle=f"Eliminó la solicitud {solicitud_id}")
    return None
