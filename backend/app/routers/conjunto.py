"""Gestión de conjuntos / copropiedades (multi- administración).

Endpoints usados por el "Panel Multi-Administrador" y por el selector
"Cambiar conjunto" del dashboard (HU-07).

Nada de esto reemplaza comportamiento existente: solo añade rutas nuevas.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.colores import normalizar_color, sugerir_color
from app.database import get_db
from app.deps import require_permiso, get_current_user, usuario_tiene_permiso
from app.conjunto_ctx import (
    conjuntos_del_usuario, ids_conjuntos_usuario, ve_todos_los_conjuntos,
)
from app.models import (
    Conjunto, Usuario, UsuarioConjunto, Propiedad, Residente,
    MovimientoFinanciero, ConceptoFinanciero,
)
from app.redis_client import cache_del

router = APIRouter(prefix="/conjuntos", tags=["Conjuntos"])

_VER = [Depends(require_permiso("conjuntos.ver"))]
_CREAR = [Depends(require_permiso("conjuntos.crear"))]
_EDITAR = [Depends(require_permiso("conjuntos.editar"))]
_ELIMINAR = [Depends(require_permiso("conjuntos.eliminar"))]


# ---------------------------------------------------------------------------
# Listado público (sin sesión)
# ---------------------------------------------------------------------------
@router.get(
    "/publicos",
    response_model=list[schemas.ConjuntoSimple],
    summary="Conjuntos activos (público)",
)
def listar_publicos(db: Session = Depends(get_db)):
    """Conjuntos activos con solo id y nombre (sin datos sensibles).

    Lo consume la pantalla de registro para que un residente elija el
    conjunto al que pertenece. No requiere sesión ni permisos.
    """
    filas = (
        db.query(Conjunto.id, Conjunto.nombre)
        .filter(Conjunto.activo.is_(True))
        .order_by(Conjunto.nombre)
        .all()
    )
    return [{"id": fila[0], "nombre": fila[1]} for fila in filas]


# ---------------------------------------------------------------------------
# Serialización
# ---------------------------------------------------------------------------
def _metricas(db: Session, conjunto_ids: list[int]) -> dict[int, dict]:
    """Propiedades, residentes y saldo por conjunto (una sola pasada)."""
    if not conjunto_ids:
        return {}

    props = dict(
        db.query(Propiedad.id_conjunto, func.count(Propiedad.id))
        .filter(Propiedad.id_conjunto.in_(conjunto_ids))
        .group_by(Propiedad.id_conjunto)
        .all()
    )
    resis = dict(
        db.query(Residente.id_conjunto, func.count(Residente.id))
        .filter(Residente.id_conjunto.in_(conjunto_ids), Residente.activo.is_(True))
        .group_by(Residente.id_conjunto)
        .all()
    )

    saldo: dict[int, float] = {cid: 0.0 for cid in conjunto_ids}
    conceptos = {c.id: c.tipo for c in db.query(ConceptoFinanciero).all()}
    movs = (
        db.query(
            MovimientoFinanciero.id_conjunto,
            MovimientoFinanciero.concepto_id,
            MovimientoFinanciero.monto,
            MovimientoFinanciero.estado,
        )
        .filter(MovimientoFinanciero.id_conjunto.in_(conjunto_ids))
        .all()
    )
    for cid, concepto_id, monto, estado in movs:
        if cid is None or estado != "pagado" or monto is None:
            continue
        valor = float(monto)
        saldo[cid] = saldo.get(cid, 0.0) + (valor if conceptos.get(concepto_id) == "ingreso" else -valor)

    return {
        cid: {
            "propiedades": props.get(cid, 0),
            "residentes": resis.get(cid, 0),
            "saldo": round(saldo.get(cid, 0.0), 2),
        }
        for cid in conjunto_ids
    }


def serializar(db: Session, c: Conjunto, metricas: dict | None = None) -> dict:
    m = (metricas or {}).get(c.id, {})
    return {
        "id": c.id,
        "nombre": c.nombre,
        "nit": c.nit,
        "direccion": c.direccion,
        "ciudad": c.ciudad,
        "telefono": c.telefono,
        "correo": c.correo,
        "administrador": c.administrador,
        "habitantes": c.habitantes or 0,
        "cuota": float(c.cuota) if c.cuota is not None else 0.0,
        "dia_cobro": c.dia_cobro,
        "reunion": c.reunion,
        "silencio": c.silencio,
        "logo": c.logo,
        "color": c.color,
        "activo": bool(c.activo),
        "fecha_creacion": c.fecha_creacion,
        "propiedades": m.get("propiedades", 0),
        "residentes": m.get("residentes", 0),
        "saldo": m.get("saldo", 0.0),
    }


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------
@router.get("", response_model=list[schemas.ConjuntoResponse], dependencies=_VER)
def listar(
    todos: bool = Query(False, description="Solo super_admin: incluye conjuntos inactivos."),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Conjuntos a cargo del usuario autenticado (CA-07.1 / CA-07.7)."""
    if todos and ve_todos_los_conjuntos(db, usuario):
        conjuntos = db.query(Conjunto).order_by(Conjunto.id).all()
    else:
        conjuntos = conjuntos_del_usuario(db, usuario)
    metricas = _metricas(db, [c.id for c in conjuntos])
    return [serializar(db, c, metricas) for c in conjuntos]


