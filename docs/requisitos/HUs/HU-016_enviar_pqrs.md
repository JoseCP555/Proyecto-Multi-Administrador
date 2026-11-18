# HU-016 — Radicación de PQRS por el residente

| Campo | Valor |
|---|---|
| **ID** | HU-016 |
| **Rol** | Residente |
| **Módulo** | PQRS |
| **Permisos** | `pqrs.crear`, `pqrs.ver` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** residente, **quiero** quiero enviar una PQRS a la administración desde la plataforma,
> **para** para comunicar de forma formal mis solicitudes, quejas o sugerencias al administrador.

## Criterio de aceptación

> El formulario permite clasificar la solicitud por tipo (petición, queja, reclamo, sugerencia). El residente recibe confirmación de radicado y puede consultar el estado de su caso.

## Implementación

### Backend
- `POST /pqrs` — crea la solicitud con `tipo` (`peticion|queja|reclamo|sugerencia`), `categoria`,
  `asunto` y `descripcion`. Genera el **radicado** correlativo `PQRS-<conjunto>-<n>` y responde `201`
  con `estado = "pendiente"`.
- `POST /pqrs/con-adjunto` — misma operación con archivo adjunto (imagen o PDF).
- `GET /pqrs` — el residente sólo ve sus propios casos; el personal ve todos.
  `GET /pqrs/{id}` y `GET /pqrs/{id}/adjunto` para consultar el detalle y el adjunto.
- `PUT /pqrs/{id}/responder`, `PUT /pqrs/{id}/cerrar` y `DELETE /pqrs/{id}` para la administración.

### Frontend
- `frontend/src/pages/Dashboard/PQRS.tsx`: botón **Radicar PQRS** con el formulario (tipo, categoría,
  asunto, descripción, adjunto opcional); el panel muestra el radicado, el estado (pendiente,
  en proceso, cerrada), la respuesta de la administración y los filtros por estado y tipo.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_pqrs_flujo_completo` — radicado, consulta del residente,
  respuesta y cierre por la administración, y `403` cuando el residente intenta responder.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
