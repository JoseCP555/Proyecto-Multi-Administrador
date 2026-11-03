# 🔌 Conectar DBeaver a la base de datos de Multi-Administrador

Los datos salen de `docker-compose.yml` y de tu `.env`. **No cambies nada en el
proyecto**: solo copia estos valores en DBeaver.

---

## Caso A · Proyecto levantado con Docker (lo más común)

Si ejecutaste `./levantar.sh`, `levantar.bat` o `docker compose up -d`, el
contenedor de PostgreSQL publica el puerto **5433** en tu equipo (no el 5432,
para no chocar con un PostgreSQL instalado).

En DBeaver: **Nueva conexión → PostgreSQL → pestaña "Principal"**

| Campo DBeaver | Valor |
|---|---|
| **Host / Servidor** | `localhost` |
| **Puerto** | `5433` |
| **Database / Base de datos** | `multiadmin_db` |
| **Usuario** | `multiadmin` |
| **Contraseña** | `multiadmin` |
| **Guardar contraseña** | ✔ (opcional) |
| **Driver** | PostgreSQL (el que trae DBeaver) |

URL de conexión (JDBC, si la necesitas):

```
jdbc:postgresql://localhost:5433/multiadmin_db
```

Cadena "estilo URI":

```
postgresql://multiadmin:multiadmin@localhost:5433/multiadmin_db
```

> Si en tu `.env` cambiaste `POSTGRES_PORT`, `POSTGRES_USER`,
> `POSTGRES_PASSWORD` o `POSTGRES_DB`, usa esos valores.
> Para ver los que están activos:
> ```bash
> docker compose ps
> docker compose exec db env | grep POSTGRES
> ```

---

## Caso B · PostgreSQL instalado en tu equipo (sin Docker)

Usaste `db/crear_bd.sh` / `db/crear_bd.bat`, así que la base está en tu
PostgreSQL local (puerto por defecto **5432**).

| Campo DBeaver | Valor |
|---|---|
| **Host** | `localhost` |
| **Puerto** | `5432` |
| **Database** | `multiadmin_db` |
| **Usuario** | `postgres` (o el que uses) |
| **Contraseña** | la de tu instalación |

```
jdbc:postgresql://localhost:5432/multiadmin_db
```

Los mismos datos deben estar en `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:TU_CLAVE@localhost:5432/multiadmin_db
```

> ¿No sabes si la base existe? `./db/crear_bd.sh --recrear` la crea y aplica
> `db/init.sql`. Luego recarga DBeaver (F5).

---

## Caso C · Modo sin PostgreSQL (SQLite)

Si la API arrancó sin PostgreSQL, los datos están en un archivo SQLite:

**Nueva conexión → SQLite → Base de datos existente**

```
/home/user/multi-admin/backend/multiadmin.db      (Linux/macOS)
C:\ruta\del\proyecto\backend\multiadmin.db        (Windows)
```

No lleva usuario ni contraseña. DBeaver debe tener el driver SQLite
(lo descarga solo la primera vez).

---

## Comprobar que entraste bien

Abre una **SQL Editor** (F3) y ejecuta:

```sql
-- ¿Qué base y usuario soy?
SELECT current_database(), current_user, version();

-- ¿Están las 18 tablas?
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Datos sembrados
SELECT (SELECT count(*) FROM usuarios)               AS usuarios,
       (SELECT count(*) FROM conjuntos)              AS conjuntos,
       (SELECT count(*) FROM residentes)             AS residentes,
       (SELECT count(*) FROM propiedades)            AS propiedades,
       (SELECT count(*) FROM movimientos_financieros) AS movimientos,
       (SELECT count(*) FROM permisos)               AS permisos;

-- El usuario administrador del sistema
SELECT id, nombre, correo, rol_id, activo, correo_verificado
FROM usuarios
ORDER BY id;

-- Roles y cuántos permisos tiene cada uno
SELECT r.id, r.nombre, count(rp.permiso_id) AS permisos
FROM roles r
LEFT JOIN rol_permisos rp ON rp.rol_id = r.id
GROUP BY r.id, r.nombre
ORDER BY r.id;
```

Resultado esperado (base recién sembrada):

| Consulta | Esperado |
|---|---|
| `usuarios` | 1 (`admin@multiadmin.com`) |
| `conjuntos` | 4 |
| `residentes` | 27 |
| `propiedades` | 24 |
| `movimientos_financieros` | ~222 |
| `permisos` | 40 |
| Roles | 5 (`super_admin`, `admin`, `residente`, `tesoreria`, `seguridad`) |

> **Si `usuarios` sale vacío:** la API todavía no ha sembrado. Arráncala una vez
> (`uvicorn app.main:app` o `docker compose up -d`) o ejecuta
> `cd backend && python verificar_bd.py`.

---

## Errores típicos en DBeaver y su causa

| Error | Qué significa | Solución |
|---|---|---|
| `Connection refused` en `localhost:5433` | El contenedor `db` no está levantado (o publicaste otro puerto) | `docker compose up -d db` y revisa `docker compose ps` |
| `Connection refused` en `localhost:5432` (Caso B) | El servicio de PostgreSQL está apagado | Enciende el servicio / `pg_ctl start` |
| `database "multiadmin_db" does not exist` | La base nunca se creó | `./db/crear_bd.sh` (o `docker compose down -v && docker compose up -d`) |
| `password authentication failed for user "multiadmin"` | La contraseña del contenedor no es la que escribiste (PostgreSQL solo aplica `POSTGRES_PASSWORD` al crear el volumen) | Ver **[SOLUCION_PASSWORD_DBEAVER.md](SOLUCION_PASSWORD_DBEAVER.md)** o ejecuta `./db/arreglar_password.sh` |
| `FATAL: no pg_hba.conf entry` | Tu IP no está autorizada (Postgres remoto) | Ajusta `pg_hba.conf` o la red del hosting |
| Ves las tablas pero sin datos | El seed solo corre con la base vacía / aún no arrancó la API | `python backend/verificar_bd.py` (siembra lo que falte) |
| Solo ves `information_schema` | Estás conectado a otra base (p. ej. `postgres`) | Revisa el campo **Database** = `multiadmin_db` |

**Tip:** en DBeaver, si no ves la base, ve a la pestaña **PostgreSQL** de las
propiedades de la conexión y activa **"Show all databases"**, o cambia
*Database* a `postgres` para comprobar que el usuario existe.
