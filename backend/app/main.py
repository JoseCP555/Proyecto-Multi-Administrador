"""Punto de entrada de la API de Multi-Administrador (FastAPI)."""
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import (
    Base, engine, SessionLocal, MOTOR, AVISO_BD, DATABASE_URL_ENMASCARADA,
)
import app.models  # noqa: F401  (registra los modelos)
from app.routers import (
    auth, usuario, residente, propiedad, finanzas,
    mantenimiento, documento, evento, configuracion, reporte, chatbot,
    notificacion, admin, conjunto, logos,
)
from app.seed import ejecutar_seed, sembrar_conjuntos
from app.permisos import sincronizar_permisos

logging.basicConfig(level=logging.INFO)

# Crea las tablas si no existen.
Base.metadata.create_all(bind=engine)

# Migración ligera: columnas nuevas en bases ya existentes (idempotente).
from sqlalchemy import text, inspect  # noqa: E402

# Sentencias que sólo aplican a PostgreSQL (ADD COLUMN IF NOT EXISTS).
_MIGRACIONES_PG = (
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS correo_verificado BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS token_verificacion VARCHAR(255)",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS expira_verificacion TIMESTAMP",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_verificacion VARCHAR(6)",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_recuperacion VARCHAR(6)",
    # Las cuentas creadas antes de esta función se consideran verificadas.
    "UPDATE usuarios SET correo_verificado = TRUE WHERE token_verificacion IS NULL AND correo_verificado = FALSE",
    # --- Multi-conjunto (HU-07) -------------------------------------------
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS id_conjunto INTEGER",
    "ALTER TABLE residentes ADD COLUMN IF NOT EXISTS id_conjunto INTEGER",
    "ALTER TABLE propiedades ADD COLUMN IF NOT EXISTS id_conjunto INTEGER",
    "ALTER TABLE movimientos_financieros ADD COLUMN IF NOT EXISTS id_conjunto INTEGER",
    "ALTER TABLE tareas_mantenimiento ADD COLUMN IF NOT EXISTS id_conjunto INTEGER",
    "ALTER TABLE documentos ADD COLUMN IF NOT EXISTS id_conjunto INTEGER",
    "ALTER TABLE eventos ADD COLUMN IF NOT EXISTS id_conjunto INTEGER",
    "ALTER TABLE sesiones_chat ADD COLUMN IF NOT EXISTS id_conjunto INTEGER",
    # --- Color del conjunto ------------------------------------------------
    "ALTER TABLE conjuntos ADD COLUMN IF NOT EXISTS color VARCHAR(20)",
    # --- Preferencias de notificaciones ------------------------------------
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notificaciones_correo BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notificaciones_push BOOLEAN NOT NULL DEFAULT TRUE",
)

_es_postgres = engine.dialect.name == "postgresql"
# En otros motores (p. ej. SQLite en desarrollo) esas sentencias no aplican:
# `create_all` ya crea las columnas del modelo y sólo se ejecuta el UPDATE.
_MIGRACIONES_SQL = (
    "UPDATE usuarios SET correo_verificado = TRUE WHERE token_verificacion IS NULL AND correo_verificado = FALSE",
)
with engine.begin() as _conn:
    for _sql in (_MIGRACIONES_PG if _es_postgres else _MIGRACIONES_SQL):
        try:
            _conn.execute(text(_sql))
        except Exception as _exc:  # noqa: BLE001 - una columna que ya existe no debe tumbar la API
            logging.getLogger("app.migraciones").warning("Migración omitida (%s): %s", _sql[:60], _exc)

