# Multi-Administrador

<p align="center">
  <strong>Sistema web para la administración integral de conjuntos residenciales y propiedades horizontales.</strong>
</p>

> 🚀 **¿Solo quieres que la base de datos funcione?** Empieza por
> [`ARRANQUE_RAPIDO.md`](ARRANQUE_RAPIDO.md) y
> [`INFORME_ARREGLOS_BD.md`](INFORME_ARREGLOS_BD.md).

**Multi-Administrador** es una plataforma web profesional que centraliza los procesos administrativos, financieros y documentales de una copropiedad: residentes, propiedades, pagos, mantenimientos, documentos, reportes y un **asistente virtual (chatbot)** que responde con datos reales del sistema.

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS 3 + Framer Motion + React Router 6 |
| Backend | Python + FastAPI + SQLAlchemy + Pydantic |
| Base de datos | PostgreSQL 16 |
| Caché / sesiones | Redis 7 |
| Asistente virtual | Motor local (RAG sobre la BD) u OpenAI (opcional) |
| Orquestación | Docker Compose |
| Paquete | PNPM |

## Módulo multi-conjunto

El sistema administra **varios conjuntos desde un solo panel**: el *Panel Multi-Administrador*
(`/dashboard`) lista las copropiedades a tu cargo y, al abrir una, trabajas dentro de ella con su
propia información. Desde el botón **"Cambiar conjunto"** (en el bloque *Gestionando conjunto* y en
la barra superior) se despliegan **todos los conjuntos** y se cambia de uno a otro **sin cerrar sesión**.
Cada conjunto tiene sus residentes, propiedades, finanzas, mantenimientos, documentos y eventos
completamente separados.

Detalles técnicos en [`docs/MULTI_CONJUNTO.md`](docs/MULTI_CONJUNTO.md).

## Módulos

- Landing page de presentación antes del login/registro.
- Autenticación (registro, login, JWT) y **recuperación de contraseña por correo real** (SMTP).
- Gestión de **usuarios** con **RBAC real** (roles: super_admin, admin, residente, tesorería, seguridad). La matriz rol → permisos vive en `backend/app/permisos.py` y se sincroniza en la BD al arrancar.

  | Módulo | super_admin | admin | tesorería | residente | seguridad |
  |---|---|---|---|---|---|
  | Usuarios | CRUD + eliminar | ver/crear/editar | — | — | — |
  | Residentes | CRUD | CRUD | ver | — | ver |
  | Propiedades | CRUD | CRUD | ver | ver | ver |
  | Finanzas / reportes | CRUD | CRUD | CRUD | — | — |
  | Mantenimiento | CRUD | CRUD | — | ver + crear solicitud | ver/crear/editar |
  | Documentos | CRUD + descargar | CRUD + descargar | ver/descargar | ver/descargar | ver/descargar |
  | Eventos | CRUD | CRUD | — | ver | ver |
  | Configuración / respaldo BD | sí / sí | sí / — | — | — | — |
  | Chatbot | sí | sí | sí (solo módulos permitidos) | sí (solo módulos permitidos) | sí (solo módulos permitidos) |

  El registro público (`/register`) siempre crea **residentes**; asignar otro rol exige estar autenticado con `usuarios.crear` (y solo un super_admin crea super_admins).
- Gestión de **residentes** y **propiedades**.
- Gestión **financiera** (conceptos, movimientos, resumen, gráficas).
- Mantenimiento (órdenes, prioridades, estados).
- Documentos y eventos.
- Dashboard con estadísticas en tiempo real y chatbot flotante.

## Arquitectura

```text
Cliente (navegador)  ──►  Frontend (:3000)  ──►  Backend FastAPI (:8000)
                                                        │
                                    ┌───────────────────┼────────────────────┐
                                    │                   │                    │
                              PostgreSQL (:5432)     Redis (:6379)      Chatbot
                                                            │        (local/LLM)
                                                       caché/sesiones
```

## Novedades de la interfaz

- **Logo y color por conjunto**: el modal *Agregar conjunto / Editar conjunto*
  permite subir una imagen (PNG/JPG/WEBP, máx. 2 MB) con vista previa y elegir
  el **color** del conjunto (6 tonos de paleta o un hexadecimal libre). El
  logo, el color y su vista previa se muestran en las tarjetas, en el selector
  "Cambiar conjunto" y en todo el tema del conjunto.
