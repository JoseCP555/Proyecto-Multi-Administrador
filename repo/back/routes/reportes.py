from fastapi import APIRouter, Depends;
from sqlalchemy.orm import Session;

from database import SessionLocal;
from routes.documentos import Documento, DocumentoResponse;

router = APIRouter(prefix="/reportes", tags=["Reportes"]);


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
        
# Rutas 


@router.get("", response_model=list[DocumentoResponse])
def listar_reportes(
    categoria: str | None = None,
    copropiedad: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Vista de solo lectura sobre los documentos ya cargados
    (Actas, Reglamentos, Manuales, Contratos, Pólizas, Soporte, Evidencias).
    Para crear, subir o eliminar documentos, se usa /documentos.
    """
    query = db.query(Documento)
 
    if categoria:
        query = query.filter(Documento.categoria == categoria)
    if copropiedad:
        query = query.filter(Documento.copropiedad == copropiedad)
 
    return query.order_by(Documento.fecha_creacion.desc()).all()
 