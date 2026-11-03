-- ============================================================================
--  MULTI-ADMINISTRADOR · SCRIPT COMPLETO DE BASE DE DATOS (PostgreSQL 16)
--  Crea el esquema, las tablas, restricciones, índices y triggers.
--  Los datos iniciales (roles, admin, demo) los siembra el backend
--  automáticamente al arrancar (app/seed.py), para una única fuente de verdad.
--
--  Se ejecuta automáticamente desde /docker-entrypoint-initdb.d cuando el
--  volumen de PostgreSQL es nuevo.
-- ============================================================================

-- 1) Extensiones -------------------------------------------------------------
--  IMPORTANTE: aquí NINGUNA extensión es obligatoria. Antes se hacía
--  `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"` sin protección y en servidores
--  donde esa extensión no está compilada (PostgreSQL "slim", RDS, Supabase,
--  algunos hosting, o un Postgres instalado a mano) el script ABORTABA en la
--  primera línea y la base quedaba SIN NINGUNA TABLA: el backend arrancaba
--  pero todo fallaba ("la base de datos no funciona").
--  Ahora cada extensión se intenta dentro de un bloque que captura el error.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'uuid-ossp') THEN
        EXECUTE 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"';
        RAISE NOTICE 'Extensión "uuid-ossp" habilitada.';
    ELSE
        RAISE NOTICE 'Extensión "uuid-ossp" no disponible: se omite (no es obligatoria).';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'No se pudo habilitar "uuid-ossp" (%): se omite.', SQLERRM;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'pgcrypto') THEN
        EXECUTE 'CREATE EXTENSION IF NOT EXISTS "pgcrypto"';
        RAISE NOTICE 'Extensión "pgcrypto" habilitada.';
    ELSE
        RAISE NOTICE 'Extensión "pgcrypto" no disponible: se omite (las contraseñas se hashean en Python con bcrypt).';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'No se pudo habilitar "pgcrypto" (%): se omite.', SQLERRM;
END $$;

-- La extensión "vector" (pgvector) es OPCIONAL: solo se habilita si está instalada
-- en el servidor. Es necesaria únicamente si usas el chatbot con RAG vectorial;
-- el motor local del chatbot no la requiere. Se crea de forma condicional.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector') THEN
        EXECUTE 'CREATE EXTENSION IF NOT EXISTS vector';
        RAISE NOTICE 'Extensión "vector" (pgvector) habilitada.';
    ELSE
        RAISE NOTICE 'Extensión "vector" no instalada; se omite (no es obligatoria).';
    END IF;
END $$;

-- 2) Esquema y tablas --------------------------------------------------------

