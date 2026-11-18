"""Punto de entrada de la API de Multi-Administrador (FastAPI)."""
import os
import logging

from fastapi import FastAPI, Request
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
    # Historias de usuario UH-01 a UH-32
    pqrs, reserva, comunicado, visitante, pago,
    votacion, aprobacion, auditoria, perfil,
    # Mensajería directa residente <-> administrador
    mensajeria,
)
from app.auditoria import AuditoriaMiddleware
from app import programador
from app.seed import ejecutar_seed, sembrar_conjuntos, sincronizar_config_chatbot
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
    # --- Historias de usuario UH-01 a UH-32 ---------------------------------
    # UH-20: foto de perfil.
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto TEXT",
    # UH-04 / UH-01: hora, tipo y bandera del aviso de 48 horas.
    "ALTER TABLE eventos ADD COLUMN IF NOT EXISTS hora VARCHAR(5)",
    "ALTER TABLE eventos ADD COLUMN IF NOT EXISTS tipo VARCHAR(30) DEFAULT 'actividad'",
    "ALTER TABLE eventos ADD COLUMN IF NOT EXISTS notificado_48h BOOLEAN NOT NULL DEFAULT FALSE",
    # UH-26: umbral de gasto por conjunto.
    "ALTER TABLE conjuntos ADD COLUMN IF NOT EXISTS umbral_gasto NUMERIC(12, 2) DEFAULT 2000000",
    # UH-21: categoría y evidencias del reporte de daños.
    "ALTER TABLE tareas_mantenimiento ADD COLUMN IF NOT EXISTS categoria VARCHAR(30) DEFAULT 'unidad'",
    "ALTER TABLE tareas_mantenimiento ADD COLUMN IF NOT EXISTS evidencias TEXT",
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
            ("usuarios", "foto", "TEXT"),
            ("eventos", "hora", "VARCHAR(5)"),
            ("eventos", "tipo", "VARCHAR(30) DEFAULT 'actividad'"),
            ("eventos", "notificado_48h", "BOOLEAN NOT NULL DEFAULT 0"),
            ("conjuntos", "umbral_gasto", "NUMERIC(12, 2) DEFAULT 2000000"),
            ("tareas_mantenimiento", "categoria", "VARCHAR(30) DEFAULT 'unidad'"),
            ("tareas_mantenimiento", "evidencias", "TEXT"),
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
        ("pqrs", "pqrs_id_conjunto_fkey"),
        ("zonas_comunes", "zonas_comunes_id_conjunto_fkey"),
        ("reservas_zonas", "reservas_zonas_id_conjunto_fkey"),
        ("comunicados", "comunicados_id_conjunto_fkey"),
        ("visitantes", "visitantes_id_conjunto_fkey"),
        ("comprobantes_pago", "comprobantes_pago_id_conjunto_fkey"),
        ("votaciones", "votaciones_id_conjunto_fkey"),
        ("solicitudes_aprobacion", "solicitudes_aprobacion_id_conjunto_fkey"),
        ("auditoria", "auditoria_id_conjunto_fkey"),
        ("conversaciones_directas", "conversaciones_directas_id_conjunto_fkey"),
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
    # Permite pruebas desde celulares en la misma red Wi-Fi local (192.168.x.x, 10.x.x.x, 172.16-31.x.x).
    allow_origin_regex=r"^https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# ----------------------------- Auditoría (UH-29) ----------------------------
# Se añade después del CORS para que la cabecera de la respuesta se mantenga.
app.add_middleware(AuditoriaMiddleware)


@app.middleware("http")
async def detectar_origen_frontend(request: Request, call_next):
    """Detecta la URL real desde la que se abre el frontend (LAN / túnel / dominio)
    para que los botones 'Ver en la aplicación' de los correos abran esa URL."""
    from app.correo import registrar_origen_frontend, restaurar_origen_frontend

    origen = request.headers.get("origin") or request.headers.get("referer")
    if not origen:
        fwd_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
        fwd_proto = (request.headers.get("x-forwarded-proto") or "http").split(",")[0].strip()
        if fwd_host and not fwd_host.endswith(":8000"):
            origen = f"{fwd_proto}://{fwd_host}"
    token = registrar_origen_frontend(origen)
    try:
        return await call_next(request)
    finally:
        restaurar_origen_frontend(token)

