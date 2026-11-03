# 🔧 "password authentication failed for user multiadmin" en DBeaver

Ese mensaje **no es de DBeaver**: lo devuelve PostgreSQL. Significa que el
usuario `multiadmin` existe en ese servidor, pero la contraseña que enviaste no
coincide. Hay una causa que explica el 90 % de los casos:

> **PostgreSQL solo aplica `POSTGRES_PASSWORD` la PRIMERA vez que se crea el
> volumen.** Si ya habías arrancado el proyecto antes (aunque fuera con otra
> contraseña, o con el `.env` de ejemplo), la clave real del contenedor es
> **la vieja**. Cambiar `POSTGRES_PASSWORD` en el `.env` después **no la cambia**:
> el contenedor arranca con la clave que quedó guardada en el volumen.

---

## Paso 0 · ¿Es realmente el contenedor el que responde en el 5433?

```bash
docker compose ps
```

- **`db ... Up (healthy) 0.0.0.0:5433->5432/tcp`** → es el contenedor. Ve al Paso 1.
- **No aparece `db` / no hay nada en 5433** → estás conectando a **otro**
  PostgreSQL de tu equipo que sí está escuchando en 5433. En ese caso usa las
  credenciales de esa instalación (normalmente usuario `postgres` y su clave),
  o cambia el puerto del contenedor en `.env` (`POSTGRES_PORT=5434`) y
  `docker compose up -d db`.
- Si `db` está en **`Restarting`**: mira `docker compose logs db`. Cuando la
  contraseña o la versión del volumen no cuadran, el contenedor entra en bucle.

Comprueba de qué servidor se trata (sin contraseña, solo el saludo del protocolo):

```bash
docker compose exec db psql -U multiadmin -d multiadmin_db -c "SELECT current_user, current_database();"
```

Si **eso** funciona, el servidor y el usuario están bien → el problema es solo
la contraseña que usa DBeaver.

---

## Paso 1 · Ver la contraseña que tiene el contenedor AHORA

```bash
# Linux / macOS / Git Bash
docker compose exec db env | grep POSTGRES

# Windows PowerShell
docker compose exec db env | Select-String POSTGRES
```

Apunta `POSTGRES_PASSWORD`. **Esa** es la que debes escribir en DBeaver
(sin comillas, sin espacios). Si dudabas entre varias, prueba primero esta.

> ⚠️ Si esa clave es distinta de la que usaste al crear el volumen, la del
> `env` **no** es la válida: es solo la que el `.env` pide ahora. Sigue al Paso 2.

---

## Paso 2 · Arreglo recomendado: poner la clave que quieres, SIN perder datos

Dentro del contenedor, la conexión local por socket entra como `trust`, así que
podemos cambiar la contraseña sin saber la anterior:

### Linux / macOS / Git Bash
```bash
docker compose exec db psql -U multiadmin -d postgres \
  -c "ALTER ROLE multiadmin WITH PASSWORD 'multiadmin';"
```

### Windows PowerShell (una sola línea)
```powershell
docker compose exec db psql -U multiadmin -d postgres -c "ALTER ROLE multiadmin WITH PASSWORD 'multiadmin';"
```

Luego **en DBeaver**: cierra la conexión, vuelve a escribir la contraseña
`multiadmin` y pulsa **Test Connection**. Debe salir *Connected*.

> Si tu `POSTGRES_USER` no es `multiadmin`, cámbialo en ambos lados.
> Si prefieres otra clave, cambia `'multiadmin'` por la tuya **y** pon la misma
> en `.env` (`POSTGRES_PASSWORD=...`).

### Si el comando dice `role "multiadmin" does not exist`
El volumen se creó con otro usuario. Mira cuál existe:

```bash
docker compose exec db psql -U postgres -d postgres -c "\du"
```

y usa ese nombre (o créalo: `CREATE ROLE multiadmin LOGIN PASSWORD 'multiadmin' CREATEDB;`
y `GRANT ALL ON DATABASE multiadmin_db TO multiadmin;`).

---

## Paso 2-bis · Arreglo "empezar de cero" (borra los datos)

Válido si no te importa perder lo que haya (se vuelve a sembrar solo):

```bash
docker compose down -v      # -v borra el volumen db_data
docker compose up -d        # se crea con la clave del .env actual
```

o directamente:

```bash
./db/reiniciar_docker.sh
```

---

## Paso 3 · Si el comando del Paso 2 también falla

