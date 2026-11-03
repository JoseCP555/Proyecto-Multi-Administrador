"""Contexto de conjunto (multi-copropiedad).

Implementa la HU-07: un mismo usuario puede administrar varios conjuntos y
cambiar de uno a otro **sin cerrar sesión**.

Reglas
------
* El super administrador (o quien tenga el permiso `conjuntos.gestionar`)
  ve TODOS los conjuntos activos.
* Cualquier otro rol ve únicamente los conjuntos asignados en la tabla
  `usuario_conjuntos` (o, si no tiene filas, el de `usuarios.id_conjunto` /
  `usuarios.id_copropiedad`).
* El frontend envía el conjunto activo en la cabecera `X-Conjunto-Id`.
  Si el id no pertenece al usuario → HTTP 403 (CA-07.7).
* Si no llega la cabecera: el super administrador conserva el comportamiento
  histórico (sin filtro, ve todo) y el resto trabaja sobre su único conjunto.

Todo es aditivo: si no hay conjuntos en la base, `conjunto_activo` devuelve
`None` y los endpoints se comportan exactamente como antes.
"""
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, usuario_tiene_permiso
from app.permisos import tiene_acceso_total
from app.models import (
    Usuario, Conjunto, UsuarioConjunto,
    Propiedad, Residente, MovimientoFinanciero,
    TareaMantenimiento, Documento, Evento, SesionChat,
)

CABECERA = "X-Conjunto-Id"


# ---------------------------------------------------------------------------
# Consultas base
# ---------------------------------------------------------------------------
def ve_todos_los_conjuntos(db: Session, usuario: Usuario) -> bool:
    """¿El usuario puede ver/gestionar todos los conjuntos del sistema?"""
    # super_admin y admin ven/gestionan TODOS los conjuntos, igual que antes
    # lo hacía solo el super_admin.
    return tiene_acceso_total(usuario) or usuario_tiene_permiso(db, usuario, "conjuntos.gestionar")


def conjuntos_del_usuario(db: Session, usuario: Usuario) -> list[Conjunto]:
    """Conjuntos a los que tiene acceso el usuario (siempre activos)."""
    if ve_todos_los_conjuntos(db, usuario):
        todos = db.query(Conjunto).filter(Conjunto.activo.is_(True)).order_by(Conjunto.id).all()
        if todos:
            return todos

    ids = [
        fila[0]
        for fila in db.query(UsuarioConjunto.conjunto_id)
        .filter(UsuarioConjunto.usuario_id == usuario.id)
        .all()
    ]
    if not ids:
        propio = getattr(usuario, "id_conjunto", None) or getattr(usuario, "id_copropiedad", None)
        if propio:
            ids = [propio]
    if not ids:
        # Sin asignaciones: se cae al conjunto por defecto para no dejar la
        # pantalla vacía (primer conjunto activo del sistema).
        defecto = db.query(Conjunto).filter(Conjunto.activo.is_(True)).order_by(Conjunto.id).first()
        return [defecto] if defecto else []

    return (
        db.query(Conjunto)
        .filter(Conjunto.id.in_(ids), Conjunto.activo.is_(True))
        .order_by(Conjunto.id)
        .all()
    )


def ids_conjuntos_usuario(db: Session, usuario: Usuario) -> set[int]:
    return {c.id for c in conjuntos_del_usuario(db, usuario)}


def conjunto_por_defecto(db: Session, usuario: Usuario) -> Optional[int]:
    """Id del conjunto que se usa cuando el frontend no manda la cabecera."""
    permitidos = sorted(ids_conjuntos_usuario(db, usuario))
    if not permitidos:
        return None
    propio = getattr(usuario, "id_conjunto", None) or getattr(usuario, "id_copropiedad", None)
    if propio in permitidos:
        return propio
    return permitidos[0]


# ---------------------------------------------------------------------------
# Dependencia FastAPI
# ---------------------------------------------------------------------------
def conjunto_activo(
    x_conjunto_id: Optional[str] = Header(None, alias=CABECERA),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[int]:
    """Devuelve el `id_conjunto` que debe filtrar la consulta (o None = todos)."""
    permitidos = ids_conjuntos_usuario(db, usuario)

    if x_conjunto_id is not None and str(x_conjunto_id).strip() != "":
        try:
            valor = int(x_conjunto_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Cabecera X-Conjunto-Id inválida.")
        if valor not in permitidos:
            raise HTTPException(
                status_code=403,
                detail="No tienes acceso a ese conjunto (no está a tu cargo).",
            )
        return valor

    # Sin cabecera: el super admin mantiene la vista global histórica; el
    # resto trabaja sobre su conjunto.
    if ve_todos_los_conjuntos(db, usuario):
        return None
    return conjunto_por_defecto(db, usuario)


# ---------------------------------------------------------------------------
# Helpers de filtrado / asignación
# ---------------------------------------------------------------------------
def filtrar(consulta, modelo, id_conjunto: Optional[int]):
    """Aplica el filtro por conjunto si el modelo tiene la columna."""
    if id_conjunto is None:
        return consulta
    columna = getattr(modelo, "id_conjunto", None)
    if columna is None:
        return consulta
    return consulta.filter(columna == id_conjunto)


def asignar(objeto, id_conjunto: Optional[int]):
    """Asigna el conjunto a un registro nuevo (si el modelo lo soporta)."""
    if id_conjunto is not None and hasattr(objeto, "id_conjunto"):
        if getattr(objeto, "id_conjunto", None) is None:
            objeto.id_conjunto = id_conjunto
    return objeto


__all__ = [
    "CABECERA", "conjunto_activo", "conjuntos_del_usuario", "ids_conjuntos_usuario",
    "conjunto_por_defecto", "ve_todos_los_conjuntos", "filtrar", "asignar",
    "Propiedad", "Residente", "MovimientoFinanciero", "TareaMantenimiento",
    "Documento", "Evento", "SesionChat",
]