# ----------------------------- Routers --------------------------------------
for r in [
    auth.router, usuario.router, residente.router, propiedad.router,
    finanzas.router, mantenimiento.router, documento.router, evento.router,
    configuracion.router, reporte.router, chatbot.router,
    notificacion.router, admin.router, conjunto.router, logos.router,
    # UH-09 · UH-10 · UH-11 · UH-12 · UH-13 · UH-14 · UH-16 · UH-17
    # UH-19 · UH-20 · UH-21 · UH-22 · UH-23 · UH-24 · UH-25 · UH-26
    # UH-29 · UH-32
    pqrs.router, reserva.router, comunicado.router, visitante.router,
    pago.router, votacion.router, aprobacion.router, auditoria.router,
    perfil.router, mensajeria.router,
]:
    app.include_router(r)


@app.on_event("startup")
def arrancar():
    """Siembra datos iniciales si la base está vacía (idempotente)."""
    from app.email_config import advertencia_enlaces, resumen_smtp, mail_configurado
    (logging.getLogger("app.correo").info if mail_configurado() else logging.getLogger("app.correo").error)(
        "[correo] %s", resumen_smtp()
    )
    if mail_configurado() and advertencia_enlaces():
        logging.getLogger("app.correo").warning("[correo] %s", advertencia_enlaces())
    db: Session = SessionLocal()
    try:
        sincronizar_permisos(db)
        ejecutar_seed(db)
        try:
            sincronizar_config_chatbot(db)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("app.chatbot").error("No se pudo sincronizar config chatbot: %s", exc)
            db.rollback()
        # Conjuntos de demostración y datos por conjunto (idempotente).
        try:
            sembrar_conjuntos(db)
        except Exception as exc:  # noqa: BLE001 - el seed nunca debe tumbar la API
            logging.getLogger("app.seed").error("No se pudo sembrar los conjuntos: %s", exc)
            db.rollback()
        # Datos de demostración de los módulos nuevos (idempotente).
        try:
            from app.seed import sembrar_modulos_nuevos

            sembrar_modulos_nuevos(db)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("app.seed").error("No se pudo sembrar los módulos nuevos: %s", exc)
            db.rollback()
        # Asegurar que todos los documentos registrados tengan PDF/archivo descargable.
        try:
            from app.routers.documento import asegurar_archivos_documentos

            generados = asegurar_archivos_documentos(db)
            if generados:
                logging.getLogger("app.documentos").info(
                    "[documentos] Se generaron %d archivos PDF descargables.", generados
                )
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("app.documentos").error("No se pudieron asegurar los documentos: %s", exc)
            db.rollback()
        from app.chatbot import obtener_config_chatbot
        from app.ollama_client import ollama_base_url
        motor_cb, modelo_cb = obtener_config_chatbot(db)
        logging.getLogger("app.chatbot").info(
            "[chatbot] Motor=%s Modelo=%s OllamaURL=%s",
            motor_cb, modelo_cb, ollama_base_url(),
        )
    finally:
        db.close()

    # UH-01 / UH-25: avisos de asambleas a 48 h y cierre de votaciones.
    programador.iniciar()


@app.get("/")
def home():
    return {"mensaje": "Multi-Administrador API funcionando", "docs": "/docs"}


@app.get("/health")
def health():
    from app.email_config import diagnostico
    from app.routers.auth import _registro_admin_habilitado
    from app.ollama_client import ollama_base_url, ollama_modelo_defecto
    return {
        "status": "ok",
        "base_datos": {
            "motor": MOTOR,
            "destino": DATABASE_URL_ENMASCARADA,
            "aviso": AVISO_BD,
        },
        # Datos del SMTP sin exponer la contraseña: sirve para diagnosticar por qué
        # no llegan los correos (configurado, servidor, puerto, cifrado).
        "correo": diagnostico(),
        "chatbot": {
            "motor_env": (os.getenv("CHATBOT_ENGINE") or "ollama").strip().lower(),
            "ollama_url": ollama_base_url(),
            "ollama_model": ollama_modelo_defecto(),
        },
        "registro_admin_habilitado": _registro_admin_habilitado(),
    }
