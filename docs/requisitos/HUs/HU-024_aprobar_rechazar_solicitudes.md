# HU-024 — Aprobación o rechazo de solicitudes del administrador

| Campo | Valor |
|---|---|
| **ID** | HU-024 |
| **Rol** | Consejo del conjunto |
| **Módulo** | Aprobaciones |
| **Permisos** | `aprobaciones.ver`, `aprobaciones.crear`, `aprobaciones.decidir` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** consejo del conjunto, **quiero** quiero aprobar o rechazar solicitudes enviadas por el administrador,
> **para** para mantener el control y la transparencia en las decisiones administrativas.

## Criterio de aceptación

> Las solicitudes del administrador aparecen en el panel del consejo con opción de aprobar o rechazar. La decisión queda registrada con fecha, hora y miembro que la tomó.

## Implementación

### Backend
- `POST /aprobaciones` — el administrador crea la solicitud (`tipo`, `titulo`, `descripcion`,
  `monto`); queda `pendiente` y se notifica al consejo.
- `GET /aprobaciones` — el consejo ve todas las solicitudes del conjunto (pendientes y decididas).
- `PUT /aprobaciones/{id}/decidir` — `{decision: "aprobada"|"rechazada", comentario}` guarda
  `decidido_por`, `decidido_por_nombre`, `fecha_decision` (fecha y hora) y el comentario.

### Frontend
- `frontend/src/pages/Dashboard/Aprobaciones.tsx`: tarjetas con monto, tipo, descripción y botones
  **Aprobar**/**Rechazar**; las decididas muestran quién y cuándo decidió.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_aprobacion_del_consejo` — creación por el administrador,
  decisión del consejo y persistencia de `decidido_por` y `fecha_decision`.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