-- Roles
-- ---------------------------------------------------------------------------
-- CONJUNTOS / COPROPIEDADES (multi-administración, HU-07)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conjuntos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) UNIQUE NOT NULL,
    nit             VARCHAR(30),
    direccion       VARCHAR(200),
    ciudad          VARCHAR(80),
    telefono        VARCHAR(30),
    correo          VARCHAR(255),
    administrador   VARCHAR(150),
    habitantes      INTEGER DEFAULT 0,
    cuota           NUMERIC(12,2) DEFAULT 0,
    dia_cobro       INTEGER,
    reunion         VARCHAR(120),
    silencio        VARCHAR(60),
    logo            VARCHAR(500),
    -- Id de paleta ("azul", ...) o hexadecimal #RRGGBB. NULL = automático.
    color           VARCHAR(20),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roles (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(60) UNIQUE NOT NULL,
    descripcion VARCHAR(255),
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id                 SERIAL PRIMARY KEY,
    nombre             VARCHAR(150) NOT NULL,
    telefono           VARCHAR(30),
    correo             VARCHAR(255) UNIQUE NOT NULL,
    contrasena_hash    VARCHAR(255) NOT NULL,
    rol_id             INTEGER NOT NULL REFERENCES roles(id),
    activo             BOOLEAN DEFAULT TRUE,
    fecha_creacion     TIMESTAMP DEFAULT NOW(),
    ultimo_acceso      TIMESTAMP,
    id_copropiedad     INTEGER,
    id_conjunto        INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    token_recuperacion VARCHAR(255),
    expira_token       TIMESTAMP,
    codigo_recuperacion VARCHAR(6),
    correo_verificado  BOOLEAN NOT NULL DEFAULT FALSE,
    token_verificacion VARCHAR(255),
    expira_verificacion TIMESTAMP,
    codigo_verificacion VARCHAR(6),
    notificaciones_correo BOOLEAN NOT NULL DEFAULT TRUE,
    notificaciones_push   BOOLEAN NOT NULL DEFAULT TRUE
);
-- Migración idempotente para bases creadas antes de la verificación de correo
-- o antes del código de 6 dígitos (los modelos ya las declaran; si la tabla
-- venía de una versión anterior, se agregan aquí para no romper el registro).
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS correo_verificado  BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS token_verificacion VARCHAR(255);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS expira_verificacion TIMESTAMP;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_verificacion VARCHAR(6);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_recuperacion VARCHAR(6);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notificaciones_correo BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notificaciones_push   BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS id_conjunto INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS usuario_conjuntos (
    id           SERIAL PRIMARY KEY,
    usuario_id   INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    conjunto_id  INTEGER NOT NULL REFERENCES conjuntos(id) ON DELETE CASCADE
);

-- Residentes
CREATE TABLE IF NOT EXISTS residentes (
    id                  SERIAL PRIMARY KEY,
    usuario_id          INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    tipo                VARCHAR(20) DEFAULT 'propietario',
    identificacion      VARCHAR(30) UNIQUE NOT NULL,
    telefono_adicional  VARCHAR(30),
    contacto_emergencia VARCHAR(150),
    telefono_emergencia VARCHAR(30),
    activo              BOOLEAN DEFAULT TRUE,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    fecha_creacion      TIMESTAMP DEFAULT NOW()
);

