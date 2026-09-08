# REPORTE DE TESTING — Multi-Administrador

**Fecha:** 2026-09-06
**Entorno:** Backend conectado a **PostgreSQL real** y **Redis real** en vivo. Frontend servido en `:3000` (dev) y build de producción generado.

---

## 1. Resumen de resultados

| Año | Método | Resultado |
|-----|--------|-----------|
| API (integración) | `pytest tests/test_api.py` — 20 pruebas | ✅ **20/20 passed** |
| Backend (unit) | `pytest tests/test_unit.py` — 8 pruebas | ✅ **8/8 passed** |
| Frontend | `tsc --noEmit` (strict) | ✅ **0 errores** |
| Frontend | `vite build` (producción) | ✅ **OK** |
| Recuperación de contraseña | end-to-end manual | ✅ **funciona** |
| Rutas SPA | 7 rutas | ✅ **todas 200** |
| Docker Compose | validación YAML | ✅ **válido** |
| **TOTAL backend** | 28 pruebas | ✅ **28/28** |

---

## 2. Backend — API (integración, contra PostgreSQL + Redis reales)

`backend/tests/test_api.py` — `pytest -v` → **20 passed**.

- `test_health` / `test_root` → servicio sano.
- `test_roles` → existen `super_admin`, `admin`, `residente`, etc.
- `test_login_correcto` → JWT emitido correctamente.
- `test_login_incorrecto` → credenciales erróneas rechazadas.
- `test_register_duplicado` → 400 si el correo existe.
- `test_logout_revoca_token` → token entra a la **blacklist de Redis**; reuso → **401**.
- `test_dashboard_stats`, `test_finanzas_resumen`, `test_finanzas_por_mes` → datos reales.
- `test_listar_propiedades`, `test_listar_residentes`, `test_crear_y_eliminar_propiedad` → CRUD.
- `test_mantenimiento_listar`, `test_documentos_listar`, `test_eventos_listar`, `test_usuarios_listar`.
- `test_chatbot_respuesta`, `test_chatbot_persiste_historial`, `test_chatbot_conceptos` → chatbot con datos reales y persistencia.

## 3. Backend — Unit tests

`backend/tests/test_unit.py` — ✅ **8 passed** (hashing bcrypt, JWT, detección de intents del chatbot, formato de moneda).

## 4. Recuperación de contraseña (end-to-end)

```
Solicitar enlace  → token guardado en BD (30 min)
  → POST /restablecer-password con el token
  → login con la NUEVA contraseña  ✅ ok
  → token de recuperación limpiado en BD ✅
```

## 5. Redis (verificado con `redis-cli`)

| Caso de uso | Clave | Estado |
|-------------|-------|--------|
| Caché de dashboard | `dashboard_stats` | ✅ con TTL |
| Caché finanzas | `finanzas_resumen`, `finanzas_por_mes` | ✅ |
| Revocación de sesión | `blacklist:<token>` | ✅ (rechaza 401) |
| Rate limiting | `rl:<ip>:login:...` | ✅ (HTTP 429 al exceder) |

## 6. Frontend

- **TypeScript strict** sin errores.
- **Build de producción** generado (`dist/`).
- Todas las rutas SPA responden **200** (landing, login, register, recuperar, dashboard y módulos).
- Login y registro reales contra la API.

## 7. Docker Compose

`docker-compose.yml` **válido** (estructura + servicios `db`, `redis`, `backend`, `frontend`).
Frontend expuesto en **`3000:80`**. El `db` monta `./db/init.sql` (esquema automático) y el backend usa `REDIS_URL=redis:6379`.

> ⚠️ **Nota del sandbox:** Docker no está disponible en este entorno, por lo que **no se pudo levantar `docker compose` aquí**; la validación fue estructural. Los 5 servicios ya fueron probados **de forma equivalente** corriendo nativamente (PostgreSQL 17 real, Redis 8 real, uvicorn, Vite), cubriendo el mismo stack.

## 8. Cómo ejecutar las pruebas

