# HU-026 — Alerta de gastos que superan el umbral

| Campo | Valor |
|---|---|
| **ID** | HU-026 |
| **Rol** | Consejo del conjunto |
| **Módulo** | Finanzas / Notificaciones |
| **Permisos** | `finanzas.crear`, `finanzas.ver` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** consejo del conjunto, **quiero** quiero recibir alertas cuando se registren movimientos financieros significativos,
> **para** para supervisar el manejo del dinero del conjunto y detectar irregularidades oportunamente.

## Criterio de aceptación

> El sistema notifica al consejo cuando un gasto supera el umbral configurado. La alerta incluye el monto, la categoría y el administrador que registró el movimiento.

## Implementación

### Backend
- `Conjunto.umbral_gasto` (configurable desde `PUT /conjuntos/{id}`, por defecto `2.000.000 COP`).
- Al crear o actualizar un movimiento de tipo gasto en `POST/PUT /finanzas`, si `monto > umbral_gasto`
  se genera la notificación `alerta_gasto` para el consejo con monto, concepto (categoría) y el
  usuario que registró el movimiento.

### Frontend
- `frontend/src/pages/Dashboard/Conjuntos.tsx`: campo **Umbral de alerta de gastos (COP)** con texto
  de ayuda; el consejo recibe la alerta en la campana de notificaciones.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_alerta_por_gasto_sobre_umbral` — se baja el umbral a
  100.000, se registra un gasto mayor y se comprueba la notificación `alerta_gasto` para el consejo.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
