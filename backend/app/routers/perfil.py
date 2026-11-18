"""Datos personales del usuario autenticado (UH-20).

El residente puede actualizar su teléfono, correo y foto de perfil; los
cambios quedan guardados al confirmar la actualización. También puede cambiar
su propia contraseña.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.auditoria import registrar_seguro
from app.crud import serializar_usuario
from app.database import get_db
from app.deps import get_current_user, require_permiso
from app.models import Auditoria, Notificacion, Usuario
from app.security import hashear_password, verificar_password

router = APIRouter(prefix="/perfil", tags=["Perfil"])

TAMANO_MAX_FOTO = 2 * 1024 * 1024     # 2 MB


@router.get("", dependencies=[Depends(require_permiso("perfil.ver"))])
def ver_perfil(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    datos = serializar_usuario(usuario, db)
    datos["preferencias"] = {
        "correo": bool(usuario.notificaciones_correo),
        "push": bool(usuario.notificaciones_push),
    }
    datos["ultimo_acceso"] = usuario.ultimo_acceso
    datos["fecha_creacion"] = usuario.fecha_creacion
    return datos


@router.put("", dependencies=[Depends(require_permiso("perfil.editar"))])
def actualizar_perfil(
    data: schemas.PerfilUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Guarda los cambios de nombre, teléfono, correo y foto (UH-20)."""
    if data.correo and data.correo.strip().lower() != usuario.correo:
        nuevo_correo = data.correo.strip().lower()
        existe = db.query(Usuario).filter(
            Usuario.correo == nuevo_correo, Usuario.id != usuario.id
        ).first()
        if existe:
            raise HTTPException(status_code=400, detail="Ese correo ya está registrado por otro usuario.")
        usuario.correo = nuevo_correo

    if data.nombre is not None:
        if not data.nombre.strip():
            raise HTTPException(status_code=400, detail="El nombre no puede quedar vacío.")
        usuario.nombre = data.nombre.strip()
    if data.telefono is not None:
        usuario.telefono = data.telefono.strip()

    if data.foto is not None:
        # Se acepta una imagen como data URI (base64) o una URL http(s).
        foto = data.foto.strip()
        if foto and not (foto.startswith("data:image/") or foto.startswith("http://") or foto.startswith("https://")):
            raise HTTPException(status_code=400, detail="La foto debe ser una imagen (data URI o URL).")
        if len(foto.encode("utf-8")) > TAMANO_MAX_FOTO:
            raise HTTPException(status_code=400, detail="La foto de perfil no puede superar 2 MB.")
        usuario.foto = foto or None

    db.commit()
    db.refresh(usuario)
    registrar_seguro(
        db=db, usuario=usuario, accion="editar", modulo="Perfil",
        entidad="usuario", entidad_id=usuario.id,
        detalle="Actualizó sus datos personales",
    )
    return {"ok": True, "mensaje": "Datos actualizados correctamente.", "usuario": serializar_usuario(usuario, db)}


@router.put("/password", dependencies=[Depends(require_permiso("perfil.editar"))])
def cambiar_password(
    data: schemas.CambioPassword,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cambio de contraseña comprobando la actual."""
    if not verificar_password(data.actual, usuario.contrasena_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta.")
    usuario.contrasena_hash = hashear_password(data.nueva)
    db.commit()
    registrar_seguro(
        db=db, usuario=usuario, accion="editar", modulo="Perfil",
        entidad="usuario", entidad_id=usuario.id, detalle="Cambió su contraseña",
    )
    return {"ok": True, "mensaje": "Contraseña actualizada correctamente."}


@router.get("/actividad", dependencies=[Depends(require_permiso("perfil.ver"))])
def mi_actividad(
    limite: int = 30,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Últimas acciones del propio usuario (transparencia del historial)."""
    limite = max(1, min(limite, 200))
    filas = (
        db.query(Auditoria)
        .filter(Auditoria.usuario_id == usuario.id)
        .order_by(Auditoria.fecha_creacion.desc())
        .limit(limite)
        .all()
    )
    return [
        {
            "id": f.id,
            "accion": f.accion,
            "modulo": f.modulo,
            "detalle": f.detalle or f.ruta,
            "fecha_creacion": f.fecha_creacion,
        }
        for f in filas
    ]
