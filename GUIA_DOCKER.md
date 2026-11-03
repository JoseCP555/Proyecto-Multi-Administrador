# Guía rápida: dejar Docker funcionando

> Repositorio: `sayethbermudez/expo` — Multi-Administrador.
> Esta guía acompaña los archivos ya corregidos en este proyecto.

---

## 1. Inicio rápido

Necesitas **Docker Desktop** (Windows/macOS) o **Docker Engine + Compose v2** (Linux)
y que el daemon esté corriendo. Comprueba:

```bash
docker --version
docker compose version
docker info          # si falla aquí, abre Docker Desktop / inicia el servicio
```

Desde la **raíz del proyecto** (donde está `docker-compose.yml`):

```bash
# Windows (PowerShell o CMD)
copy .env.example .env
levantar.bat

# Linux / macOS / Git Bash
cp .env.example .env
bash levantar.sh
```

`levantar.bat` / `levantar.sh` hacen exactamente esto:

```bash
docker compose config              # valida el YAML
docker compose up --build -d       # construye y levanta los 4 servicios
docker compose ps                  # muestra el estado
```

Si prefieres hacerlo a mano:

```bash
docker compose up --build -d
docker compose logs -f backend     # Ctrl+C para salir de los logs
```

Abre **http://localhost:3000** → inicia sesión con:

| Correo | Contraseña |
|---|---|
| `admin@multiadmin.com` | `Admin2026!` |

Otros endpoints:

| URL | Qué es |
|---|---|
| http://localhost:3000 | Frontend (React) |
| http://localhost:3000/api/health | API a través del proxy de nginx |
| http://localhost:8000/health | API directa |
| http://localhost:8000/docs | Swagger / OpenAPI |

La primera vez tarda 2–5 min (descarga de imágenes + `npm ci` + `pip install`).

---

## 2. Qué estaba fallando

| # | Problema | Consecuencia | Corrección |
|---|---|---|---|
| 1 | `frontend/Dockerfile` ejecutaba `pnpm install --no-frozen-lockfile` **sin copiar `pnpm-lock.yaml`** (se copiaba después, con `COPY . .`). | Cada build resolvía versiones nuevas de 140+ paquetes; `@types/node`, `tsc` o Vite podían romper el build de forma aleatoria. Además dependía de `corepack` descargando pnpm durante el build. | Build con `npm ci` usando el `package-lock.json` del repo: **determinista y ya verificado**. |
| 2 | El frontend se compilaba con `VITE_API_URL=http://localhost:8000` **fijo**. | Si entrabas por otra IP, por un túnel o cambiabas el puerto, el navegador llamaba a `localhost:8000` de la máquina equivocada y aparecían errores de CORS / "No se pudo conectar con el servidor". | `VITE_API_URL` vacío por defecto → el bundle usa `/api` y **nginx hace de proxy inverso** a `backend:8000`. Un solo origen, sin CORS. |
| 3 | `nginx.conf` solo servía estáticos; no existía ruta `/api`. | Con el cambio anterior, `/api/...` habría dado 404. | Se añadió `location ^~ /api/` con `proxy_pass` al servicio `backend`, usando el DNS interno de Docker. |
| 4 | `db:5432` y `redis:6379` publicados en el host. | Si tienes PostgreSQL/Redis instalados localmente (el repo incluye `init.bat` para eso) → **`port is already allocated`** y el stack no levanta. | Host `5433` y `6380` por defecto, configurables en `.env`. Dentro de Docker siguen siendo `db:5432` / `redis:6379`. |
| 5 | `frontend` usaba `depends_on: - backend` (sin esperar salud). | nginx podía arrancar antes que la API → 502 temporales. | `depends_on: backend: condition: service_healthy`. |
| 6 | No había `backend/.dockerignore`. | Se copiaban al contenedor `.venv`, `__pycache__`, `*.db` y un posible `backend/.env` con `DATABASE_URL=...localhost...`. | `.dockerignore` nuevo para backend y uno más estricto para frontend. |
| 7 | `.env.example` traía credenciales SMTP falsas (`tu@gmail.com` / `xxxxxxxx`). | La app creía que el correo estaba configurado y fallaba al registrar/recuperar contraseña. | SMTP vacío y comentado: **opcional**, el sistema arranca sin él. |
| 8 | El proxy de desarrollo de Vite apuntaba a `:8041` pero uvicorn corre en `:8000`. | En modo local (sin Docker), `/api` daba 502. | `vite.config.ts` apunta a `:8000`. |

Validado en este entorno (sin Docker, pero con las mismas herramientas): `npm ci` + `npm run build` ✅,
`pip install -r requirements.txt` ✅, `db/init.sql` contra PostgreSQL 17 con `ON_ERROR_STOP=1` ✅,
arranque de FastAPI + seed + `/health` ✅, y el proxy nginx sirviendo `/api/*` ✅.

---

## 3. Cómo verificar que todo quedó bien

