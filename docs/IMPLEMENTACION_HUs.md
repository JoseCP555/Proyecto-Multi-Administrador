# Implementación de las historias de usuario (HU-01 … HU-32)

Este documento es el **mapa de trazabilidad** entre las 32 historias de usuario del
sistema Multi-Administrador de Copropiedades y el código que las implementa.
El estado es **32/32 historias implementadas** y cubiertas por pruebas automatizadas
o por verificación funcional de la interfaz.

- Ficha detallada de cada historia: [`docs/requisitos/HUs/`](requisitos/HUs/)
  (HU-001 a HU-014 en su formato original y HU-015 a HU-032 con el mismo esquema).
- Resultados de las pruebas: [`REPORTE_TESTING.md`](REPORTE_TESTING.md).

## Resumen

| ID | Rol | Funcionalidad | Backend | Frontend | Verificación |
|---|---|---|---|---|---|
| HU-01 | Administrador | Notificar asambleas con 48 h de antelación | `programador.avisar_asambleas` (push + correo) | Campana de notificaciones | `test_evento_con_hora_y_aviso_48h` |
| HU-02 | Administrador | CRUD de cuentas de residentes | `routers/usuario.py`, `residente.py` | `Residentes.tsx`, `Usuarios.tsx` | `test_unit.py`, RBAC |
| HU-03 | Administrador | Documentos PDF/Word hasta 20 MB | `routers/documento.py` (`MAX_BYTES`, `EXTENSIONES_PERMITIDAS`) | `Documentos.tsx` | `test_documento_pdf_y_limite_de_20mb` |
| HU-04 | Administrador | Programar y gestionar reuniones/asambleas | `routers/evento.py` (`fecha`, `hora`, `tipo`, `lugar`) | `Eventos.tsx` | `test_evento_con_hora_y_aviso_48h` |
| HU-05 | Administrador | Ingresos y gastos con balance en tiempo real | `routers/finanzas.py`, `reporte.dashboard` | `Finanzas.tsx`, `Inicio.tsx` | `test_unit.py` |
| HU-06 | Administrador | Reportes de cartera por unidad en PDF/Excel | `reporte.cartera`, `reportes/exportar/*` | `Finanzas.tsx` (`ExportMenu`) | `test_acta_y_reporte_del_consejo` |
| HU-07 | Administrador | Multi-conjunto sin cambiar de sesión | `conjunto_ctx.py`, `routers/conjunto.py` | Selector **Cambiar conjunto** | `test_unit.py`, RBAC |
| HU-08 | Administrador | Roles y permisos con efecto inmediato | `permisos.py`, `deps.require_permiso` | `lib/usePermisos.ts` | `test_rbac.py`, `test_rbac_consejo` |
| HU-09 | Administrador | Gestión de PQRS (responder y cerrar) | `routers/pqrs.py` | `PQRS.tsx` | `test_pqrs_flujo_completo` |
| HU-10 | Administrador | Reservas sin duplicados de zona/horario | `routers/reserva.py` (`409`) | `Reservas.tsx` | `test_reservas_evitan_duplicados` |
| HU-11 | Administrador | Comunicados masivos por notificación y correo | `routers/comunicado.py` | `Comunicados.tsx` | `test_comunicado_masivo` |
| HU-12 | Administrador | Registro y control de visitantes | `routers/visitante.py` (+ `exportar.xlsx`) | `Visitantes.tsx` | `test_visitantes_registro_y_salida` |
| HU-13 | Residente | Comprobante de pago «En revisión» | `routers/pago.py` (`comprobantes`, `revisar`) | `Pagos.tsx` | `test_comprobante_de_pago` |
| HU-14 | Residente | Reserva de zona común desde la app | `GET /reservas/disponibilidad`, `POST /reservas` | `Reservas.tsx` | `test_disponibilidad_zona` |
| HU-15 | Residente | Calendario general con filtro por tipo y detalle | `GET /eventos?tipo=…` | `Eventos.tsx` | `test_calendario_filtra_por_tipo` |
| HU-16 | Residente | Radicación de PQRS con tipo y radicado | `POST /pqrs`, `GET /pqrs` | `PQRS.tsx` | `test_pqrs_flujo_completo` |
| HU-17 | Residente | Estado de cuenta y exportación en PDF | `GET /pagos/estado-cuenta(.pdf)` | `Pagos.tsx` | `test_estado_de_cuenta_y_pdf` |
| HU-18 | Residente | Notificaciones de comunicados/eventos y preferencias | `notificaciones_servicio.py`, `routers/notificacion.py` | Campana + `Configuracion.tsx` | `test_comunicado_masivo` |
| HU-19 | Residente | Consulta y descarga de documentos por categoría y fecha | `GET /documentos`, `/descargar` | `Documentos.tsx` | `test_documento_pdf_y_limite_de_20mb` |
| HU-20 | Residente | Edición de teléfono, correo y foto | `routers/perfil.py` | `Perfil.tsx` | `test_actualizar_perfil` |
| HU-21 | Residente | Reporte de daño con fotos → tarea pendiente | `mantenimiento` (`categoria`, `evidencias`) | `Mantenimiento.tsx` | `test_mantenimiento_con_categoria_y_evidencia` |
| HU-22 | Consejo | Acta de la última asamblea en PDF, no editable | `documentos` (`403` al editar) | `Consejo.tsx` | `test_acta_y_reporte_del_consejo` |
| HU-23 | Consejo | Reporte de ingresos/egresos por período, gráficas y export | `finanzas/resumen`, `reportes/consejo.pdf/xlsx` | `Consejo.tsx` | `test_acta_y_reporte_del_consejo` |
| HU-24 | Consejo | Aprobar/rechazar solicitudes con quién y cuándo | `routers/aprobacion.py` | `Aprobaciones.tsx` | `test_aprobacion_del_consejo` |
| HU-25 | Consejo | Votaciones: un voto por miembro y resultados al cierre | `routers/votacion.py` (`409`) | `Votaciones.tsx` | `test_votacion_un_solo_voto` |
| HU-26 | Consejo | Alerta cuando un gasto supera el umbral | `Conjunto.umbral_gasto` + notificación `alerta_gasto` | `Conjuntos.tsx` | `test_alerta_por_gasto_sobre_umbral` |
| HU-27 | Administrador | Login, bloqueo 5 intentos/10 min, sesión 30 min inactiva | `routers/auth.py`, `auth_jwt.py` | `AuthContext.tsx`, `Login.tsx` | `test_bloqueo_tras_cinco_intentos`, `test_token_expira_en_30_minutos` |
| HU-28 | Administrador | Interfaz responsiva | API única para web/móvil | Tailwind *mobile first*, menú móvil | Verificación visual (Playwright) |
| HU-29 | Administrador | Auditoría con usuario, acción, fecha y hora | `auditoria.py`, `routers/auditoria.py` | `Auditoria.tsx` | `test_auditoria_registra_acciones`, `test_residente_sin_acceso_a_auditoria` |
| HU-30 | Residente | Recuperación de contraseña con enlace de 30 min | `crud.enviar_recuperacion`, `expira_token` | `Recuperar.tsx`, `Restablecer.tsx` | `test_recuperacion_expira_en_30_minutos` |
| HU-31 | Administrador | Nombre, logo (JPG/PNG ≤ 2 MB), dirección y teléfono | `PUT /conjuntos/{id}`, `POST /conjuntos/{id}/logo` | `Conjuntos.tsx` | Verificación por API e interfaz |
| HU-32 | Consejo | Notificación de PQRS de zonas comunes al consejo | `pqrs.py` (notificación `pqrs_consejo`) | Campana + `PQRS.tsx` | `test_pqrs_flujo_completo` |