@router.get("/{conjunto_id}", response_model=schemas.ConjuntoResponse, dependencies=_VER)
def detalle(conjunto_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    c = db.query(Conjunto).get(conjunto_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conjunto no encontrado.")
    if c.id not in ids_conjuntos_usuario(db, usuario):
        raise HTTPException(status_code=403, detail="No tienes acceso a ese conjunto.")
    return serializar(db, c, _metricas(db, [c.id]))


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------
@router.post("", response_model=schemas.ConjuntoResponse, status_code=201, dependencies=_CREAR)
def crear(data: schemas.ConjuntoCreate, db: Session = Depends(get_db)):
    existe = db.query(Conjunto).filter(Conjunto.nombre == data.nombre.strip()).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un conjunto con ese nombre.")
    c = Conjunto(
        nombre=data.nombre.strip(),
        nit=data.nit,
        direccion=data.direccion,
        ciudad=data.ciudad,
        telefono=data.telefono,
        correo=data.correo,
        administrador=data.administrador,
        habitantes=data.habitantes or 0,
        cuota=data.cuota or 0,
        dia_cobro=data.dia_cobro,
        reunion=data.reunion,
        silencio=data.silencio,
        # "" (sin logo) se normaliza a NULL para que el frontend lo trate igual.
        logo=(data.logo or None),
        # Si no eligió color se le asigna el siguiente de la paleta, así el
        # conjunto recién creado mantiene un color propio y estable.
        color=normalizar_color(data.color) or sugerir_color(
            db.query(Conjunto).count()
        ),
        activo=True if data.activo is None else data.activo,
        fecha_creacion=datetime.utcnow(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    notif.notificar_seguro(
        db=db, id_conjunto=c.id, tipo="conjunto",
        titulo="Nuevo conjunto creado",
        mensaje=f"Se añadió «{c.nombre}» al panel multi-administrador.",
        clave=f"creado:{c.id}",
    )
    cache_del("dashboard_stats")
    return serializar(db, c, _metricas(db, [c.id]))


@router.put("/{conjunto_id}", response_model=schemas.ConjuntoResponse, dependencies=_EDITAR)
def actualizar(
    conjunto_id: int,
    data: schemas.ConjuntoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    c = db.query(Conjunto).get(conjunto_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conjunto no encontrado.")
    if c.id not in ids_conjuntos_usuario(db, usuario):
        raise HTTPException(status_code=403, detail="No tienes acceso a ese conjunto.")

    # `color` se trata aparte: enviar "" significa "volver al automático"
    # (NULL), y el validador de Pydantic ya lo convierte en None. Usar
    # model_fields_set permite distinguir "no enviado" de "borrar".
    if "color" in getattr(data, "model_fields_set", set()):
        c.color = normalizar_color(data.color)

    for campo in ("nombre", "nit", "direccion", "ciudad", "telefono", "correo",
                  "administrador", "habitantes", "cuota", "dia_cobro",
                  "reunion", "silencio", "logo", "activo"):
        valor = getattr(data, campo, None)
        # El frontend envía "" cuando el usuario quitó el logo; en ese caso
        # hay que borrarlo en vez de ignorarlo como un campo no enviado.
        if campo == "logo" and valor == "":
            valor = None
            setattr(c, campo, None)
            continue
        if valor is not None:
            if campo == "nombre":
                valor = valor.strip()
                duplicado = (
                    db.query(Conjunto)
                    .filter(Conjunto.nombre == valor, Conjunto.id != c.id)
                    .first()
                )
                if duplicado:
                    raise HTTPException(status_code=400, detail="Ya existe un conjunto con ese nombre.")
            setattr(c, campo, valor)
    db.commit()
    db.refresh(c)
    cache_del("dashboard_stats")
    return serializar(db, c, _metricas(db, [c.id]))


@router.delete("/{conjunto_id}", status_code=200, dependencies=_ELIMINAR)
def eliminar(
    conjunto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Desactiva el conjunto (borrado lógico) para no perder su historial.

    Si el conjunto no tiene datos asociados se elimina físicamente.
    """
    c = db.query(Conjunto).get(conjunto_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conjunto no encontrado.")
    if c.id not in ids_conjuntos_usuario(db, usuario):
        raise HTTPException(status_code=403, detail="No tienes acceso a ese conjunto.")

    metricas = _metricas(db, [c.id]).get(c.id, {})
    if (metricas.get("propiedades") or 0) or (metricas.get("residentes") or 0):
        c.activo = False
        db.commit()
        cache_del("dashboard_stats")
        return {"ok": True, "mensaje": f"'{c.nombre}' se desactivó (tiene datos asociados)."}

    db.query(UsuarioConjunto).filter(UsuarioConjunto.conjunto_id == c.id).delete(
        synchronize_session=False
    )
    db.delete(c)
    db.commit()
    cache_del("dashboard_stats")
    return {"ok": True, "mensaje": f"'{c.nombre}' se eliminó correctamente."}


# ---------------------------------------------------------------------------
# Asignación de usuarios a conjuntos
# ---------------------------------------------------------------------------
@router.get("/{conjunto_id}/usuarios", dependencies=_VER)
def usuarios_del_conjunto(
    conjunto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Usuarios asignados a un conjunto (incluye al super_admin si no hay filas)."""
    if conjunto_id not in ids_conjuntos_usuario(db, usuario):
        raise HTTPException(status_code=403, detail="No tienes acceso a ese conjunto.")
    filas = (
        db.query(Usuario)
        .join(UsuarioConjunto, UsuarioConjunto.usuario_id == Usuario.id)
        .filter(UsuarioConjunto.conjunto_id == conjunto_id)
        .all()
    )
    return [
        {"id": u.id, "nombre": u.nombre, "correo": u.correo, "rol_id": u.rol_id}
        for u in filas
    ]


@router.post("/{conjunto_id}/usuarios/{usuario_id}", dependencies=_EDITAR)
def asignar_usuario(
    conjunto_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    """Asigna un usuario a un conjunto (idempotente)."""
    c = db.query(Conjunto).get(conjunto_id)
    u = db.query(Usuario).get(usuario_id)
    if not c or not u:
        raise HTTPException(status_code=404, detail="Conjunto o usuario no encontrado.")
    if c.id not in ids_conjuntos_usuario(db, actual):
        raise HTTPException(status_code=403, detail="No tienes acceso a ese conjunto.")
    if not usuario_tiene_permiso(db, actual, "usuarios.editar"):
        raise HTTPException(status_code=403, detail="No tienes permiso para asignar usuarios.")

    existe = (
        db.query(UsuarioConjunto)
        .filter(UsuarioConjunto.usuario_id == usuario_id, UsuarioConjunto.conjunto_id == conjunto_id)
        .first()
    )
    if not existe:
        db.add(UsuarioConjunto(usuario_id=usuario_id, conjunto_id=conjunto_id))
        db.commit()
    return {"ok": True, "mensaje": f"{u.nombre} ahora pertenece a {c.nombre}."}


@router.delete("/{conjunto_id}/usuarios/{usuario_id}", dependencies=_EDITAR)
def quitar_usuario(
    conjunto_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    c = db.query(Conjunto).get(conjunto_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conjunto no encontrado.")
    if c.id not in ids_conjuntos_usuario(db, actual):
        raise HTTPException(status_code=403, detail="No tienes acceso a ese conjunto.")
    if not usuario_tiene_permiso(db, actual, "usuarios.editar"):
        raise HTTPException(status_code=403, detail="No tienes permiso para reasignar usuarios.")
    db.query(UsuarioConjunto).filter(
        UsuarioConjunto.usuario_id == usuario_id,
        UsuarioConjunto.conjunto_id == conjunto_id,
    ).delete(synchronize_session=False)
    db.commit()
    return {"ok": True, "mensaje": "Usuario retirado del conjunto."}
