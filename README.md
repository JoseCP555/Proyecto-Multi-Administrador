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
- Gestión de **usuarios** con **RBAC real** (roles: super_admin, admin, residente, tesorería, seguridad y **consejo de administración**). La matriz rol → permisos vive en `backend/app/permisos.py` y se sincroniza en la BD al arrancar.

  | Módulo | super_admin | admin | tesorería | residente | seguridad | consejo |
  |---|---|---|---|---|---|---|
  | Usuarios | CRUD + eliminar | ver/crear/editar | — | — | — | — |
  | Residentes | CRUD | CRUD | ver | — | ver | ver |
  | Propiedades | CRUD | CRUD | ver | ver | ver | ver |
  | Finanzas / reportes | CRUD | CRUD | CRUD | — | — | ver + reportes |
  | Mantenimiento | CRUD | CRUD | — | ver + crear solicitud | ver/crear/editar | ver |
  | Documentos | CRUD + descargar | CRUD + descargar | ver/descargar | ver/descargar | ver/descargar | ver/descargar |
  | Eventos / calendario | CRUD | CRUD | — | ver | ver | ver |
  | PQRS | CRUD + responder | CRUD + responder | ver | crear + ver las propias | ver | ver |
  | Zonas y reservas | CRUD | CRUD | — | reservar + historial | ver | ver |
  | Comunicados | CRUD | CRUD | ver | ver | ver | ver |
  | Visitantes | CRUD + exportar | CRUD + exportar | — | — | CRUD | ver |
  | Pagos / comprobantes | revisar + exportar | revisar + exportar | revisar + exportar | subir + estado de cuenta (PDF) | — | ver |
  | Votaciones | CRUD | CRUD | — | votar | — | crear/votar/cerrar |
  | Aprobaciones | CRUD | CRUD | — | — | — | aprobar/rechazar |
  | Auditoría | ver + exportar | ver + exportar | — | — | — | ver |
  | Mi perfil | editar | editar | editar | editar | editar | editar |
  | Configuración / respaldo BD | sí / sí | sí / — | — | — | — | — |
  | Chatbot | sí | sí | sí (solo módulos permitidos) | sí (solo módulos permitidos) | sí (solo módulos permitidos) | sí (solo módulos permitidos) |

  El registro público (`/register`) siempre crea **residentes**; asignar otro rol exige estar autenticado con `usuarios.crear` (y solo un super_admin crea super_admins).
- Gestión de **residentes** y **propiedades**.
- Gestión **financiera** (conceptos, movimientos, resumen, gráficas, cartera por unidad, umbral de alerta de gastos).
- Mantenimiento (órdenes, prioridades, estados, **categoría y evidencias fotográficas**).
- Documentos (**PDF/Word hasta 20 MB**, actas) y **calendario de eventos** con filtro por tipo.
- **PQRS** con radicado, adjuntos, respuesta y cierre; **notificación al consejo** de las de zonas comunes.
- **Zonas comunes y reservas** con validación de disponibilidad (sin solapamientos).
- **Comunicados** masivos y **control de visitantes** con historial filtrable y exportación.
- **Pagos**: comprobantes con estado «En revisión», revisión por la administración, estado de cuenta y PDF.
- **Consejo de administración**: aprobaciones de solicitudes, votaciones, reportes financieros por período (PDF/Excel) y acta de la asamblea.
- **Auditoría** de todas las acciones (usuario, acción, fecha y hora) y **Mi perfil** con foto.
- Dashboard con estadísticas en tiempo real y chatbot flotante.

## Historias de usuario (32/32)

Las **32 historias de usuario** del proyecto están implementadas y verificadas.
La trazabilidad completa (historia → endpoints → pantalla → prueba) está en
[`docs/IMPLEMENTACION_HUs.md`](docs/IMPLEMENTACION_HUs.md) y cada ficha en
[`docs/requisitos/HUs/`](docs/requisitos/HUs/). El informe de entrega con el resumen,
la trazabilidad, las capturas y los resultados de las pruebas está en
[`docs/Informe_Entrega_HUs.pdf`](docs/Informe_Entrega_HUs.pdf).

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

## Documentación de la API (adición)

El backend de este repositorio está desarrollado con FastAPI. Cuando el backend está en ejecución, se puede consultar la documentación interactiva y el esquema OpenAPI en estas direcciones:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Esquema OpenAPI en JSON: <http://localhost:8000/openapi.json>
- Estado del backend: <http://localhost:8000/health>

Swagger UI y ReDoc muestran las rutas y esquemas registrados por la versión del backend que esté ejecutándose. Algunas operaciones requieren iniciar sesión y tener permisos suficientes. La ruta `/health` informa el estado y parte de la configuración de servicios; no es una prueba completa de todos los módulos.

Este README documenta la API FastAPI de este repositorio. Si el criterio de entrega que menciona la “API del cuarto backend” se refiere a otro backend o repositorio del equipo, no debe identificarse como este sin confirmar primero con el docente cuál es.

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
- **Correo real configurable**: verificación de cuenta y recuperación con SMTP
  (STARTTLS en 587 o SSL en 465), diagnóstico con `python backend/probar_correo.py`
  y estado en `GET /health`; incluye un buzón local (Mailpit) para desarrollo.
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

