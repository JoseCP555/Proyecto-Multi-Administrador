"""Configuración global y por conjunto del sistema."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.models import Configuracion
from app.database import get_db
from app.deps import require_permiso

router = APIRouter(prefix="/configuracion", tags=["Configuración"], dependencies=[Depends(require_permiso("config.ver"))])

TIPOS_VALIDOS = ("texto", "numero", "booleano", "json")


def _listar(db: Session, categoria: Optional[str] = None):
    q = db.query(Configuracion)
    if categoria:
        q = q.filter(Configuracion.categoria == categoria)
    return q.order_by(Configuracion.categoria, Configuracion.clave, Configuracion.id_conjunto).all()


@router.get("", response_model=list[schemas.ConfigResponse])
def listar(categoria: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return _listar(db, categoria)


@router.put("", response_model=list[schemas.ConfigResponse], dependencies=[Depends(require_permiso("config.editar"))])
def actualizar(items: list[schemas.ConfigSchema], db: Session = Depends(get_db)):
    for item in items:
        conf = (
            db.query(Configuracion)
            .filter(Configuracion.clave == item.clave, Configuracion.id_conjunto == item.id_conjunto)
            .first()
        )
        tipo = item.tipo if item.tipo in TIPOS_VALIDOS else None
        if conf:
            if not conf.editable:
                continue
            conf.valor = item.valor
            if item.descripcion is not None:
                conf.descripcion = item.descripcion
            if item.categoria:
                conf.categoria = item.categoria
            if tipo:
                conf.tipo = tipo
        else:
            # Un valor por conjunto hereda categoría, tipo y descripción del global.
            base = (
                db.query(Configuracion)
                .filter(Configuracion.clave == item.clave, Configuracion.id_conjunto.is_(None))
                .first()
            )
            db.add(Configuracion(
                clave=item.clave, valor=item.valor,
                descripcion=item.descripcion or (base.descripcion if base else None),
                categoria=item.categoria or (base.categoria if base else "general"),
                tipo=tipo or (base.tipo if base else "texto"),
                id_conjunto=item.id_conjunto,
            ))
    db.commit()
    return _listar(db)
