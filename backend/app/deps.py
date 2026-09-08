"""Dependencias de autenticación y autorización para los endpoints protegidos."""
from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_jwt import verificar_token
from app.database import get_db
from app.models import Usuario, Rol, Permiso, RolPermiso
from app.redis_client import token_revocado


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> Usuario:
    """Extrae y valida el token JWT; rechaza si está revocado en Redis."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado.")

    token = authorization.split(" ", 1)[1].strip()
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    # Sesión cerrada previamente (revocada vía Redis).
    if token_revocado(token):
        raise HTTPException(status_code=401, detail="Sesión cerrada. Inicia sesión de nuevo.")

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Token sin sujeto.")

    usuario = db.query(Usuario).get(int(sub))
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no válido.")

    return usuario


def get_rol_nombre(db: Session, rol_id: int) -> str:
    rol = db.query(Rol).get(rol_id)
    return rol.nombre if rol else "sin_rol"


def usuario_tiene_permiso(db: Session, usuario: Usuario, codigo: str) -> bool:
    """¿El rol del usuario tiene el permiso `codigo`? (consulta rol_permisos)."""
    return (
        db.query(RolPermiso)
        .join(Permiso, Permiso.id == RolPermiso.permiso_id)
        .filter(RolPermiso.rol_id == usuario.rol_id, Permiso.codigo == codigo)
        .first()
        is not None
    )


def require_permiso(codigo: str):
    """Dependencia de autorización: exige que el rol del usuario autenticado
    tenga el permiso `codigo` (tabla rol_permisos). Devuelve 403 si no."""
    def _dependencia(
        usuario: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Usuario:
        if not usuario_tiene_permiso(db, usuario, codigo):
            raise HTTPException(
                status_code=403,
                detail=f"El rol '{get_rol_nombre(db, usuario.rol_id)}' no tiene el permiso '{codigo}'.",
            )
        return usuario

    return _dependencia


def require_alguno(*codigos: str):
    """Autoriza si el rol tiene AL MENOS UNO de los permisos indicados."""
    def _dependencia(
        usuario: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Usuario:
        if not any(usuario_tiene_permiso(db, usuario, c) for c in codigos):
            raise HTTPException(
                status_code=403,
                detail=f"El rol '{get_rol_nombre(db, usuario.rol_id)}' no tiene permiso para esta acción.",
            )
        return usuario

    return _dependencia
