from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from pydantic import BaseModel
 
from database import Base, SessionLocal
 
router = APIRouter(prefix="/propiedades", tags=["Propiedades"])
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        


# modelo (tabla nueva, no existía antes)


class Propiedad(Base):
    __tablename__ = "propiedades"
 
    id = Column(Integer, primary_key=True, index=True)
    identificador = Column(String, nullable=False)   
    tipo = Column(String, nullable=False)             
    copropiedad = Column(String, nullable=False)       
    direccion = Column(String, nullable=True)
    propietario = Column(String, nullable=True)       
    estado = Column(String, nullable=True)       
    
    
    
    # ESQUEMAS

 
class PropiedadCreate(BaseModel):
    identificador: str
    tipo: str
    copropiedad: str
    direccion: str | None = None
    propietario: str | None = None
    estado: str | None = None
 
 
class PropiedadUpdate(BaseModel):
    identificador: str | None = None
    tipo: str | None = None
    copropiedad: str | None = None
    direccion: str | None = None
    propietario: str | None = None
    estado: str | None = None
 
 
class PropiedadResponse(BaseModel):
    id: int
    identificador: str
    tipo: str
    copropiedad: str
    direccion: str | None = None
    propietario: str | None = None
    estado: str | None = None
 
    class Config:
        from_attributes = True
 
 

# RUTAS

 
@router.get("", response_model=list[PropiedadResponse])
def listar_propiedades(
    copropiedad: str | None = None,
    tipo: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Propiedad)
 
    if copropiedad:
        query = query.filter(Propiedad.copropiedad == copropiedad)
    if tipo:
        query = query.filter(Propiedad.tipo == tipo)
 
    return query.all()
 
 
@router.get("/{propiedad_id}", response_model=PropiedadResponse)
def obtener_propiedad(propiedad_id: int, db: Session = Depends(get_db)):
    propiedad = db.query(Propiedad).filter(Propiedad.id == propiedad_id).first()
 
    if not propiedad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propiedad no encontrada."
        )
 
    return propiedad
 
 
@router.post("", response_model=PropiedadResponse, status_code=status.HTTP_201_CREATED)
def crear_propiedad(datos: PropiedadCreate, db: Session = Depends(get_db)):
    nueva = Propiedad(
        identificador=datos.identificador,
        tipo=datos.tipo,
        copropiedad=datos.copropiedad,
        direccion=datos.direccion,
        propietario=datos.propietario,
        estado=datos.estado
    )
 
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
 
    return nueva
 
 
@router.put("/{propiedad_id}", response_model=PropiedadResponse)
def actualizar_propiedad(propiedad_id: int, datos: PropiedadUpdate, db: Session = Depends(get_db)):
    propiedad = db.query(Propiedad).filter(Propiedad.id == propiedad_id).first()
 
    if not propiedad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propiedad no encontrada."
        )
 
    if datos.identificador is not None:
        propiedad.identificador = datos.identificador
    if datos.tipo is not None:
        propiedad.tipo = datos.tipo
    if datos.copropiedad is not None:
        propiedad.copropiedad = datos.copropiedad
    if datos.direccion is not None:
        propiedad.direccion = datos.direccion
    if datos.propietario is not None:
        propiedad.propietario = datos.propietario
    if datos.estado is not None:
        propiedad.estado = datos.estado
 
    db.commit()
    db.refresh(propiedad)
 
    return propiedad
 
 
@router.delete("/{propiedad_id}", status_code=status.HTTP_200_OK)
def eliminar_propiedad(propiedad_id: int, db: Session = Depends(get_db)):
    propiedad = db.query(Propiedad).filter(Propiedad.id == propiedad_id).first()
 
    if not propiedad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propiedad no encontrada."
        )
 
    db.delete(propiedad)
    db.commit()
 
    return {"mensaje": "Propiedad eliminada correctamente."}
        