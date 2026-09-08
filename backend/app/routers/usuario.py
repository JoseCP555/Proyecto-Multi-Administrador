"""Gestión de usuarios."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.deps import require_permiso, get_current_user
from app.models import Usuario
from app.permisos import SUPER_ADMIN

router = APIRouter(prefix="/usuarios", tags=["Usuarios"], dependencies=[Depends(require_permiso("usuarios.ver"))])


@router.get("", response_model=list[schemas.UsuarioResponse])
def listar(db: Session = Depends(get_db)):
    return [crud.serializar_usuario(u, db) for u in crud.listar_usuarios(db)]


@router.get("/{usuario_id}", response_model=schemas.UsuarioResponse)
def detalle(usuario_id: int, db: Session = Depends(get_db)):
    u = crud.obtener_usuario_por_id(db, usuario_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return crud.serializar_usuario(u, db)


@router.put("/{usuario_id}", response_model=schemas.UsuarioResponse)
def actualizar(
    usuario_id: int,
    data: schemas.UsuarioUpdate,
    actual: Usuario = Depends(require_permiso("usuarios.editar")),
    db: Session = Depends(get_db),
):
    u = crud.obtener_usuario_por_id(db, usuario_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    es_super = actual.rol_id == SUPER_ADMIN
    # Solo el super_admin puede tocar cuentas super_admin o asignar ese rol.
    if not es_super and (u.rol_id == SUPER_ADMIN or data.rol_id == SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Solo un super administrador puede gestionar ese rol.")
    # Nadie se cambia su propio rol ni se desactiva a sí mismo.
    if u.id == actual.id:
        if data.rol_id is not None and data.rol_id != u.rol_id:
            raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol.")
        if data.activo is False:
            raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta.")

    u = crud.actualizar_usuario(db, u, data)
    return crud.serializar_usuario(u, db)


@router.delete("/{usuario_id}", status_code=204)
def eliminar(
    usuario_id: int,
    actual: Usuario = Depends(require_permiso("usuarios.eliminar")),
    db: Session = Depends(get_db),
):
    u = crud.obtener_usuario_por_id(db, usuario_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if u.id == actual.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta.")
    if u.rol_id == SUPER_ADMIN and actual.rol_id != SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Solo un super administrador puede eliminar a otro.")
    crud.eliminar_usuario(db, u)
    return None
