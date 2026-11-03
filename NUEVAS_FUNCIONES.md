# Nuevas funciones de la interfaz

Cambios aplicados: **Agregar conjunto** (logo y color), **Crear cuenta** (tipo de
cuenta y reglas de contraseña), **notificaciones reales** (persistentes,
accionables, por correo y push), **equiparación de `admin` con `super_admin`**
y **ojito para ver la contraseña al iniciar sesión**. Todo está conectado al
backend (no es solo decoración).

---

## 1. Logo en "Agregar conjunto" / "Editar conjunto"

Debajo del nombre del conjunto hay un apartado **"Logo del conjunto (opcional)"**:

- Botón **Subir logo** o **arrastrar y soltar** la imagen en el recuadro.
- **Vista previa** inmediata antes de guardar.
- Botón **Quitar** para eliminar el logo de un conjunto ya existente.
- Formatos: **PNG, JPG, WEBP**. Tamaño máximo **2 MB**.
- El archivo se sube a `POST /subidas/logo` (requiere permiso `conjuntos.crear`
  o `conjuntos.editar`) y se guarda en disco dentro del volumen Docker
  `documentos_data` (`/app/archivos_documentos/logos/`). En la base de datos solo
  se guarda una ruta corta, por ejemplo `archivos/logos/9f3c….png`.
- `GET /archivos/logos/<nombre>` sirve la imagen (público, con validación de
  extensión y protección contra *path traversal*).
- El logo se muestra en las **tarjetas del Panel Multi-Administrador** y en el
  desplegable **"Cambiar conjunto"**. Si no hay logo (o la imagen falla) se ve
  la inicial del conjunto, como antes.

> Para quitar un logo se envía `logo: ""`; el backend lo convierte en `NULL`
> (`PUT /conjuntos/{id}`), porque una actualización parcial ignora los `null`.

---

## 2. "Crear cuenta"

### Tipo de cuenta (desplegable)

Nuevo selector con dos opciones:

| Opción | Rol creado | Permisos |
|---|---|---|
| 👤 Usuario (residente) — valor por defecto | `residente` (3) | Consulta de su conjunto |
| 🛡️ Administrador | `admin` (2) | Gestión de residentes, finanzas, documentos, usuarios… |

Debajo del selector aparece una descripción del tipo elegido. El formulario
envía a `/register` (usuarios) o a **`/register/admin`** (administradores).

### Seguridad del alta de administradores

`POST /register/admin` es una ruta **aparte**: el endpoint original `/register`
sigue siendo igual de estricto (un visitante anónimo solo puede crear
residentes), por lo que las pruebas de RBAC siguen pasando sin cambios.

La nueva ruta se controla con:

```env
PERMITIR_REGISTRO_ADMIN=true
```

- **Viene activada por defecto**: en `.env`, en `.env.example`, en
  `docker-compose.yml` y en el propio backend. Es decir, funciona incluso si no
  hay `.env` o si solo aplicaste el parche (modo demo/desarrollo).
- Si aparece el recuadro rojo **"El registro de administradores está
  desactivado"**, tu contenedor se levantó antes de este cambio (o con la
  variable en `false`). Solución: **`docker compose up --build -d`** (un simple
  `restart` no recarga las variables) y comprueba con
  `curl http://localhost:8000/health` que diga
  `"registro_admin_habilitado": true`.
- En producción define `PERMITIR_REGISTRO_ADMIN=false` en `.env` y vuelve a
  levantar: el selector seguirá visible, pero el servidor responderá 403 con un
  mensaje claro. Así se evita que cualquiera se autoproclame administrador.
- Las cuentas creadas por esta ruta **también deben verificar su correo**, igual
  que las de residente. No se crean super administradores.

### Ojito para ver la contraseña

Los dos campos de contraseña tienen un botón con icono de ojo
(`Mostrar contraseña` / `Ocultar contraseña`), con `aria-label` para accesibilidad.

### Requisitos de la contraseña en verde / rojo

