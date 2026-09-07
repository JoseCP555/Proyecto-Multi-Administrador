# RF-018 — Vista financiera del consejo

## Identificación

| Campo | Valor |
| ------------- | ------------------------------------------------------ |
| **ID** | RF-018 |
| **Nombre** | Consulta de información financiera para el Consejo de Administración |
| **Módulo** | Reportes Financieros |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Fecha** | Julio 2026 |

## Descripción

El sistema debe ofrecer al Consejo de Administración una vista de solo
lectura del estado financiero actual, la morosidad, y los reportes de
ingresos/egresos.

## Entradas

## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
| -------------------- | -------- | ----------- | ------------------------------------------------------------------------- |
| `property_id` | UUID | Sí | Debe corresponder a una copropiedad registrada. |
| `report_type` | Enum | Sí | Valores permitidos: Estado Financiero, Morosidad, Ingresos, Egresos. |
| `report_period` | Fecha | No | Debe corresponder a un período válido cuando se aplique el filtro. |
| `council_member_id` | UUID | Sí | Debe corresponder a un miembro activo del Consejo de Administración. |
| `filter_by_unit` | UUID | No | Si se especifica, debe corresponder a una unidad registrada. |
| `export_format` | Enum | No | Valores permitidos: PDF, Excel. Solo para descarga de reportes con permisos autorizados. |

## Proceso

## Proceso

1. El miembro del Consejo de Administración inicia sesión en el sistema.
2. El sistema verifica que el usuario tenga el rol **Consejero** y permisos de consulta.
3. El usuario accede al módulo de reportes financieros.
4. El sistema muestra las opciones de consulta del estado financiero, morosidad e ingresos/egresos de la copropiedad.
5. El usuario selecciona el tipo de reporte y, si lo desea, aplica filtros como período o unidad.
6. El sistema valida los parámetros ingresados y consulta la información financiera correspondiente.
7. El sistema genera una vista consolidada de los datos solicitados en modo de solo lectura.
8. El usuario puede visualizar el estado financiero, los índices de morosidad y el detalle de ingresos y egresos.
9. Si el sistema lo permite, el usuario puede descargar el reporte en el formato autorizado sin modificar la información.
10. El sistema registra la consulta realizada, indicando el usuario, la fecha y la hora para fines de auditoría.
## Salidas

| Escenario | Código HTTP | Respuesta |
| ------------------------------------- | ----------- | --------------------------------------------------------------------------------------------- |
| Consulta realizada exitosamente | 200 | Información financiera mostrada correctamente en modo de solo lectura. |
| Reporte generado exitosamente | 200 | Reporte del estado financiero, morosidad o ingresos/egresos disponible para consulta o descarga. |
| No se encontraron registros | 204 | Mensaje indicando que no existen datos para los filtros seleccionados. |
| Usuario no autorizado | 403 | Mensaje de error: "No tiene permisos para acceder a esta información". |
| Parámetros inválidos | 422 | Detalle de los errores de validación de los filtros ingresados. |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error al consultar la información financiera. |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ---------------------------------------- | -------------- | ------------------------------------------------------------------------ |
| GET | `/api/v1/council/financial-summary` | Sí | Consulta el estado financiero general de la copropiedad. |
| GET | `/api/v1/council/delinquency-report` | Sí | Consulta el reporte de morosidad por unidad. |
| GET | `/api/v1/council/income-expenses` | Sí | Consulta el reporte de ingresos y egresos. |
| GET | `/api/v1/council/reports/export` | Sí | Descarga los reportes financieros autorizados en formato PDF o Excel. |

## Reglas de negocio

- RN-001: Solo los miembros del Consejo de Administración con permisos vigentes podrán consultar la información financiera de la copropiedad.
- RN-002: La información disponible para el Consejo será exclusivamente de **solo lectura**; no podrá ser modificada desde este módulo.
- RN-003: El sistema mostrará únicamente la información correspondiente a la copropiedad a la que pertenece el consejero.
- RN-004: Los datos financieros, de morosidad e ingresos/egresos deberán reflejar la información actualizada al momento de la consulta.
- RN-005: Toda consulta realizada por un miembro del Consejo deberá registrarse en el historial de auditoría, indicando usuario, fecha y hora.
- RN-006: El acceso a los reportes estará restringido según los permisos asignados al rol **Consejero**.
- RN-007: Si el sistema permite la descarga de reportes, estos deberán conservar la integridad de la información y generarse únicamente en los formatos autorizados.
- RN-008: El sistema no permitirá la visualización de información financiera de otras copropiedades a usuarios sin autorización.
