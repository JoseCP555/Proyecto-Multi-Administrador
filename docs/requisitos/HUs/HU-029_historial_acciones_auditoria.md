# HU-029 — Historial de auditoría de acciones

| Campo | Valor |
|---|---|
| **ID** | HU-029 |
| **Rol** | Administrador |
| **Módulo** | Auditoría |
| **Permisos** | `auditoria.ver` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** administrador, **quiero** quiero que el sistema registre un historial de todas las acciones realizadas en la plataforma,
> **para** para tener trazabilidad de los cambios y auditar cualquier acción cuando sea necesario.

## Criterio de aceptación

> El sistema guarda un log con usuario, acción, fecha y hora de cada operación relevante. El historial es visible para el administrador y no puede ser eliminado por usuarios comunes.

## Implementación

### Backend
- `AuditoriaMiddleware` + `auditoria.registrar_seguro(...)`: cada operación relevante guarda
  `usuario_id`, `usuario_nombre`, `rol`, `accion`, `modulo`, `entidad`, `entidad_id`, `detalle`,
  `metodo`, `ruta`, `estado_http`, `ip`, `fecha` y `id_conjunto`.
- `GET /auditoria` (filtros por usuario, módulo, acción y rango de fechas), `GET /auditoria/resumen`
  y `GET /auditoria/exportar.xlsx`.
- No existe endpoint de borrado del log: sólo usuarios con `auditoria.ver` (administración y
  consejo) pueden consultarlo; el residente recibe `403`.

### Frontend
- `frontend/src/pages/Dashboard/Auditoria.tsx`: tabla con usuario, acción, módulo, detalle, IP,
  estado HTTP y fecha/hora, filtros y exportación a Excel.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_auditoria_registra_acciones` (la creación de un evento queda
  registrada con usuario y fecha) y `::test_residente_sin_acceso_a_auditoria` (`403`).

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
