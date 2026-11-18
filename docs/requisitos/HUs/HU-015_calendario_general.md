# HU-015 — Calendario general del conjunto

| Campo | Valor |
|---|---|
| **ID** | HU-015 |
| **Rol** | Residente |
| **Módulo** | Eventos / calendario |
| **Permisos** | `eventos.ver` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** residente, **quiero** quiero ver el calendario general del conjunto con todos los eventos publicados por el administrador,
> **para** para enterarme de actividades, reuniones y fechas importantes de la copropiedad.

## Criterio de aceptación

> El calendario muestra todos los eventos publicados por el administrador. El residente puede filtrar por tipo de evento y ver el detalle de cada uno.

## Implementación

### Backend
- `GET /eventos?tipo=asamblea|actividad|reunion|mantenimiento` — devuelve el calendario del
  conjunto activo ordenado por `fecha` y `hora`; el parámetro `tipo` es opcional (también acepta
  `todos`). Cada registro incluye título, descripción, fecha, hora, tipo, lugar y `notificado_48h`,
  suficiente para el detalle.
- `GET /eventos` sigue devolviendo todos los eventos cuando no se envía filtro (retrocompatible).

### Frontend
- `frontend/src/pages/Dashboard/Eventos.tsx`: selector **Tipo de evento** que filtra el calendario
  y la vista de lista; el calendario (`components/dashboard/CalendarioEventos.tsx`) resalta los días
  con eventos y el panel lateral muestra el detalle del día seleccionado. Al pulsar el título de un
  evento se abre el modal de detalle (tipo, fecha, hora, lugar, descripción).

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_calendario_filtra_por_tipo` — crea un evento de cada tipo,
  comprueba que el listado general los devuelve todos, que `?tipo=asamblea` sólo devuelve asambleas y
  que el detalle viene en el propio listado.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