- **Crear cuenta**: desplegable **Usuario / Administrador**, botón de **ojito**
  para ver u ocultar la contraseña y **requisitos en verde/rojo** (longitud,
  mayúscula, minúscula, número y coincidencia de las contraseñas) con barra de
  fortaleza.
- **Iniciar sesión**: el campo de contraseña también tiene su **ojito** para
  mostrarla u ocultarla.
- **Admin = Super Admin**: el rol `admin` tiene los mismos 40 permisos, ve el
  mismo menú y puede hacer lo mismo que `super_admin` (respaldos, gestión de
  usuarios y de todos los conjuntos). Los demás roles no cambian.
- **Notificaciones reales**: la campana guarda avisos persistentes generados
  por pagos, eventos, mantenimientos, documentos y residentes; se pueden marcar
  como leídas, descartar y abrir el módulo correspondiente. Se entregan por
  **correo** y por **push del navegador** (Web Push/VAPID), con preferencias por
  usuario y botón de prueba.

Detalles, seguridad del alta de administradores y archivos cambiados en
[`NUEVAS_FUNCIONES.md`](NUEVAS_FUNCIONES.md).

## Ejecución con Docker Compose (recomendado)

Requisitos: Docker Desktop (Windows/macOS) o Docker Engine + **Compose v2** (Linux), con el daemon en marcha.
Guía completa y solución de problemas: **[`GUIA_DOCKER.md`](GUIA_DOCKER.md)**.

```bash
# 1. Copiar variables de entorno (opcional: todos los valores tienen default)
cp .env.example .env          # Windows: copy .env.example .env

# 2. Levantar todos los servicios (DB + Redis + Backend + Frontend)
docker compose up --build -d
#   Windows también puedes ejecutar:  levantar.bat
#   Linux/macOS:                     bash levantar.sh

# 3. Acceder
#    Frontend : http://localhost:3000
#    API      : http://localhost:3000/api/health  (proxy de nginx, sin CORS)
#    API      : http://localhost:8000/docs       (acceso directo, Swagger)
```

El frontend llama a la API por `/api` y **nginx la reenvía a `backend:8000`**, así que funciona
desde `localhost`, desde otra IP o desde un túnel. Si prefieres que el navegador ataque
directamente al puerto 8000, define `VITE_API_URL` en `.env` y **recompila** el frontend
(`docker compose up --build -d frontend`).

Puertos por defecto en el host: `3000` (web), `8000` (API), `5433` (PostgreSQL) y `6380` (Redis);
todos se cambian en `.env`. Los puertos internos siguen siendo `5432` y `6379`.

> El backend **crea la base de datos y siembra datos demo** automáticamente al arrancar (roles, admin, propiedades, finanzas, etc.). Es 100 % funcional desde el primer arranque.

### Credenciales de demostración

| Campo | Valor |
|-------|-------|
| Correo | `admin@multiadmin.com` |
| Contraseña | `Admin2026!` |

