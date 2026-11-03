"""Gestión de usuarios."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.deps import require_permiso, get_current_user
from app.models import Usuario
from app.permisos import SUPER_ADMIN, tiene_acceso_total
from app.conjunto_ctx import conjunto_activo, filtrar
from app.models import Usuario as ModeloUsuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios"], dependencies=[Depends(require_permiso("usuarios.ver"))])


@router.get("", response_model=list[schemas.UsuarioResponse])
def listar(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    # CA-07.4: en el contexto de un conjunto solo aparecen sus usuarios.
    usuarios = filtrar(crud.listar_usuarios_query(db), ModeloUsuario, cid).all()
    # Compatibilidad: se conserva el orden histórico por id.
    return [crud.serializar_usuario(u, db) for u in sorted(usuarios, key=lambda u: u.id)]


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

    acceso_total = tiene_acceso_total(actual)
    # super_admin y admin (acceso total) pueden tocar cuentas super_admin
    # y asignar ese rol; los demás roles no.
    if not acceso_total and (u.rol_id == SUPER_ADMIN or data.rol_id == SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Solo un administrador con acceso total puede gestionar ese rol.")
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
    if u.rol_id == SUPER_ADMIN and not tiene_acceso_total(actual):
        raise HTTPException(status_code=403, detail="Solo un administrador con acceso total puede eliminar a otro.")
    crud.eliminar_usuario(db, u)
    return None
