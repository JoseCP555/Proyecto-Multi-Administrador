# HU-032 — Notificación al consejo de PQRS de zonas comunes

| Campo | Valor |
|---|---|
| **ID** | HU-032 |
| **Rol** | Consejo del conjunto |
| **Módulo** | PQRS / Notificaciones |
| **Permisos** | `pqrs.ver` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** consejo del conjunto, **quiero** quiero recibir notificaciones cuando un residente envíe una PQRS relacionada con zonas comunes,
> **para** para estar informado de situaciones que requieren atención colectiva del consejo.

## Criterio de aceptación

> El sistema notifica al consejo cuando se radica una PQRS categorizada como 'zona común'. La notificación incluye el resumen y un enlace directo al caso.

## Implementación

### Backend
- `POST /pqrs` (y `/pqrs/con-adjunto`): si `categoria` es `zonas_comunes`/`zona_comun`, se crea una
  notificación de tipo `pqrs_consejo` dirigida a los usuarios con rol consejo, con el radicado, el
  asunto como resumen y `url = /dashboard/pqrs?caso=<id>`.
- La notificación se entrega también por correo y push según las preferencias del consejo.

### Frontend
- El consejo ve el aviso en la campana y al pulsarlo abre `PQRS` con el caso resaltado; el listado
  del consejo incluye las PQRS del conjunto en modo lectura.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_pqrs_flujo_completo` — comprueba que el consejo recibe una
  notificación `pqrs_consejo` al radicarse una queja de zonas comunes.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
