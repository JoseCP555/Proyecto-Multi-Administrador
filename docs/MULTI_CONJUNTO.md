# Módulo multi-conjunto (HU-07)

Permite administrar **varios conjuntos / copropiedades desde un solo panel**,
cambiando de uno a otro sin cerrar sesión y con la información de cada uno
completamente separada.

---

## 1. Qué se ve en la aplicación

### 1.1 Panel Multi-Administrador (`/dashboard`)

Es la pantalla que aparece al entrar cuando el usuario administra más de un
conjunto (o es super administrador):

- Encabezado **“Panel Multi-Administrador”** con la descripción:
  *“Selecciona un conjunto residencial para gestionar sus habitantes, finanzas,
  documentos, eventos y más. Cada conjunto mantiene sus propias reglas.”*
- Indicadores: **Conjuntos**, **Total habitantes** y **Conjunto activo**.
- Sección **“Tus conjuntos”** (*“Haz clic en uno para gestionarlo”*) con el
  botón **+ Agregar conjunto**.
- Una tarjeta por conjunto con: nombre, dirección, teléfono, **Habitantes** e
  **ID Conjunto #N**, número de propiedades, saldo y la acción *Gestionar*.
- Tarjeta final **“Agregar nuevo conjunto”** (*“Añade otra copropiedad con su
  propio logo y reglas.”*).

Al hacer clic en una tarjeta se entra al **Inicio** de ese conjunto.

Si el usuario sólo tiene **un** conjunto, `/dashboard` lo manda directo a
`/dashboard/inicio` (comportamiento que ya tenía la app).

### 1.2 Trabajar dentro de un conjunto (`/dashboard/inicio`)

Arriba del dashboard aparece el bloque **“GESTIONANDO CONJUNTO”**:

| Elemento | Contenido |
|---|---|
| Título | Nombre del conjunto + badge *Activo* |
| Botón | **Cambiar conjunto** (desplegable) |
| Meta | Dirección · Teléfono · *N* habitantes registrados |
| **Contacto** | Correo y administrador del conjunto |
| **Finanzas** | Cuota de administración y día de cobro |
| **Reglas** | Tipo de reuniones y horario de silencio |

Además, en la **barra superior** (junto al perfil) hay un selector compacto que
muestra el conjunto activo y abre el mismo desplegable.

### 1.3 Desplegable “Cambiar de conjunto”

- Lista **todos** los conjuntos a cargo del usuario, con nombre, dirección y
  número de habitantes.
- Marca con un ✓ el conjunto activo.
- Si hay más de 5 conjuntos incluye un **buscador**.
- Al elegir uno cambia el contexto **sin cerrar sesión** y **sin salir de la
  pantalla actual**: todos los módulos (Residentes, Propiedades, Finanzas,
  Mantenimiento, Documentos, Eventos, Usuarios, Chatbot) se recargan solos con
  la información del nuevo conjunto.
- Incluye la opción **“Ver todos los conjuntos”** para volver al panel.

---

## 2. Base de datos

### Tablas nuevas

| Tabla | Descripción |
|---|---|
| `conjuntos` | Cada copropiedad: nombre, NIT, dirección, ciudad, teléfono, correo, administrador, habitantes, cuota, día de cobro, reunión, silencio, logo, activo. |
| `usuario_conjuntos` | Asignación de un usuario a los conjuntos que tiene a su cargo. |

### Columnas nuevas

`id_conjunto` (FK → `conjuntos.id`, `ON DELETE SET NULL`) en:
`usuarios`, `residentes`, `propiedades`, `movimientos_financieros`,
`tareas_mantenimiento`, `documentos`, `eventos` y `sesiones_chat`.

La migración es **automática e idempotente**: al arrancar, el backend crea las
tablas que falten, añade las columnas con
`ALTER TABLE … ADD COLUMN IF NOT EXISTS` y **reasigna al primer conjunto**
(`id_conjunto = 1`) todos los registros que quedaron sin conjunto, de modo que
nada de lo que ya existía deja de verse.

`db/init.sql` también quedó actualizado para instalaciones nuevas.

---

## 3. Backend

| Archivo | Cambio |
|---|---|
| `app/models.py` | Modelos `Conjunto` y `UsuarioConjunto` + columna `id_conjunto`. |
| `app/schemas.py` | `ConjuntoCreate` / `ConjuntoUpdate` / `ConjuntoResponse`; `id_conjunto` en usuario. |
| `app/conjunto_ctx.py` **(nuevo)** | Contexto del conjunto: conjuntos del usuario, validación de acceso y helpers `filtrar` / `asignar`. |
| `app/routers/conjunto.py` **(nuevo)** | CRUD de conjuntos y asignación de usuarios. |
| `app/permisos.py` | Permisos `conjuntos.ver` / `.crear` / `.editar` / `.eliminar` / `.gestionar`. |
| `app/seed.py` | Conjuntos de demostración, backfill y datos por conjunto. |
| `app/routers/*.py`, `app/exportar.py`, `app/chatbot.py` | Filtrado por conjunto activo. |
| `app/main.py` | Migración, router nuevo y siembra de conjuntos al arrancar. |

