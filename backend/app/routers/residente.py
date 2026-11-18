"""Gestión de residentes (propietarios e inquilinos) — UH-02.

Permite registrar, editar y eliminar cuentas de residentes con nombre,
apartamento, correo y rol desde un único flujo, manteniendo total
compatibilidad con las llamadas clásicas que solo envían ficha de residente.
"""
from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import schemas
from app import notificaciones_servicio as notif
from app.auditoria import registrar_seguro
from app.conjunto_ctx import conjunto_activo, filtrar
from app.database import get_db
from app.deps import get_current_user, require_permiso
from app.models import Conjunto, Propiedad, Residente, Rol, Usuario, UsuarioConjunto
from app.permisos import RESIDENTE, SUPER_ADMIN, tiene_acceso_total
from app.redis_client import cache_del, cache_del_prefix
from app.security import hashear_password

router = APIRouter(
    prefix="/residentes",
    tags=["Residentes"],
    dependencies=[Depends(require_permiso("residentes.ver"))],
)


def _serializar(r: Residente, db: Session) -> dict:
    nombre = None
    correo = None
    rol_id = None
    nombre_rol = None
    if r.usuario_id:
        u = db.query(Usuario).get(r.usuario_id)
        if u:
            nombre = u.nombre
            correo = u.correo
            rol_id = u.rol_id
            rol = db.query(Rol).get(u.rol_id) if u.rol_id else None
            nombre_rol = rol.nombre if rol else None

    prop_q = db.query(Propiedad).filter(Propiedad.residente_id == r.id)
    if r.id_conjunto is not None:
        prop_q = prop_q.filter(Propiedad.id_conjunto == r.id_conjunto)
    prop = prop_q.first() or db.query(Propiedad).filter(Propiedad.residente_id == r.id).first()

    return {
        "id": r.id,
        "usuario_id": r.usuario_id,
        "tipo": r.tipo,
        "identificacion": r.identificacion,
        "telefono_adicional": r.telefono_adicional,
        "contacto_emergencia": r.contacto_emergencia,
        "telefono_emergencia": r.telefono_emergencia,
        "activo": r.activo,
        "nombre": nombre,
        "correo": correo,
        "rol_id": rol_id,
        "nombre_rol": nombre_rol,
        "apartamento": prop.apartamento if prop else None,
        "propiedad_id": prop.id if prop else None,
    }


def _vincular_usuario_conjunto(db: Session, usuario_id: int, cid: int | None) -> None:
    if cid is None:
        return
    existe = (
        db.query(UsuarioConjunto)
        .filter(UsuarioConjunto.usuario_id == usuario_id, UsuarioConjunto.conjunto_id == cid)
        .first()
    )
    if not existe:
        db.add(UsuarioConjunto(usuario_id=usuario_id, conjunto_id=cid))


def _vincular_apartamento(
    db: Session,
    r: Residente,
    cid: int | None,
    propiedad_id: int | None,
    apartamento: str | None,
) -> None:
    """Asocia al residente con una propiedad existente o crea el apartamento si no existe."""
    apt = (apartamento or "").strip()
    if propiedad_id is None and not apt:
        return

    objetivo: Propiedad | None = None
    if propiedad_id is not None:
        objetivo = db.query(Propiedad).get(propiedad_id)
        if not objetivo or (cid is not None and objetivo.id_conjunto not in (None, cid)):
            raise HTTPException(status_code=404, detail="Propiedad/apartamento no encontrado en este conjunto.")
    elif apt:
        q = filtrar(db.query(Propiedad), Propiedad, cid)
        objetivo = q.filter(func.lower(Propiedad.apartamento) == apt.lower()).first()
        if not objetivo:
            conjunto = db.query(Conjunto).get(cid) if cid else None
            objetivo = Propiedad(
                residencial=conjunto.nombre if conjunto else "Conjunto Residencial",
                apartamento=apt,
                estado="ocupado",
                residente_id=r.id,
                id_conjunto=cid,
            )
            db.add(objetivo)
            db.flush()

    if objetivo is not None:
        # Si el residente tenía otra unidad asignada en este conjunto, la liberamos al reasignar.
        anteriores = db.query(Propiedad).filter(
            Propiedad.residente_id == r.id,
            Propiedad.id != objetivo.id,
        )
        if cid is not None:
            anteriores = anteriores.filter(Propiedad.id_conjunto == cid)
        for ant in anteriores.all():
            ant.residente_id = None
        objetivo.residente_id = r.id
        if objetivo.estado == "disponible":
            objetivo.estado = "ocupado"


