"""Gestión de residentes (propietarios e inquilinos)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.models import Residente, Usuario
from app.database import get_db
from app.deps import require_permiso

router = APIRouter(prefix="/residentes", tags=["Residentes"], dependencies=[Depends(require_permiso("residentes.ver"))])


def _serializar(r: Residente, db: Session) -> dict:
    nombre = None
    if r.usuario_id:
        u = db.query(Usuario).get(r.usuario_id)
        nombre = u.nombre if u else None
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
    }


@router.get("", response_model=list[schemas.ResidenteResponse])
def listar(db: Session = Depends(get_db)):
    return [_serializar(r, db) for r in db.query(Residente).all()]


@router.post("", response_model=schemas.ResidenteResponse, status_code=201, dependencies=[Depends(require_permiso("residentes.crear"))])
def crear(data: schemas.ResidenteCreate, db: Session = Depends(get_db)):
    r = Residente(
        usuario_id=data.usuario_id, tipo=data.tipo,
        identificacion=data.identificacion,
        telefono_adicional=data.telefono_adicional,
        contacto_emergencia=data.contacto_emergencia,
        telefono_emergencia=data.telefono_emergencia,
        activo=data.activo,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _serializar(r, db)


@router.put("/{residente_id}", response_model=schemas.ResidenteResponse, dependencies=[Depends(require_permiso("residentes.editar"))])
def actualizar(residente_id: int, data: schemas.ResidenteCreate, db: Session = Depends(get_db)):
    r = db.query(Residente).get(residente_id)
    if not r:
        raise HTTPException(status_code=404, detail="Residente no encontrado.")
    r.tipo = data.tipo
    r.identificacion = data.identificacion
    r.telefono_adicional = data.telefono_adicional
    r.contacto_emergencia = data.contacto_emergencia
    r.telefono_emergencia = data.telefono_emergencia
    r.activo = data.activo
    db.commit()
    db.refresh(r)
    return _serializar(r, db)


@router.delete("/{residente_id}", status_code=204, dependencies=[Depends(require_permiso("residentes.eliminar"))])
def eliminar(residente_id: int, db: Session = Depends(get_db)):
    r = db.query(Residente).get(residente_id)
    if not r:
        raise HTTPException(status_code=404, detail="Residente no encontrado.")
    r.activo = False
    db.commit()
    return None
