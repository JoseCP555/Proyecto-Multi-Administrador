"""Comunicados y circulares masivas (UH-11 · UH-18).

Al publicar un comunicado se envía por **notificación y correo** a todos los
residentes activos del conjunto y queda guardado para consulta posterior.
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
from app.deps import get_current_user, require_permiso
from app.models import Comunicado, Usuario

router = APIRouter(prefix="/comunicados", tags=["Comunicados"])

CATEGORIAS = {"informativo", "normas", "evento", "urgente"}
PRIORIDADES = {"alta", "media", "baja"}


def _serializar(db: Session, c: Comunicado) -> dict:
    autor = db.query(Usuario).get(c.enviado_por) if c.enviado_por else None
    return {
        "id": c.id,
        "titulo": c.titulo,
        "contenido": c.contenido,
        "categoria": c.categoria,
        "prioridad": c.prioridad,
        "fijado": c.fijado,
        "enviado_por": c.enviado_por,
        "autor": autor.nombre if autor else "Administración",
        "fecha_creacion": c.fecha_creacion,
    }


@router.get("", response_model=list[schemas.ComunicadoResponse], dependencies=[Depends(require_permiso("comunicados.ver"))])
def listar(
    categoria: str | None = None,
    db: Session = Depends(get_db),
    cid: int | None = Depends(conjunto_activo),
):
    q = filtrar(db.query(Comunicado), Comunicado, cid)
    if categoria:
        q = q.filter(Comunicado.categoria == categoria)
    # Los fijados primero; luego los más recientes.
    return [_serializar(db, c) for c in q.order_by(Comunicado.fijado.desc(), Comunicado.fecha_creacion.desc()).all()]


@router.post("", response_model=schemas.ComunicadoResponse, status_code=201, dependencies=[Depends(require_permiso("comunicados.crear"))])
def publicar(
    data: schemas.ComunicadoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    if data.categoria not in CATEGORIAS:
        raise HTTPException(status_code=400, detail=f"Categoría inválida. Usa: {', '.join(sorted(CATEGORIAS))}.")
    if data.prioridad not in PRIORIDADES:
        raise HTTPException(status_code=400, detail="Prioridad inválida: alta, media o baja.")

    c = Comunicado(
        titulo=data.titulo.strip(), contenido=data.contenido.strip(),
        categoria=data.categoria, prioridad=data.prioridad, fijado=data.fijado,
        enviado_por=usuario.id, id_conjunto=cid, fecha_creacion=datetime.utcnow(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    # Notificación + correo a todos los residentes activos (UH-11 / UH-18).
    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="comunicado", autor_id=usuario.id,
        titulo=f"Comunicado: {c.titulo}",
        mensaje=(c.contenido[:220] + ("…" if len(c.contenido) > 220 else "")),
        clave=f"creado:{c.id}",
        severidad="alta" if c.prioridad == "alta" or c.categoria == "urgente" else "media",
        url="/dashboard/comunicados",
    )
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Comunicados",
                     entidad="comunicado", entidad_id=c.id, id_conjunto=cid,
                     detalle=f"Publicó el comunicado «{c.titulo}»")
    return _serializar(db, c)


@router.put("/{comunicado_id}", response_model=schemas.ComunicadoResponse, dependencies=[Depends(require_permiso("comunicados.editar"))])
def editar(
    comunicado_id: int,
    data: schemas.ComunicadoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    c = db.query(Comunicado).get(comunicado_id)
    if not c or (cid is not None and c.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Comunicado no encontrado.")
    c.titulo = data.titulo.strip()
    c.contenido = data.contenido.strip()
    c.categoria = data.categoria
    c.prioridad = data.prioridad
    c.fijado = data.fijado
    db.commit()
    db.refresh(c)
    registrar_seguro(db=db, usuario=usuario, accion="editar", modulo="Comunicados",
                     entidad="comunicado", entidad_id=c.id, id_conjunto=cid,
                     detalle=f"Editó el comunicado «{c.titulo}»")
    return _serializar(db, c)


@router.delete("/{comunicado_id}", status_code=204, dependencies=[Depends(require_permiso("comunicados.eliminar"))])
def eliminar(
    comunicado_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    c = db.query(Comunicado).get(comunicado_id)
    if not c or (cid is not None and c.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Comunicado no encontrado.")
    db.delete(c)
    db.commit()
    registrar_seguro(db=db, usuario=usuario, accion="eliminar", modulo="Comunicados",
                     entidad="comunicado", entidad_id=comunicado_id, id_conjunto=cid,
                     detalle=f"Eliminó el comunicado {comunicado_id}")
    return None