Un recuadro muestra en tiempo real:

- ✅ Al menos 8 caracteres
- ✅ Una letra mayúscula
- ✅ Una letra minúscula
- ✅ Al menos un número
- ✅ Las contraseñas coinciden

Reglas en **verde** cuando se cumplen y en **rojo** cuando no (gris antes de
empezar a escribir, para no mostrar una pantalla llena de errores al abrir).
Además:

- Barra de fortaleza de 4 segmentos con etiqueta *Débil / Regular / Buena / Fuerte*.
- Mensaje bajo "Confirmar contraseña": **"Las contraseñas coinciden"** en verde o
  **"Las contraseñas no coinciden"** en rojo, y el borde del campo cambia de color.
- El botón **Registrarse** se desactiva hasta que todas las reglas estén en verde.

> `AuthShell` se ajustó con `my-auto` para que este formulario, que ahora es más
> alto, se pueda desplazar sin que se corte la parte superior en pantallas
> pequeñas.

---

## 3. `admin` ve y puede hacer lo mismo que `super_admin`

Antes el rol `admin` tenía menos permisos (sin respaldo de BD, sin crear/editar
cuentas `super_admin`, sin ver todos los conjuntos, etc.). Ahora **ambos roles
tienen exactamente los mismos 40 permisos** y la interfaz ya no esconde nada a
`admin`.

| Dónde | Qué cambió |
|---|---|
| `backend/app/permisos.py` | `MATRIZ[ADMIN] = MATRIZ[SUPER_ADMIN] = TODOS`; `SOLO_SUPER_ADMIN` queda vacío; nueva función `tiene_acceso_total()` (`rol_id` 1 y 2). |
| `db/init.sql` | Los permisos iniciales del rol 2 se copian de los del rol 1, para que una base de datos nueva nazca igual. |
| Rutas de usuario (`backend/app/routers/usuario.py`) | `admin` puede crear, editar, desactivar y borrar cuentas `super_admin`. |
| Registro autenticado (`backend/app/routers/auth.py`) | `admin` puede crear cuentas con `rol_id=1`. |
| Contexto de conjuntos (`backend/app/conjunto_ctx.py`) | `admin` ve y administra **todos** los conjuntos, igual que el super admin. |
| `frontend/src/lib/permisos.ts` | `rolesAsignables()` ofrece todos los roles (incluido *Super administrador*) a `admin`. |
| `frontend/src/pages/Dashboard/Usuarios.tsx` | `admin` puede editar/borrar filas de super administradores. |
| Menú lateral | Sin cambios: tanto `admin` como `super_admin` ven los 11 módulos (Inicio, Usuarios, Residentes, Propiedades, Finanzas, Mantenimiento, Documentos, Eventos, Chat asistente, Configuración y Dashboard). |

**Lo que NO cambió:** los roles `residente`, `seguridad` y `tesoreria` conservan
sus permisos; el registro público anónimo sigue sin poder elegir un rol
privilegiado (responde 403); y las protecciones para no desactivarse/borrarse a
sí mismo siguen activas. Es decir, solo se subió al `admin`, no se bajó la
seguridad general.

> En el menú de Configuración ahora aparece el botón **Respaldar BD** para
> `admin`, que antes solo veía `super_admin`.

---

## 4. Ojito en la contraseña del inicio de sesión

`frontend/src/pages/Login.tsx` añade al campo de contraseña un botón con icono
de ojo que alterna `type="password"` / `type="text"`:

- Icono `Eye` cuando está oculta y `EyeOff` cuando se está mostrando.
- `aria-label` dinámico (**Mostrar contraseña** / **Ocultar contraseña**).
- `autoComplete="current-password"` para que los gestores de contraseñas
  sigan funcionando.

Es el mismo comportamiento que ya tenían los dos campos de contraseña del
registro; no se tocó el envío ni la validación del formulario.

---

## 5. Color del conjunto en "Agregar conjunto" / "Editar conjunto"

Debajo del logo hay un apartado **"Color del conjunto (opcional)"**:

