"""Configuración global del sistema."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.models import Configuracion
from app.database import get_db
from app.deps import require_permiso

router = APIRouter(prefix="/configuracion", tags=["Configuración"], dependencies=[Depends(require_permiso("config.ver"))])


@router.get("", response_model=list[schemas.ConfigResponse])
def listar(db: Session = Depends(get_db)):
    return db.query(Configuracion).all()


@router.put("", response_model=list[schemas.ConfigResponse], dependencies=[Depends(require_permiso("config.editar"))])
def actualizar(items: list[schemas.ConfigSchema], db: Session = Depends(get_db)):
    for item in items:
        conf = db.query(Configuracion).filter(Configuracion.clave == item.clave).first()
        if conf:
            conf.valor = item.valor
        else:
            db.add(Configuracion(clave=item.clave, valor=item.valor, descripcion=item.descripcion))
    db.commit()
    return db.query(Configuracion).all()