```bash
# 1) Los 4 contenedores deben estar "Up" y db/redis/backend "healthy"
docker compose ps

# 2) Salud de la API (directo y por el proxy)
curl -i http://localhost:8000/health
curl -i http://localhost:3000/api/health

# 3) El frontend responde y el fallback de React Router funciona
curl -I http://localhost:3000/
curl -I http://localhost:3000/login

# 4) Login de prueba (debe devolver "ok":true y un access_token)
# Linux/macOS/Git Bash:
curl -X POST http://localhost:3000/api/login -H "Content-Type: application/json" -d '{"correo":"admin@multiadmin.com","password":"Admin2026!"}'

# PowerShell (usa curl.exe, no el alias "curl" de Invoke-WebRequest):
$body = '{"correo":"admin@multiadmin.com","password":"Admin2026!"}'
curl.exe -X POST http://localhost:3000/api/login -H "Content-Type: application/json" -d $body

# CMD de Windows:
curl -X POST http://localhost:3000/api/login -H "Content-Type: application/json" -d "{\"correo\":\"admin@multiadmin.com\",\"password\":\"Admin2026!\"}"
```

> Ojo: el campo de la contraseña del endpoint `/login` es **`password`**
> (no `contrasena`), tal como lo envía `frontend/src/context/AuthContext.tsx`.

Si el paso 2 funciona pero el 3 no, reconstruye el frontend:
`docker compose up --build -d frontend`.

---

## 4. Solución de problemas

| Síntoma | Causa | Solución |
|---|---|---|
| `port is already allocated` | Otro servicio usa 3000/8000/5433/6380. | Cambia `FRONTEND_PORT` / `BACKEND_PORT` / `POSTGRES_PORT` / `REDIS_PORT` en `.env` y `docker compose up -d`. |
| `Cannot connect to the Docker daemon` | Docker Desktop cerrado o servicio detenido. | Abre Docker Desktop; en Linux `sudo systemctl start docker`. |
| El backend se reinicia sin parar | BD no lista o `init.sql` falló. | `docker compose logs -f db backend`. Si el volumen quedó a medias: `docker compose down -v` y vuelve a levantar. |
| Cambié `db/init.sql` pero no hace nada | Ese script **solo corre al crear el volumen**. | `docker compose down -v && docker compose up --build -d` (⚠️ borra los datos). |
| La página carga, pero el login dice "No se pudo conectar con el servidor" | El bundle viejo aún apunta a `localhost:8000` o el proxy no está. | `docker compose up --build -d frontend` (el build es quien inyecta `VITE_API_URL`). Revisa con curl el paso 2 de la verificación. |
| `502 Bad Gateway` en `/api/...` | Backend caído o nginx arrancó antes. | `docker compose ps`, `docker compose logs --tail=100 backend`, `docker compose restart frontend`. |
| Error de CORS en la consola | Estás usando `VITE_API_URL=http://...` directo. | Déjalo vacío en `.env` y reconstruye el frontend, o añade tu origen a `ALLOWED_ORIGINS`. |
| `npm ci` falla en el build | Lockfile modificado o sin conexión. | Asegúrate de tener `frontend/package-lock.json` y ejecuta `npm install` en `frontend/` para regenerarlo, luego reconstruye. |
| Cambié el `.env` y no pasa nada | Los cambios de variables requieren recrear contenedores; los de `VITE_API_URL` además requieren **recompilar** el front. | `docker compose up --build -d` (no solo `restart`). |
| En Windows: error de montaje de `db/init.sql` | Docker Desktop sin compartir la unidad, o archivo con CRLF/final de línea extraño. | Comparte la unidad en Docker Desktop → Resources → File sharing. El `.sql` debe estar en UTF-8. |
| Poco espacio / builds lentos | Caché de Docker acumulada. | `docker system prune -a` (⚠️ borra imágenes no usadas). |

### Reinicio completo (borra la base de datos y los documentos)

```bash
docker compose down -v --remove-orphans
docker compose up --build -d
```

---

## 5. Registro de administradores (modo demo)

La pantalla **Crear cuenta** tiene un desplegable *Usuario / Administrador*.
La opción "Administrador" está **activa por defecto** (modo demostración) tanto
en el `.env` como en `docker-compose.yml` y en el backend, así que funciona sin
configurar nada.

Si ves el error rojo **"El registro de administradores está desactivado"**, es
porque el contenedor se levantó antes del cambio. Ejecuta:

```bash
docker compose up --build -d        # no basta con "restart": recrea con las variables nuevas
curl http://localhost:8000/health  # debe decir "registro_admin_habilitado": true
```

En producción pon `PERMITIR_REGISTRO_ADMIN=false` en `.env` y vuelve a levantar:
el selector seguirá ahí, pero el servidor rechazará el alta con un 403. El
endpoint normal `/register` sigue siendo estricto (un visitante anónimo solo
puede crear residentes). Más detalles en `NUEVAS_FUNCIONES.md`.

---

## 6. Correo de verificación (SMTP)

El `.env` trae credenciales SMTP (Gmail con **contraseña de aplicación**) para
que lleguen los correos de verificación de cuenta y de recuperación:

```env
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASSWORD=xxxxxxxxxxxxxxxx   # 16 letras, SIN espacios
MAIL_FROM=tu_correo@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
```

- La contraseña real va **solo en `.env`** (ignorado por git). `.env.example`
  lleva marcadores de posición: nunca subas la contraseña a GitHub.
- Comprueba que el backend la leyó con `curl http://localhost:8000/health` →
  `"correo": {"configurado": true, ...}`. Ese mismo endpoint informa
  `"registro_admin_habilitado"`.
- Si cambias el `.env`, **recrea** los contenedores: `docker compose up -d`.
- El enlace del correo usa `FRONTEND_URL`; debe apuntar a donde abres la app.
- Para evitar rebotes, el sistema **omite el envío** a dominios de prueba
  (`x.com`, `test.com`, `example.com`, `example.org`, `ejemplo.com`,
  `ejemplo.es`, `prueba.com`, `correo.com`, `localhost`). Prueba con un correo
  real (Gmail, Outlook…).
- Si Gmail rechaza el acceso, regenera la contraseña de aplicación y confirma
  que la verificación en 2 pasos está activa.

---

## 6b. Notificaciones reales (correo + push)

La campana del dashboard guarda avisos en PostgreSQL (tabla `notificaciones`),
los marca como leídos/descartados, navega al módulo que los originó y los
entrega por dos canales opcionales.

### Correo

Usa las **mismas credenciales SMTP** de la sección 6. No hay nada extra que
configurar: si `/health` dice `"correo": {"configurado": true}`, los avisos de
eventos, pagos, documentos, residentes, etc. se enviarán por correo. La
entrega va en segundo plano para no retrasar la API.

- Interruptor de emergencia: `NOTIFICACIONES_CORREO=false` en `.env`.
- Cada usuario puede desactivarlos desde la propia campana.
- Los recordatorios diarios (moras, vencimientos) **no** se mandan por correo
  para no llenar la bandeja; los hechos puntuales y las alertas críticas sí.

### Push del navegador (Web Push / VAPID)

Necesitas un par de claves VAPID. Si partiste de `.env.example`, genéralas:

```bash
python backend/generar_vapid.py --guardar   # añade las claves a tu .env
docker compose up --build -d                # reinicia el backend
```

Comprueba con:

```bash
curl http://localhost:8000/notificaciones/config
# {"vapid_publico":"BA...", "push_configurado":true, "correo_configurado":true}
```

Luego, en la campana, activa **"Notificaciones del navegador"** y acepta el
permiso. El service worker (`/sw.js`) se registra solo y la suscripción queda
guardada en `push_suscripciones`. El botón **"Enviar aviso de prueba"** crea un
aviso real e indica si el correo salió y cuántos push se entregaron.

Notas:

- Las notificaciones push requieren **HTTPS** (o `localhost`) y un navegador
  compatible (Chrome, Firefox, Edge). La clave **privada** va solo en `.env`.
- Si cambias las claves VAPID, las suscripciones antiguas se renuevan solas al
  volver a abrir la app.
- `pywebpush` se instala desde `backend/requirements.txt`; el primer
  `docker compose up --build` lo incluye.

---

## 7. Modo alternativo: API directa (sin proxy)

Si necesitas que el navegador hable directamente con el backend (por ejemplo,
frontend y backend en servidores distintos), en `.env`:

```env
VITE_API_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=http://localhost:3000
```

Luego **recompila el frontend** (`docker compose up --build -d frontend`), porque
`VITE_API_URL` se incrusta en el bundle en tiempo de build. Si accedes por una IP
o dominio distinto, sustituye `localhost` por ese host en las tres variables.

---

## 8. Archivos modificados

```
docker-compose.yml          puertos configurables, healthchecks, depends_on con salud, VITE_API_URL vacío
frontend/Dockerfile         npm ci + package-lock.json (build determinista)
frontend/nginx.conf         proxy inverso /api -> backend:8000 + SPA fallback
frontend/.dockerignore      evita que un .env local contamine el build
backend/.dockerignore       NUEVO: evita copiar .venv, .env, cachés y *.db
frontend/vite.config.ts     proxy de desarrollo :8041 -> :8000
frontend/.env.example       ahora es específico de Vite
.env.example                SMTP opcional, puertos y explicación de VITE_API_URL
.env                        NUEVO (generado, ignorado por git): listo para usar
levantar.bat / levantar.sh  scripts de arranque con validación
GUIA_DOCKER.md              este documento
NUEVAS_FUNCIONES.md         logo por conjunto + cambios en Crear cuenta
backend/app/routers/logos.py  subida/servicio de logos; auth.py añade /register/admin
frontend/src/pages/Register.tsx / Dashboard/Conjuntos.tsx / AuthShell.tsx
                            selector de cuenta, ojitos, checklist y apartado de logo
```

Los detalles de las nuevas pantallas están en `NUEVAS_FUNCIONES.md`.
