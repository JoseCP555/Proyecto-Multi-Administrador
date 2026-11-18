"""Comprobantes de pago y estado de cuenta del residente (UH-13 · UH-17).

* El residente sube una imagen o PDF de su comprobante; el pago queda en
  estado **En revisión** hasta que la administración lo confirme (UH-13).
* Cada usuario puede consultar sus pagos, fechas y saldo pendiente y exportar
  el estado de cuenta en PDF (UH-17).
"""
from __future__ import annotations

import os
import secrets
import shutil
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.auditoria import registrar_seguro
from app.conjunto_ctx import conjunto_activo, filtrar
from app.database import get_db
from app.deps import get_current_user, require_permiso, usuario_tiene_permiso
from app.models import (
    ComprobantePago, ConceptoFinanciero, MovimientoFinanciero, Propiedad, Residente, Usuario,
)

router = APIRouter(prefix="/pagos", tags=["Pagos"])

ARCHIVOS_DIR = os.getenv("ARCHIVOS_DIR", "./archivos_documentos")
os.makedirs(ARCHIVOS_DIR, exist_ok=True)
EXTENSIONES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
MAX_BYTES = 10 * 1024 * 1024


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _puede_revisar(db: Session, usuario: Usuario) -> bool:
    return usuario_tiene_permiso(db, usuario, "pagos.revisar")


def _serializar(db: Session, c: ComprobantePago) -> dict:
    u = db.query(Usuario).get(c.usuario_id)
    return {
        "id": c.id,
        "usuario_id": c.usuario_id,
        "solicitante": u.nombre if u else None,
        "movimiento_id": c.movimiento_id,
        "periodo": c.periodo,
        "monto": float(c.monto or 0),
        "ruta_archivo": c.ruta_archivo,
        "nombre_archivo": c.nombre_archivo,
        "mime": c.mime,
        "tamano": c.tamano,
        "estado": c.estado,
        "observacion": c.observacion,
        "revisado_por": c.revisado_por,
        "fecha_revision": c.fecha_revision,
        "fecha_creacion": c.fecha_creacion,
    }


def _propiedades_del_usuario(db: Session, usuario: Usuario, cid: int | None):
    q = db.query(Residente).filter(Residente.usuario_id == usuario.id)
    if cid is not None:
        q = q.filter(Residente.id_conjunto == cid)
    residentes = q.all()
    ids = [r.id for r in residentes]
    if not ids:
        return []
    return db.query(Propiedad).filter(Propiedad.residente_id.in_(ids)).all()


def _movimientos_de(db: Session, usuario: Usuario, cid: int | None):
    props = _propiedades_del_usuario(db, usuario, cid)
    if not props:
        return [], []
    ids = [p.id for p in props]
    movs = (
        filtrar(db.query(MovimientoFinanciero).filter(MovimientoFinanciero.propiedad_id.in_(ids)),
                MovimientoFinanciero, cid)
        .order_by(MovimientoFinanciero.fecha_vencimiento.desc())
        .all()
    )
    return props, movs


def _estado_cuenta(db: Session, usuario: Usuario, cid: int | None) -> dict:
    conceptos = {c.id: c for c in db.query(ConceptoFinanciero).all()}
    props, movs = _movimientos_de(db, usuario, cid)

    total_facturado = total_pagado = saldo = 0.0
    items = []
    for m in movs:
        concepto = conceptos.get(m.concepto_id)
        es_ingreso = (concepto.tipo if concepto else "ingreso") == "ingreso"
        monto = float(m.monto or 0)
        if es_ingreso:
            total_facturado += monto
        if m.estado == "pagado":
            if es_ingreso:
                total_pagado += monto
        elif m.estado in ("pendiente", "vencido"):
            saldo += monto
        items.append({
            "id": m.id,
            "concepto": concepto.nombre if concepto else "—",
            "tipo": concepto.tipo if concepto else "ingreso",
            "monto": monto,
            "fecha_vencimiento": m.fecha_vencimiento,
            "fecha_pago": m.fecha_pago,
            "estado": m.estado,
            "numero_recibo": m.numero_recibo,
            "propiedad": next((p.apartamento for p in props if p.id == m.propiedad_id), None),
        })

    pendientes = [i for i in items if i["estado"] in ("pendiente", "vencido")]
    proximo = min((i["fecha_vencimiento"] for i in pendientes), default=None)

    comprobantes = (
        filtrar(db.query(ComprobantePago).filter(ComprobantePago.usuario_id == usuario.id),
                ComprobantePago, cid)
        .order_by(ComprobantePago.fecha_creacion.desc())
        .all()
    )

    return {
        "usuario": {"id": usuario.id, "nombre": usuario.nombre, "correo": usuario.correo},
        "unidades": [{"id": p.id, "apartamento": p.apartamento, "torre": p.torre, "bloque": p.bloque} for p in props],
        "sin_unidad": len(props) == 0,
        "total_facturado": round(total_facturado, 2),
        "total_pagado": round(total_pagado, 2),
        "saldo": round(saldo, 2),
        "proximo_vencimiento": proximo,
        "movimientos": items,
        "comprobantes": [_serializar(db, c) for c in comprobantes],
        "generado": datetime.utcnow(),
    }