def _validar_rol_asignable(db: Session, rol_id: int, actual: Usuario) -> int:
    rol = db.query(Rol).get(rol_id)
    if not rol:
        raise HTTPException(status_code=400, detail="El rol seleccionado no existe.")
    if rol_id == SUPER_ADMIN and not tiene_acceso_total(actual):
        raise HTTPException(status_code=403, detail="Solo un administrador con acceso total puede asignar ese rol.")
    return rol_id


@router.get("", response_model=list[schemas.ResidenteResponse])
def listar(db: Session = Depends(get_db), cid: int = Depends(conjunto_activo)):
    q = filtrar(db.query(Residente), Residente, cid)
    return [_serializar(r, db) for r in q.order_by(Residente.id.desc()).all()]


@router.post(
    "",
    response_model=schemas.ResidenteResponse,
    status_code=201,
    dependencies=[Depends(require_permiso("residentes.crear"))],
)
def crear(
    data: schemas.ResidenteCreate,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
    actual: Usuario = Depends(get_current_user),
):
    """Registra un residente.

    Si se envían `nombre` y `correo` (UH-02), crea automáticamente su cuenta
    de usuario verificada con el `rol_id` indicado (residente por defecto), lo
    vincula al conjunto activo y asocia su `apartamento`.
    """
    usuario_id = data.usuario_id

    if usuario_id is None and data.correo:
        correo_limpio = str(data.correo).strip().lower()
        existe = db.query(Usuario).filter(func.lower(Usuario.correo) == correo_limpio).first()
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe un usuario registrado con ese correo.")

        nombre_limpio = (data.nombre or "").strip()
        if not nombre_limpio:
            raise HTTPException(status_code=400, detail="El nombre del residente es obligatorio.")

        rol_id = _validar_rol_asignable(db, data.rol_id or RESIDENTE, actual)
        if data.contrasena is not None and data.contrasena != "":
            if len(data.contrasena) < 8:
                raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres.")
            clave_plana = data.contrasena
        else:
            clave_plana = f"Ma{secrets.token_urlsafe(9)}!"

        u = Usuario(
            nombre=nombre_limpio,
            telefono=(data.telefono_adicional or "").strip(),
            correo=correo_limpio,
            contrasena_hash=hashear_password(clave_plana),
            rol_id=rol_id,
            activo=bool(data.activo),
            fecha_creacion=datetime.utcnow(),
            id_conjunto=cid,
            correo_verificado=True,
        )
        db.add(u)
        db.flush()
        _vincular_usuario_conjunto(db, u.id, cid)
        usuario_id = u.id
    elif usuario_id is not None:
        _vincular_usuario_conjunto(db, usuario_id, cid)

    identificacion = (data.identificacion or "").strip()
    if not identificacion:
        identificacion = f"RES-{secrets.token_hex(3).upper()}"

    r = Residente(
        usuario_id=usuario_id,
        tipo=data.tipo,
        id_conjunto=cid,
        identificacion=identificacion,
        telefono_adicional=data.telefono_adicional,
        contacto_emergencia=data.contacto_emergencia,
        telefono_emergencia=data.telefono_emergencia,
        activo=data.activo,
    )
    db.add(r)
    db.flush()

    _vincular_apartamento(db, r, cid, data.propiedad_id, data.apartamento)

    db.commit()
    db.refresh(r)

    etiqueta = (data.nombre or "").strip() or r.identificacion
    notif.notificar_seguro(
        db=db,
        id_conjunto=cid,
        tipo="residente",
        autor_id=actual.id,
        titulo="Nuevo residente registrado",
        mensaje=f"Se registró el residente {etiqueta}"
                + (f" (Apto {data.apartamento.strip()})" if data.apartamento and data.apartamento.strip() else f" (ID {r.identificacion})")
                + ".",
        clave=f"creado:{r.id}",
    )
    registrar_seguro(
        db=db,
        usuario=actual,
        accion="crear",
        modulo="Residentes",
        entidad="residente",
        entidad_id=r.id,
        id_conjunto=cid,
        detalle=f"Registró al residente {etiqueta}",
    )
    cache_del("dashboard_stats")
    cache_del_prefix("dashboard_stats:")
    return _serializar(r, db)


