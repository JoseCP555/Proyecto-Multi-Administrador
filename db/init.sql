-- ============================================================================
--  MULTI-ADMINISTRADOR · ESQUEMA COMPLETO DE BASE DE DATOS (PostgreSQL 16)
--
--  Script único, idempotente y ordenado por módulos. Se puede ejecutar varias
--  veces sobre la misma base sin perder datos (CREATE ... IF NOT EXISTS,
--  ALTER ... IF NOT EXISTS, INSERT ... ON CONFLICT DO NOTHING).
--
--  Contenido:
--    0. Extensiones y funciones auxiliares
--    1. Núcleo: conjuntos, roles, usuarios y accesos
--    2. RBAC: permisos y permisos por rol
--    3. Residentes y propiedades
--    4. Finanzas: conceptos, movimientos y comprobantes de pago
--    5. Operación: mantenimiento, documentos, eventos y comunicados
--    6. Comunidad: PQRS, zonas comunes, reservas y visitantes
--    7. Gobierno: votaciones y solicitudes de aprobación del consejo
--    8. Comunicación: chatbot, mensajería directa y notificaciones
--    9. Configuración del sistema (tabla `configuraciones`)
--   10. Auditoría
--   11. Restricciones CHECK y llaves foráneas complementarias
--   12. Índices · 13. Triggers · 14. RBAC · 15. Documentación del esquema
--
--  Los datos de demostración (usuario admin, conjuntos, propiedades, etc.) los
--  siembra el backend al arrancar (app/seed.py). Aquí solo se cargan los datos
--  de referencia: roles, permisos y parámetros de configuración.
--
--  En Docker se ejecuta una sola vez, al crearse el volumen de PostgreSQL.
-- ============================================================================


-- ============================================================================
-- 0. EXTENSIONES Y FUNCIONES AUXILIARES
-- ============================================================================
-- Ninguna extensión es obligatoria: cada una se intenta de forma protegida para
-- que un servidor sin ellas (PostgreSQL "slim", RDS, Supabase...) no aborte el
-- script y deje la base sin tablas.
DO $$
DECLARE
    ext TEXT;
BEGIN
    FOREACH ext IN ARRAY ARRAY['uuid-ossp', 'pgcrypto', 'vector'] LOOP
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = ext) THEN
                EXECUTE format('CREATE EXTENSION IF NOT EXISTS %I', ext);
                RAISE NOTICE 'Extensión "%" habilitada.', ext;
            ELSE
                RAISE NOTICE 'Extensión "%" no disponible: se omite (no es obligatoria).', ext;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'No se pudo habilitar "%" (%): se omite.', ext, SQLERRM;
        END;
    END LOOP;
END $$;

-- Función genérica: mantiene al día la columna `actualizado` / `fecha_actualizacion`.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION set_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 1. NÚCLEO: CONJUNTOS, ROLES, USUARIOS Y ACCESOS
-- ============================================================================

-- Conjuntos / copropiedades gestionados por la plataforma (multi-administración).
-- Casi todas las demás tablas cuelgan de aquí mediante `id_conjunto`.
CREATE TABLE IF NOT EXISTS conjuntos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL UNIQUE,
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
    color           VARCHAR(20),                     -- id de paleta o #RRGGBB; NULL = automático
    umbral_gasto    NUMERIC(12,2) DEFAULT 2000000,   -- gasto que dispara alerta al consejo
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP DEFAULT NOW()
);
ALTER TABLE conjuntos ADD COLUMN IF NOT EXISTS color        VARCHAR(20);
ALTER TABLE conjuntos ADD COLUMN IF NOT EXISTS umbral_gasto NUMERIC(12,2) DEFAULT 2000000;

-- Roles del sistema (IDs fijos: 1 super_admin · 2 admin · 3 residente · 4 tesoreria · 5 seguridad).
CREATE TABLE IF NOT EXISTS roles (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(60) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    created_at  TIMESTAMP DEFAULT NOW()
);

INSERT INTO roles (id, nombre, descripcion) VALUES
    (1, 'super_admin', 'Acceso total al sistema'),
    (2, 'admin',       'Administrador del conjunto'),
    (3, 'residente',   'Residente propietario o inquilino'),
    (4, 'tesoreria',   'Encargado de finanzas'),
    (5, 'seguridad',   'Personal de vigilancia')
ON CONFLICT DO NOTHING;
SELECT setval(pg_get_serial_sequence('roles', 'id'), GREATEST((SELECT MAX(id) FROM roles), 5));

-- Usuarios de la plataforma.
CREATE TABLE IF NOT EXISTS usuarios (
    id                    SERIAL PRIMARY KEY,
    nombre                VARCHAR(150) NOT NULL,
    telefono              VARCHAR(30),
    correo                VARCHAR(255) NOT NULL UNIQUE,
    contrasena_hash       VARCHAR(255) NOT NULL,
    foto                  TEXT,                                   -- data URI o URL
    rol_id                INTEGER NOT NULL REFERENCES roles(id),
    id_conjunto           INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,  -- contexto por defecto
    id_copropiedad        INTEGER,                                -- heredado; lo usa el backend
    activo                BOOLEAN DEFAULT TRUE,
    -- Recuperación de contraseña
    token_recuperacion    VARCHAR(255),
    expira_token          TIMESTAMP,
    codigo_recuperacion   VARCHAR(6),
    -- Verificación de correo
    correo_verificado     BOOLEAN NOT NULL DEFAULT FALSE,
    token_verificacion    VARCHAR(255),
    expira_verificacion   TIMESTAMP,
    codigo_verificacion   VARCHAR(6),
    -- Preferencias de notificación
    notificaciones_correo BOOLEAN NOT NULL DEFAULT TRUE,
    notificaciones_push   BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion        TIMESTAMP DEFAULT NOW(),
    ultimo_acceso         TIMESTAMP
);
-- Migraciones idempotentes para bases creadas con versiones anteriores.
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto                  TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS id_conjunto           INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS correo_verificado     BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS token_verificacion    VARCHAR(255);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS expira_verificacion   TIMESTAMP;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_verificacion   VARCHAR(6);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_recuperacion   VARCHAR(6);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notificaciones_correo BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS notificaciones_push   BOOLEAN NOT NULL DEFAULT TRUE;