| Rol | Correo | Contraseña |
|-----|--------|------------|
| super_admin / admin | `admin@multiadmin.com` | `Admin2026!` |
| Consejo de administración | `consejo@multiadmin.com` | `Consejo2026!` |
| Residente | `residente@multiadmin.com` | `Residente2026!` |

El usuario residente de demostración ya tiene una unidad (`A-T1-101`), pagos, una PQRS y
una reserva, para recorrer las historias de su rol sin configurar nada.

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

## Pruebas

```bash
# 24 pruebas de las historias de usuario (SQLite + TestClient, sin servicios externos)
cd backend
rm -f hus_test.db && DESACTIVAR_PROGRAMADOR=1 .venv/bin/python -m pytest tests/test_hus_nuevas.py -q

# Pruebas unitarias
.venv/bin/python -m pytest tests/test_unit.py -q

# RBAC contra la API en ejecución y compilación del frontend
TEST_API_URL=http://localhost:8000 .venv/bin/python -m pytest tests/test_rbac.py -q
cd ../frontend && npm ci && npx tsc --noEmit && npm run build
```

Detalle de cada caso en [`docs/IMPLEMENTACION_HUs.md`](docs/IMPLEMENTACION_HUs.md) y
[`REPORTE_TESTING.md`](REPORTE_TESTING.md).


### Aclaración para registrar pruebas de la entrega (adición)

Los comandos y resultados ya descritos arriba pertenecen a la documentación existente y al reporte de testing. Para la entrega actual, ejecuta las pruebas en la rama y el commit que se van a presentar y registra la salida real; no tomes la presencia de un archivo de test como prueba de que pasó.

En el código consultado en la rama `Main` se observan 10 funciones de prueba (`test_...`) en `backend/tests/test_unit.py` y 30 en `backend/tests/test_hus_nuevas.py`. Es un recuento de funciones escritas, no de ejecuciones exitosas. Las pruebas de `test_hus_nuevas.py` ejercitan la API con `TestClient` y SQLite; no deben sumarse automáticamente como unitarias. Por tanto, ese recuento de `test_unit.py` por sí solo no alcanza un requisito de 20 pruebas unitarias distintas.

Al actualizar el reporte de entrega, registra al menos:

| Fecha de ejecución | Rama / commit | Comando o suite | Tipo de prueba | Aprobadas | Fallidas | Omitidas / errores | Evidencia |
|---|---|---|---|---:|---:|---:|---|
| [completar con la ejecución real] | [completar] | [completar] | [unitaria / API-integración / UI / arranque] | [n] | [n] | [n] | [ruta o enlace] |

No publiques contraseñas, claves, tokens ni datos personales en la salida o en las capturas. Los resultados históricos de `REPORTE_TESTING.md` deben conservar su fecha y no presentarse como una ejecución nueva.

## Correo de verificación y recuperación (SMTP)