@router.put(
    "/{residente_id}",
    response_model=schemas.ResidenteResponse,
    dependencies=[Depends(require_permiso("residentes.editar"))],
)
def actualizar(
    residente_id: int,
    data: schemas.ResidenteCreate,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
    actual: Usuario = Depends(get_current_user),
):
    r = db.query(Residente).get(residente_id)
    if not r or (cid is not None and r.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Residente no encontrado.")

    r.tipo = data.tipo
    if data.identificacion is not None and data.identificacion.strip():
        r.identificacion = data.identificacion.strip()
    r.telefono_adicional = data.telefono_adicional
    r.contacto_emergencia = data.contacto_emergencia
    r.telefono_emergencia = data.telefono_emergencia
    r.activo = data.activo

    # Actualizar cuenta de usuario vinculada (o crearla si el residente no tenía cuenta y se aporta correo).
    u = db.query(Usuario).get(r.usuario_id) if r.usuario_id else None
    if u is None and data.correo and data.nombre:
        correo_limpio = str(data.correo).strip().lower()
        duplicado = db.query(Usuario).filter(func.lower(Usuario.correo) == correo_limpio).first()
        if duplicado:
            raise HTTPException(status_code=400, detail="Ya existe un usuario registrado con ese correo.")
        rol_id = _validar_rol_asignable(db, data.rol_id or RESIDENTE, actual)
        clave_plana = (
            data.contrasena
            if data.contrasena and len(data.contrasena) >= 8
            else f"Ma{secrets.token_urlsafe(9)}!"
        )
        u = Usuario(
            nombre=data.nombre.strip(),
            telefono=(data.telefono_adicional or "").strip(),
            correo=correo_limpio,
            contrasena_hash=hashear_password(clave_plana),
            rol_id=rol_id,
            activo=bool(data.activo),
            fecha_creacion=datetime.utcnow(),
            id_conjunto=cid,
            correo_verificado=True,
        )
        db.add(u)
        db.flush()
        r.usuario_id = u.id
        _vincular_usuario_conjunto(db, u.id, cid)
    elif u is not None:
        if data.nombre is not None and data.nombre.strip():
            u.nombre = data.nombre.strip()
        if data.correo is not None:
            correo_limpio = str(data.correo).strip().lower()
            if correo_limpio != (u.correo or "").lower():
                duplicado = (
                    db.query(Usuario)
                    .filter(func.lower(Usuario.correo) == correo_limpio, Usuario.id != u.id)
                    .first()
                )
                if duplicado:
                    raise HTTPException(status_code=400, detail="Ya existe un usuario registrado con ese correo.")
                u.correo = correo_limpio
        if data.rol_id is not None and data.rol_id != u.rol_id:
            if u.id == actual.id:
                raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol.")
            if not tiene_acceso_total(actual) and u.rol_id == SUPER_ADMIN:
                raise HTTPException(status_code=403, detail="Solo un administrador con acceso total puede gestionar ese rol.")
            u.rol_id = _validar_rol_asignable(db, data.rol_id, actual)
        if data.telefono_adicional is not None:
            u.telefono = data.telefono_adicional.strip()
        if u.id != actual.id:
            u.activo = bool(data.activo)
        _vincular_usuario_conjunto(db, u.id, cid)

    _vincular_apartamento(db, r, cid, data.propiedad_id, data.apartamento)

    db.commit()
    db.refresh(r)
    registrar_seguro(
        db=db,
        usuario=actual,
        accion="editar",
        modulo="Residentes",
        entidad="residente",
        entidad_id=r.id,
        id_conjunto=cid,
        detalle=f"Actualizó al residente {r.identificacion}",
    )
    cache_del("dashboard_stats")
    cache_del_prefix("dashboard_stats:")
    return _serializar(r, db)


@router.delete(
    "/{residente_id}",
    status_code=204,
    dependencies=[Depends(require_permiso("residentes.eliminar"))],
)
def eliminar(
    residente_id: int,
    db: Session = Depends(get_db),
    cid: int = Depends(conjunto_activo),
    actual: Usuario = Depends(get_current_user),
):
    r = db.query(Residente).get(residente_id)
    if not r or (cid is not None and r.id_conjunto not in (None, cid)):
        raise HTTPException(status_code=404, detail="Residente no encontrado.")
    r.activo = False
    db.commit()
    registrar_seguro(
        db=db,
        usuario=actual,
        accion="eliminar",
        modulo="Residentes",
        entidad="residente",
        entidad_id=residente_id,
        id_conjunto=cid,
        detalle=f"Desactivó al residente {r.identificacion}",
    )
    cache_del("dashboard_stats")
    cache_del_prefix("dashboard_stats:")
    return None
