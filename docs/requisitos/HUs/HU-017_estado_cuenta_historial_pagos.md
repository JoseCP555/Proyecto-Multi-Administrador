# HU-017 — Estado de cuenta e historial de pagos

| Campo | Valor |
|---|---|
| **ID** | HU-017 |
| **Rol** | Residente |
| **Módulo** | Pagos |
| **Permisos** | `pagos.ver` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** residente, **quiero** quiero consultar mis estados de cuenta y el historial de pagos,
> **para** para verificar que mis pagos han sido realizados, fechas y saldos pendientes del residente autenticado.

## Criterio de aceptación

> El sistema muestra los pagos registrados y el saldo pendiente del residente autenticado. La información se puede exportar en PDF.

## Implementación

### Backend
- `GET /pagos/estado-cuenta` — filtrar por el usuario autenticado: total facturado, total pagado,
  saldo pendiente, próximo vencimiento y el listado de movimientos con su unidad.
- `GET /pagos/estado-cuenta.pdf` — mismo contenido en PDF (`exportar.estado_cuenta_pdf`).

### Frontend
- `frontend/src/pages/Dashboard/Pagos.tsx`: tarjetas de totales, tabla de movimientos con estado y
  botón **Exportar PDF** (`descargarArchivo`). Si el usuario no tiene unidad vinculada se muestra el
  aviso correspondiente.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_estado_de_cuenta_y_pdf` — totales numéricos y PDF que
  empieza por `%PDF`.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
