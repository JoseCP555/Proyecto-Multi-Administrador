"""PQRS: peticiones, quejas, reclamos y sugerencias (UH-09 · UH-16 · UH-32).

* El residente radica una PQRS y recibe un **número de radicado**; sólo ve las
  suyas y puede consultar su estado (UH-16).
* El administrador las ve todas en su panel, las pone en proceso, responde y
  las cierra (UH-09).
* Cuando la PQRS es de la categoría **zona común** el consejo recibe una
  notificación con el resumen y un enlace directo al caso (UH-32).
"""
from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.auditoria import registrar_seguro
from app.conjunto_ctx import conjunto_activo, filtrar
from app.database import get_db
from app.deps import get_current_user, require_permiso, usuario_tiene_permiso
from app.models import Pqrs, Propiedad, Residente, Usuario

router = APIRouter(prefix="/pqrs", tags=["PQRS"])

ARCHIVOS_DIR = os.getenv("ARCHIVOS_DIR", "./archivos_documentos")
os.makedirs(ARCHIVOS_DIR, exist_ok=True)

TIPOS = {"peticion", "queja", "reclamo", "sugerencia"}
CATEGORIAS = {"zonas_comunes", "administracion", "convivencia", "finanzas", "otra"}
ESTADOS = {"pendiente", "en_proceso", "cerrada"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _radicado() -> str:
    """Número de radicado legible y único: PQRS-AAAAMMDD-XXXXXX."""
    return f"PQRS-{datetime.utcnow():%Y%m%d}-{secrets.token_hex(3).upper()}"


def _residente_de(db: Session, usuario: Usuario, cid: int | None) -> Residente | None:
    q = db.query(Residente).filter(Residente.usuario_id == usuario.id)
    if cid is not None:
        q = q.filter(Residente.id_conjunto == cid)
    return q.first()


def _apartamento_de(db: Session, residente: Residente | None) -> str | None:
    if not residente:
        return None
    prop = db.query(Propiedad).filter(Propiedad.residente_id == residente.id).first()
    return prop.apartamento if prop else None


def _es_staff(db: Session, usuario: Usuario) -> bool:
    """¿Puede ver y gestionar las PQRS de todo el conjunto?

    La administración (responder/cerrar/eliminar) y el consejo de
    administración ven todas las PQRS del conjunto (UH-09 / UH-32).
    """
    from app.permisos import CONSEJO

    if usuario.rol_id == CONSEJO:
        return True
    return any(
        usuario_tiene_permiso(db, usuario, p)
        for p in ("pqrs.responder", "pqrs.cerrar", "pqrs.eliminar")
    )


def _serializar(db: Session, p: Pqrs) -> dict:
    solicitante = db.query(Usuario).get(p.usuario_id) if p.usuario_id else None
    residente = db.query(Residente).get(p.residente_id) if p.residente_id else None
    respondido = db.query(Usuario).get(p.respondido_por) if p.respondido_por else None
    return {
        "id": p.id,
        "radicado": p.radicado,
        "usuario_id": p.usuario_id,
        "residente_id": p.residente_id,
        "tipo": p.tipo,
        "categoria": p.categoria,
        "asunto": p.asunto,
        "descripcion": p.descripcion,
        "adjunto": p.adjunto,
        "estado": p.estado,
        "respuesta": p.respuesta,
        "respondido_por": p.respondido_por,
        "respondido_por_nombre": respondido.nombre if respondido else None,
        "fecha_respuesta": p.fecha_respuesta,
        "fecha_creacion": p.fecha_creacion,
        "fecha_actualizacion": p.fecha_actualizacion,
        "solicitante": solicitante.nombre if solicitante else None,
        "apartamento": _apartamento_de(db, residente),
    }


def _obtener(db: Session, pqrs_id: int, usuario: Usuario, cid: int | None) -> Pqrs:
    p = db.query(Pqrs).get(pqrs_id)
    if not p or (cid is not None and p.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="PQRS no encontrada.")
    if not _es_staff(db, usuario) and p.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo puedes consultar tus propias PQRS.")
    return p


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("", response_model=list[schemas.PqrsResponse], dependencies=[Depends(require_permiso("pqrs.ver"))])
def listar(
    estado: str | None = None,
    tipo: str | None = None,
    categoria: str | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Panel de PQRS. El residente sólo ve las suyas; la administración, todas."""
    q = filtrar(db.query(Pqrs), Pqrs, cid)
    if not _es_staff(db, usuario):
        q = q.filter(Pqrs.usuario_id == usuario.id)
    if estado:
        q = q.filter(Pqrs.estado == estado)
    if tipo:
        q = q.filter(Pqrs.tipo == tipo)
    if categoria:
        q = q.filter(Pqrs.categoria == categoria)
    filas = q.order_by(Pqrs.fecha_creacion.desc()).all()
    return [_serializar(db, p) for p in filas]


@router.get("/{pqrs_id}", response_model=schemas.PqrsResponse, dependencies=[Depends(require_permiso("pqrs.ver"))])
def detalle(
    pqrs_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    return _serializar(db, _obtener(db, pqrs_id, usuario, cid))


@router.get("/{pqrs_id}/adjunto", dependencies=[Depends(require_permiso("pqrs.ver"))])
def descargar_adjunto(
    pqrs_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    p = _obtener(db, pqrs_id, usuario, cid)
    if not p.adjunto:
        raise HTTPException(status_code=404, detail="La PQRS no tiene adjunto.")
    ruta = p.adjunto if os.path.isabs(p.adjunto) else os.path.join(ARCHIVOS_DIR, os.path.basename(p.adjunto))
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="El archivo ya no existe en el servidor.")
    return FileResponse(ruta, filename=os.path.basename(p.adjunto))


@router.post("", response_model=schemas.PqrsResponse, status_code=201, dependencies=[Depends(require_permiso("pqrs.crear"))])
def radicar(
    data: schemas.PqrsCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Radica una PQRS y devuelve el número de radicado (UH-16)."""
    if data.tipo not in TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Usa uno de: {', '.join(sorted(TIPOS))}.")
    if data.categoria not in CATEGORIAS:
        raise HTTPException(status_code=400, detail=f"Categoría inválida. Usa una de: {', '.join(sorted(CATEGORIAS))}.")

    residente = _residente_de(db, usuario, cid)
    p = Pqrs(
        radicado=_radicado(),
        usuario_id=usuario.id,
        residente_id=residente.id if residente else None,
        tipo=data.tipo,
        categoria=data.categoria,
        asunto=data.asunto.strip(),
        descripcion=data.descripcion.strip(),
        adjunto=data.adjunto,
        estado="pendiente",
        id_conjunto=cid,
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    # Aviso a la administración (panel de PQRS con enlace directo al caso).
    enlace_caso = f"/dashboard/pqrs?id={p.id}"
    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="pqrs", autor_id=usuario.id,
        titulo=f"Nueva PQRS radicada ({p.tipo})",
        mensaje=f"Radicado {p.radicado}: {p.asunto}",
        clave=f"creado:{p.id}", severidad="alta" if p.tipo == "queja" else "media",
        url=enlace_caso,
    )
    # UH-32: si es de zonas comunes, el consejo recibe el resumen y el enlace directo al caso.
    if p.categoria == "zonas_comunes":
        from app.permisos import CONSEJO

        resumen_desc = (p.descripcion or "").strip()
        if len(resumen_desc) > 140:
            resumen_desc = resumen_desc[:140].rstrip() + "…"
        notif.notificar_seguro(
            db=db, id_conjunto=cid, tipo="pqrs_consejo", autor_id=usuario.id,
            titulo="PQRS de zona común recibida",
            mensaje=(
                f"Radicado {p.radicado}: {p.asunto}."
                + (f" Resumen: {resumen_desc}" if resumen_desc else "")
                + " Requiere atención del consejo."
            ),
            clave=f"consejo:{p.id}", severidad="alta",
            url=enlace_caso, solo_roles=[CONSEJO],
        )
    registrar_seguro(
        db=db, usuario=usuario, accion="crear", modulo="PQRS",
        entidad="pqrs", entidad_id=p.id, id_conjunto=cid,
        detalle=f"Radicó la PQRS {p.radicado} ({p.tipo}/{p.categoria}): {p.asunto}",
    )
    return _serializar(db, p)


@router.post("/con-adjunto", response_model=schemas.PqrsResponse, status_code=201, dependencies=[Depends(require_permiso("pqrs.crear"))])
def radicar_con_adjunto(
    tipo: str = Form("peticion"),
    categoria: str = Form("administracion"),
    asunto: str = Form(...),
    descripcion: str = Form(...),
    archivo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Igual que `POST /pqrs` pero aceptando una imagen o PDF de soporte."""
    adjunto = None
    if archivo is not None and archivo.filename:
        ext = os.path.splitext(os.path.basename(archivo.filename))[1].lower()
        if ext not in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
            raise HTTPException(status_code=400, detail="Adjunta un PDF o una imagen (PNG/JPG/WEBP).")
        nombre = f"pqrs-{secrets.token_hex(8)}{ext}"
        destino = os.path.join(ARCHIVOS_DIR, nombre)
        with open(destino, "wb") as out:
            shutil.copyfileobj(archivo.file, out)
        if os.path.getsize(destino) > 10 * 1024 * 1024:
            os.remove(destino)
            raise HTTPException(status_code=400, detail="El adjunto supera el máximo de 10 MB.")
        adjunto = nombre

    return radicar(
        schemas.PqrsCreate(tipo=tipo, categoria=categoria, asunto=asunto,
                          descripcion=descripcion, adjunto=adjunto),
        db=db, usuario=usuario, cid=cid,
    )


@router.put("/{pqrs_id}/responder", response_model=schemas.PqrsResponse, dependencies=[Depends(require_permiso("pqrs.responder"))])
def responder(
    pqrs_id: int,
    data: schemas.PqrsRespuesta,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Responde la PQRS y/o la pasa a 'en proceso' (UH-09)."""
    p = _obtener(db, pqrs_id, usuario, cid)
    if data.estado and data.estado not in ESTADOS:
        raise HTTPException(status_code=400, detail="Estado inválido.")
    if data.respuesta:
        p.respuesta = data.respuesta.strip()
        p.respondido_por = usuario.id
        p.fecha_respuesta = datetime.utcnow()
    p.estado = data.estado or ("en_proceso" if p.estado == "pendiente" else p.estado)
    db.commit()
    db.refresh(p)

    if p.usuario_id:
        notif.notificar_seguro(
            db=db, id_conjunto=cid, tipo="pqrs", autor_id=usuario.id,
            titulo=f"Respuesta a tu PQRS {p.radicado}",
            mensaje=f"Tu solicitud pasó a estado '{p.estado}'." + (f" Respuesta: {p.respuesta[:180]}" if p.respuesta else ""),
            clave=f"respuesta:{p.id}:{p.estado}:{int(p.fecha_respuesta.timestamp()) if p.fecha_respuesta else 0}",
            severidad="media", url=f"/dashboard/pqrs?id={p.id}", solo_usuario_id=p.usuario_id,
        )
    registrar_seguro(
        db=db, usuario=usuario, accion="editar", modulo="PQRS", entidad="pqrs",
        entidad_id=p.id, id_conjunto=cid,
        detalle=f"Respondió la PQRS {p.radicado} (estado {p.estado})",
    )
    return _serializar(db, p)


@router.put("/{pqrs_id}/cerrar", response_model=schemas.PqrsResponse, dependencies=[Depends(require_permiso("pqrs.cerrar"))])
def cerrar(
    pqrs_id: int,
    data: schemas.PqrsRespuesta | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Cierra la PQRS dejando la respuesta final registrada (UH-09)."""
    p = _obtener(db, pqrs_id, usuario, cid)
    if data and data.respuesta:
        p.respuesta = data.respuesta.strip()
        p.respondido_por = usuario.id
        p.fecha_respuesta = datetime.utcnow()
    p.estado = "cerrada"
    db.commit()
    db.refresh(p)

    if p.usuario_id:
        notif.notificar_seguro(
            db=db, id_conjunto=cid, tipo="pqrs", autor_id=usuario.id,
            titulo=f"PQRS {p.radicado} cerrada",
            mensaje=f"Tu solicitud fue cerrada. {p.respuesta or ''}".strip(),
            clave=f"cerrada:{p.id}", severidad="baja",
            url=f"/dashboard/pqrs?id={p.id}", solo_usuario_id=p.usuario_id,
        )
    registrar_seguro(
        db=db, usuario=usuario, accion="editar", modulo="PQRS", entidad="pqrs",
        entidad_id=p.id, id_conjunto=cid, detalle=f"Cerró la PQRS {p.radicado}",
    )
    return _serializar(db, p)


@router.delete("/{pqrs_id}", status_code=204, dependencies=[Depends(require_permiso("pqrs.eliminar"))])
def eliminar(
    pqrs_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    p = _obtener(db, pqrs_id, usuario, cid)
    db.delete(p)
    db.commit()
    registrar_seguro(
        db=db, usuario=usuario, accion="eliminar", modulo="PQRS", entidad="pqrs",
        entidad_id=pqrs_id, id_conjunto=cid, detalle=f"Eliminó la PQRS {pqrs_id}",
    )
    return None