- **6 colores de paleta**: azul, verde, ámbar, rosa, violeta y cian (los mismos
  que ya usaban las tarjetas), con el nombre y una marca de selección.
- Botón **Automático**: vuelve al comportamiento histórico (color según la
  posición del conjunto en la lista).
- **Color libre**: un selector de color nativo y un campo de texto para
  escribir un hexadecimal (`#0EA5E9`, `#ABC`, …). Se valida en el frontend y
  en el backend (422 si no es válido).
- **Vista previa en vivo**: una tarjeta muestra el avatar, el título, el fondo
  y el botón con el color elegido antes de guardar.

El valor se guarda en la columna **`conjuntos.color`** (id de paleta o
`#rrggbb`) y se devuelve en `GET /conjuntos`. `NULL` = automático. El backend
asigna un color de la paleta automáticamente a los conjuntos que no tienen
ninguno, tanto al crearlos como en el seed de demostración.

El color se aplica a **todo el conjunto**: tarjetas del panel, avatar, selector
"Cambiar conjunto" (punto de color) y —mediante las variables CSS `--pc-*`— a
botones, menú activo, barra de búsqueda, gráficas y fondos del dashboard.
Los colores personalizados generan su propia escala de tonos claros/oscuros
para que el contraste se mantenga legible.

---

## 6. Notificaciones reales

Antes la campana calculaba recordatorios al vuelo: no se guardaban, no se
podían marcar como leídas ni hacer clic en ellas. Ahora son **avisos
persistentes** en la tabla `notificaciones`, uno por usuario, con deduplicación
por `referencia` (un mismo hecho nunca genera dos avisos iguales).

### De dónde nacen

| Origen | Ejemplo |
|---|---|
| Hechos del sistema | Nuevo evento, movimiento financiero, solicitud de mantenimiento, documento, residente, propiedad o conjunto. Se notifica desde el propio endpoint (`notificar_seguro`). |
| Recordatorios calculados | Pagos vencidos, pagos que vencen en 7 días, eventos próximos y mantenimientos críticos sin resolver. |

Los recordatorios se **agrupan por conjunto**: "Hay 24 pagos vencidos por
$2.800.000 en Los Pinos" en vez de 24 avisos idénticos. El recuento y el
importe forman parte de la referencia, así que un cambio en los datos genera
un aviso nuevo. Se recalculan como máximo cada 30 s, de forma perezosa, al
abrir la campana.

Cada aviso respeta el **RBAC**: solo lo reciben los usuarios que tienen el
permiso de ver ese módulo en ese conjunto, y también se filtra al leerlo.

### Qué se puede hacer con ellas

- **Contador real** de no leídas en la campana (antes contaba solo las de
  severidad alta).
- **Marcar como leída** al hacer clic, **marcar todas como leídas** o
  **descartar** (borrado lógico).
- **Navegación**: al hacer clic se abre el módulo correspondiente y, si el
  aviso es de otro conjunto, se cambia el contexto de trabajo.
- **Hora relativa** ("hace 3 min", "ayer") y nombre del conjunto.
- **Actualización automática** cada 30 s y al volver a la pestaña.
- **Preferencias por usuario**: interruptores para activar/desactivar correo
  y notificaciones del navegador (`GET/PUT /notificaciones/preferencias`).
- Botón **"Enviar aviso de prueba"** que crea un aviso real e informa si el
  correo salió y cuántos push se entregaron.

### Correo

`backend/app/correo_notificaciones.py` envía el aviso con **SMTP + STARTTLS**
usando las mismas credenciales de `.env` que la verificación de cuenta. Es
síncrono (`smtplib`) porque los endpoints son `def`, y se ejecuta en un hilo
en segundo plano para no retrasar la respuesta de la API. Se omite para
dominios de prueba y cuentas de demo (evita rebotes), y hay un interruptor
global `NOTIFICACIONES_CORREO=false`. Los recordatorios diarios no se mandan
por correo (evita spam); los hechos discretos y los avisos de severidad alta
sí.

