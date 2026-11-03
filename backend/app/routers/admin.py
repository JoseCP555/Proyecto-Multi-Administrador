"""Utilidades de administración: respaldo de la base de datos.

El respaldo funciona en los dos escenarios:

* **PostgreSQL con `pg_dump` instalado**  -> usa `pg_dump --no-owner`
  (respaldo nativo, el más fiel).
* **Cualquier otro caso** (SQLite, Docker sin `pg_dump`, Postgres remoto sin
  binarios del cliente) -> genera el respaldo con Python: recorre las tablas y
  escribe un archivo `.sql` con `CREATE TABLE` + `INSERT`, que se puede volver
  a cargar con `psql` o `sqlite3`.

Antes, si `pg_dump` no existía, la ruta devolvía siempre HTTP 500
("pg_dump no está disponible") y el respaldo nunca funcionaba.
"""
import datetime as _dt
import os
import shutil
import subprocess
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import inspect, text

from app.database import Base, engine, ES_POSTGRES
from app.deps import require_permiso

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_permiso("sistema.respaldar"))])


def _respaldo_con_pg_dump() -> bytes | None:
    """Devuelve el volcado de pg_dump o None si no se puede usar."""
    url = os.getenv("DATABASE_URL", "")
    if not ES_POSTGRES or shutil.which("pg_dump") is None:
        return None

    parsed = urllib.parse.urlparse(url)
    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = parsed.password

    comando = [
        "pg_dump",
        "-h", parsed.hostname or "127.0.0.1",
        "-p", str(parsed.port or 5432),
        "-U", parsed.username or "",
        "-d", (parsed.path.lstrip("/") or "multiadmin_db"),
        "--no-owner",
    ]
    try:
        proc = subprocess.run(comando, env=env, capture_output=True, timeout=120)
    except Exception:  # noqa: BLE001 - cualquier fallo cae al respaldo en Python
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _literal(valor) -> str:
    """Convierte un valor de Python en un literal SQL seguro."""
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, (int, float)):
        return repr(valor)
    if isinstance(valor, _dt.datetime):
        return "'" + valor.isoformat(sep=" ") + "'"
    if isinstance(valor, (_dt.date, _dt.time)):
        return "'" + valor.isoformat() + "'"
    if isinstance(valor, (bytes, bytearray, memoryview)):
        return "'\\x" + bytes(valor).hex() + "'"
    texto = str(valor).replace("'", "''")
    return "'" + texto + "'"


def _orden_por_dependencias(tablas: list[str]) -> list[str]:
    """Ordena las tablas respetando las claves foráneas (padres primero).

    Así el archivo de respaldo se puede restaurar sin desactivar las FK: los
    DELETE van en orden inverso y los INSERT en orden directo.
    """
    conocidas = {t.name for t in Base.metadata.sorted_tables}
    if set(tablas) <= conocidas:
        orden = [t.name for t in Base.metadata.sorted_tables if t.name in tablas]
        orden += [t for t in tablas if t not in orden]
        return orden
    return sorted(tablas)


def _respaldo_en_python() -> bytes:
    """Respaldo portable: estructura + datos en un único archivo .sql."""
    inspector = inspect(engine)
    lineas: list[str] = [
        "-- Respaldo Multi-Administrador",
        f"-- Generado: {_dt.datetime.utcnow().isoformat(timespec='seconds')}Z",
        f"-- Motor: {engine.dialect.name}",
        f"-- Base: {engine.url.database}",
        "-- Restaurar con:  psql -U usuario -d base -f este_archivo.sql",
        "--                 sqlite3 multiadmin.db < este_archivo.sql",
        "BEGIN;",
        "",
    ]
    tablas = _orden_por_dependencias(inspector.get_table_names())
    with engine.connect() as conn:
        # DELETE en orden inverso (hijos primero) para no violar las FK.
        for tabla in reversed(tablas):
            lineas.append(f"DELETE FROM {tabla};")
        lineas.append("")
        for tabla in tablas:
            lineas.append(f"-- ------------------------------ {tabla}")
            filas = conn.execute(text(f"SELECT * FROM {tabla}")).mappings().all()
            for fila in filas:
                columnas = ", ".join(fila.keys())
                valores = ", ".join(_literal(v) for v in fila.values())
                lineas.append(f"INSERT INTO {tabla} ({columnas}) VALUES ({valores});")
            lineas.append("")
    lineas.append("COMMIT;")
    return ("\n".join(lineas) + "\n").encode("utf-8")


@router.get("/backup")
def backup_db():
    """Genera un respaldo de la base de datos y lo devuelve como archivo .sql."""
    try:
        contenido = _respaldo_con_pg_dump()
        origen = "pg_dump"
        if contenido is None:
            contenido = _respaldo_en_python()
            origen = "python"
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"No se pudo realizar el respaldo: {exc}")

    nombre = f"multiadmin_backup_{_dt.datetime.utcnow():%Y%m%d_%H%M%S}.sql"
    return Response(
        content=contenido,
        media_type="application/sql",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
            "X-Respaldo-Origen": origen,
        },
    )