### Endpoints

| Método | Ruta | Permiso | Descripción |
|---|---|---|---|
| GET | `/conjuntos` | `conjuntos.ver` | Conjuntos a cargo del usuario (con métricas). |
| GET | `/conjuntos/{id}` | `conjuntos.ver` | Detalle de un conjunto. |
| POST | `/conjuntos` | `conjuntos.crear` | Crear conjunto. |
| PUT | `/conjuntos/{id}` | `conjuntos.editar` | Editar conjunto. |
| DELETE | `/conjuntos/{id}` | `conjuntos.eliminar` | Eliminar (o desactivar si tiene datos). |
| GET | `/conjuntos/{id}/usuarios` | `conjuntos.ver` | Usuarios asignados. |
| POST | `/conjuntos/{id}/usuarios/{usuario_id}` | `conjuntos.editar` + `usuarios.editar` | Asignar usuario. |
| DELETE | `/conjuntos/{id}/usuarios/{usuario_id}` | `conjuntos.editar` + `usuarios.editar` | Retirar usuario. |

### ¿Cómo se elige el conjunto activo?

El frontend envía la cabecera **`X-Conjunto-Id`** en todas las peticiones.
El backend la valida contra los conjuntos del usuario:

- Si el id **no** pertenece al usuario → **HTTP 403** (CA-07.7).
- Si no llega la cabecera, el super administrador conserva la vista global
  histórica y el resto trabaja sobre su único conjunto.

La caché de Redis del dashboard (`dashboard_stats`, `finanzas_por_mes`,
`finanzas_resumen`) ahora se guarda **por conjunto**, así las cifras nunca se
mezclan.

### Reglas de acceso

- **super_admin**: todos los conjuntos (permiso `conjuntos.gestionar`).
- **admin**: crea y edita conjuntos; ve los que se le asignen.
- **resto de roles**: sólo lectura (`conjuntos.ver`) de sus conjuntos.
- Un usuario sin asignación explícita cae en el primer conjunto del sistema
  (lo hace el seed automáticamente para no dejar la pantalla vacía).

---

## 4. Frontend

| Archivo | Cambio |
|---|---|
| `src/context/ConjuntoContext.tsx` **(nuevo)** | Estado global: conjuntos, conjunto activo, `seleccionar(id)`. |
| `src/components/layout/SelectorConjunto.tsx` **(nuevo)** | Desplegable “Cambiar conjunto” (variantes `banner` y `topbar`). |
| `src/pages/Dashboard/Conjuntos.tsx` **(nuevo)** | Panel Multi-Administrador + alta/edición/eliminación. |
| `src/pages/Dashboard/Inicio.tsx` | Bloque “GESTIONANDO CONJUNTO” y recarga de cifras al cambiar. |
| `src/components/layout/Topbar.tsx` | Selector compacto y título *Inicio*. |
| `src/components/layout/Sidebar.tsx` | Ítem *Inicio*; *Dashboard* sólo si hay más de un conjunto. |
| `src/lib/api.ts` | Cabecera `X-Conjunto-Id` automática + persistencia en `localStorage`. |
| `src/hooks/useFetch.ts` | Recarga los datos al cambiar de conjunto. |
| `src/App.tsx`, `src/main.tsx` | Rutas `/dashboard/inicio`, `/dashboard/conjuntos` y provider. |

---

## 5. Datos de demostración

El seed crea 4 conjuntos (idempotente: se puede ejecutar mil veces):

| # | Conjunto | Dirección | Habitantes | Cuota | Administrador |
|---|---|---|---|---|---|
| 1 | Conjunto Residencial Los Pinos | Cra 15 #45-67, Bogotá | 248 | $180.000 | Carlos Ramírez |
| 2 | Edificio Altos del Parque | Calle 82 #12-34, Chapinero | 186 | $240.000 | María Fernanda López |
| 3 | Reservas de la Colina | Av. Circunvalar #99-88, Norte | 312 | $210.000 | Andrés Felipe Murcia |
| 4 | Torres de San Martín | Cra 50 #23-11, Teusaquillo | 164 | $195.000 | Luz Dary Castañeda |

Cada uno recibe sus propios residentes, propiedades, movimientos financieros,
tareas de mantenimiento, documentos y eventos, con cifras distintas.

---

## 6. Compatibilidad

- Nada de lo anterior se eliminó: los módulos, rutas y respuestas existentes
  siguen igual y sólo se les agregó el filtro por conjunto.
- Si la base no tiene ningún conjunto, `conjunto_activo` devuelve `None` y los
  endpoints se comportan exactamente como antes (sin filtro).
- La configuración global (`/configuracion`) sigue siendo única para todo el
  sistema: no se dividió por conjunto porque la tabla tiene `clave` única.