### Push del navegador (Web Push / VAPID)

- `backend/app/push.py` usa **`pywebpush`** para entregar a las suscripciones
  guardadas en `push_suscripciones`, con claves **VAPID** leídas de
  `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`.
- `frontend/public/sw.js` es el service worker que muestra la notificación
  (incluso con la pestaña en segundo plano) y abre la ruta al hacer clic.
- `frontend/src/lib/push.ts` registra el SW, pide permiso, suscribe al
  `PushManager` y envía la suscripción al backend. Si no hay suscripción
  activa, se muestra además un aviso local mientras la pestaña está abierta.
- Genera tus propias claves con:

  ```bash
  python backend/generar_vapid.py           # imprime las variables
  python backend/generar_vapid.py --guardar # las añade al .env
  docker compose up --build -d              # reinicia para tomarlas
  ```

> Las claves VAPID van en `.env` (gitignored). `.env.example` solo lleva los
> marcadores. `GET /notificaciones/config` expone únicamente la clave pública
> y el estado de los canales.

---

## Archivos modificados

```
backend/app/routers/logos.py            NUEVO · subida y servicio de logos
backend/app/routers/auth.py             endpoint /register/admin (con interruptor)
backend/app/routers/conjunto.py         normaliza "" -> NULL al quitar el logo
backend/app/main.py                     registra el router de logos
frontend/src/pages/Dashboard/Conjuntos.tsx   apartado de logo + avatares con imagen
frontend/src/components/layout/SelectorConjunto.tsx  logo en el desplegable
frontend/src/pages/Register.tsx         tipo de cuenta, ojitos y checklist
frontend/src/components/ui/AuthShell.tsx     scroll correcto en formularios altos
frontend/src/lib/api.ts                 exporta API_BASE
frontend/src/lib/logo.ts                urlApi() / urlLogo()
docker-compose.yml, .env.example, .env  PERMITIR_REGISTRO_ADMIN
frontend/src/pages/Login.tsx            ojito en contraseña de inicio de sesión
frontend/src/lib/permisos.ts            admin puede asignar todos los roles
frontend/src/pages/Dashboard/Usuarios.tsx  admin gestiona cuentas super_admin
backend/app/permisos.py                 MATRIZ admin == super_admin, tiene_acceso_total()
backend/app/routers/usuario.py          admin gestiona cuentas super_admin
backend/app/routers/auth.py             admin puede crear rol_id=1
backend/app/conjunto_ctx.py             admin ve todos los conjuntos
db/init.sql                             permisos iniciales del rol 2
backend/tests/test_rbac.py, tests/conftest.py  pruebas y entorno de pruebas

# --- Color del conjunto ---
backend/app/colores.py                  NUEVO · paleta y validación de color
backend/app/models.py                   Conjunto.color
backend/app/schemas.py                  valida/normaliza el color (422 si inválido)
backend/app/routers/conjunto.py         guarda y devuelve el color
backend/app/seed.py                     color estable para los conjuntos demo
db/init.sql, backend/app/main.py        columna + migración idempotente
frontend/src/lib/coloresConjunto.ts     escala por paleta o hexadecimal libre
frontend/src/pages/Dashboard/Conjuntos.tsx      selector de color + vista previa
frontend/src/components/layout/SelectorConjunto.tsx  punto de color
frontend/src/types/index.ts             Conjunto.color

# --- Notificaciones reales ---
backend/app/models.py                   Notificacion, PushSuscripcion, preferencias
backend/app/notificaciones_servicio.py  NUEVO · generación, RBAC y entrega
backend/app/correo_notificaciones.py    NUEVO · SMTP síncrono
backend/app/push.py                     NUEVO · Web Push / VAPID
backend/app/routers/notificacion.py     reescrito (lista, leer, descartar, prefs, prueba)
backend/app/routers/{evento,mantenimiento,finanzas,documento,residente,propiedad,conjunto}.py
                                        generan avisos al crear registros
backend/generar_vapid.py                NUEVO · CLI para generar claves
backend/requirements.txt                pywebpush
frontend/public/sw.js                   NUEVO · service worker
frontend/nginx.conf                     sirve /sw.js sin caché y con scope "/"
frontend/src/lib/push.ts                NUEVO · suscripción Web Push
frontend/src/components/layout/Notificaciones.tsx  reescrito
frontend/src/types/index.ts             Notificacion, PreferenciasNotificacion
backend/tests/test_notificaciones_reales.py  NUEVO · 6 pruebas
.env, .env.example, docker-compose.yml  VAPID + interruptor de correo
GUIA_DOCKER.md, README.md               documentación
```