# ---------------------------------------------------------------------------
# COMPROBANTES
# ---------------------------------------------------------------------------
@router.get("/comprobantes", response_model=list[schemas.ComprobanteResponse], dependencies=[Depends(require_permiso("pagos.ver"))])
def listar_comprobantes(
    estado: str | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    q = filtrar(db.query(ComprobantePago), ComprobantePago, cid)
    if not _puede_revisar(db, usuario):
        q = q.filter(ComprobantePago.usuario_id == usuario.id)
    if estado:
        q = q.filter(ComprobantePago.estado == estado)
    return [_serializar(db, c) for c in q.order_by(ComprobantePago.fecha_creacion.desc()).all()]


@router.post("/comprobantes", response_model=schemas.ComprobanteResponse, status_code=201, dependencies=[Depends(require_permiso("pagos.crear"))])
def subir_comprobante(
    monto: float = Form(...),
    periodo: str = Form(None),
    movimiento_id: int = Form(None),
    observacion: str = Form(None),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Sube la imagen/PDF del comprobante; queda **En revisión** (UH-13)."""
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor que cero.")
    nombre_original = os.path.basename(archivo.filename or "comprobante")
    ext = os.path.splitext(nombre_original)[1].lower()
    if ext not in EXTENSIONES:
        raise HTTPException(status_code=400, detail="El comprobante debe ser PDF o imagen (PNG/JPG/WEBP).")

    if movimiento_id is not None:
        mov = db.query(MovimientoFinanciero).get(movimiento_id)
        if not mov or (cid is not None and mov.id_conjunto not in (None, cid)):
            raise HTTPException(status_code=404, detail="Movimiento no encontrado.")

    nombre_guardado = f"comprobante-{secrets.token_hex(8)}{ext}"
    destino = os.path.join(ARCHIVOS_DIR, nombre_guardado)
    with open(destino, "wb") as out:
        shutil.copyfileobj(archivo.file, out)
    tamano = os.path.getsize(destino)
    if tamano > MAX_BYTES:
        os.remove(destino)
        raise HTTPException(status_code=400, detail="El comprobante supera el máximo de 10 MB.")

    c = ComprobantePago(
        usuario_id=usuario.id,
        movimiento_id=movimiento_id,
        periodo=periodo or date.today().strftime("%Y-%m"),
        monto=monto,
        ruta_archivo=nombre_guardado,
        nombre_archivo=nombre_original,
        mime=archivo.content_type,
        tamano=tamano,
        estado="en_revision",
        observacion=observacion,
        id_conjunto=cid,
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    from app.permisos import ADMIN, SUPER_ADMIN, TESORERIA

    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="comprobante", autor_id=usuario.id,
        titulo="Nuevo comprobante de pago por revisar",
        mensaje=f"{usuario.nombre} subió un comprobante por ${monto:,.0f} (estado: En revisión).",
        clave=f"creado:{c.id}", severidad="media", url="/dashboard/pagos",
        solo_roles=[SUPER_ADMIN, ADMIN, TESORERIA],
    )
    registrar_seguro(db=db, usuario=usuario, accion="crear", modulo="Comprobantes de pago",
                     entidad="comprobante", entidad_id=c.id, id_conjunto=cid,
                     detalle=f"Subió un comprobante por ${monto:,.0f} ({c.periodo})")
    return _serializar(db, c)


@router.get("/comprobantes/{comprobante_id}/descargar", dependencies=[Depends(require_permiso("pagos.ver"))])
def descargar_comprobante(
    comprobante_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    c = db.query(ComprobantePago).get(comprobante_id)
    if not c or (cid is not None and c.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Comprobante no encontrado.")
    if not _puede_revisar(db, usuario) and c.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="No puedes descargar comprobantes de otro usuario.")
    ruta = c.ruta_archivo if os.path.isabs(c.ruta_archivo) else os.path.join(ARCHIVOS_DIR, os.path.basename(c.ruta_archivo))
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="El archivo ya no existe en el servidor.")
    return FileResponse(ruta, media_type=c.mime or "application/octet-stream",
                        filename=c.nombre_archivo or "comprobante")


@router.put("/comprobantes/{comprobante_id}/revisar", response_model=schemas.ComprobanteResponse, dependencies=[Depends(require_permiso("pagos.revisar"))])
def revisar_comprobante(
    comprobante_id: int,
    data: schemas.ComprobanteRevision,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Confirma (aprobado) o rechaza el comprobante y avisa al residente (UH-13)."""
    if data.estado not in {"aprobado", "rechazado"}:
        raise HTTPException(status_code=400, detail="Estado inválido: aprobado o rechazado.")
    c = db.query(ComprobantePago).get(comprobante_id)
    if not c or (cid is not None and c.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Comprobante no encontrado.")

    c.estado = data.estado
    c.observacion = data.observacion
    c.revisado_por = usuario.id
    c.fecha_revision = datetime.utcnow()

    # Si el comprobante está asociado a una cuota, se marca como pagada.
    if data.estado == "aprobado" and c.movimiento_id:
        mov = db.query(MovimientoFinanciero).get(c.movimiento_id)
        if mov:
            mov.estado = "pagado"
            mov.fecha_pago = date.today()
            mov.metodo_pago = mov.metodo_pago or "comprobante"
    db.commit()
    db.refresh(c)
    if data.estado == "aprobado":
        from app.redis_client import cache_del, cache_del_prefix
        cache_del("dashboard_stats")
        cache_del_prefix("dashboard_stats:", "finanzas_resumen:", "finanzas_por_mes:")

    notif.notificar_seguro(
        db=db, id_conjunto=cid, tipo="comprobante_revision", autor_id=usuario.id,
        titulo=f"Comprobante {c.estado}",
        mensaje=f"Tu comprobante de ${float(c.monto):,.0f} fue {c.estado}."
                + (f" Observación: {c.observacion}" if c.observacion else ""),
        clave=f"revision:{c.id}:{c.estado}", severidad="alta",
        url="/dashboard/pagos", solo_usuario_id=c.usuario_id,
    )
    registrar_seguro(db=db, usuario=usuario, accion="editar", modulo="Comprobantes de pago",
                     entidad="comprobante", entidad_id=c.id, id_conjunto=cid,
                     detalle=f"Marcó el comprobante {c.id} como {c.estado}")
    return _serializar(db, c)


# ---------------------------------------------------------------------------
# ESTADO DE CUENTA (UH-17)
# ---------------------------------------------------------------------------
@router.get("/estado-cuenta", dependencies=[Depends(require_permiso("pagos.ver"))])
def estado_cuenta(
    usuario_id: int | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Pagos, fechas y saldo pendiente del usuario autenticado.

    La administración puede consultar el de un residente concreto pasando
    `usuario_id`.
    """
    objetivo = usuario
    if usuario_id and usuario_id != usuario.id:
        if not usuario_tiene_permiso(db, usuario, "pagos.revisar"):
            raise HTTPException(status_code=403, detail="No puedes consultar el estado de cuenta de otro usuario.")
        objetivo = db.query(Usuario).get(usuario_id)
        if not objetivo:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return _estado_cuenta(db, objetivo, cid)


@router.get("/estado-cuenta.pdf", dependencies=[Depends(require_permiso("pagos.ver"))])
def estado_cuenta_pdf(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    cid: int | None = Depends(conjunto_activo),
):
    """Exporta el estado de cuenta del usuario en PDF (UH-17)."""
    from app import exportar as exp

    datos = _estado_cuenta(db, usuario, cid)
    contenido = exp.estado_cuenta_pdf(datos)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="estado_cuenta.pdf"'},
    )


@router.get("/comprobantes.xlsx", dependencies=[Depends(require_permiso("pagos.revisar"))])
def exportar_comprobantes(
    db: Session = Depends(get_db),
    cid: int | None = Depends(conjunto_activo),
):
    """Listado de comprobantes para revisión (Excel)."""
    from app import exportar as exp

    contenido = exp.comprobantes_xlsx(db, cid)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="comprobantes.xlsx"'},
    )