```bash
# Backend (API de integración + unit)
cd backend
.venv/bin/python -m pytest tests/ -v

# Frontend
cd ../frontend
npx tsc --noEmit        # typecheck estricto
npx vite build          # build producción
```

## 9. Editar / Eliminar / Descarga (nuevo, probado en vivo)

- **Editar y eliminar** disponibles en **todos** los módulos del dashboard:
  Usuarios, Residentes, Propiedades, Finanzas, Mantenimiento, Documentos y Eventos.
  Cada fila tiene botones ✏️ (editar, abre modal prellenado) y 🗑️ (eliminar con diálogo de confirmación).
- **Usuarios**: además se puede **activar/desactivar** (clic en el badge de estado).
- **Documentos**:
  - **Subir archivo real** (`POST /documentos/upload`, multipart) → se guarda en disco.
  - **Descargar** (`GET /documentos/{id}/descargar` → `FileResponse` con nombre del archivo).
  - **Editar** metadatos y **eliminar** (borra también el archivo físico).

**Verificado con `curl` real (PostgreSQL + Redis + disco):**
- Subir: id creado, `tamano=68`, `mime=text/plain` ✅
- Descargar: contenido devuelto + `Content-Disposition: filename=Reglamento de prueba` ✅
- Editar: título cambiado y visible en la lista ✅
- Eliminar: `204` y archivo físico borrado ✅
- Propiedades/Residentes/Eventos/Mantenimiento: crear→editar→eliminar → `204` ✅
- Usuarios: editar rol → `admin` ✅

## 10. Pendientes / recomendaciones

- Docker no pudo ejecutarse en este sandbox (validar `docker compose up --build -d` en una máquina con Docker).
- Se probó sin SMTP real (la recuperación guarda el token y no revela si el correo existe). Con credenciales SMTP en `.env` se envía el correo de verdad.
- Opcional: añadir CI (GitHub Actions) que corra estos tests automáticamente.

---

## 11. Auditoría y corrección de permisos por rol (RBAC) — 2026-09-07

### Problemas encontrados (probado en vivo con un usuario por rol)

| # | Problema | Gravedad |
|---|----------|----------|
| 1 | `POST /register` era público y aceptaba `rol_id` → **cualquiera podía registrarse como super_admin** | Crítica |
| 2 | El frontend daba acceso total por `rol_id` 1/2 ignorando la lista real de permisos (bypass de RBAC) | Alta |
| 3 | No existía `DELETE /usuarios/{id}` (la UI mostraba el botón → 405) | Alta |
| 4 | `admin` y `super_admin` tenían exactamente los mismos permisos | Media |
| 5 | Cualquier rol con `chat.usar` podía leer las conversaciones de otros usuarios y obtener saldos/residentes por el chatbot | Alta |
| 6 | Notificaciones mostraban pagos en mora a residentes/seguridad (sin `finanzas.ver`) | Media |
| 7 | Botones "Completar", toggle Activo/Inactivo, "Exportar" y "Respaldar BD" visibles sin permiso | Media |
| 8 | Dashboard de roles sin reportes mostraba siempre 0 (endpoint devolvía 403) | Baja |
| 9 | Un admin podía cambiarse su propio rol, desactivarse o editar al super_admin | Media |
| 10 | Exportar mantenimiento exigía `reportes.ver`, así que residentes/seguridad no podían | Baja |

### Correcciones
- `backend/app/permisos.py`: **matriz única** rol→permisos, sincronizada al arrancar (`sincronizar_permisos`). `db/init.sql` alineado.
- Nuevo permiso `sistema.respaldar`; `usuarios.eliminar` y `sistema.respaldar` exclusivos de super_admin.
- `/register`: público solo como residente; otros roles requieren `usuarios.crear`; super_admin solo por super_admin.
- `DELETE /usuarios/{id}` implementado con reglas (no a uno mismo, no a super_admin si no eres super_admin).
- `PUT /usuarios/{id}`: no cambiar el propio rol ni auto-desactivarse; admin no toca super_admin.
- Chatbot: sesiones aisladas por usuario; respuestas filtradas por permiso de módulo.
- Notificaciones y nuevo `GET /reportes/resumen-basico` filtrados por permisos del rol.
- Frontend: `tienePermiso` usa **solo** `usuario.permisos`; página "Acceso restringido"; selectores de rol según quién edita; botones condicionados a permisos.

