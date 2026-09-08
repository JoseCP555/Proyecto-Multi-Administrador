"""Gestión de propiedades / inmuebles."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.models import Propiedad, Residente
from app.database import get_db
from app.deps import require_permiso

router = APIRouter(prefix="/propiedades", tags=["Propiedades"], dependencies=[Depends(require_permiso("propiedades.ver"))])


def _serializar(p: Propiedad, db: Session) -> dict:
    nombre = None
    if p.residente_id:
        r = db.query(Residente).get(p.residente_id)
        if r and r.usuario_id:
            from app.models import Usuario
            u = db.query(Usuario).get(r.usuario_id)
            nombre = u.nombre if u else None
    return {
        "id": p.id, "residencial": p.residencial, "bloque": p.bloque,
        "torre": p.torre, "apartamento": p.apartamento, "piso": p.piso,
        "area": float(p.area) if p.area is not None else None,
        "habitaciones": p.habitaciones, "banos": p.banos, "parqueaderos": p.parqueaderos,
        "estado": p.estado, "estrato": p.estrato, "residente_id": p.residente_id,
        "residente_nombre": nombre,
    }


@router.get("", response_model=list[schemas.PropiedadResponse])
def listar(estado: str = None, db: Session = Depends(get_db)):
    q = db.query(Propiedad)
    if estado:
        q = q.filter(Propiedad.estado == estado)
    return [_serializar(p, db) for p in q.all()]


@router.post("", response_model=schemas.PropiedadResponse, status_code=201, dependencies=[Depends(require_permiso("propiedades.crear"))])
def crear(data: schemas.PropiedadCreate, db: Session = Depends(get_db)):
    p = Propiedad(
        residencial=data.residencial, bloque=data.bloque, torre=data.torre,
        apartamento=data.apartamento, piso=data.piso, area=data.area,
        habitaciones=data.habitaciones, banos=data.banos, parqueaderos=data.parqueaderos,
        estado=data.estado, estrato=data.estrato, residente_id=data.residente_id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _serializar(p, db)


@router.put("/{propiedad_id}", response_model=schemas.PropiedadResponse, dependencies=[Depends(require_permiso("propiedades.editar"))])
def actualizar(propiedad_id: int, data: schemas.PropiedadCreate, db: Session = Depends(get_db)):
    p = db.query(Propiedad).get(propiedad_id)
    if not p:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada.")
    for campo in ("residencial", "bloque", "torre", "apartamento", "piso", "area",
                  "habitaciones", "banos", "parqueaderos", "estado", "estrato", "residente_id"):
        setattr(p, campo, getattr(data, campo))
    db.commit()
    db.refresh(p)
    return _serializar(p, db)


@router.delete("/{propiedad_id}", status_code=204, dependencies=[Depends(require_permiso("propiedades.eliminar"))])
def eliminar(propiedad_id: int, db: Session = Depends(get_db)):
    p = db.query(Propiedad).get(propiedad_id)
    if not p:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada.")
    db.delete(p)
    db.commit()
    return None
