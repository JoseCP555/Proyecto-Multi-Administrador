"""Gestión documental: CRUD + subida y descarga real de archivos."""
import os
import uuid
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import schemas
from app.models import Documento
from app.database import get_db
from app.deps import require_permiso

router = APIRouter(prefix="/documentos", tags=["Documentos"], dependencies=[Depends(require_permiso("documentos.ver"))])

# Carpeta donde se guardan los archivos subidos.
ARCHIVOS_DIR = os.getenv("ARCHIVOS_DIR", "./archivos_documentos")
os.makedirs(ARCHIVOS_DIR, exist_ok=True)

TIPO_POR_EXT = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain",
    ".csv": "text/csv",
}


@router.get("", response_model=list[schemas.DocumentoResponse])
def listar(db: Session = Depends(get_db)):
    return db.query(Documento).order_by(Documento.fecha_creacion.desc()).all()


@router.get("/{documento_id}/descargar", dependencies=[Depends(require_permiso("documentos.descargar"))])
def descargar(documento_id: int, db: Session = Depends(get_db)):
    """Descarga el archivo físico asociado al documento."""
    d = db.query(Documento).get(documento_id)
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    ruta = d.ruta_archivo
    if not os.path.isabs(ruta):
        ruta = os.path.join(ARCHIVOS_DIR, os.path.basename(ruta))

    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="El archivo ya no existe en el servidor.")

    return FileResponse(ruta, media_type=d.mime or "application/octet-stream", filename=d.titulo)


@router.post("", response_model=schemas.DocumentoResponse, status_code=201, dependencies=[Depends(require_permiso("documentos.crear"))])
def crear(data: schemas.DocumentoCreate, db: Session = Depends(get_db)):
    d = Documento(
        titulo=data.titulo, descripcion=data.descripcion, ruta_archivo=data.ruta_archivo,
        tipo_documento=data.tipo_documento, mime=data.mime, tamano=data.tamano,
        propiedad_id=data.propiedad_id, publico=data.publico,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.post("/upload", response_model=schemas.DocumentoResponse, status_code=201, dependencies=[Depends(require_permiso("documentos.crear"))])
def subir(
    titulo: str = Form(...),
    descripcion: str = Form(None),
    tipo_documento: str = Form(None),
    publico: bool = Form(False),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Recibe un archivo real, lo guarda en disco y registra el documento."""
    nombre_original = os.path.basename(archivo.filename or "documento")
    ext = os.path.splitext(nombre_original)[1].lower()
    nombre_guardado = f"{uuid.uuid4().hex}{ext}"
    destino = os.path.join(ARCHIVOS_DIR, nombre_guardado)

    # Escribir el archivo de forma segura (en trozos).
    with open(destino, "wb") as out:
        shutil.copyfileobj(archivo.file, out)

    tamano = os.path.getsize(destino)
    # si no se pasó título, usar el nombre original sin extensión
    titulo_final = titulo.strip() or os.path.splitext(nombre_original)[0]

    d = Documento(
        titulo=titulo_final,
        descripcion=descripcion,
        ruta_archivo=nombre_guardado,
        tipo_documento=tipo_documento,
        mime=archivo.content_type or TIPO_POR_EXT.get(ext, "application/octet-stream"),
        tamano=tamano,
        publico=publico,
        version=1,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.put("/{documento_id}", response_model=schemas.DocumentoResponse, dependencies=[Depends(require_permiso("documentos.editar"))])
def actualizar(documento_id: int, data: schemas.DocumentoCreate, db: Session = Depends(get_db)):
    d = db.query(Documento).get(documento_id)
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    d.titulo = data.titulo
    d.descripcion = data.descripcion
    d.ruta_archivo = data.ruta_archivo
    d.tipo_documento = data.tipo_documento
    d.mime = data.mime
    d.tamano = data.tamano
    d.propiedad_id = data.propiedad_id
    d.publico = data.publico
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{documento_id}", status_code=204, dependencies=[Depends(require_permiso("documentos.eliminar"))])
def eliminar(documento_id: int, db: Session = Depends(get_db)):
    d = db.query(Documento).get(documento_id)
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    # Borrar el archivo físico si existe.
    ruta = d.ruta_archivo
    if not os.path.isabs(ruta):
        ruta = os.path.join(ARCHIVOS_DIR, os.path.basename(ruta))
    if os.path.exists(ruta):
        try:
            os.remove(ruta)
        except OSError:
            pass
    db.delete(d)
    db.commit()
    return None