# En bases nuevas (o SQLite de desarrollo) las columnas ya las crea SQLAlchemy.
if not _es_postgres:
    with engine.begin() as _conn:
        for _tabla, _col, _tipo in (
            ("usuarios", "id_conjunto", "INTEGER"), ("residentes", "id_conjunto", "INTEGER"),
            ("propiedades", "id_conjunto", "INTEGER"), ("movimientos_financieros", "id_conjunto", "INTEGER"),
            ("tareas_mantenimiento", "id_conjunto", "INTEGER"), ("documentos", "id_conjunto", "INTEGER"),
            ("eventos", "id_conjunto", "INTEGER"), ("sesiones_chat", "id_conjunto", "INTEGER"),
            ("conjuntos", "color", "VARCHAR(20)"),
            ("usuarios", "notificaciones_correo", "BOOLEAN NOT NULL DEFAULT 1"),
            ("usuarios", "notificaciones_push", "BOOLEAN NOT NULL DEFAULT 1"),
        ):
            try:
                columnas = [c["name"] for c in inspect(_conn).get_columns(_tabla)]
                if _col not in columnas:
                    _conn.execute(text(f"ALTER TABLE {_tabla} ADD COLUMN {_col} {_tipo}"))
            except Exception:  # noqa: BLE001
                pass

# Claves foráneas del multi-conjunto (solo si la tabla `conjuntos` ya existe).
if _es_postgres:
    _FKs = (
        ("usuarios", "usuarios_id_conjunto_fkey"),
        ("residentes", "residentes_id_conjunto_fkey"),
        ("propiedades", "propiedades_id_conjunto_fkey"),
        ("movimientos_financieros", "movimientos_financieros_id_conjunto_fkey"),
        ("tareas_mantenimiento", "tareas_mantenimiento_id_conjunto_fkey"),
        ("documentos", "documentos_id_conjunto_fkey"),
        ("eventos", "eventos_id_conjunto_fkey"),
        ("sesiones_chat", "sesiones_chat_id_conjunto_fkey"),
    )
    with engine.begin() as _conn:
        for _tabla, _nombre in _FKs:
            try:
                _conn.execute(text(
                    f"DO $$ BEGIN "
                    f"IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{_nombre}') THEN "
                    f"ALTER TABLE {_tabla} ADD CONSTRAINT {_nombre} "
                    f"FOREIGN KEY (id_conjunto) REFERENCES conjuntos(id) ON DELETE SET NULL; "
                    f"END IF; END $$;"
                ))
            except Exception as _exc:  # noqa: BLE001 - la FK es opcional: no tumba la API
                logging.getLogger("app.migraciones").warning(
                    "FK %s omitida: %s", _nombre, _exc
                )

app = FastAPI(
    title="Multi-Administrador API",
    description="API del sistema de administración de conjuntos residenciales.",
    version="1.0.0",
)

# ----------------------------- CORS -----------------------------------------
_origenes_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000",
)
ALLOWED_ORIGINS = [o.strip() for o in _origenes_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------- Routers --------------------------------------
for r in [
    auth.router, usuario.router, residente.router, propiedad.router,
    finanzas.router, mantenimiento.router, documento.router, evento.router,
    configuracion.router, reporte.router, chatbot.router,
    notificacion.router, admin.router, conjunto.router, logos.router,
]:
    app.include_router(r)


@app.on_event("startup")
def arrancar():
    """Siembra datos iniciales si la base está vacía (idempotente)."""
    from app.email_config import resumen_smtp, mail_configurado
    (logging.getLogger("app.correo").info if mail_configurado() else logging.getLogger("app.correo").error)(
        "[correo] %s", resumen_smtp()
    )
    db: Session = SessionLocal()
    try:
        sincronizar_permisos(db)
        ejecutar_seed(db)
        # Conjuntos de demostración y datos por conjunto (idempotente).
        try:
            sembrar_conjuntos(db)
        except Exception as exc:  # noqa: BLE001 - el seed nunca debe tumbar la API
            logging.getLogger("app.seed").error("No se pudo sembrar los conjuntos: %s", exc)
            db.rollback()
    finally:
        db.close()


@app.get("/")
def home():
    return {"mensaje": "Multi-Administrador API funcionando", "docs": "/docs"}


@app.get("/health")
def health():
    from app.email_config import mail_configurado, EMAIL_USER, MAIL_SERVER
    from app.routers.auth import _registro_admin_habilitado
    return {
        "status": "ok",
        "base_datos": {
            "motor": MOTOR,
            "destino": DATABASE_URL_ENMASCARADA,
            "aviso": AVISO_BD,
        },
        "correo": {"configurado": mail_configurado(), "remitente": EMAIL_USER or None, "servidor": MAIL_SERVER or None},
        "registro_admin_habilitado": _registro_admin_habilitado(),
    }