## Desarrollo local (sin Docker)

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # o: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev          # inicia en http://localhost:3000
```

La app espera un PostgreSQL y Redis en ejecución (o usa Docker para `db` y `redis`):

```bash
docker compose up -d db redis
```

Sin PostgreSQL la API **también arranca**: cae automáticamente a SQLite
(`backend/multiadmin.db`) y lo indica en el log y en `/health`.
Para crear la base manualmente: `./db/crear_bd.sh` (Windows: `db\crear_bd.bat --recrear`).
Todo el detalle está en [`ARRANQUE_RAPIDO.md`](ARRANQUE_RAPIDO.md).

## Recuperación de contraseña (SMTP)

Para que el correo se envíe de verdad, configura en `.env`:

```env
MAIL_SERVER=smtp.gmail.com
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASSWORD=tu_contraseña_de_app
MAIL_FROM=tu_correo@gmail.com
```

Si no hay SMTP configurado, el sistema igual guarda el token en la BD y responde de forma segura sin revelar si el correo existe.

## Chatbot

- **Motor local (por defecto):** responde con datos reales de la BD (finanzas, pagos, mantenimiento, propiedades, residentes, documentos, eventos). No requiere servicios de pago.
- **Motor LLM (opcional):** configura `CHATBOT_ENGINE=llm` y `OPENAI_API_KEY` para usar un modelo externo.

## Base de datos y Redis

### Base de datos (PostgreSQL o SQLite)
- El script `db/init.sql` define el **esquema completo** (18 tablas, índices estratégicos, trigger de `updated_at` y el RBAC). Las extensiones (`uuid-ossp`, `pgcrypto`, `vector`) son **opcionales**: si el servidor no las tiene, el script avisa y continúa en vez de abortar.
- **SQLite de respaldo**: si `DATABASE_URL` no está definida o PostgreSQL no responde, la API arranca en SQLite (`backend/multiadmin.db`) en lugar de fallar. Ver [`ARRANQUE_RAPIDO.md`](ARRANQUE_RAPIDO.md).
- **Diagnóstico**: `cd backend && python verificar_bd.py` revisa (y repara) tablas, columnas, roles, permisos y el usuario admin.
- **Crear la base sin Docker**: `./db/crear_bd.sh` (Windows: `db\crear_bd.bat`).
- En **Docker**, se ejecuta automáticamente desde `/docker-entrypoint-initdb.d` cuando el volumen es nuevo, como el usuario `POSTGRES_USER` (dueño), así que los permisos quedan correctos.
- Los datos iniciales (roles, admin, propiedades, finanzas, etc.) los siembra el backend al arrancar (`app/seed.py`), que es **idempotente**: solo pobla si la BD está vacía.

#### Creación manual en PostgreSQL (sin Docker)
```bash
# 1) Ser superusuario (o con psql -U postgres)
sudo -u postgres psql << 'SQL'
  CREATE ROLE multiadmin LOGIN PASSWORD 'multiadmin' CREATEDB;
  CREATE DATABASE multiadmin_db OWNER multiadmin;
  \c multiadmin_db
  GRANT ALL ON SCHEMA public TO multiadmin;
SQL

# 2) Aplicar el esquema
psql -U multiadmin -d multiadmin_db -f db/init.sql

# 3) Arrancar el backend apuntando a esa BD
cd backend
DATABASE_URL=postgresql://multiadmin:multiadmin@localhost:5432/multiadmin_db uvicorn app.main:app --reload
```

> Nota: si ejecutas `init.sql` como un superusuario distinto al de la app, otorga los privilegios:
> `GRANT ALL ON ALL TABLES/SEQUENCES IN SCHEMA public TO multiadmin;`

### Redis
Se usa para 4 casos reales (verificado contra un servidor Redis 8 en vivo):
1. **Caché de respuestas** (estadísticas del dashboard, resumen financiero, serie mensual) con TTL de 60s — clave `dashboard_stats`, expira automáticamente.
2. **Rate limiting** de login y recuperación de contraseña (anti fuerza bruta) — clave `rl:ip:login:/login`; al superar 5 intentos en 60s devuelve **HTTP 429**.
3. **Revocación de sesiones**: el endpoint `POST /logout` añade el JWT a una *lista negra* en Redis (clave `blacklist:<token>`) con TTL = vida del token; la dependencia `get_current_user` rechaza tokens revocados con `"Sesión cerrada. Inicia sesión de nuevo."`.
4. **Métricas** de uso del sistema.

Si Redis no está disponible (ej. desarrollo sin Docker), el sistema **degrada a memoria** automáticamente y sigue funcionando.

#### Configurar y ver Redis
```bash
# En Docker, el backend ya usa REDIS_URL=redis://redis:6379/0.

# Ver las claves activas (caché, blacklist, rate-limit)
redis-cli keys '*'

# TTL de la caché del dashboard (~60s)
redis-cli ttl dashboard_stats

# Ver la lista negra de tokens (sesiones cerradas)
redis-cli keys 'blacklist:*'

# Vaciar (reinicio)
redis-cli flushall
```

## Estructura

```text
multi-admin/
├── backend/         # FastAPI + SQLAlchemy + Redis
│   └── app/
│       ├── main.py
│       ├── models.py / schemas.py / crud.py
│       ├── chatbot.py / seed.py
│       ├── redis_client.py / deps.py
│       └── routers/ (auth, finanzas, mantenimiento, etc.)
├── frontend/        # React + TS + Tailwind + Framer Motion
│   └── src/
│       ├── pages/ (LandingPage, Login, Register, Dashboard/*)
│       ├── components/ (landing, ui, layout)
│       └── hooks/ lib/ context/ types/ utils/
├── db/
│   └── init.sql     # Esquema completo de PostgreSQL (DDL)
├── docker-compose.yml
└── .env.example
```

---

Desarrollado con React, FastAPI y PostgreSQL. Proyecto académico.
# Multi.Admin