### Pruebas
```
backend/tests/test_rbac.py   → 78 passed  (login como los 5 roles, 60+ combinaciones rol×endpoint,
                                escalada por /register, reglas de usuarios, chat, notificaciones)
backend/tests/test_api.py    → 20 passed
backend/tests/test_unit.py   →  8 passed
frontend/tests_ui_rbac.py    → 36/36 OK  (Playwright: login real por rol, menú, rutas bloqueadas,
                                botones visibles/ocultos, dashboard). Capturas en capturas_rbac/
```

---

## 12. Verificación de correo y recuperación de contraseña — 2026-09-07

- **Registro público** → cuenta creada con `correo_verificado = false` + token (24 h) + correo HTML con botón "Verificar mi correo" (`/verificar/{token}`). No puede iniciar sesión hasta confirmar (`codigo: correo_no_verificado`); el login ofrece "Reenviar correo de verificación".
- **Usuarios creados por un administrador** quedan verificados de inmediato (no se les exige el paso).
- **Recuperación** → `/recuperar-password` (respuesta idéntica exista o no el correo) → correo HTML con botón → `/restablecer/{token}` valida el enlace antes de mostrar el formulario (30 min, un solo uso, mínimo 8 caracteres).
- **Migración automática**: al arrancar, el backend añade las columnas nuevas y marca como verificadas las cuentas existentes.
- Sin SMTP configurado la API funciona en **modo demo** (devuelve el enlace en la respuesta).
- Pruebas: `test_rbac.py` +4 (registro→bloqueo→verificar→login; reenvío anti-enumeración; alta por admin verificada; recuperación completa). **Total 111/111 ✅**.
- ⚠️ Envío real con Gmail: la contraseña de aplicación suministrada fue rechazada por Google (`535 BadCredentials`) — ver README/.env.example para generar una nueva.

## 13. Códigos de verificación de 6 dígitos (registro y recuperación)

Además del enlace, cada correo incluye un **código numérico de 6 dígitos** (aleatorio con `secrets`) que se escribe directamente en la aplicación.

| Flujo | Endpoint | Comportamiento |
|---|---|---|
| Registro | `POST /verificar-codigo {correo, codigo}` | Activa la cuenta. Estados: `ok` / `expirado` (24 h) / `invalido`. Idempotente. Rate limit 10/5 min. |
| Reenvío | `POST /reenviar-verificacion` | Genera un código y un enlace nuevos. |
| Olvidé contraseña | `POST /validar-codigo-recuperacion {correo, codigo}` | Si es correcto y vigente (30 min) devuelve el `token` para `POST /restablecer-password`. Rate limit 10/5 min. |

- Comparación en tiempo constante (`secrets.compare_digest`); el código nunca viaja en respuestas HTTP, solo por correo.
- Pantallas: `/register` (paso de código tras crear la cuenta), `/verificar-codigo?correo=` (desde el aviso de "cuenta no verificada" en login), `/recuperar` (correo → código → nueva contraseña). Componente `CodigoInput` (6 casillas, acepta pegar).
- Los enlaces de los correos siguen funcionando (`/verificar/:token`, `/restablecer/:token`).
- Tests: `test_verificacion_con_codigo_de_6_digitos`, `test_recuperacion_con_codigo_de_6_digitos` → suite 113/113.
- Prueba real (Playwright + Gmail real a sl99081201125@gmail.com): registro → código incorrecto rechazado → código correcto verifica → login OK → recuperar → código → nueva contraseña → login OK. Capturas: `capturas_diseno/registro_codigo*.png`, `recuperar_codigo.png`, `recuperar_nueva_password.png`, `recuperar_listo.png`.