-- Propiedades
CREATE TABLE IF NOT EXISTS propiedades (
    id            SERIAL PRIMARY KEY,
    residencial   VARCHAR(120) DEFAULT 'Conjunto Central',
    bloque        VARCHAR(30),
    torre         VARCHAR(30),
    apartamento   VARCHAR(30) NOT NULL,
    piso          INTEGER,
    area          NUMERIC(10,2),
    habitaciones  INTEGER DEFAULT 0,
    banos         INTEGER DEFAULT 0,
    parqueaderos  INTEGER DEFAULT 0,
    estado        VARCHAR(30) DEFAULT 'ocupado',
    estrato       INTEGER,
    residente_id  INTEGER REFERENCES residentes(id) ON DELETE SET NULL,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Conceptos financieros
CREATE TABLE IF NOT EXISTS conceptos_financieros (
    id            SERIAL PRIMARY KEY,
    codigo        VARCHAR(30) UNIQUE NOT NULL,
    nombre        VARCHAR(120) NOT NULL,
    tipo          VARCHAR(20) NOT NULL,
    monto_default NUMERIC(12,2) DEFAULT 0,
    recurrente    BOOLEAN DEFAULT FALSE,
    descripcion   VARCHAR(255)
);

-- Movimientos financieros
CREATE TABLE IF NOT EXISTS movimientos_financieros (
    id             SERIAL PRIMARY KEY,
    propiedad_id   INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
    concepto_id    INTEGER NOT NULL REFERENCES conceptos_financieros(id),
    monto          NUMERIC(12,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    fecha_pago     DATE,
    estado         VARCHAR(20) DEFAULT 'pendiente',
    numero_recibo  VARCHAR(50) UNIQUE,
    metodo_pago    VARCHAR(30),
    referencia     VARCHAR(100),
    notas          TEXT,
    creado_por     INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Tareas de mantenimiento
CREATE TABLE IF NOT EXISTS tareas_mantenimiento (
    id              SERIAL PRIMARY KEY,
    propiedad_id    INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
    residente_id    INTEGER REFERENCES residentes(id) ON DELETE SET NULL,
    titulo          VARCHAR(150) NOT NULL,
    descripcion     TEXT NOT NULL,
    prioridad       VARCHAR(20) DEFAULT 'media',
    estado          VARCHAR(30) DEFAULT 'pendiente',
    asignado_a      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    costo_estimado  NUMERIC(12,2),
    fecha_programada DATE,
    fecha_completada TIMESTAMP,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    fecha_creacion  TIMESTAMP DEFAULT NOW()
);

-- Documentos
CREATE TABLE IF NOT EXISTS documentos (
    id           SERIAL PRIMARY KEY,
    titulo       VARCHAR(255) NOT NULL,
    descripcion  TEXT,
    ruta_archivo VARCHAR(500) NOT NULL,
    tipo_documento VARCHAR(60),
    mime         VARCHAR(120),
    tamano       INTEGER,
    propiedad_id INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
    subido_por   INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    publico      BOOLEAN DEFAULT FALSE,
    version      INTEGER DEFAULT 1,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Eventos
CREATE TABLE IF NOT EXISTS eventos (
    id          SERIAL PRIMARY KEY,
    titulo      VARCHAR(150) NOT NULL,
    descripcion TEXT,
    fecha       DATE NOT NULL,
    lugar       VARCHAR(150),
    creado_por  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Configuración del sistema
CREATE TABLE IF NOT EXISTS configuraciones (
    id          SERIAL PRIMARY KEY,
    clave       VARCHAR(120) UNIQUE NOT NULL,
    valor       TEXT NOT NULL,
    descripcion VARCHAR(255),
    actualizado TIMESTAMP DEFAULT NOW()
);

-- Chatbot: sesiones y mensajes
CREATE TABLE IF NOT EXISTS sesiones_chat (
    id           SERIAL PRIMARY KEY,
    usuario_id   INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    titulo       VARCHAR(255) DEFAULT 'Nueva conversación',
    estado       VARCHAR(20) DEFAULT 'activa',
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mensajes_chat (
    id           SERIAL PRIMARY KEY,
    sesion_id    INTEGER NOT NULL REFERENCES sesiones_chat(id) ON DELETE CASCADE,
    rol          VARCHAR(20) NOT NULL,
    contenido    TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- 3) Índices estratégicos ----------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_usuarios_correo     ON usuarios(correo);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol        ON usuarios(rol_id);
CREATE INDEX IF NOT EXISTS idx_residentes_id       ON residentes(identificacion);
CREATE INDEX IF NOT EXISTS idx_propiedades_resi    ON propiedades(residente_id);
CREATE INDEX IF NOT EXISTS idx_propiedades_estado  ON propiedades(estado);
CREATE INDEX IF NOT EXISTS idx_mov_venc            ON movimientos_financieros(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_mov_estado          ON movimientos_financieros(estado);
CREATE INDEX IF NOT EXISTS idx_mant_estado         ON tareas_mantenimiento(estado);
CREATE INDEX IF NOT EXISTS idx_docs_publico        ON documentos(publico);
CREATE INDEX IF NOT EXISTS idx_chat_sesion_usuario ON sesiones_chat(usuario_id);
CREATE INDEX IF NOT EXISTS idx_chat_msg_sesion     ON mensajes_chat(sesion_id, fecha_creacion);
CREATE INDEX IF NOT EXISTS idx_conj_activo         ON conjuntos(activo);
CREATE INDEX IF NOT EXISTS idx_usuario_conjunto    ON usuario_conjuntos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_prop_conjunto       ON propiedades(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_res_conjunto        ON residentes(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_mov_conjunto        ON movimientos_financieros(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_mant_conjunto       ON tareas_mantenimiento(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_doc_conjunto        ON documentos(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_evento_conjunto     ON eventos(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_usuario_conjunto_ref ON usuario_conjuntos(conjunto_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_conjunto   ON usuarios(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_conjuntos_nombre    ON conjuntos(nombre);
-- Índice único tolerante: si la base vieja trae pares duplicados, se limpia
-- antes en lugar de abortar el script.
DO $$
BEGIN
    DELETE FROM usuario_conjuntos a
     USING usuario_conjuntos b
     WHERE a.ctid < b.ctid
       AND a.usuario_id = b.usuario_id
       AND a.conjunto_id = b.conjunto_id;
    CREATE UNIQUE INDEX IF NOT EXISTS uq_usuario_conjunto
        ON usuario_conjuntos(usuario_id, conjunto_id);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'No se pudo crear uq_usuario_conjunto (%): se omite.', SQLERRM;
END $$;

-- (Opcional) Índice vectorial para RAG cuando se use la extensión pgvector
-- CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding
--     ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 4) Triggers de actualización automática -----------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Creación idempotente del trigger (solo si no existe).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_configuraciones') THEN
        CREATE TRIGGER trg_configuraciones
            BEFORE UPDATE ON configuraciones
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
END $$;

-- 5) CONTROL DE ACCESO POR ROLES (RBAC) --------------------------------------
--  Tabla de permisos granulares y su asignación a cada rol.
--  Roles (IDs fijos, coinciden con el seed del backend):
--    1 = super_admin · 2 = admin · 3 = residente · 4 = tesoreria · 5 = seguridad

-- Garantiza que los roles existan (idempotente) para poder asignar permisos.
--  OJO: antes era `ON CONFLICT (id) DO NOTHING`, que fallaba con
--  "duplicate key value violates unique constraint roles_nombre_key" si en la
--  base ya existía un rol con el mismo nombre pero otro id. Sin destino, el
--  conflicto se resuelve por cualquier restricción única (id o nombre).
INSERT INTO roles (id, nombre, descripcion) VALUES
    (1, 'super_admin', 'Acceso total al sistema'),
    (2, 'admin',       'Administrador del conjunto'),
    (3, 'residente',   'Residente propietario o inquilino'),
    (4, 'tesoreria',   'Encargado de finanzas'),
    (5, 'seguridad',   'Personal de vigilancia')
ON CONFLICT DO NOTHING;

-- Catálogo de permisos (módulo + acción).
CREATE TABLE IF NOT EXISTS permisos (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(120) UNIQUE NOT NULL,
    modulo      VARCHAR(60) NOT NULL,
    accion      VARCHAR(30) NOT NULL,
    descripcion VARCHAR(255)
);

-- Bases creadas con versiones anteriores tenían codigo VARCHAR(60)/modulo
-- VARCHAR(40): se amplían para que coincidan con el modelo (evita errores de
-- "value too long for type character varying(60)" al sincronizar permisos.
ALTER TABLE permisos ALTER COLUMN codigo TYPE VARCHAR(120);
ALTER TABLE permisos ALTER COLUMN modulo TYPE VARCHAR(60);

-- Asignación N:M rol <-> permiso.
CREATE TABLE IF NOT EXISTS rol_permisos (
    rol_id     INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permiso_id INTEGER NOT NULL REFERENCES permisos(id) ON DELETE CASCADE,
    PRIMARY KEY (rol_id, permiso_id)
);

-- Insertar el catálogo de permisos (idempotente).
INSERT INTO permisos (codigo, modulo, accion, descripcion) VALUES
    ('dashboard.ver',      'dashboard', 'ver',      'Ver el panel de control'),
    ('reportes.ver',       'reportes',  'ver',      'Ver reportes y estadísticas'),
    ('usuarios.ver',       'usuarios',  'ver',      'Ver usuarios'),
    ('usuarios.crear',     'usuarios',  'crear',    'Crear usuarios'),
    ('usuarios.editar',    'usuarios',  'editar',   'Editar / activar-desactivar usuarios'),
    ('usuarios.eliminar',  'usuarios',  'eliminar', 'Eliminar usuarios'),
    ('residentes.ver',     'residentes','ver',      'Ver residentes'),
    ('residentes.crear',   'residentes','crear',    'Crear residentes'),
    ('residentes.editar',  'residentes','editar',   'Editar residentes'),
    ('residentes.eliminar','residentes','eliminar', 'Eliminar residentes'),
    ('propiedades.ver',    'propiedades','ver',     'Ver propiedades'),
    ('propiedades.crear',  'propiedades','crear',   'Crear propiedades'),
    ('propiedades.editar', 'propiedades','editar',  'Editar propiedades'),
    ('propiedades.eliminar','propiedades','eliminar','Eliminar propiedades'),
    ('finanzas.ver',       'finanzas',  'ver',      'Ver movimientos financieros'),
    ('finanzas.crear',     'finanzas',  'crear',    'Registrar movimientos'),
    ('finanzas.editar',    'finanzas',  'editar',   'Editar movimientos'),
    ('finanzas.eliminar',  'finanzas',  'eliminar', 'Eliminar movimientos'),
    ('mantenimiento.ver',  'mantenimiento','ver',   'Ver tareas de mantenimiento'),
    ('mantenimiento.crear','mantenimiento','crear', 'Crear tareas'),
    ('mantenimiento.editar','mantenimiento','editar','Editar / completar tareas'),
    ('mantenimiento.eliminar','mantenimiento','eliminar','Eliminar tareas'),
    ('documentos.ver',     'documentos','ver',      'Ver listado de documentos'),
    ('documentos.crear',   'documentos','crear',    'Subir documentos'),
    ('documentos.editar',  'documentos','editar',   'Editar documentos'),
    ('documentos.eliminar','documentos','eliminar', 'Eliminar documentos'),
    ('documentos.descargar','documentos','descargar','Descargar archivos'),
    ('eventos.ver',        'eventos',   'ver',      'Ver eventos'),
    ('eventos.crear',      'eventos',   'crear',    'Crear eventos'),
    ('eventos.editar',     'eventos',   'editar',   'Editar eventos'),
    ('eventos.eliminar',   'eventos',   'eliminar', 'Eliminar eventos'),
    ('config.ver',         'config',    'ver',      'Ver configuración del sistema'),
    ('config.editar',      'config',    'editar',   'Editar configuración'),
    ('chat.usar',          'chat',      'usar',     'Usar el chatbot / asistente'),
    ('sistema.respaldar',  'sistema',   'respaldar','Generar respaldo de la base de datos')
ON CONFLICT (codigo) DO NOTHING;

-- Asignación de permisos por rol (congruente con cada perfil de usuario).
-- NOTA: la fuente de verdad es backend/app/permisos.py (MATRIZ); el backend la
-- sincroniza al arrancar. Este bloque la replica para un despliegue limpio.
DO $$
DECLARE
    cod TEXT;
BEGIN
    -- super_admin: TODOS los permisos.
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT 1, id FROM permisos ON CONFLICT DO NOTHING;

    -- admin: ACCESO TOTAL, exactamente igual que el super_admin.
    -- (Antes se excluían 'usuarios.eliminar' y 'sistema.respaldar'.)
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT 2, id FROM permisos ON CONFLICT DO NOTHING;

    -- tesoreria: finanzas completas, reportes, lectura de propiedades/residentes/documentos y chatbot.
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT 4, id FROM permisos WHERE codigo IN (
        'dashboard.ver','reportes.ver',
        'finanzas.ver','finanzas.crear','finanzas.editar','finanzas.eliminar',
        'propiedades.ver','residentes.ver',
        'documentos.ver','documentos.descargar','chat.usar')
    ON CONFLICT DO NOTHING;

    -- residente: lectura de su conjunto + crear solicitudes de mantenimiento + chatbot.
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT 3, id FROM permisos WHERE codigo IN (
        'dashboard.ver','propiedades.ver','documentos.ver','documentos.descargar',
        'eventos.ver','mantenimiento.ver','mantenimiento.crear','chat.usar')
    ON CONFLICT DO NOTHING;

    -- seguridad: lectura operativa + reportar/actualizar mantenimientos + chatbot.
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT 5, id FROM permisos WHERE codigo IN (
        'dashboard.ver','propiedades.ver','residentes.ver',
        'mantenimiento.ver','mantenimiento.crear','mantenimiento.editar',
        'eventos.ver','documentos.ver','documentos.descargar','chat.usar')
    ON CONFLICT DO NOTHING;

    RAISE NOTICE 'Permisos por rol asignados correctamente (RBAC).';
END $$;

-- Índice para acelerar la consulta de permisos de un rol.
CREATE INDEX IF NOT EXISTS idx_rol_permisos_rol  ON rol_permisos(rol_id);
CREATE INDEX IF NOT EXISTS idx_permisos_modulo   ON permisos(modulo);

-- ============================================================================
--  NOTIFICACIONES REALES
--  Avisos persistentes por usuario + suscripciones Web Push (VAPID).
--  SQLAlchemy también las crea con create_all; están aquí para que una base
--  nueva tenga los índices y restricciones desde el principio.
-- ============================================================================
CREATE TABLE IF NOT EXISTS notificaciones (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE CASCADE,
    tipo            VARCHAR(40) NOT NULL,
    severidad       VARCHAR(10) NOT NULL DEFAULT 'media',
    titulo          VARCHAR(200) NOT NULL,
    mensaje         TEXT,
    url             VARCHAR(200),
    fecha           DATE,
    referencia      VARCHAR(160) NOT NULL,
    leida           BOOLEAN NOT NULL DEFAULT FALSE,
    descartada      BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_lectura   TIMESTAMP,
    enviada_correo  BOOLEAN NOT NULL DEFAULT FALSE,
    enviada_push    BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion  TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_notificacion_usuario_referencia UNIQUE (usuario_id, referencia)
);

CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(usuario_id, leida, descartada);
CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha   ON notificaciones(fecha_creacion);

CREATE TABLE IF NOT EXISTS push_suscripciones (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    endpoint        TEXT NOT NULL UNIQUE,
    p256dh          TEXT NOT NULL,
    auth            TEXT NOT NULL,
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
--  VERIFICACIÓN FINAL
--  Comprueba que TODAS las tablas quedaron creadas. Si algo falta, el script
--  termina con un error explícito (y PostgreSQL hará rollback de todo) en vez
--  de dejar una base a medias que hace fallar al backend sin explicación.
-- ============================================================================
DO $$
DECLARE
    faltantes TEXT;
BEGIN
    SELECT string_agg(t.nombre, ', ')
      INTO faltantes
      FROM (VALUES
            ('conjuntos'), ('roles'), ('usuarios'), ('usuario_conjuntos'),
            ('residentes'), ('propiedades'), ('conceptos_financieros'),
            ('movimientos_financieros'), ('tareas_mantenimiento'), ('documentos'),
            ('eventos'), ('configuraciones'), ('sesiones_chat'), ('mensajes_chat'),
            ('permisos'), ('rol_permisos'), ('notificaciones'), ('push_suscripciones')
           ) AS t(nombre)
     WHERE to_regclass('public.' || t.nombre) IS NULL;

    IF faltantes IS NOT NULL THEN
        RAISE EXCEPTION 'Base de datos incompleta: faltan las tablas %', faltantes;
    END IF;

    RAISE NOTICE '✔ Base de datos Multi-Administrador lista: 18 tablas, permisos y RBAC.';
END $$;

-- ============================================================================
--  FIN DEL SCRIPT
-- ============================================================================