## Cómo ejecutar las pruebas

### Pruebas de las historias (aisladas, sin PostgreSQL ni Redis)

```bash
cd backend
rm -f hus_test.db
DESACTIVAR_PROGRAMADOR=1 .venv/bin/python -m pytest tests/test_hus_nuevas.py -q
```

Salida esperada: **24 passed** (HU-01, 03, 04, 09-17, 19-27, 29, 30, 32, RBAC del consejo
y configuración de correo).

### Pruebas unitarias y RBAC

```bash
cd backend
.venv/bin/python -m pytest tests/test_unit.py -q     # 8 passed
# RBAC contra la API en ejecución (PostgreSQL + Redis):
TEST_API_URL=http://localhost:8000 .venv/bin/python -m pytest tests/test_rbac.py -q
```

### Compilación del frontend

```bash
cd frontend
npm ci
npx tsc --noEmit        # 0 errores
npm run build           # ✓ built
```

## Credenciales de demostración

| Rol | Correo | Contraseña |
|---|---|---|
| super_admin / admin | `admin@multiadmin.com` | `Admin2026!` |
| Consejo de administración (rol 6) | `consejo@multiadmin.com` | `Consejo2026!` |
| Residente (rol 3) | `residente@multiadmin.com` | `Residente2026!` |