-- Conjuntos a cargo de cada usuario (relación N:M).
CREATE TABLE IF NOT EXISTS usuario_conjuntos (
    id          SERIAL PRIMARY KEY,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id)  ON DELETE CASCADE,
    conjunto_id INTEGER NOT NULL REFERENCES conjuntos(id) ON DELETE CASCADE
);


-- ============================================================================
-- 2. RBAC: PERMISOS Y PERMISOS POR ROL
-- ============================================================================
-- La fuente de verdad es backend/app/permisos.py (MATRIZ); el backend la
-- sincroniza al arrancar. Este bloque la replica para un despliegue limpio.
CREATE TABLE IF NOT EXISTS permisos (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(120) NOT NULL UNIQUE,
    modulo      VARCHAR(60)  NOT NULL,
    accion      VARCHAR(30)  NOT NULL,
    descripcion VARCHAR(255)
);
ALTER TABLE permisos ALTER COLUMN codigo TYPE VARCHAR(120);
ALTER TABLE permisos ALTER COLUMN modulo TYPE VARCHAR(60);

CREATE TABLE IF NOT EXISTS rol_permisos (
    rol_id     INTEGER NOT NULL REFERENCES roles(id)    ON DELETE CASCADE,
    permiso_id INTEGER NOT NULL REFERENCES permisos(id) ON DELETE CASCADE,
    PRIMARY KEY (rol_id, permiso_id)
);


