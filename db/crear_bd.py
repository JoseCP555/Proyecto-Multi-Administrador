"""Crea la base de datos de Multi-Administrador y aplica db/init.sql.

Sirve para quien NO usa Docker (o para recrear la base desde cero).
Funciona en Windows, Linux y macOS.

Uso:
    python db/crear_bd.py                       # usa DATABASE_URL del .env
    python db/crear_bd.py --recrear             # BORRA y vuelve a crear la base
    python db/crear_bd.py --url postgresql://usuario:clave@localhost:5432/multiadmin_db
    python db/crear_bd.py --db multiadmin_db --user postgres --password 1234 --host localhost

Qué hace, en orden:
 1. Se conecta a la base administrativa `postgres`.
 2. Crea la base de datos si no existe (con --recrear la elimina primero).
 3. Ejecuta db/init.sql (crea las 18 tablas, índices, triggers y el RBAC).
 4. Muestra un resumen de lo creado.
El usuario administrador y los datos demo los siembra el backend al arrancar
(backend/app/seed.py), así que basta con iniciar la API después.
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RUTA_SQL = RAIZ / "db" / "init.sql"

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:  # pragma: no cover
    print("ERROR: falta psycopg2. Instala las dependencias primero:\n"
          "    pip install -r backend/requirements.txt", file=sys.stderr)
    raise SystemExit(2)


def _leer_env() -> dict:
    """Lee backend/.env o el .env de la raíz sin dependencias externas."""
    datos: dict[str, str] = {}
    for ruta in (RAIZ / ".env", RAIZ / "backend" / ".env"):
        if ruta.is_file():
            for linea in ruta.read_text(encoding="utf-8", errors="ignore").splitlines():
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                clave, valor = linea.split("=", 1)
                datos.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))
    return datos


def _partir_url(url: str) -> dict:
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    p = urllib.parse.urlparse(url)
    return {
        "host": p.hostname or "localhost",
        "port": p.port or 5432,
        "user": p.username or "postgres",
        "password": p.password or "",
        "dbname": (p.path or "/multiadmin_db").lstrip("/") or "multiadmin_db",
    }


def _conectar(cfg: dict, dbname: str):
    return psycopg2.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"],
        password=cfg["password"], dbname=dbname, connect_timeout=8,
    )


def main() -> int:
    env = _leer_env()
    parser = argparse.ArgumentParser(description="Crea y prepara la base de datos.")
    parser.add_argument("--url", default=os.getenv("DATABASE_URL") or env.get("DATABASE_URL"),
                        help="URL de conexión (por defecto DATABASE_URL del .env)")
    parser.add_argument("--host"), parser.add_argument("--port", type=int)
    parser.add_argument("--user"), parser.add_argument("--password")
    parser.add_argument("--db", dest="dbname")
    parser.add_argument("--recrear", action="store_true",
                        help="Elimina la base si existe antes de crearla")
    args = parser.parse_args()

    cfg = _partir_url(args.url) if args.url else {
        "host": "localhost", "port": 5432, "user": "postgres",
        "password": "", "dbname": "multiadmin_db",
    }
    cfg["host"] = args.host or cfg["host"]
    cfg["port"] = args.port or cfg["port"]
    cfg["user"] = args.user or env.get("POSTGRES_USER") or cfg["user"]
    cfg["password"] = args.password if args.password is not None else (
        env.get("POSTGRES_PASSWORD") or cfg["password"]
    )
    cfg["dbname"] = args.dbname or env.get("POSTGRES_DB") or cfg["dbname"]

    print(f"→ Servidor : {cfg['host']}:{cfg['port']}  (usuario: {cfg['user']})")
    print(f"→ Base     : {cfg['dbname']}")

    # 1) Conexión a la base administrativa
    try:
        admin = _conectar(cfg, "postgres")
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ No se pudo conectar a PostgreSQL: {exc}\n"
              "   • Verifica que el servicio esté encendido (Docker: docker compose up -d db)\n"
              "   • Revisa usuario/contraseña/puerto\n"
              "   • ¿No tienes PostgreSQL? Usa Docker o trabaja con SQLite\n"
              "     (la API cae a SQLite automáticamente si la base no responde).",
              file=sys.stderr)
        return 1
    admin.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = admin.cursor()

    # 2) Crear (o recrear) la base
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (cfg["dbname"],))
    existe = cur.fetchone() is not None
    if existe and args.recrear:
        print("→ Eliminando la base existente (--recrear)...")
        cur.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(cfg["dbname"])))
        existe = False
    if not existe:
        print("→ Creando base de datos...")
        cur.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'").format(
            sql.Identifier(cfg["dbname"])))
    else:
        print("→ La base ya existe: se aplicará el script (es idempotente).")
    cur.close()
    admin.close()

    # 3) Aplicar init.sql
    if not RUTA_SQL.is_file():
        print(f"❌ No se encontró {RUTA_SQL}", file=sys.stderr)
        return 1
    script = RUTA_SQL.read_text(encoding="utf-8")
    try:
        conn = _conectar(cfg, cfg["dbname"])
    except Exception as exc:  # noqa: BLE001
        print(f"❌ No se pudo abrir «{cfg['dbname']}»: {exc}", file=sys.stderr)
        return 1
    try:
        with conn, conn.cursor() as cur2:
            cur2.execute(script)
        print("→ Script db/init.sql aplicado correctamente.")
        with conn.cursor() as cur3:
            cur3.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
            tablas = cur3.fetchone()[0]
            cur3.execute("SELECT count(*) FROM roles")
            roles = cur3.fetchone()[0]
            try:
                cur3.execute("SELECT count(*) FROM rol_permisos")
                asignaciones = cur3.fetchone()[0]
            except Exception:  # noqa: BLE001
                asignaciones = 0
        print(f"\n✅ BASE DE DATOS LISTA")
        print(f"   • Tablas creadas      : {tablas}")
        print(f"   • Roles               : {roles}")
        print(f"   • Permisos asignados  : {asignaciones}")
        print("\n   Siguiente paso: arranca el backend (uvicorn app.main:app) para que")
        print("   se siembre el usuario admin@multiadmin.com / Admin2026! y los datos demo.")
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(f"❌ Error aplicando db/init.sql:\n   {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