## Cambios técnicos introducidos

### Base de datos (`app/models.py`)

| Tabla | Historia |
|---|---|
| `pqrs` | HU-09, HU-16, HU-32 |
| `zonas_comunes`, `reservas_zona` | HU-10, HU-14 |
| `comunicados` | HU-11, HU-18 |
| `visitantes` | HU-12 |
| `comprobantes_pago` | HU-13, HU-17 |
| `votaciones`, `votaciones_opciones`, `votos` | HU-25 |
| `solicitudes_aprobacion` | HU-24 |
| `auditoria` | HU-29 |
| `conjuntos.umbral_gasto` | HU-26 |
| `eventos.hora`, `eventos.tipo`, `eventos.notificado_48h` | HU-01, HU-04, HU-15 |
| `usuarios.foto` | HU-20 |
| `tareas_mantenimiento.categoria`, `tareas_mantenimiento.evidencias` | HU-21 |

Las columnas nuevas se crean de forma **idempotente** al arrancar (`app/main.py`:
`ALTER TABLE … IF NOT EXISTS` en PostgreSQL y verificación con `PRAGMA table_info`
en SQLite), por lo que una base de datos existente se actualiza sin migraciones manuales.

### Roles y permisos (`app/permisos.py`)

- Nuevo rol **6 · Consejo de administración**, con acceso de sólo lectura a la información
  del conjunto y permisos de decisión: `aprobaciones.*`, `votaciones.crear|votar|cerrar`,
  `auditoria.ver`, `pagos.ver`, `finanzas.ver`, `reportes.ver`, `pqrs.ver`, `zonas.ver`,
  `reservas.ver`, `visitantes.ver`.
- Permisos nuevos para los módulos: `pqrs.*`, `zonas.*`, `reservas.*`, `comunicados.*`,
  `visitantes.*`, `pagos.*`, `votaciones.*`, `aprobaciones.*`, `auditoria.ver`,
  `perfil.ver|editar`.
- El rol `admin` sigue teniendo la misma matriz que `super_admin`; `tesoreria`,
  `residente` y `seguridad` se ampliaron con los permisos de los módulos que les
  corresponden (ver `tests/test_rbac.py`).

### API (`app/routers/`)

Routers nuevos: `pqrs.py`, `reserva.py` (zonas y reservas), `comunicado.py`, `visitante.py`,
`pago.py` (comprobantes, estado de cuenta), `votacion.py`, `aprobacion.py`, `auditoria.py`,
`perfil.py`. Routers ampliados: `evento.py` (hora, tipo, filtro por tipo, aviso 48 h),
`finanzas.py` (umbral de gasto, filtro por período), `mantenimiento.py` (categoría y
evidencias), `documento.py` (límite de 20 MB y formatos), `reporte.py` (reportes del
consejo, cartera, exportaciones), `conjunto.py` (`umbral_gasto`), `auth.py` (bloqueo y
recuperación).

### Frontend (`src/pages/Dashboard/`)

Páginas nuevas: `PQRS.tsx`, `Reservas.tsx`, `Comunicados.tsx`, `Visitantes.tsx`,
`Pagos.tsx`, `Votaciones.tsx`, `Aprobaciones.tsx`, `Auditoria.tsx`, `Consejo.tsx`,
`Perfil.tsx`. Rutas: `/dashboard/{pqrs,reservas,comunicados,visitantes,pagos,votaciones,aprobaciones,auditoria,consejo,perfil}`,
protegidas por permiso (`components/layout/Sidebar.tsx` + `lib/usePermisos.ts`);
accesos rápidos desde `Inicio.tsx`.
