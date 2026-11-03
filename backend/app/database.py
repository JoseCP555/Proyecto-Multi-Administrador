"""Configuración de la conexión a la base de datos con SQLAlchemy.

Objetivos de este módulo (reescrito para que la base "siempre funcione"):

1. Carga la configuración desde `backend/.env`, `.env` de la raíz o variables
   de entorno (en Docker llegan del compose).
2. Normaliza la URL (`postgres://` -> `postgresql://`, recorta espacios, etc.).
3. **Espera a que PostgreSQL esté listo** (reintentos). Antes, si la base
   todavía no aceptaba conexiones, la API moría en el arranque.
4. Si NO hay `DATABASE_URL` o si PostgreSQL no responde, cae automáticamente a
   **SQLite** (`backend/multiadmin.db`) y lo avisa en el log, en lugar de lanzar
   `Exception("❌ DATABASE_URL no cargada")`. Así el proyecto arranca en
   cualquier equipo sin Docker, sin instalar nada y sin dejar la app inservible.
   Para exigir PostgreSQL de forma obligatoria:
       PERMITIR_SQLITE_FALLBACK=false
5. Deja disponibles `engine`, `SessionLocal`, `Base`, `get_db()` y datos de
   diagnóstico (`MOTOR`, `DATABASE_URL_USADA`, `AVISO_BD`).
"""
import logging
import os
import time
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

logger = logging.getLogger("app.database")

# ---------------------------------------------------------------------------
# 1) Carga de .env (backend/.env y, si no existe, el .env de la raíz)
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parents[1]
for _ruta in (_BACKEND_DIR / ".env", _BACKEND_DIR.parent / ".env"):
    if _ruta.is_file():
        load_dotenv(_ruta, override=False)
load_dotenv(override=False)


# ---------------------------------------------------------------------------
# 2) Utilidades
# ---------------------------------------------------------------------------
def _normalizar_url(url: str) -> str:
    """Limpia la URL: espacios, comillas y el esquema viejo `postgres://`."""
    url = (url or "").strip().strip('"').strip("'")
    if url.startswith("postgres://"):
        # Heroku/Render y muchos tutoriales usan `postgres://`, que SQLAlchemy
        # ya no reconoce; sin esto la conexión falla con "No such dialect".
        url = "postgresql://" + url[len("postgres://"):]
    return url


def _url_sqlite() -> str:
    """SQLite local como plan B (el archivo queda junto al backend)."""
    return "sqlite:///" + str(_BACKEND_DIR / "multiadmin.db")


def _crear_engine(url: str):
    """Crea el engine con parámetros razonables según el motor."""
    kwargs = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # No dejar peticiones colgadas eternamente si la base no responde.
        kwargs["connect_args"] = {"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5"))}
        kwargs["pool_recycle"] = 1800
    return create_engine(url, echo=os.getenv("SQL_ECHO", "false").lower() == "true", **kwargs)


def _esperar_base(engine, intentos: int, espera: float) -> bool:
    """Reintenta la conexión: en Docker la base puede tardar unos segundos."""
    for intento in range(1, intentos + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:  # noqa: BLE001
            if intento == intentos:
                logger.warning("Base de datos no disponible tras %s intentos: %s", intentos, exc)
                return False
            logger.info("Esperando a la base de datos (%s/%s)...", intento, intentos)
            time.sleep(espera)
    return False


# ---------------------------------------------------------------------------
# 3) Selección del motor
# ---------------------------------------------------------------------------
_DB_URL_ENV = _normalizar_url(os.getenv("DATABASE_URL", ""))
_PERMITIR_FALLBACK = os.getenv("PERMITIR_SQLITE_FALLBACK", "true").strip().lower() not in (
    "0", "false", "no", "off",
)
_INTENTOS = int(os.getenv("DB_STARTUP_RETRIES", "5"))
_ESPERA = float(os.getenv("DB_STARTUP_DELAY", "1.5"))

AVISO_BD = None

if _DB_URL_ENV:
    DATABASE_URL_USADA = _DB_URL_ENV
    engine = _crear_engine(DATABASE_URL_USADA)
    if not _esperar_base(engine, _INTENTOS, _ESPERA):
        if not _PERMITIR_FALLBACK:
            raise RuntimeError(
                "❌ No se pudo conectar a la base de datos indicada en DATABASE_URL:\n"
                f"   {DATABASE_URL_USADA}\n"
                "   Revisa que el servidor PostgreSQL esté encendido, que la base y el\n"
                "   usuario existan y que la contraseña sea correcta.\n"
                "   En Docker:  docker compose up -d db\n"
                "   Sin Docker: ./db/crear_bd.sh   (crea la base y aplica db/init.sql)"
            )
        engine.dispose()
        DATABASE_URL_USADA = _url_sqlite()
        AVISO_BD = (
            "No se pudo conectar a DATABASE_URL; se está usando SQLite local "
            f"({DATABASE_URL_USADA}). Los datos NO son los de PostgreSQL."
        )
        logger.error("⚠ %s", AVISO_BD)
        engine = _crear_engine(DATABASE_URL_USADA)
else:
    DATABASE_URL_USADA = _url_sqlite()
    AVISO_BD = (
        "DATABASE_URL no está definida; se usa SQLite local "
        f"({DATABASE_URL_USADA}). Copia backend/.env.example a backend/.env "
        "para trabajar con PostgreSQL."
    )
    logger.warning("⚠ %s", AVISO_BD)
    engine = _crear_engine(DATABASE_URL_USADA)

ES_POSTGRES = engine.dialect.name == "postgresql"
MOTOR = "PostgreSQL" if ES_POSTGRES else engine.dialect.name
DATABASE_URL_ENMASCARADA = (
    DATABASE_URL_USADA.split("@")[-1] if "@" in DATABASE_URL_USADA else DATABASE_URL_USADA
)
logger.info("Base de datos en uso: %s (%s)", MOTOR, DATABASE_URL_ENMASCARADA)

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
