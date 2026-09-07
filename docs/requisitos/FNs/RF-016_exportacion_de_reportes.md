# RF-016 — Exportación de reportes

## Identificación

| Campo | Valor |
| ------------- | ------------------------------------------- |
| **ID** | RF-016 |
| **Nombre** | Exportación de reportes contables |
| **Módulo** | Reportes Financieros |
| **Prioridad** | Media |
| **Estado** | Pendiente |
| **Fecha** | Julio 2026 |

## Descripción

El Administrador debe poder exportar los reportes contables (ej.
Balances) en formatos estándar como PDF o Excel/CSV.

## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
| ---------------------- | -------- | ----------- | --------------------------------------------------------------------------- |
| `report_type` | Enum | Sí | Valores permitidos: Balance General, Estado de Resultados, Flujo de Caja, Libro Mayor. |
| `property_id` | UUID | Sí | Debe corresponder a una copropiedad registrada. |
| `report_period` | Fecha | Sí | Debe indicar un período válido (mes y año). |
| `export_format` | Enum | Sí | Valores permitidos: PDF, Excel, CSV. |
| `generated_by` | UUID | Sí | Debe corresponder a un administrador autenticado. |

## Proceso

1. El administrador accede al módulo de reportes contables.
2. El sistema muestra la lista de reportes disponibles para exportación.
3. El administrador selecciona el tipo de reporte, la copropiedad, el período y el formato de exportación (PDF, Excel o CSV).
4. El sistema valida que el usuario tenga permisos para exportar el reporte solicitado.
5. El sistema verifica que existan datos para el período seleccionado.
6. El sistema recopila y consolida la información contable correspondiente.
7. El sistema genera el archivo en el formato seleccionado, manteniendo la estructura y los datos del reporte.
8. El sistema almacena un registro de la exportación indicando el usuario, la fecha, la hora y el tipo de reporte generado.
9. El sistema pone el archivo a disposición del administrador para su descarga.
10. El sistema confirma que la exportación se realizó correctamente.

## Salidas
| Escenario | Código HTTP | Respuesta |
| ------------------------------ | ----------- | --------------------------------------------------------------------------------------------- |
| Exportación exitosa | 200 | Archivo del reporte generado correctamente en el formato seleccionado (PDF, Excel o CSV). |
| No existen datos para exportar | 204 | Mensaje indicando que no se encontraron registros para el período seleccionado. |
| Parámetros inválidos | 422 | Detalle de los errores de validación de los datos de entrada. |
| Usuario no autorizado | 403 | Mensaje de error: "No tiene permisos para exportar este reporte". |
| Error interno del servidor | 500 | Mensaje de error indicando que ocurrió un problema durante la generación del archivo. |

## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ----------------------------------------- | -------------- | ---------------------------------------------------------------------- |
| GET | `/api/v1/reports/accounting` | Sí | Consulta los reportes contables disponibles para exportación. |
| GET | `/api/v1/reports/accounting/{report_id}` | Sí | Obtiene la información de un reporte contable específico. |
| GET | `/api/v1/reports/accounting/export` | Sí | Exporta el reporte contable en formato PDF, Excel o CSV. |

## Reglas de negocio
- RN-001: Solo los administradores autorizados pueden exportar reportes contables.
- RN-002: El sistema solo permitirá exportar reportes correspondientes a copropiedades registradas.
- RN-003: Los reportes exportados deben contener información íntegra y actualizada al momento de la generación.
- RN-004: El sistema debe permitir únicamente los formatos de exportación soportados: PDF, Excel y CSV.
- RN-005: Si no existen datos para el período seleccionado, no se generará el archivo de exportación y se notificará al usuario.
- RN-006: Toda exportación de reportes debe registrarse en el historial de auditoría, indicando el usuario, la fecha, la hora y el tipo de reporte exportado.
- RN-007: Los archivos generados deben conservar el formato y la estructura del reporte original, garantizando la legibilidad de la información.
- RN-008: El usuario solo podrá exportar los reportes para los cuales tenga permisos de acceso según su rol.
