# HU-023 — Reporte de ingresos y gastos para el consejo

| Campo | Valor |
|---|---|
| **ID** | HU-023 |
| **Rol** | Consejo del conjunto |
| **Módulo** | Reportes / Panel del consejo |
| **Permisos** | `finanzas.ver`, `reportes.ver` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** consejo del conjunto, **quiero** quiero revisar los reportes de pagos y gastos del conjunto,
> **para** para tomar decisiones informadas sobre el presupuesto de la copropiedad.

## Criterio de aceptación

> El consejo puede visualizar el balance de ingresos y egresos filtrado por período. El reporte incluye gráficas resumen y puede exportarse en PDF o Excel.

## Implementación

### Backend
- `GET /finanzas/resumen?desde=&hasta=` — ingresos, egresos, saldo y pendiente de cobro del período
  (caché por período).
- `GET /reportes/finanzas-por-mes?desde=&hasta=` — serie mensual de ingresos para la gráfica.
- `GET /reportes/exportar/consejo.pdf?desde=&hasta=` — PDF con gráfica y tablas
  (`exportar.reporte_consejo_pdf`).
- `GET /reportes/exportar/consejo.xlsx` — mismo reporte en Excel (`exportar.reporte_consejo_xlsx`).

### Frontend
- `frontend/src/pages/Dashboard/Consejo.tsx`: selector de período (3, 6, 12 meses o histórico),
  tarjetas de balance, gráfica de barras y `ExportMenu` con PDF/Excel. También disponible desde
  `Finanzas.tsx`.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_acta_y_reporte_del_consejo` — totales, serie mensual, PDF con
  cabecera `%PDF` y Excel con firma `PK`.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
