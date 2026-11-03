# Informe · Arreglos de base de datos (Multi-Administrador)

Fecha: 27/10/2026 · Repositorio base: `sayethbermudez/multi-admin..`

Este documento explica **qué estaba mal en la capa de base de datos**, **qué se
cambió** y **cómo se comprobó**. Todo lo marcado como verificado se probó contra
un motor PostgreSQL real (PostgreSQL 18, vía PGlite) y contra SQLite.

---

## 1. Resumen de lo arreglado

| # | Problema encontrado | Consecuencia real | Estado |
|---|---|---|---|
| 1 | `CREATE EXTENSION "uuid-ossp"` y `"pgcrypto"` sin protección en `db/init.sql` | Si el servidor no trae esas extensiones (Postgres "slim", RDS, Supabase, instalado a mano), **el script aborta en la línea 12 y la base queda sin ninguna tabla** → "la base de datos no funciona" | ✅ Corregido: extensiones opcionales con bloque `EXCEPTION` |
| 2 | Faltaban las columnas `codigo_verificacion` y `codigo_recuperacion` en `usuarios` del SQL | La verificación por código de 6 dígitos fallaba en bases creadas solo con `init.sql` | ✅ Agregadas (+ `ALTER ... IF NOT EXISTS` para bases viejas) |
| 3 | `permisos.codigo VARCHAR(60)` / `modulo VARCHAR(40)` vs. modelo (`120`/`60`) | Riesgo de `value too long for type character varying` al sincronizar el RBAC | ✅ Ampliadas en `CREATE` y con `ALTER COLUMN ... TYPE` |
| 4 | `INSERT INTO roles ... ON CONFLICT (id)` | Si existía un rol con el mismo nombre y otro id: `duplicate key value violates unique constraint roles_nombre_key` y el script moría | ✅ `ON CONFLICT DO NOTHING` (cubre id y nombre) |
| 5 | El backend **lanzaba excepción** si faltaba `DATABASE_URL` | `❌ DATABASE_URL no cargada` → la API no arrancaba sin `.env` | ✅ Reescrito `database.py`: reintentos, normalización de URL y **respaldo automático a SQLite** |
| 6 | Sin reintentos de conexión al arrancar | Carrera típica en Docker: la API moría porque Postgres aún no aceptaba conexiones | ✅ `esperar_base()` con reintentos configurables |
| 7 | `GET /admin/backup` devolvía **500** si no existía `pg_dump` | El respaldo nunca funcionaba fuera de Docker con cliente instalado | ✅ Respaldo alternativo generado en Python (restaurable) + `postgresql-client` en la imagen |
| 8 | No había forma de crear/verificar la base sin Docker | Alumnos sin PostgreSQL quedaban bloqueados | ✅ `db/crear_bd.py` (+ `.sh`/`.bat`), `backend/verificar_bd.py`, `db/reiniciar_docker.sh` |
| 9 | `init.sql` podía quedar "a medias" sin avisar | Base incompleta y errores opacos en el backend | ✅ Bloque final de verificación: si falta una tabla, lanza excepción explícita |
| 10 | Índices faltantes (`usuarios.id_conjunto`, `usuario_conjuntos.conjunto_id`, etc.) | Consultas por conjunto más lentas | ✅ Agregados (55 índices en total) |

---

## 2. Verificación ejecutada

### 2.1 Esquema en PostgreSQL real
`db/init.sql` se ejecutó sobre PostgreSQL 18 (motor real compilado a WASM):

```
✅ EJECUTADO OK (sin extensiones disponibles)
   • Tablas creadas      : 18
   • Roles               : 5
   • Permisos            : 35 → 40 tras la sincronización del backend
   • Permisos asignados  : 112
   • Índices             : 55
   • Trigger             : trg_configuraciones
   • Re-ejecución        : OK (idempotente)
```

Comparación automática `information_schema` ↔ `app/models.py`:

```
✔ Todas las tablas del modelo existen en PostgreSQL
✔ Ninguna columna del modelo falta en la base
✔ Ninguna columna marcada NOT NULL en el modelo se crea como NULL
```

### 2.2 Arranque de la API contra esa base
```
INFO:app.permisos:RBAC sincronizado: 13 asignaciones ajustadas.
INFO:     Application startup complete.
```
`python verificar_bd.py` → `✅ La base de datos está completa y funcionando.`

### 2.3 Pruebas funcionales de la API
| Escenario | Resultado |
|---|---|
| SQLite (sin `DATABASE_URL`) | 27/27 endpoints OK (GET, POST, PUT, DELETE, exportaciones y respaldo) |
| PostgreSQL real | 20/20 GET OK · POST/PUT OK (201/200) · `/admin/backup` genera 135 KB con 512 INSERT |
| Respaldo → restauración | Volcado aplicado en una base nueva: `usuarios: 1`, `movimientos: 222` ✔ |
| Suite `pytest tests/` | **114 passed**, 5 failed — las 5 dependen de Redis y de un PostgreSQL accesible por red en este entorno de pruebas (revocación de tokens, flujos RBAC con SQL directo), no de los cambios |

---

## 3. Archivos modificados / nuevos

**Modificados**
- `db/init.sql` — extensiones opcionales, columnas faltantes, RBAC robusto, índices y verificación final.
- `backend/app/database.py` — reescrito: reintentos, normalización de URL, respaldo SQLite, diagnóstico.
- `backend/app/main.py` — `/health` informa motor, destino y avisos de la base.
- `backend/app/routers/admin.py` — respaldo con `pg_dump` o generador en Python, ordenado por claves foráneas.
- `backend/Dockerfile` — añade `postgresql-client` (aporta `pg_dump`) y `curl`.
- `README.md` — sección de base de datos actualizada.

**Nuevos**
- `ARRANQUE_RAPIDO.md` — cómo levantar la base en 3 escenarios + tabla de problemas/soluciones.
- `INFORME_ARREGLOS_BD.md` — este documento.
- `db/crear_bd.py` — crea la base y aplica `init.sql` (sirve `--recrear`).
- `db/crear_bd.sh`, `db/crear_bd.bat` — atajos para Linux/macOS y Windows.
- `db/reiniciar_docker.sh` — `docker compose down -v` + reconstrucción guiada.
- `backend/verificar_bd.py` — diagnóstico y autorreparación idempotente.
- `.env` y `backend/.env` — configuración lista para usar (estaban solo como `.example`).

---

## 4. Cómo usarlo

```bash
# Docker
./levantar.sh                        # o levantar.bat en Windows

# PostgreSQL local
cd backend && pip install -r requirements.txt
cd .. && ./db/crear_bd.sh            # db\crear_bd.bat en Windows
cd backend && uvicorn app.main:app --reload --port 8000

# Sin PostgreSQL (SQLite automático)
cd backend && uvicorn app.main:app --reload --port 8000

# Comprobar siempre
cd backend && python verificar_bd.py
```

Credenciales sembradas: `admin@multiadmin.com` / `Admin2026!`

---

## 5. Notas

- El `db/init.sql` **solo** se ejecuta en Docker cuando el volumen es nuevo; para
  volver a aplicarlo: `docker compose down -v` (o `./db/reiniciar_docker.sh`).
- Si `DATABASE_URL` no responde, la API arranca en SQLite y lo advierte en el log
  y en `/health`. Para exigir PostgreSQL: `PERMITIR_SQLITE_FALLBACK=false`.
- Los archivos `.env` incluidos son plantillas de desarrollo; **no** pongas
  contraseñas reales en un repositorio público.
