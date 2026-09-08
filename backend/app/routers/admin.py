"""Utilidades de administración: respaldo de la base de datos."""
import os
import shutil
import subprocess

from fastapi import APIRouter, Depends, HTTPException, Response

from app.database import get_db
from app.deps import require_permiso

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_permiso("sistema.respaldar"))])


@router.get("/backup")
def backup_db():
    """Genera un respaldo de la base de datos (pg_dump) y lo devuelve como archivo SQL."""
    url = os.getenv("DATABASE_URL", "")
    # Extraer host/port/user/db desde postgresql://user:pass@host:port/db
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = str(parsed.port or 5432)
    user = parsed.username or ""
    password = parsed.password or ""
    dbname = parsed.path.lstrip("/") or "multiadmin_db"

    if shutil.which("pg_dump") is None:
        raise HTTPException(status_code=500, detail="pg_dump no está disponible.")

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    try:
        proc = subprocess.run(
            ["pg_dump", "-h", host, "-p", port, "-U", user, "-d", dbname, "--no-owner"],
            env=env, capture_output=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="El respaldo tardó demasiado.")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"No se pudo realizar el respaldo: {e}")

    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=proc.stderr.decode()[:400])

    contenido = proc.stdout
    return Response(
        content=contenido,
        media_type="application/sql",
        headers={"Content-Disposition": 'attachment; filename="multiadmin_db_backup.sql"'},
    )
