# RF-015 — Reporte financiero

## Identificación

| Campo | Valor |
| ------------- | -------------------------------------- |
| **ID** | RF-015 |
| **Nombre** | Generación de reporte financiero de morosidad |
| **Módulo** | Reportes Financieros |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Fecha** | Julio 2026 |

## Descripción

El sistema debe generar un Reporte Financiero que muestre el estado
de morosidad de cada Copropiedad, clasificado por unidad y
antigüedad de la deuda.

## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
| ------------------ | -------- | ----------- | ------------------------------------------------------------------------ |
| `property_id` | UUID | Sí | Debe corresponder a una copropiedad registrada. |
| `report_period` | Fecha | Sí | Debe indicar un período válido (mes y año). |
| `unit_id` | UUID | No | Si se especifica, debe corresponder a una unidad existente. |
| `debt_status` | Enum | No | Valores permitidos: Al día, Moroso, Vencido. |
| `debt_age` | Entero | No | Debe ser mayor o igual a 0 (días de antigüedad de la deuda). |
| `report_format` | Enum | Sí | Valores permitidos: PDF, Excel, CSV. |

## Proceso

1. El administrador accede al módulo de reportes financieros.
2. El sistema solicita el período y los filtros para generar el reporte.
3. El administrador selecciona la copropiedad, el período y, opcionalmente, la unidad o el estado de la deuda.
4. El sistema valida que los parámetros ingresados sean válidos.
5. El sistema consulta la información financiera de la copropiedad y calcula el estado de morosidad de cada unidad.
6. El sistema clasifica las deudas según su antigüedad (por ejemplo: 0–30, 31–60, 61–90 y más de 90 días).
7. El sistema genera el reporte consolidado con el detalle de las unidades, saldos pendientes y antigüedad de la deuda.
8. El sistema presenta una vista previa del reporte al administrador.
9. El administrador puede exportar el reporte en el formato seleccionado (PDF, Excel o CSV).
10. El sistema registra la fecha y hora de generación del reporte para fines de auditoría.

## Salidas
| Escenario | Código HTTP | Respuesta |
| ----------------------------- | ----------- | -------------------------------------------------------------------------------------------- |
| Reporte generado exitosamente | 200 | Reporte financiero generado con el detalle de morosidad por unidad y antigüedad de la deuda. |
| No se encontraron registros | 204 | Mensaje indicando que no existen datos para los filtros seleccionados. |
| Parámetros inválidos | 422 | Detalle de los errores de validación de los filtros o período seleccionado. |
| Usuario no autorizado | 403 | Mensaje de error: "No tiene permisos para generar este reporte". |
| Error interno del servidor | 500 | Mensaje de error indicando que ocurrió un problema durante la generación del reporte. |

## Endpoints asociados
| Método | Ruta | Auth requerida | Descripción |
| ------ | ------------------------------------------- | -------------- | ------------------------------------------------------------------------ |
| GET | `/api/v1/reports/financial` | Sí | Genera y consulta el reporte financiero de morosidad. |
| GET | `/api/v1/reports/financial/{property_id}` | Sí | Obtiene el reporte financiero de una copropiedad específica. |
| GET | `/api/v1/reports/financial/export` | Sí | Exporta el reporte financiero en formato PDF, Excel o CSV. |

## Reglas de negocio

- RN-001: Solo los administradores autorizados pueden generar reportes financieros de morosidad.
- RN-002: El reporte debe incluir únicamente la información correspondiente a la copropiedad seleccionada.
- RN-003: La morosidad debe clasificarse por unidad y por antigüedad de la deuda.
- RN-004: Los saldos presentados en el reporte deben calcularse con base en la información financiera registrada al momento de la consulta.
- RN-005: El sistema debe excluir del reporte las obligaciones que hayan sido pagadas en su totalidad.
- RN-006: El reporte puede filtrarse por período, unidad o estado de la deuda cuando el administrador lo solicite.
- RN-007: El sistema debe permitir la exportación del reporte en los formatos PDF, Excel o CSV.
- RN-008: Cada generación de un reporte debe registrarse en el historial del sistema, indicando la fecha, hora y el usuario que realizó la consulta.