## Verificación realizada

- `npm ci` + `tsc` + `vite build` → ✅
- `docker compose config` (Compose v2.39.4) → ✅
- Backend contra PostgreSQL + Redis reales: `/register` sigue devolviendo 403 a
  roles privilegiados, `/register/admin` da 403 con el flag apagado y 200 con
  `rol_id=2` con el flag encendido, subida de logo (401 sin token, 400 con
  archivo falso, 201 con PNG válido), lectura pública del logo, y
  creación/lectura/borrado del logo en `/conjuntos` → ✅
- Prueba end-to-end en navegador (Playwright): registrar, iniciar sesión, abrir
  el modal, subir el logo, crear el conjunto y ver el logo en la tarjeta → ✅
  (capturas en `capturas_ui/`).
- **Suite completa de backend: `113 passed`** (`pytest tests/ -q` contra
  PostgreSQL y Redis reales) → ✅
- `db/init.sql` ejecutado en una base de datos vacía con `ON_ERROR_STOP=1` → ✅
  (35/35 permisos iniciales tanto para el rol 1 como para el rol 2).
- Igualdad de roles comprobada por API: `super_admin` y `admin` devuelven
  **40/40 permisos**; `admin` obtiene `200` en `/admin/backup`, `200` al crear un
  `rol_id=1`, `200`/`204` al editar/borrar un super admin, y ve la misma cantidad
  de conjuntos. El registro público con `rol_id=2` sigue devolviendo `403` → ✅
- Comparación visual en navegador: menú lateral de `admin` y `super_admin`
  idéntico (los mismos 11 módulos), botón **Respaldar BD** visible para `admin` y
  ojito del login mostrando/ocultando la contraseña → ✅
  (capturas `7` a `11` en `capturas_ui/`).
- **Suite completa tras estas dos funciones: `119 passed`**
  (`pytest tests/ -q`, incluye las 6 pruebas nuevas de color y notificaciones).
- Color en navegador: elegir paleta, escribir `#0EA5E9`, ver la vista previa y
  comprobar que el backend guardó `#0ea5e9`; `""` vuelve a automático y un
  valor inválido devuelve 422 → ✅ (capturas `12` a `14`).
- Correo: entrega real contra un servidor SMTP local con STARTTLS y AUTH; se
  verificó el asunto, el cuerpo y el enlace del mensaje MIME → ✅
- Web Push: par de claves VAPID válido (P-256, 65/32 bytes), suscripción
  almacenada y `webpush()` invocado con el payload y los claims correctos → ✅
  (capturas `15` y `16` muestran la campana y el aviso de prueba).
- `GET /health`, `/notificaciones/config`, Docker Compose (`docker compose
  config`), `db/init.sql` en BD vacía y build de producción → ✅

> **Límite del entorno de pruebas:** el Chromium del sandbox (headless y bajo
> Xvfb) rechaza `PushManager.subscribe()` con *"Registration failed -
> permission denied"* porque esa compilación no trae credenciales del servicio
> push de Google/FCM. El código del navegador registra el service worker,
> gestiona el permiso y reporta el error con un mensaje claro; en un
> Chrome/Firefox/Edge normal con las notificaciones permitidas la suscripción
> se completa. Usa **"Enviar aviso de prueba"** para comprobarlo en tu equipo.