-- ============================================================================
-- 3. RESIDENTES Y PROPIEDADES
-- ============================================================================
CREATE TABLE IF NOT EXISTS residentes (
    id                  SERIAL PRIMARY KEY,
    usuario_id          INTEGER REFERENCES usuarios(id)  ON DELETE SET NULL,
    id_conjunto         INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    tipo                VARCHAR(20) DEFAULT 'propietario',      -- propietario | inquilino
    identificacion      VARCHAR(30) NOT NULL UNIQUE,
    telefono_adicional  VARCHAR(30),
    contacto_emergencia VARCHAR(150),
    telefono_emergencia VARCHAR(30),
    activo              BOOLEAN DEFAULT TRUE,
    fecha_creacion      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS propiedades (
    id             SERIAL PRIMARY KEY,
    id_conjunto    INTEGER REFERENCES conjuntos(id)  ON DELETE SET NULL,
    residente_id   INTEGER REFERENCES residentes(id) ON DELETE SET NULL,
    residencial    VARCHAR(120) DEFAULT 'Conjunto Central',
    bloque         VARCHAR(30),
    torre          VARCHAR(30),
    apartamento    VARCHAR(30) NOT NULL,
    piso           INTEGER,
    area           NUMERIC(10,2),
    habitaciones   INTEGER DEFAULT 0,
    banos          INTEGER DEFAULT 0,
    parqueaderos   INTEGER DEFAULT 0,
    estado         VARCHAR(30) DEFAULT 'ocupado',      -- ocupado | vacio | mantenimiento | arrendado
    estrato        INTEGER,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);


-- ============================================================================
-- 4. FINANZAS
-- ============================================================================
CREATE TABLE IF NOT EXISTS conceptos_financieros (
    id            SERIAL PRIMARY KEY,
    codigo        VARCHAR(30)  NOT NULL UNIQUE,
    nombre        VARCHAR(120) NOT NULL,
    tipo          VARCHAR(20)  NOT NULL,               -- ingreso | gasto
    monto_default NUMERIC(12,2) DEFAULT 0,
    recurrente    BOOLEAN DEFAULT FALSE,
    descripcion   VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS movimientos_financieros (
    id                SERIAL PRIMARY KEY,
    id_conjunto       INTEGER REFERENCES conjuntos(id)   ON DELETE SET NULL,
    propiedad_id      INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
    concepto_id       INTEGER NOT NULL REFERENCES conceptos_financieros(id),
    monto             NUMERIC(12,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    fecha_pago        DATE,
    estado            VARCHAR(20) DEFAULT 'pendiente', -- pendiente | pagado | vencido | cancelado
    numero_recibo     VARCHAR(50) UNIQUE,
    metodo_pago       VARCHAR(30),
    referencia        VARCHAR(100),
    notas             TEXT,
    creado_por        INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha_creacion    TIMESTAMP DEFAULT NOW()
);

-- Comprobantes de pago que sube el residente y revisa tesorería.
CREATE TABLE IF NOT EXISTS comprobantes_pago (
    id             SERIAL PRIMARY KEY,
    id_conjunto    INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    movimiento_id  INTEGER REFERENCES movimientos_financieros(id) ON DELETE SET NULL,
    periodo        VARCHAR(30),                         -- ej. 2026-11
    monto          NUMERIC(12,2) NOT NULL,
    ruta_archivo   VARCHAR(500) NOT NULL,
    nombre_archivo VARCHAR(255),
    mime           VARCHAR(120),
    tamano         INTEGER,
    estado         VARCHAR(20) NOT NULL DEFAULT 'en_revision',  -- en_revision | aprobado | rechazado
    observacion    TEXT,
    revisado_por   INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha_revision TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);


-- ============================================================================
-- 5. OPERACIÓN: MANTENIMIENTO, DOCUMENTOS, EVENTOS Y COMUNICADOS
-- ============================================================================
CREATE TABLE IF NOT EXISTS tareas_mantenimiento (
    id               SERIAL PRIMARY KEY,
    id_conjunto      INTEGER REFERENCES conjuntos(id)   ON DELETE SET NULL,
    propiedad_id     INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
    residente_id     INTEGER REFERENCES residentes(id)  ON DELETE SET NULL,
    asignado_a       INTEGER REFERENCES usuarios(id)    ON DELETE SET NULL,
    titulo           VARCHAR(150) NOT NULL,
    descripcion      TEXT NOT NULL,
    categoria        VARCHAR(30) DEFAULT 'unidad',      -- zona_comun | unidad | otro
    evidencias       TEXT,                              -- archivos separados por coma
    prioridad        VARCHAR(20) DEFAULT 'media',       -- baja | media | alta | critica
    estado           VARCHAR(30) DEFAULT 'pendiente',   -- pendiente | en_proceso | completada | rechazada
    costo_estimado   NUMERIC(12,2),
    fecha_programada DATE,
    fecha_completada TIMESTAMP,
    fecha_creacion   TIMESTAMP DEFAULT NOW()
);
ALTER TABLE tareas_mantenimiento ADD COLUMN IF NOT EXISTS categoria  VARCHAR(30) DEFAULT 'unidad';
ALTER TABLE tareas_mantenimiento ADD COLUMN IF NOT EXISTS evidencias TEXT;

CREATE TABLE IF NOT EXISTS documentos (
    id             SERIAL PRIMARY KEY,
    id_conjunto    INTEGER REFERENCES conjuntos(id)   ON DELETE SET NULL,
    propiedad_id   INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
    subido_por     INTEGER REFERENCES usuarios(id)    ON DELETE SET NULL,
    titulo         VARCHAR(255) NOT NULL,
    descripcion    TEXT,
    ruta_archivo   VARCHAR(500) NOT NULL,
    tipo_documento VARCHAR(60),
    mime           VARCHAR(120),
    tamano         INTEGER,
    publico        BOOLEAN DEFAULT FALSE,
    version        INTEGER DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eventos (
    id             SERIAL PRIMARY KEY,
    id_conjunto    INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    creado_por     INTEGER REFERENCES usuarios(id)  ON DELETE SET NULL,
    titulo         VARCHAR(150) NOT NULL,
    descripcion    TEXT,
    fecha          DATE NOT NULL,
    hora           VARCHAR(5),                          -- HH:MM
    tipo           VARCHAR(30) DEFAULT 'actividad',     -- asamblea | reunion | actividad | mantenimiento
    lugar          VARCHAR(150),
    notificado_48h BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);
ALTER TABLE eventos ADD COLUMN IF NOT EXISTS hora           VARCHAR(5);
ALTER TABLE eventos ADD COLUMN IF NOT EXISTS tipo           VARCHAR(30) DEFAULT 'actividad';
ALTER TABLE eventos ADD COLUMN IF NOT EXISTS notificado_48h BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS comunicados (
    id             SERIAL PRIMARY KEY,
    id_conjunto    INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    enviado_por    INTEGER REFERENCES usuarios(id)  ON DELETE SET NULL,
    titulo         VARCHAR(200) NOT NULL,
    contenido      TEXT NOT NULL,
    categoria      VARCHAR(30) DEFAULT 'informativo',   -- informativo | normas | evento | urgente
    prioridad      VARCHAR(10) NOT NULL DEFAULT 'media',-- alta | media | baja
    fijado         BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);


-- ============================================================================
-- 6. COMUNIDAD: PQRS, ZONAS COMUNES, RESERVAS Y VISITANTES
-- ============================================================================
CREATE TABLE IF NOT EXISTS pqrs (
    id                  SERIAL PRIMARY KEY,
    id_conjunto         INTEGER REFERENCES conjuntos(id)  ON DELETE SET NULL,
    radicado            VARCHAR(30) NOT NULL UNIQUE,
    usuario_id          INTEGER REFERENCES usuarios(id)   ON DELETE SET NULL,
    residente_id        INTEGER REFERENCES residentes(id) ON DELETE SET NULL,
    tipo                VARCHAR(20) NOT NULL,           -- peticion | queja | reclamo | sugerencia
    categoria           VARCHAR(40) NOT NULL,           -- zonas_comunes | administracion | convivencia | finanzas | otra
    asunto              VARCHAR(200) NOT NULL,
    descripcion         TEXT NOT NULL,
    adjunto             VARCHAR(500),
    estado              VARCHAR(20) NOT NULL DEFAULT 'pendiente',  -- pendiente | en_proceso | cerrada
    respuesta           TEXT,
    respondido_por      INTEGER REFERENCES usuarios(id)   ON DELETE SET NULL,
    fecha_respuesta     TIMESTAMP,
    fecha_creacion      TIMESTAMP DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS zonas_comunes (
    id                  SERIAL PRIMARY KEY,
    id_conjunto         INTEGER REFERENCES conjuntos(id) ON DELETE CASCADE,
    nombre              VARCHAR(120) NOT NULL,
    descripcion         TEXT,
    capacidad           INTEGER DEFAULT 20,
    hora_apertura       VARCHAR(5) DEFAULT '08:00',
    hora_cierre         VARCHAR(5) DEFAULT '22:00',
    requiere_aprobacion BOOLEAN NOT NULL DEFAULT TRUE,
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reservas_zonas (
    id              SERIAL PRIMARY KEY,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    zona_id         INTEGER NOT NULL REFERENCES zonas_comunes(id) ON DELETE CASCADE,
    usuario_id      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha           DATE NOT NULL,
    hora_inicio     VARCHAR(5) NOT NULL,
    hora_fin        VARCHAR(5) NOT NULL,
    motivo          VARCHAR(255),
    asistentes      INTEGER DEFAULT 1,
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente',  -- pendiente | aprobada | rechazada | cancelada
    motivo_decision VARCHAR(255),
    decidido_por    INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha_decision  TIMESTAMP,
    fecha_creacion  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS visitantes (
    id             SERIAL PRIMARY KEY,
    id_conjunto    INTEGER REFERENCES conjuntos(id)  ON DELETE SET NULL,
    residente_id   INTEGER REFERENCES residentes(id) ON DELETE SET NULL,
    registrado_por INTEGER REFERENCES usuarios(id)   ON DELETE SET NULL,
    nombre         VARCHAR(150) NOT NULL,
    documento      VARCHAR(30)  NOT NULL,
    telefono       VARCHAR(30),
    apartamento    VARCHAR(30)  NOT NULL,
    motivo         VARCHAR(200),
    observaciones  TEXT,
    hora_ingreso   TIMESTAMP NOT NULL DEFAULT NOW(),
    hora_salida    TIMESTAMP,
    estado         VARCHAR(20) NOT NULL DEFAULT 'dentro',      -- dentro | salio
    fecha_creacion TIMESTAMP DEFAULT NOW()
);


-- ============================================================================
-- 7. GOBIERNO: VOTACIONES Y SOLICITUDES DE APROBACIÓN DEL CONSEJO
-- ============================================================================
CREATE TABLE IF NOT EXISTS votaciones (
    id             SERIAL PRIMARY KEY,
    id_conjunto    INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    creado_por     INTEGER REFERENCES usuarios(id)  ON DELETE SET NULL,
    titulo         VARCHAR(200) NOT NULL,
    descripcion    TEXT,
    fecha_cierre   DATE NOT NULL,
    estado         VARCHAR(20) NOT NULL DEFAULT 'abierta',     -- abierta | cerrada
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS votacion_opciones (
    id          SERIAL PRIMARY KEY,
    votacion_id INTEGER NOT NULL REFERENCES votaciones(id) ON DELETE CASCADE,
    texto       VARCHAR(200) NOT NULL,
    orden       INTEGER DEFAULT 0
);

-- Un voto por miembro del consejo y votación.
CREATE TABLE IF NOT EXISTS votos (
    id             SERIAL PRIMARY KEY,
    votacion_id    INTEGER NOT NULL REFERENCES votaciones(id)        ON DELETE CASCADE,
    opcion_id      INTEGER NOT NULL REFERENCES votacion_opciones(id) ON DELETE CASCADE,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id)          ON DELETE CASCADE,
    fecha_creacion TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_voto_votacion_usuario UNIQUE (votacion_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS solicitudes_aprobacion (
    id              SERIAL PRIMARY KEY,
    id_conjunto     INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    creado_por      INTEGER REFERENCES usuarios(id)  ON DELETE SET NULL,
    decidido_por    INTEGER REFERENCES usuarios(id)  ON DELETE SET NULL,
    titulo          VARCHAR(200) NOT NULL,
    descripcion     TEXT NOT NULL,
    monto           NUMERIC(12,2) NOT NULL DEFAULT 0,
    categoria       VARCHAR(40) DEFAULT 'gasto',        -- gasto | contrato | presupuesto | otro
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente',  -- pendiente | aprobada | rechazada
    fecha_decision  TIMESTAMP,
    motivo_decision TEXT,
    fecha_creacion  TIMESTAMP DEFAULT NOW()
);


-- ============================================================================
-- 8. COMUNICACIÓN: CHATBOT, MENSAJERÍA DIRECTA Y NOTIFICACIONES
-- ============================================================================
CREATE TABLE IF NOT EXISTS sesiones_chat (
    id             SERIAL PRIMARY KEY,
    id_conjunto    INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    usuario_id     INTEGER REFERENCES usuarios(id)  ON DELETE SET NULL,
    titulo         VARCHAR(255) DEFAULT 'Nueva conversación',
    estado         VARCHAR(20)  DEFAULT 'activa',       -- activa | cerrada
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mensajes_chat (
    id             SERIAL PRIMARY KEY,
    sesion_id      INTEGER NOT NULL REFERENCES sesiones_chat(id) ON DELETE CASCADE,
    rol            VARCHAR(20) NOT NULL,                -- usuario | asistente | sistema
    contenido      TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversaciones_directas (
    id                   SERIAL PRIMARY KEY,
    id_conjunto          INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    residente_usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    asunto               VARCHAR(200) NOT NULL DEFAULT 'Chat con Administración',
    estado               VARCHAR(20)  NOT NULL DEFAULT 'abierta',  -- abierta | resuelta
    ultimo_mensaje       TEXT,
    ultimo_mensaje_en    TIMESTAMP,
    ultimo_remitente_id  INTEGER,
    ultimo_remitente_rol VARCHAR(20),                   -- residente | admin
    fecha_creacion       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mensajes_directos (
    id              SERIAL PRIMARY KEY,
    conversacion_id INTEGER NOT NULL REFERENCES conversaciones_directas(id) ON DELETE CASCADE,
    remitente_id    INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    rol_remitente   VARCHAR(20) NOT NULL,               -- residente | admin
    contenido       TEXT NOT NULL,
    adjunto         VARCHAR(500),
    adjunto_nombre  VARCHAR(255),
    adjunto_mime    VARCHAR(120),
    leido           BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_lectura   TIMESTAMP,
    fecha_creacion  TIMESTAMP DEFAULT NOW()
);

-- Avisos persistentes por usuario; `referencia` evita duplicados del mismo evento.
CREATE TABLE IF NOT EXISTS notificaciones (
    id             SERIAL PRIMARY KEY,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id)  ON DELETE CASCADE,
    id_conjunto    INTEGER REFERENCES conjuntos(id) ON DELETE CASCADE,
    tipo           VARCHAR(40)  NOT NULL,               -- mora | proximo | evento | mantenimiento | ...
    severidad      VARCHAR(10)  NOT NULL DEFAULT 'media',  -- alta | media | baja
    titulo         VARCHAR(200) NOT NULL,
    mensaje        TEXT,
    url            VARCHAR(200),
    fecha          DATE,
    referencia     VARCHAR(160) NOT NULL,
    leida          BOOLEAN NOT NULL DEFAULT FALSE,
    descartada     BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_lectura  TIMESTAMP,
    enviada_correo BOOLEAN NOT NULL DEFAULT FALSE,
    enviada_push   BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_notificacion_usuario_referencia UNIQUE (usuario_id, referencia)
);

-- Suscripciones Web Push (VAPID) de cada navegador.
CREATE TABLE IF NOT EXISTS push_suscripciones (
    id             SERIAL PRIMARY KEY,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    endpoint       TEXT NOT NULL UNIQUE,
    p256dh         TEXT NOT NULL,
    auth           TEXT NOT NULL,
    activa         BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);


-- ============================================================================
-- 9. CONFIGURACIÓN DEL SISTEMA  (tabla `configuraciones`)
-- ============================================================================
-- Almacén clave/valor de TODOS los parámetros editables desde el panel de
-- Configuración. Cada fila tiene:
--   categoria    agrupa los parámetros en la pantalla (general, finanzas, ...)
--   tipo         cómo interpretar `valor`: texto | numero | booleano | json
--   id_conjunto  NULL = parámetro global; con valor = sobreescribe el global
--                solo para ese conjunto (ver función fn_config).
--   editable     FALSE = informativo, no se modifica desde el panel.
CREATE TABLE IF NOT EXISTS configuraciones (
    id          SERIAL PRIMARY KEY,
    clave       VARCHAR(120) NOT NULL,
    valor       TEXT NOT NULL,
    descripcion VARCHAR(255),
    categoria   VARCHAR(40) NOT NULL DEFAULT 'general',
    tipo        VARCHAR(20) NOT NULL DEFAULT 'texto',
    id_conjunto INTEGER REFERENCES conjuntos(id) ON DELETE CASCADE,
    editable    BOOLEAN NOT NULL DEFAULT TRUE,
    actualizado TIMESTAMP DEFAULT NOW()
);

-- Migración de bases anteriores (la tabla antigua solo tenía clave/valor/descripcion).
ALTER TABLE configuraciones ADD COLUMN IF NOT EXISTS categoria   VARCHAR(40) NOT NULL DEFAULT 'general';
ALTER TABLE configuraciones ADD COLUMN IF NOT EXISTS tipo        VARCHAR(20) NOT NULL DEFAULT 'texto';
ALTER TABLE configuraciones ADD COLUMN IF NOT EXISTS id_conjunto INTEGER REFERENCES conjuntos(id) ON DELETE CASCADE;
ALTER TABLE configuraciones ADD COLUMN IF NOT EXISTS editable    BOOLEAN NOT NULL DEFAULT TRUE;

-- La clave ya no es única por sí sola: puede repetirse una vez por conjunto.
ALTER TABLE configuraciones DROP CONSTRAINT IF EXISTS configuraciones_clave_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_config_global
    ON configuraciones (clave) WHERE id_conjunto IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_config_conjunto
    ON configuraciones (clave, id_conjunto) WHERE id_conjunto IS NOT NULL;

-- Parámetros globales de referencia (solo se insertan si no existen; nunca pisan
-- lo que el administrador ya haya personalizado).
INSERT INTO configuraciones (clave, valor, descripcion, categoria, tipo) VALUES
    -- General
    ('company_name',              'Multi-Administrador S.A.S.', 'Nombre de la empresa administradora',                 'general',        'texto'),
    ('currency',                  'COP',                        'Moneda (pesos colombianos)',                          'general',        'texto'),
    ('timezone',                  'America/Bogota',             'Zona horaria del sistema',                            'general',        'texto'),
    -- Finanzas
    ('interest_rate_late',        '0.02',                       'Interés mensual por mora',                            'finanzas',       'numero'),
    -- Seguridad
    ('session_expire_minutes',    '30',                         'Minutos de vigencia de la sesión',                    'seguridad',      'numero'),
    ('max_login_attempts',        '5',                          'Intentos de inicio de sesión antes de bloquear',      'seguridad',      'numero'),
    ('login_lockout_minutes',     '10',                         'Minutos de bloqueo tras exceder los intentos',        'seguridad',      'numero'),
    ('email_verification_hours',  '24',                         'Horas de vigencia del enlace de verificación',        'seguridad',      'numero'),
    -- Archivos
    ('max_upload_documento_mb',   '20',                         'Tamaño máximo de documentos (MB)',                    'archivos',       'numero'),
    ('max_upload_pago_mb',        '10',                         'Tamaño máximo de comprobantes de pago (MB)',          'archivos',       'numero'),
    ('max_upload_adjunto_mb',     '10',                         'Tamaño máximo de adjuntos del chat (MB)',             'archivos',       'numero'),
    ('max_upload_foto_mb',        '2',                          'Tamaño máximo de foto de perfil (MB)',                'archivos',       'numero'),
    ('max_upload_logo_mb',        '2',                          'Tamaño máximo del logo del conjunto (MB)',            'archivos',       'numero'),
    -- Notificaciones
    ('notificaciones_correo',     'true',                       'Envío de notificaciones por correo (global)',         'notificaciones', 'booleano'),
    ('scheduler_interval_seconds','1800',                       'Cada cuántos segundos corre el programador',          'notificaciones', 'numero'),
    ('event_reminder_hours',      '48',                         'Horas de anticipación del aviso de eventos',          'notificaciones', 'numero'),
    -- Chatbot
    ('chatbot_engine',            'ollama',                     'Motor del chatbot (ollama o local)',                  'chatbot',        'texto'),
    ('ollama_model',              'llama3.2:3b',                'Modelo de Ollama para el chatbot',                    'chatbot',        'texto')
ON CONFLICT (clave) WHERE id_conjunto IS NULL DO NOTHING;

-- Ordena en categorías los parámetros que ya existían en bases anteriores.
UPDATE configuraciones SET categoria = 'finanzas' WHERE categoria = 'general' AND clave IN ('interest_rate_late');
UPDATE configuraciones SET categoria = 'chatbot'  WHERE categoria = 'general' AND clave IN ('chatbot_engine', 'ollama_model');
UPDATE configuraciones SET tipo = 'numero'   WHERE tipo = 'texto' AND clave IN ('interest_rate_late');

-- Devuelve el valor de un parámetro: primero el del conjunto, si no existe el global.
--   SELECT fn_config('interest_rate_late', 3);
CREATE OR REPLACE FUNCTION fn_config(p_clave TEXT, p_conjunto INTEGER DEFAULT NULL)
RETURNS TEXT AS $$
    SELECT valor
      FROM configuraciones
     WHERE clave = p_clave
       AND (id_conjunto = p_conjunto OR id_conjunto IS NULL)
     ORDER BY (id_conjunto IS NULL)      -- primero el específico del conjunto
     LIMIT 1;
$$ LANGUAGE sql STABLE;


-- ============================================================================
-- 10. AUDITORÍA
-- ============================================================================
-- Historial de acciones. Solo se consulta desde la aplicación (no hay DELETE).
CREATE TABLE IF NOT EXISTS auditoria (
    id             SERIAL PRIMARY KEY,
    usuario_id     INTEGER REFERENCES usuarios(id)  ON DELETE SET NULL,
    id_conjunto    INTEGER REFERENCES conjuntos(id) ON DELETE SET NULL,
    usuario_nombre VARCHAR(150),
    usuario_rol    VARCHAR(60),
    accion         VARCHAR(30) NOT NULL,                -- crear | editar | eliminar | login | logout | consultar
    modulo         VARCHAR(60) NOT NULL,
    metodo         VARCHAR(10),
    ruta           VARCHAR(255),
    entidad        VARCHAR(80),
    entidad_id     INTEGER,
    detalle        TEXT,
    ip             VARCHAR(60),
    estado_http    INTEGER,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);


-- ============================================================================
-- 11. RESTRICCIONES DE INTEGRIDAD (CHECK)
-- ============================================================================
-- Cada restricción se agrega de forma protegida: si una base antigua trae datos
-- que no la cumplen, se avisa con NOTICE y se continúa (no aborta el script).
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM (VALUES
        ('conjuntos',               'ck_conjuntos_dia_cobro',   'dia_cobro IS NULL OR dia_cobro BETWEEN 1 AND 31'),
        ('conjuntos',               'ck_conjuntos_cuota',       'cuota IS NULL OR cuota >= 0'),
        ('conjuntos',               'ck_conjuntos_habitantes',  'habitantes IS NULL OR habitantes >= 0'),
        ('residentes',              'ck_residentes_tipo',       $c$tipo IN ('propietario','inquilino')$c$),
        ('propiedades',             'ck_propiedades_estado',    $c$estado IN ('ocupado','vacio','mantenimiento','arrendado')$c$),
        ('propiedades',             'ck_propiedades_estrato',   'estrato IS NULL OR estrato BETWEEN 1 AND 6'),
        ('conceptos_financieros',   'ck_conceptos_tipo',        $c$tipo IN ('ingreso','gasto')$c$),
        ('movimientos_financieros', 'ck_movimientos_estado',    $c$estado IN ('pendiente','pagado','vencido','cancelado')$c$),
        ('movimientos_financieros', 'ck_movimientos_monto',     'monto >= 0'),
        ('comprobantes_pago',       'ck_comprobantes_estado',   $c$estado IN ('en_revision','aprobado','rechazado')$c$),
        ('tareas_mantenimiento',    'ck_tareas_prioridad',      $c$prioridad IN ('baja','media','alta','critica')$c$),
        ('tareas_mantenimiento',    'ck_tareas_estado',         $c$estado IN ('pendiente','en_proceso','completada','rechazada')$c$),
        ('comunicados',             'ck_comunicados_prioridad', $c$prioridad IN ('alta','media','baja')$c$),
        ('pqrs',                    'ck_pqrs_tipo',             $c$tipo IN ('peticion','queja','reclamo','sugerencia')$c$),
        ('pqrs',                    'ck_pqrs_estado',           $c$estado IN ('pendiente','en_proceso','cerrada')$c$),
        ('reservas_zonas',          'ck_reservas_estado',       $c$estado IN ('pendiente','aprobada','rechazada','cancelada')$c$),
        ('visitantes',              'ck_visitantes_estado',     $c$estado IN ('dentro','salio')$c$),
        ('votaciones',              'ck_votaciones_estado',     $c$estado IN ('abierta','cerrada')$c$),
        ('solicitudes_aprobacion',  'ck_solicitudes_estado',    $c$estado IN ('pendiente','aprobada','rechazada')$c$),
        ('notificaciones',          'ck_notificaciones_severidad', $c$severidad IN ('alta','media','baja')$c$),
        ('configuraciones',         'ck_config_tipo',           $c$tipo IN ('texto','numero','booleano','json')$c$)
    ) AS t(tabla, nombre, expr)
    LOOP
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = r.nombre) THEN
                EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I CHECK (%s)', r.tabla, r.nombre, r.expr);
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'No se pudo crear %: % (se omite)', r.nombre, SQLERRM;
        END;
    END LOOP;
END $$;

-- Pares usuario-conjunto duplicados en bases viejas: se limpian antes del índice único.
DO $$
BEGIN
    DELETE FROM usuario_conjuntos a USING usuario_conjuntos b
     WHERE a.ctid < b.ctid AND a.usuario_id = b.usuario_id AND a.conjunto_id = b.conjunto_id;
    CREATE UNIQUE INDEX IF NOT EXISTS uq_usuario_conjunto ON usuario_conjuntos (usuario_id, conjunto_id);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'No se pudo crear uq_usuario_conjunto (%): se omite.', SQLERRM;
END $$;


-- ============================================================================
-- 11B. LLAVES FORÁNEAS COMPLEMENTARIAS
-- ============================================================================
-- Columnas que guardaban un id de otra tabla sin estar conectadas formalmente.
-- Con la FK aparecen en el diagrama ER (DBeaver / pgAdmin) y la base garantiza
-- que el valor exista. Si una base antigua trae valores huérfanos, la FK se crea
-- igualmente con NOT VALID: protege los datos nuevos sin tocar los existentes.
--
--   usuarios.id_copropiedad                 -> conjuntos.id  (campo heredado: mismo concepto que id_conjunto)
--   conversaciones_directas.ultimo_remitente_id -> usuarios.id (quién escribió el último mensaje)
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM (VALUES
        ('usuarios',                'fk_usuarios_copropiedad',      'id_copropiedad',      'conjuntos'),
        ('conversaciones_directas', 'fk_convdirectas_ult_remitente','ultimo_remitente_id',  'usuarios')
    ) AS t(tabla, nombre, columna, destino)
    LOOP
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = r.nombre) THEN
            CONTINUE;
        END IF;
        BEGIN
            EXECUTE format(
                'ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(id) ON DELETE SET NULL',
                r.tabla, r.nombre, r.columna, r.destino);
        EXCEPTION WHEN foreign_key_violation THEN
            EXECUTE format(
                'ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(id) ON DELETE SET NULL NOT VALID',
                r.tabla, r.nombre, r.columna, r.destino);
            RAISE NOTICE 'FK % creada como NOT VALID: hay valores huérfanos en %.%.', r.nombre, r.tabla, r.columna;
        WHEN OTHERS THEN
            RAISE NOTICE 'No se pudo crear la FK % (%): se omite.', r.nombre, SQLERRM;
        END;
    END LOOP;
END $$;


-- ============================================================================
-- 12. ÍNDICES
-- ============================================================================
-- Núcleo y accesos
CREATE INDEX IF NOT EXISTS idx_usuarios_correo        ON usuarios(correo);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol           ON usuarios(rol_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_conjunto      ON usuarios(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_usuarios_copropiedad   ON usuarios(id_copropiedad);
CREATE INDEX IF NOT EXISTS idx_conjuntos_activo       ON conjuntos(activo);
CREATE INDEX IF NOT EXISTS idx_usuario_conjunto       ON usuario_conjuntos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_usuario_conjunto_ref   ON usuario_conjuntos(conjunto_id);
CREATE INDEX IF NOT EXISTS idx_rol_permisos_rol       ON rol_permisos(rol_id);
CREATE INDEX IF NOT EXISTS idx_permisos_modulo        ON permisos(modulo);
-- Residentes y propiedades
CREATE INDEX IF NOT EXISTS idx_residentes_usuario     ON residentes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_residentes_conjunto    ON residentes(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_propiedades_residente  ON propiedades(residente_id);
CREATE INDEX IF NOT EXISTS idx_propiedades_conjunto   ON propiedades(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_propiedades_estado     ON propiedades(estado);
-- Finanzas
CREATE INDEX IF NOT EXISTS idx_mov_propiedad          ON movimientos_financieros(propiedad_id);
CREATE INDEX IF NOT EXISTS idx_mov_concepto           ON movimientos_financieros(concepto_id);
CREATE INDEX IF NOT EXISTS idx_mov_conjunto           ON movimientos_financieros(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_mov_vencimiento        ON movimientos_financieros(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_mov_estado             ON movimientos_financieros(estado);
CREATE INDEX IF NOT EXISTS idx_comprobantes_usuario   ON comprobantes_pago(usuario_id);
CREATE INDEX IF NOT EXISTS idx_comprobantes_conjunto  ON comprobantes_pago(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_comprobantes_mov       ON comprobantes_pago(movimiento_id);
-- Operación
CREATE INDEX IF NOT EXISTS idx_mant_propiedad         ON tareas_mantenimiento(propiedad_id);
CREATE INDEX IF NOT EXISTS idx_mant_asignado          ON tareas_mantenimiento(asignado_a);
CREATE INDEX IF NOT EXISTS idx_mant_conjunto          ON tareas_mantenimiento(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_mant_estado            ON tareas_mantenimiento(estado);
CREATE INDEX IF NOT EXISTS idx_docs_conjunto          ON documentos(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_docs_publico           ON documentos(publico);
CREATE INDEX IF NOT EXISTS idx_eventos_conjunto       ON eventos(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_eventos_fecha          ON eventos(fecha);
CREATE INDEX IF NOT EXISTS idx_comunicados_conjunto   ON comunicados(id_conjunto);
-- Comunidad
CREATE INDEX IF NOT EXISTS idx_pqrs_usuario           ON pqrs(usuario_id);
CREATE INDEX IF NOT EXISTS idx_pqrs_conjunto          ON pqrs(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_pqrs_estado            ON pqrs(estado);
CREATE INDEX IF NOT EXISTS idx_zonas_conjunto         ON zonas_comunes(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_reservas_zona_fecha    ON reservas_zonas(zona_id, fecha);
CREATE INDEX IF NOT EXISTS idx_reservas_usuario       ON reservas_zonas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_reservas_conjunto      ON reservas_zonas(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_visitantes_documento   ON visitantes(documento);
CREATE INDEX IF NOT EXISTS idx_visitantes_conjunto    ON visitantes(id_conjunto);
-- Gobierno
CREATE INDEX IF NOT EXISTS idx_votaciones_conjunto    ON votaciones(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_votacion_opciones_vot  ON votacion_opciones(votacion_id);
CREATE INDEX IF NOT EXISTS idx_votos_votacion         ON votos(votacion_id);
CREATE INDEX IF NOT EXISTS idx_votos_usuario          ON votos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_conjunto   ON solicitudes_aprobacion(id_conjunto);
-- Comunicación
CREATE INDEX IF NOT EXISTS idx_chat_sesion_usuario    ON sesiones_chat(usuario_id);
CREATE INDEX IF NOT EXISTS idx_chat_sesion_conjunto   ON sesiones_chat(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_chat_msg_sesion        ON mensajes_chat(sesion_id, fecha_creacion);
CREATE INDEX IF NOT EXISTS idx_conv_directa_residente ON conversaciones_directas(residente_usuario_id, id_conjunto);
CREATE INDEX IF NOT EXISTS idx_conv_directa_ultimo    ON conversaciones_directas(ultimo_mensaje_en DESC);
CREATE INDEX IF NOT EXISTS idx_conv_directa_remitente  ON conversaciones_directas(ultimo_remitente_id);
CREATE INDEX IF NOT EXISTS idx_msg_directos_conv      ON mensajes_directos(conversacion_id, fecha_creacion);
CREATE INDEX IF NOT EXISTS idx_msg_directos_leido     ON mensajes_directos(conversacion_id, rol_remitente, leido);
CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(usuario_id, leida, descartada);
CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha   ON notificaciones(fecha_creacion);
CREATE INDEX IF NOT EXISTS idx_notificaciones_conj    ON notificaciones(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_push_usuario           ON push_suscripciones(usuario_id);
-- Configuración y auditoría
CREATE INDEX IF NOT EXISTS idx_config_categoria       ON configuraciones(categoria);
CREATE INDEX IF NOT EXISTS idx_config_conjunto        ON configuraciones(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario      ON auditoria(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_conjunto     ON auditoria(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_auditoria_accion       ON auditoria(accion);
CREATE INDEX IF NOT EXISTS idx_auditoria_modulo       ON auditoria(modulo);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha        ON auditoria(fecha_creacion);

-- Índices de apoyo para llaves foráneas (una FK sin índice obliga a recorrer toda la
-- tabla hija al borrar o actualizar el registro padre y al hacer JOIN).

CREATE INDEX IF NOT EXISTS idx_comprobantes_pago_revisado_por      ON comprobantes_pago(revisado_por);
CREATE INDEX IF NOT EXISTS idx_comunicados_enviado_por             ON comunicados(enviado_por);
CREATE INDEX IF NOT EXISTS idx_conversaciones_directas_id_conjunto ON conversaciones_directas(id_conjunto);
CREATE INDEX IF NOT EXISTS idx_documentos_propiedad_id             ON documentos(propiedad_id);
CREATE INDEX IF NOT EXISTS idx_documentos_subido_por               ON documentos(subido_por);
CREATE INDEX IF NOT EXISTS idx_eventos_creado_por                  ON eventos(creado_por);
CREATE INDEX IF NOT EXISTS idx_mensajes_directos_remitente_id      ON mensajes_directos(remitente_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_financieros_creado_por  ON movimientos_financieros(creado_por);
CREATE INDEX IF NOT EXISTS idx_pqrs_residente_id                   ON pqrs(residente_id);
CREATE INDEX IF NOT EXISTS idx_pqrs_respondido_por                 ON pqrs(respondido_por);
CREATE INDEX IF NOT EXISTS idx_reservas_zonas_decidido_por         ON reservas_zonas(decidido_por);
CREATE INDEX IF NOT EXISTS idx_rol_permisos_permiso_id             ON rol_permisos(permiso_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_aprobacion_creado_por   ON solicitudes_aprobacion(creado_por);
CREATE INDEX IF NOT EXISTS idx_solicitudes_aprobacion_decidido_por ON solicitudes_aprobacion(decidido_por);
CREATE INDEX IF NOT EXISTS idx_tareas_mantenimiento_residente_id   ON tareas_mantenimiento(residente_id);
CREATE INDEX IF NOT EXISTS idx_visitantes_registrado_por           ON visitantes(registrado_por);
CREATE INDEX IF NOT EXISTS idx_visitantes_residente_id             ON visitantes(residente_id);
CREATE INDEX IF NOT EXISTS idx_votaciones_creado_por               ON votaciones(creado_por);
CREATE INDEX IF NOT EXISTS idx_votos_opcion_id                     ON votos(opcion_id);

-- (Opcional) índice vectorial para RAG si se instala pgvector:
-- CREATE INDEX idx_doc_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


-- ============================================================================
-- 13. TRIGGERS
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_configuraciones') THEN
        CREATE TRIGGER trg_configuraciones
            BEFORE UPDATE ON configuraciones
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_pqrs_actualizacion') THEN
        CREATE TRIGGER trg_pqrs_actualizacion
            BEFORE UPDATE ON pqrs
            FOR EACH ROW EXECUTE FUNCTION set_fecha_actualizacion();
    END IF;
END $$;


-- ============================================================================
-- 14. DATOS DE REFERENCIA RBAC (catálogo de permisos y asignación por rol)
-- ============================================================================
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
    ('sistema.respaldar',  'sistema',   'respaldar','Generar respaldo de la base de datos'),
    ('mensajes.ver',       'mensajes',  'ver',      'Ver conversaciones del chat con la administración'),
    ('mensajes.enviar',    'mensajes',  'enviar',   'Enviar mensajes en el chat con la administración'),
    ('mensajes.gestionar', 'mensajes',  'gestionar','Ver y responder conversaciones de todos los residentes')
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

    -- residente: lectura de su conjunto + crear solicitudes de mantenimiento + chatbot + chat con admin.
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT 3, id FROM permisos WHERE codigo IN (
        'dashboard.ver','propiedades.ver','documentos.ver','documentos.descargar',
        'eventos.ver','mantenimiento.ver','mantenimiento.crear','chat.usar',
        'mensajes.ver','mensajes.enviar')
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


-- ============================================================================
-- 15. DOCUMENTACIÓN DEL ESQUEMA (visible en DBeaver / pgAdmin)
-- ============================================================================
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM (VALUES
        ('conjuntos',               'Copropiedades gestionadas; casi todo cuelga de aquí por id_conjunto'),
        ('roles',                   'Roles del sistema (super_admin, admin, residente, tesoreria, seguridad)'),
        ('usuarios',                'Cuentas de acceso a la plataforma'),
        ('usuario_conjuntos',       'Conjuntos a cargo de cada usuario (N:M)'),
        ('permisos',                'Catálogo de permisos por módulo y acción (RBAC)'),
        ('rol_permisos',            'Asignación de permisos a cada rol (N:M)'),
        ('residentes',              'Propietarios e inquilinos de cada conjunto'),
        ('propiedades',             'Apartamentos / unidades de cada conjunto'),
        ('conceptos_financieros',   'Catálogo de conceptos de ingreso y gasto'),
        ('movimientos_financieros', 'Cobros, pagos y gastos'),
        ('comprobantes_pago',       'Comprobantes que suben los residentes para revisión'),
        ('tareas_mantenimiento',    'Solicitudes y tareas de mantenimiento'),
        ('documentos',              'Archivos y documentos del conjunto'),
        ('eventos',                 'Calendario de asambleas, reuniones y actividades'),
        ('comunicados',             'Circulares y avisos masivos a residentes'),
        ('pqrs',                    'Peticiones, quejas, reclamos y sugerencias'),
        ('zonas_comunes',           'Zonas comunes reservables'),
        ('reservas_zonas',          'Reservas de zonas comunes'),
        ('visitantes',              'Control de ingreso y salida de visitantes'),
        ('votaciones',              'Votaciones del consejo de administración'),
        ('votacion_opciones',       'Opciones de cada votación'),
        ('votos',                   'Votos emitidos (uno por usuario y votación)'),
        ('solicitudes_aprobacion',  'Solicitudes de gasto/contrato que aprueba el consejo'),
        ('sesiones_chat',           'Sesiones del chatbot asistente'),
        ('mensajes_chat',           'Mensajes de cada sesión del chatbot'),
        ('conversaciones_directas', 'Hilos de chat residente <-> administración'),
        ('mensajes_directos',       'Mensajes de los hilos de chat directo'),
        ('notificaciones',          'Avisos persistentes por usuario'),
        ('push_suscripciones',      'Suscripciones Web Push de los navegadores'),
        ('configuraciones',         'Parámetros del sistema (globales o por conjunto), agrupados por categoría'),
        ('auditoria',               'Historial de acciones realizadas en la plataforma')
    ) AS t(tabla, texto)
    LOOP
        EXECUTE format('COMMENT ON TABLE %I IS %L', r.tabla, r.texto);
    END LOOP;
END $$;


-- ============================================================================
-- 16. VERIFICACIÓN FINAL
-- ============================================================================
-- Si falta alguna tabla, el script termina con un error explícito (y se hace
-- rollback) en lugar de dejar una base a medias que falla sin explicación.
DO $$
DECLARE
    faltantes TEXT;
    total     INTEGER;
BEGIN
    SELECT string_agg(t.nombre, ', ')
      INTO faltantes
      FROM (VALUES
            ('conjuntos'), ('roles'), ('usuarios'), ('usuario_conjuntos'),
            ('permisos'), ('rol_permisos'), ('residentes'), ('propiedades'),
            ('conceptos_financieros'), ('movimientos_financieros'), ('comprobantes_pago'),
            ('tareas_mantenimiento'), ('documentos'), ('eventos'), ('comunicados'),
            ('pqrs'), ('zonas_comunes'), ('reservas_zonas'), ('visitantes'),
            ('votaciones'), ('votacion_opciones'), ('votos'), ('solicitudes_aprobacion'),
            ('sesiones_chat'), ('mensajes_chat'), ('conversaciones_directas'),
            ('mensajes_directos'), ('notificaciones'), ('push_suscripciones'),
            ('configuraciones'), ('auditoria')
           ) AS t(nombre)
     WHERE to_regclass('public.' || t.nombre) IS NULL;

    IF faltantes IS NOT NULL THEN
        RAISE EXCEPTION 'Base de datos incompleta: faltan las tablas %', faltantes;
    END IF;

    SELECT count(*) INTO total FROM information_schema.tables
     WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    RAISE NOTICE '✔ Base de datos Multi-Administrador lista: % tablas, permisos y RBAC.', total;
END $$;

-- ============================================================================
--  FIN DEL SCRIPT
-- ============================================================================