| Mensaje al ejecutar `docker compose exec` | Qué pasa | Qué hacer |
|---|---|---|
| `service "db" is not running` | Contenedor caído | `docker compose up -d db` y revisa `docker compose logs db` |
| `role "multiadmin" does not exist` | Usuario distinto | `\du` para ver el real (ver arriba) |
| `database "postgres" does not exist` | Imagen rara / base renombrada | `-d multiadmin_db` en vez de `-d postgres` |
| `psql: command not found` | No es la imagen oficial de Postgres | Estás conectando a otro servidor: revisa el Paso 0 |
| `FATAL: password authentication failed` también aquí | El contenedor ya no acepta `trust` local | Usa `docker compose down -v` (Paso 2-bis) |

---

## Paso 4 · Detalles de DBeaver que también producen este error

1. **Contraseña guardada vieja** → en la conexión: casilla *Guardar contraseña*
   desmarcada, escribe de nuevo y **Test Connection**.
2. **Espacio al final** al pegar la clave (muy común al copiar del `.env`).
3. **Perfil equivocado**: puedes tener dos conexiones abiertas, una a `5432`
   (tu Postgres local) y otra a `5433` (contenedor). Revisa el **puerto** del
   perfil que estás usando.
4. **Campo Usuario** con espacios o punto y coma al final → debe ser exactamente `multiadmin`.
5. **Autenticación**: en *Propiedades de la conexión → PostgreSQL* deja
   `Autenticación: Database Native` (no SCRAM explícito).
6. Si tu clave tiene `@`, `#`, `!`, `$`, espacios… ponla entre comillas simples
   en el `.env` y verifica que DBeaver la reciba igual (`!` en Bash hace
   historia: escribe `'clave!'` entre comillas simples en la terminal).

---

## Datos finales para DBeaver (Docker, valores por defecto del proyecto)

| Campo | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5433` |
| Database | `multiadmin_db` |
| Usuario | `multiadmin` |
| Contraseña | `multiadmin` (o la que fijaste en el Paso 2) |

```
jdbc:postgresql://localhost:5433/multiadmin_db
```

Y en `.env` deben coincidir:

```env
POSTGRES_USER=multiadmin
POSTGRES_PASSWORD=multiadmin
POSTGRES_DB=multiadmin_db
POSTGRES_PORT=5433
```

> **Recuerda:** si cambias `POSTGRES_PASSWORD` en el `.env` **después** de la
> primera ejecución, el contenedor **no** se entera. Hay que hacer el
> `ALTER ROLE` del Paso 2 o recrear el volumen (`down -v`).

---

## Verificación final

En la SQL Editor de DBeaver (F3):

```sql
SELECT current_user, current_database();

SELECT count(*) AS tablas
FROM information_schema.tables WHERE table_schema = 'public';   -- 18

SELECT count(*) AS usuarios FROM usuarios;                      -- 1
SELECT count(*) AS permisos FROM permisos;                      -- 40

SELECT id, nombre, correo, rol_id, activo FROM usuarios ORDER BY id;
```

Si `usuarios` sale en 0 (o la tabla existe pero vacía), arranca la API una vez
para que siembre los datos:

```bash
docker compose up -d --build      # o: cd backend && uvicorn app.main:app --reload
```

o, sin Docker:

```bash
cd backend && python verificar_bd.py
```

---

## Anexo · Variables de entorno para que funcione la verificación por correo

Los tres archivos ya quedaron configurados con las credenciales SMTP reales:

| Archivo | Uso | SMTP |
|---|---|---|
| `.env` (raíz) | **Docker Compose** (el que importa si usas Docker) | `multiadmin0@gmail.com` + contraseña de aplicación |
| `backend/.env` | `uvicorn` en local, sin Docker | las mismas credenciales |
| `.env.example` | plantilla que **sí** se sube a GitHub | placeholders (`tu@gmail.com`) |

Claves relevantes:

```env
EMAIL_USER=multiadmin0@gmail.com
EMAIL_PASSWORD=<contraseña de aplicación de 16 letras>
MAIL_FROM=multiadmin0@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
NOTIFICACIONES_CORREO=true
FRONTEND_URL=http://localhost:3000
```

Comprobar que el backend las tomó (en `/health`):

```json
"correo": { "configurado": true, "remitente": "multiadmin0@gmail.com", "servidor": "smtp.gmail.com" }
```

Si `configurado` sale `false`, el backend no está viendo el `.env`:
en Docker hay que **recrear** el contenedor para que tome las variables nuevas:

```bash
docker compose up -d --force-recreate backend
docker compose logs backend | grep -i correo
```
