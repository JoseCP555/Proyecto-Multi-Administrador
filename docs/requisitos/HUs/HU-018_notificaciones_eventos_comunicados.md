# HU-018 — Notificaciones de eventos y comunicados

| Campo | Valor |
|---|---|
| **ID** | HU-018 |
| **Rol** | Residente |
| **Módulo** | Notificaciones |
| **Permisos** | `dashboard.ver` (avisos propios) |
| **Estado** | ✅ Implementada |

## Historia

> **Como** residente, **quiero** quiero recibir notificaciones sobre eventos y comunicados del conjunto,
> **para** para estar al tanto de novedades importantes sin tener que revisar la plataforma constantemente.

## Criterio de aceptación

> Las notificaciones llegan por app y correo electrónico cuando el administrador publica un comunicado o evento. El residente puede configurar sus preferencias de notificación.

## Implementación

### Backend
- `notificaciones_servicio.notificar_seguro(...)` genera avisos persistentes al crear eventos
  (`evento.py`), comunicados (`comunicado.py`), documentos, pagos, mantenimientos y residentes; el
  correo y el Web Push se envían según las preferencias del usuario.
- `GET /notificaciones`, `GET /notificaciones/resumen`, `POST /notificaciones/{id}/leer`,
  `POST /notificaciones/leer-todas`, `DELETE /notificaciones/{id}`.
- `GET /notificaciones/preferencias` y `PUT /notificaciones/preferencias` — canales de correo y push,
  tipos suscritos y horario de silencio; `POST /notificaciones/suscripcion` registra el Web Push.

### Frontend
- Campana del layout (`components/layout/*`) con contador, lista de avisos y enlace al módulo;
  `frontend/src/pages/Dashboard/Configuracion.tsx` (preferencias) y botón de **notificación de prueba**.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_comunicado_masivo` verifica que el comunicado genera aviso
  y que el residente lo recibe en `GET /notificaciones`.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
