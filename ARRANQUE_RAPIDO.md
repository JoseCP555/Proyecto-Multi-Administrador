# 🗄️ Arranque rápido — Base de datos

Guía corta para dejar la base de datos **funcionando** en este proyecto.
Si algo falla, al final está la sección **Problemas y soluciones**.

---

## Opción A · Docker (recomendado)

```bash
# Linux / macOS / Git Bash
./levantar.sh

# Windows
levantar.bat
```

Eso levanta PostgreSQL + Redis + backend + frontend y aplica `db/init.sql`
automáticamente la **primera vez** (cuando el volumen está vacío).

- Frontend: <http://localhost:3000>
- API: <http://localhost:8000/docs>
- Usuario: `admin@multiadmin.com` / `Admin2026!`

> ⚠️ **Importante:** `db/init.sql` **solo** se ejecuta la primera vez que se
> crea el volumen. Si ya habías arrancado el proyecto antes (aunque fallara),
> el script NO se vuelve a ejecutar. Para empezar limpio:
>
> ```bash
> docker compose down -v     # borra la base
> docker compose up -d       # la recrea aplicando db/init.sql
> ```
> o simplemente: `./db/reiniciar_docker.sh`

---

## Opción B · PostgreSQL instalado en tu equipo (sin Docker)

```bash
cd backend
pip install -r requirements.txt

# 1) Copia la plantilla de configuración
copy .env.example .env        # Windows
cp .env.example .env          # Linux / macOS

# 2) Crea la base y aplica el esquema (Windows: db\crear_bd.bat --recrear)
cd ..
./db/crear_bd.sh

# 3) Arranca la API (siembra roles, admin y datos demo sola)
cd backend
uvicorn app.main:app --reload --port 8000
```

El `.env` del backend debe apuntar a tu PostgreSQL:

```env
DATABASE_URL=postgresql://postgres:TU_CLAVE@localhost:5432/multiadmin_db
SECRET_KEY=cualquier-cadena-larga-y-aleatoria
REDIS_URL=redis://localhost:6379/0      # si no tienes Redis, déjalo: degrada a memoria
```

---

## Opción C · Sin PostgreSQL, sin Docker, sin instalar nada

La API **arranca igual** y usa **SQLite** (`backend/multiadmin.db`):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Si `DATABASE_URL` está vacía o PostgreSQL no responde, el backend lo avisa en
el log y cae a SQLite en lugar de morirse. Todos los módulos funcionan igual
(para volver a PostgreSQL basta configurar `DATABASE_URL`).

En `/health` puedes ver siempre qué base está usando:

```json
{"status":"ok","base_datos":{"motor":"PostgreSQL","destino":"localhost:5432/multiadmin_db","aviso":null}}
```

---

## Verificar que la base quedó bien

```bash
cd backend
python verificar_bd.py
```

Comprueba y **repara** (idempotente): tablas, columnas, roles, permisos,
RBAC y el usuario administrador. Termina con `✅ La base de datos está
completa y funcionando.`

---

## Respaldos

Desde la app: **Configuración → Respaldo de la base de datos** (o
`GET /admin/backup`). Descarga un `.sql` restaurable:

```bash
psql -U usuario -d base -f multiadmin_backup_YYYYMMDD_HHMMSS.sql     # PostgreSQL
sqlite3 multiadmin.db < multiadmin_backup_YYYYMMDD_HHMMSS.sql        # SQLite
```

Funciona incluso si `pg_dump` no está instalado (genera el volcado con Python).

---

## Problemas y soluciones

| Síntoma | Causa | Solución |
|---|---|---|
| `❌ DATABASE_URL no cargada` | No existe `backend/.env` | `cp backend/.env.example backend/.env` (o simplemente arranca: ahora cae a SQLite) |
| `relation "usuarios" does not exist` | `db/init.sql` nunca se ejecutó (volumen ya existente) | `docker compose down -v && docker compose up -d`, o `python db/crear_bd.py` |
| `extension "uuid-ossp" is not available` | PostgreSQL sin extensiones contrib | **Ya corregido**: `init.sql` las trata como opcionales |
| `password authentication failed` | Clave/usuario distintos en `.env` | Ajusta `DATABASE_URL` o `POSTGRES_*` del `.env` |
| El backend arranca pero no hay datos | El seed solo corre con la base vacía | `python backend/verificar_bd.py` (siembra lo que falte) |
| `pg_dump no está disponible` | Cliente de PostgreSQL no instalado | **Ya corregido**: respaldo alternativo en Python |
| Cambié `db/init.sql` y no pasa nada en Docker | El script solo corre con el volumen vacío | `./db/reiniciar_docker.sh` |
| `port 5433 already in use` | Otro PostgreSQL usa ese puerto | Cambia `POSTGRES_PORT=5434` en el `.env` |
