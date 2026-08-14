import os
import shutil
import uuid
 
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
 
from database import Base, SessionLocal
 
router = APIRouter(prefix="/documentos", tags=["Documentos"])
 
# Carpeta donde se guardan los archivos físicos (se crea sola si no existe)
CARPETA_ARCHIVOS = "archivos_documentos"
os.makedirs(CARPETA_ARCHIVOS, exist_ok=True)
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 

# MODELO (tabla nueva, no existía antes)

 
class Documento(Base):
    __tablename__ = "documentos"
 
    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String, nullable=False)   # Actas, Reglamentos, Manuales, Contratos, Pólizas, Soporte, Evidencias
    copropiedad = Column(String, nullable=True)
 
    titulo = Column(String, nullable=False)
    numero = Column(String, nullable=True)
    descripcion = Column(String, nullable=True)
    fecha = Column(String, nullable=True)
    hora = Column(String, nullable=True)
    lugar = Column(String, nullable=True)
 
    archivo_nombre = Column(String, nullable=True)   # nombre original del archivo
    archivo_ruta = Column(String, nullable=True)      # ruta física guardada en disco
 
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
 
 

# ESQUEMAS

 
class DocumentoResponse(BaseModel):
    id: int
    categoria: str
    copropiedad: str | None = None
    titulo: str
    numero: str | None = None
    descripcion: str | None = None
    fecha: str | None = None
    hora: str | None = None
    lugar: str | None = None
    archivo_nombre: str | None = None
    fecha_creacion: datetime
 
    class Config:
        from_attributes = True
 
 

# RUTAS

 
@router.get("", response_model=list[DocumentoResponse])
def listar_documentos(
    categoria: str | None = None,
    copropiedad: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Documento)
 
    if categoria:
        query = query.filter(Documento.categoria == categoria)
    if copropiedad:
        query = query.filter(Documento.copropiedad == copropiedad)
 
    return query.order_by(Documento.fecha_creacion.desc()).all()
 
 
@router.get("/{documento_id}", response_model=DocumentoResponse)
def obtener_documento(documento_id: int, db: Session = Depends(get_db)):
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
 
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado."
        )
 
    return documento
 
 
@router.post("", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
def subir_documento(
    categoria: str = Form(...),
    copropiedad: str | None = Form(None),
    titulo: str = Form(...),
    numero: str | None = Form(None),
    descripcion: str | None = Form(None),
    fecha: str | None = Form(None),
    hora: str | None = Form(None),
    lugar: str | None = Form(None),
    archivo: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    archivo_nombre = None
    archivo_ruta = None
 
    if archivo is not None:
        extension = os.path.splitext(archivo.filename)[1]
        nombre_guardado = f"{uuid.uuid4().hex}{extension}"
        ruta_destino = os.path.join(CARPETA_ARCHIVOS, nombre_guardado)
 
        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
 
        archivo_nombre = archivo.filename
        archivo_ruta = ruta_destino
 
    nuevo = Documento(
        categoria=categoria,
        copropiedad=copropiedad,
        titulo=titulo,
        numero=numero,
        descripcion=descripcion,
        fecha=fecha,
        hora=hora,
        lugar=lugar,
        archivo_nombre=archivo_nombre,
        archivo_ruta=archivo_ruta,
        fecha_creacion=datetime.utcnow()
    )
 
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
 
    return nuevo
 
 
@router.get("/{documento_id}/descargar")
def descargar_documento(documento_id: int, db: Session = Depends(get_db)):
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
 
    if not documento or not documento.archivo_ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este documento no tiene un archivo adjunto."
        )
 
    if not os.path.exists(documento.archivo_ruta):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo ya no existe en el servidor."
        )
 
    return FileResponse(
        path=documento.archivo_ruta,
        filename=documento.archivo_nombre,
        media_type="application/octet-stream"
    )
 
 
@router.delete("/{documento_id}", status_code=status.HTTP_200_OK)
def eliminar_documento(documento_id: int, db: Session = Depends(get_db)):
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
 
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado."
        )
 
    if documento.archivo_ruta and os.path.exists(documento.archivo_ruta):
        os.remove(documento.archivo_ruta)
 
    db.delete(documento)
    db.commit()
 
    return {"mensaje": "Documento eliminado correctamente."}
 