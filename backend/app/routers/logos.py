"""Subida y servicio público de los logos de los conjuntos.

El archivo se guarda en disco (dentro del volumen `documentos_data` en Docker)
y en la columna `conjuntos.logo` solo se almacena una ruta corta y relativa:
`archivos/logos/<uuid>.png`. Así no se infla la base de datos con base64 y el
mismo valor sirve tanto si el frontend usa el proxy `/api` como si apunta
directamente al backend.
"""
import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.deps import require_alguno

logger = logging.getLogger("app.logos")

router = APIRouter(tags=["Logos"])

ARCHIVOS_DIR = os.getenv("ARCHIVOS_DIR", "./archivos_documentos")
LOGOS_DIR = os.path.join(ARCHIVOS_DIR, "logos")
RUTA_PUBLICA = "archivos/logos"
MAX_BYTES = 2 * 1024 * 1024  # 2 MB

# Extensión -> (content-type, firma binaria mínima para validar el archivo).
FIRMAS: dict[str, tuple[str, bytes | None]] = {
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".webp": ("image/webp", None),  # se valida con RIFF....WEBP más abajo
}


def _asegurar_dir() -> None:
    os.makedirs(LOGOS_DIR, exist_ok=True)


def _nombre_seguro(nombre: str) -> str | None:
    """Evita path traversal: solo nombres de archivo planos con extensión válida."""
    base = os.path.basename(nombre)
    if not base or base != nombre or base.startswith("."):
        return None
    if os.path.splitext(base)[1].lower() not in FIRMAS:
        return None
    return base


@router.post("/subidas/logo", status_code=201)
def subir_logo(
    archivo: UploadFile = File(...),
    _usuario=Depends(require_alguno("conjuntos.crear", "conjuntos.editar")),
):
    """Guarda la imagen y devuelve la ruta relativa que va en `conjuntos.logo`."""
    nombre_original = archivo.filename or ""
    ext = os.path.splitext(os.path.basename(nombre_original))[1].lower()
    if ext not in FIRMAS:
        raise HTTPException(400, "Formato no permitido. Usa una imagen PNG, JPG o WEBP.")

    contenido = archivo.file.read(MAX_BYTES + 1)
    if not contenido:
        raise HTTPException(400, "El archivo está vacío.")
    if len(contenido) > MAX_BYTES:
        raise HTTPException(400, "La imagen supera el tamaño máximo de 2 MB.")

    mime, firma = FIRMAS[ext]
    es_valida = contenido.startswith(firma) if firma else (
        contenido.startswith(b"RIFF") and contenido[8:12] == b"WEBP"
    )
    if not es_valida:
        raise HTTPException(400, "El contenido del archivo no corresponde a una imagen válida.")

    _asegurar_dir()
    nombre = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(LOGOS_DIR, nombre), "wb") as out:
        out.write(contenido)

    logger.info("Logo subido: %s (%d bytes)", nombre, len(contenido))
    return {"ok": True, "logo": f"{RUTA_PUBLICA}/{nombre}"}


@router.get("/archivos/logos/{nombre}")
def servir_logo(nombre: str):
    """Sirve la imagen. Es público (un logo no es información sensible) para
    poder usarla en una etiqueta <img> sin enviar cabeceras de autenticación."""
    seguro = _nombre_seguro(nombre)
    if not seguro:
        raise HTTPException(404, "Logo no encontrado.")
    ruta = os.path.join(LOGOS_DIR, seguro)
    if not os.path.isfile(ruta):
        raise HTTPException(404, "Logo no encontrado.")
    mime = FIRMAS[os.path.splitext(seguro)[1].lower()][0]
    return FileResponse(
        ruta,
        media_type=mime,
        headers={"Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff"},
    )
