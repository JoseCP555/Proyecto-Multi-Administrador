"""Configuración de la conexión a PostgreSQL con SQLAlchemy."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carga de variables de entorno (.env en local; en Docker llegan del compose).
from pathlib import Path as _Path
_BACKEND_DIR = _Path(__file__).resolve().parents[1]
for _ruta in (_BACKEND_DIR / ".env", _BACKEND_DIR.parent / ".env"):
    if _ruta.is_file():
        load_dotenv(_ruta, override=False)
load_dotenv(override=False)

DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    raise Exception("❌ DATABASE_URL no cargada. Revisa tu archivo .env")

# Echo de SQL en consola (útil para depurar; desactivar en producción).
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

engine = create_engine(DB_URL, echo=SQL_ECHO, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Clase base para todos los modelos ORM.
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: abre una sesión y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
