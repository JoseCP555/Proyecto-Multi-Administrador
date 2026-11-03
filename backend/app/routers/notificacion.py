"""Notificaciones reales: persistentes, accionables, por correo y por push.

`GET /notificaciones` mantiene el contrato anterior (devuelve una LISTA de
avisos con `tipo`, `severidad`, `titulo`, `mensaje` y `fecha`), así que el
frontend y las pruebas de RBAC siguen funcionando sin cambios.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, notificaciones_servicio as servicio, schemas
from app.database import get_db
from app.deps import get_current_user
from app.push import clave_publica

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


# ---------------------------------------------------------------------------
# Lectura (rutas estáticas ANTES de las dinámicas)
# ---------------------------------------------------------------------------
@router.get("")
def listar_notificaciones(
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Avisos del usuario + generación perezosa de recordatorios reales."""
    servicio.sincronizar_recordatorios(db, usuario)
    return servicio.listar_para(db, usuario)


@router.get("/resumen")
def resumen(
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Contador ligero para la campana (se consulta cada ~30 s)."""
    servicio.sincronizar_recordatorios(db, usuario)
    items = servicio.listar_para(db, usuario, limite=500)
    return {
        "no_leidas": sum(1 for n in items if not n["leida"]),
        "total": len(items),
    }


@router.get("/config")
def config_publica():
    """Clave pública VAPID y estado de los canales (sin autenticación)."""
    canales = servicio.resumen_canales()
    return {"vapid_publico": clave_publica() or None, **canales}


@router.get("/preferencias", response_model=schemas.PreferenciasNotificacionResponse)
def preferencias(
    usuario: models.Usuario = Depends(get_current_user),
):
    canales = servicio.resumen_canales()
    return {
        "correo": bool(getattr(usuario, "notificaciones_correo", True)),
        "push": bool(getattr(usuario, "notificaciones_push", True)),
        "vapid_publico": clave_publica() or None,
        **canales,
    }


@router.put("/preferencias", response_model=schemas.PreferenciasNotificacionResponse)
def actualizar_preferencias(
    data: schemas.PreferenciasNotificacionUpdate,
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.correo is not None:
        usuario.notificaciones_correo = bool(data.correo)
    if data.push is not None:
        usuario.notificaciones_push = bool(data.push)
    db.commit()
    return preferencias(usuario)


# ---------------------------------------------------------------------------
# Suscripciones Web Push
# ---------------------------------------------------------------------------
@router.post("/suscripcion")
def guardar_suscripcion(
    data: schemas.PushSuscripcionCreate,
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra (o actualiza) la suscripción push de este navegador."""
    endpoint = (data.endpoint or "").strip()
    p256dh = str(data.keys.get("p256dh", "")).strip()
    auth = str(data.keys.get("auth", "")).strip()
    if not endpoint or not p256dh or not auth:
        raise HTTPException(status_code=422, detail="Suscripción push incompleta.")

    fila = (
        db.query(models.PushSuscripcion)
        .filter(models.PushSuscripcion.endpoint == endpoint)
        .first()
    )
    if fila:
        fila.usuario_id = usuario.id
        fila.p256dh = p256dh
        fila.auth = auth
        fila.activa = True
    else:
        db.add(models.PushSuscripcion(
            usuario_id=usuario.id, endpoint=endpoint, p256dh=p256dh, auth=auth, activa=True,
        ))
    db.commit()
    return {"ok": True, "mensaje": "Notificaciones del navegador activadas."}


@router.post("/suscripcion/desactivar")
def desactivar_suscripcion(
    data: dict,
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    endpoint = str(data.get("endpoint", "")).strip()
    if not endpoint:
        raise HTTPException(status_code=422, detail="Falta el endpoint.")
    db.query(models.PushSuscripcion).filter(
        models.PushSuscripcion.endpoint == endpoint,
        models.PushSuscripcion.usuario_id == usuario.id,
    ).delete(synchronize_session=False)
    db.commit()
    return {"ok": True, "mensaje": "Notificaciones del navegador desactivadas."}


# ---------------------------------------------------------------------------
# Prueba manual de los canales
# ---------------------------------------------------------------------------
@router.post("/probar")
def probar(
    data: schemas.NotificacionPruebaCreate,
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea un aviso de prueba e intenta entregarlo por correo y/o push."""
    canal = data.canal if data.canal in ("todos", "correo", "push", "ninguno") else "todos"
    if canal == "ninguno":
        resultado = {"id": None, "correo": {"enviado": False}, "push": 0, "suscripciones": 0}
    else:
        try:
            resultado = servicio.enviar_prueba(db, usuario, canal)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"No se pudo crear el aviso: {exc}") from exc
    return {"ok": True, **resultado}


# ---------------------------------------------------------------------------
# Acciones sobre avisos
# ---------------------------------------------------------------------------
@router.post("/leer-todas")
def leer_todas(
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filas = (
        db.query(models.Notificacion)
        .filter(
            models.Notificacion.usuario_id == usuario.id,
            models.Notificacion.leida.is_(False),
            models.Notificacion.descartada.is_(False),
        )
        .all()
    )
    for n in filas:
        n.leida = True
        n.fecha_lectura = datetime.utcnow()
    db.commit()
    return {"ok": True, "actualizadas": len(filas)}


@router.post("/{notificacion_id}/leer")
def marcar_leida(
    notificacion_id: int,
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(models.Notificacion).get(notificacion_id)
    if not n or n.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    n.leida = True
    n.fecha_lectura = datetime.utcnow()
    db.commit()
    return {"ok": True, "id": n.id, "url": n.url}


@router.delete("/{notificacion_id}", status_code=204)
def descartar(
    notificacion_id: int,
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(models.Notificacion).get(notificacion_id)
    if not n or n.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    n.descartada = True
    n.leida = True
    db.commit()
    return None