Los correos de **verificación de cuenta** y **recuperación de contraseña** se envían
por SMTP. Configura en `backend/.env` (o en el `.env` de la raíz si usas Docker):

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop     # contraseña de APLICACIÓN (16 letras, sin espacios)
MAIL_FROM=tu_correo@gmail.com
```

### Gmail / Google Workspace (paso a paso)

1. Activa la **verificación en dos pasos** en la cuenta: <https://myaccount.google.com/security>.
   Sin esto Google no permite enviar por SMTP.
2. Crea una **Contraseña de aplicación**: <https://myaccount.google.com/apppasswords>
   (nombre, por ejemplo, `Multi-Administrador`). Google muestra 16 letras.
3. Pega esas 16 letras en `EMAIL_PASSWORD`. **No** sirve la contraseña normal de la
   cuenta: si la usas, el servidor responde `535 Username and Password not accepted`.
4. Reinicia el backend y comprueba el diagnóstico.

Si la cuenta es institucional, el administrador de Workspace debe permitir el acceso
SMTP de aplicaciones (política de seguridad → «Acceso de apps menos seguras»/SMTP).

### Comprobar que funciona (sin abrir la aplicación)

```bash
cd backend
.venv/bin/python probar_correo.py                      # diagnóstico de la configuración
.venv/bin/python probar_correo.py tu_correo@gmail.com  # además envía un correo de prueba
```

El comando muestra servidor, puerto, cifrado y autenticación, y traduce los errores
habituales (`535 BadCredentials`, TLS, timeouts, DNS) a instrucciones concretas.
También puedes consultar `GET /health` → `correo` (configurado, servidor, puerto,
cifrado y si la contraseña está definida, nunca la contraseña).

### Otros proveedores

| Proveedor | `MAIL_SERVER` | `MAIL_PORT` | Notas |
|---|---|---|---|
| Gmail / Workspace | `smtp.gmail.com` | 587 (o 465) | Contraseña de aplicación |
| Outlook / Hotmail | `smtp-mail.outlook.com` | 587 | Contraseña de aplicación |
| Resend | `smtp.resend.com` | 587 | usuario `resend`, clave `re_…` |
| Brevo | `smtp-relay.brevo.com` | 587 | usuario y clave SMTP del panel |
| Buzón local de pruebas | `127.0.0.1` | 1025 | `MAIL_AUTH=false` (Mailpit/MailHog) |

### Buzón local para desarrollo (sin credenciales)

Para ver los correos llegar sin usar una cuenta real:

```bash
docker compose --profile correo up -d mailpit    # interfaz web en http://localhost:8025
# en .env:
MAIL_SERVER=mailpit
MAIL_PORT=1025
MAIL_AUTH=false
```

### Que llegue a la bandeja de entrada (no a spam)

El mensaje se construye cumpliendo RFC 5322 y se envía con estas cabeceras:

- `From` con nombre visible: **Multi-Administrador <tu_correo@gmail.com>** (`MAIL_FROM_NAME`).
- `Reply-To` al remitente real, `Message-ID` del dominio del remitente, `Date` y
  `Auto-Submitted: auto-generated` (evita respuestas automáticas).
- Cuerpo **multipart/alternative**: texto plano + HTML (los filtros penalizan solo-HTML).
- Los avisos del sistema añaden `List-Unsubscribe` y `List-Unsubscribe-Post` (Gmail/Yahoo
  lo exigen a los remitentes masivos) y un pie que explica por qué se recibe.
- Nunca se envía al dominio demo `@multiadmin.com` ni a los dominios de prueba, así no
  se generan rebotes que dañen la reputación del remitente.

Al enviar desde una cuenta **@gmail.com** por `smtp.gmail.com`, Google firma con su
propio SPF/DKIM (pasan siempre), por lo que los correos llegan a la bandeja de entrada.
Si algún destinatario los ve en spam:

1. Pídele que pulse **«No es spam»** y añada el remitente a contactos: eso entrena su filtro.
2. Evita enviar muchos correos seguidos desde una cuenta recién creada (calienta la cuenta).
3. Para producción usa **tu propio dominio** con un proveedor transaccional (Resend, Brevo,
   Postmark…) y publica los registros **SPF, DKIM y DMARC** del dominio. Con dominio propio
   autenticado la entregabilidad es notablemente mejor que con un Gmail personal.
4. Define `FRONTEND_URL` con la URL pública: los enlaces a `localhost` no sirven al
   destinatario y son sospechosos para los filtros (el arranque avisa por log si pasa).

### Cifrado y detalles

- `MAIL_PORT=587` → STARTTLS (por defecto); `MAIL_PORT=465` → SSL/TLS automático.
  Puedes forzarlo con `MAIL_STARTTLS` / `MAIL_SSL_TLS`.
- `MAIL_AUTH=false` solo para servidores locales de pruebas.
- `MAIL_TIMEOUT` (por defecto 30 s) y `MAIL_SSL_CERTS=true` (validación del certificado).
- El registro público devuelve `verificacion.enviado` y un mensaje concreto si el
  correo no se pudo enviar; el residente siempre puede usar **«Reenviar verificación»**
  desde el inicio de sesión.
- Si no hay SMTP configurado el sistema sigue funcionando: guarda el token/código en
  la BD y responde sin revelar si el correo existe (anti-enumeración).
- Nunca se envían correos a los dominios de prueba ni a las cuentas demo
  (`@multiadmin.com`), así no se generan rebotes en la cuenta remitente.
- `CORREO_DESHABILITADO=1` desactiva todo envío real (lo usan las pruebas
  automatizadas para no mandar correos).

## Chatbot (Ollama)

- **Motor Ollama (por defecto):** utiliza la última versión estable de **Ollama** (`ollama/ollama:latest`) con el modelo configurado en `OLLAMA_MODEL` (por defecto `llama3.2:3b`), alimentado con los datos reales del conjunto activo y respetando estrictamente los permisos RBAC de cada rol.
- **Descarga automática en Docker:** al levantar `docker compose up --build -d`, el servicio `ollama-init` descarga el modelo automáticamente en el volumen persistente `ollama_data`. También funciona con Ollama instalado localmente en `http://localhost:11434` (`ollama pull llama3.2:3b`).
- **Respaldo local automático:** si Ollama aún está descargando el modelo o no está disponible (o si configuras `CHATBOT_ENGINE=local`), responde automáticamente con el motor local por reglas conectado a la BD sin errores.
- **Diagnóstico en tiempo real:** `GET /chat/estado` muestra la versión de Ollama, el modelo activo y los modelos descargados.

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
│       └── routers/ (auth, finanzas, mantenimiento, pqrs, reserva, comunicado,
│                     visitante, pago, votacion, aprobacion, auditoria, perfil, …)
├── frontend/        # React + TS + Tailwind + Framer Motion
│   └── src/
│       ├── pages/ (LandingPage, Login, Register, Recuperar, Restablecer, Dashboard/*)
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
