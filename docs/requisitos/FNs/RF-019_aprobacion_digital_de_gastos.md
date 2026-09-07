# RF-019 — Aprobación digital de gastos

## Identificación

| Campo | Valor |
| ------------- | ------------------------------------------------------------------- |
| **ID** | RF-019 |
| **Nombre** | Solicitud de aprobación digital para gastos extraordinarios |
| **Módulo** | Consejo de Administración |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Fecha** | Julio 2026 |

## Descripción

El sistema debe permitir al Administrador solicitar la aprobación
digital del Consejo de Administración para gastos imprevistos fuera del
presupuesto ordinario.

## Entradas


| Campo | Tipo | Obligatorio | Validaciones |
| ------------------------ | -------- | ----------- | ------------------------------------------------------------------------ |
| `property_id` | UUID | Sí | Debe corresponder a una copropiedad registrada. |
| `expense_title` | Texto | Sí | Mínimo 5 caracteres, máximo 100. |
| `expense_description` | Texto | Sí | Mínimo 10 caracteres, máximo 1000. |
| `expense_amount` | Decimal | Sí | Debe ser mayor que 0. |
| `support_document` | Archivo | No | Formatos permitidos: PDF, JPG o PNG. Tamaño máximo 10 MB. |
| `approval_deadline` | Fecha | Sí | Debe ser una fecha futura. |
| `requested_by` | UUID | Sí | Debe corresponder a un administrador autenticado. |

## Proceso

1. El administrador accede al módulo de gestión financiera y selecciona la opción para registrar un gasto extraordinario.
2. El sistema solicita la información del gasto, incluyendo el motivo, el valor, la descripción y, si aplica, los documentos de soporte.
3. El administrador diligencia la información requerida y envía la solicitud.
4. El sistema valida que los datos ingresados sean correctos y que el usuario tenga permisos para realizar la solicitud.
5. El sistema registra la solicitud con estado **Pendiente de aprobación**.
6. El sistema notifica digitalmente a los miembros del Consejo de Administración para que revisen la solicitud.
7. Cada miembro del Consejo registra su voto de **Aprobado** o **Rechazado**, pudiendo incluir observaciones.
8. El sistema consolida las respuestas recibidas y determina el resultado de la votación de acuerdo con las reglas establecidas.
9. El sistema actualiza el estado de la solicitud a **Aprobada** o **Rechazada**.
10. El sistema notifica al administrador el resultado final y registra la fecha, hora y participantes del proceso para fines de auditoría.

## Salidas

| Escenario | Código HTTP | Respuesta |
| ----------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------- |
| Solicitud registrada exitosamente | 201 | Datos de la solicitud creados con estado **Pendiente de aprobación**. |
| Solicitud aprobada | 200 | Mensaje indicando que la solicitud fue aprobada por el Consejo de Administración. |
| Solicitud rechazada | 200 | Mensaje indicando que la solicitud fue rechazada por el Consejo de Administración. |
| Datos inválidos | 422 | Detalle de los errores de validación de la solicitud. |
| Usuario no autorizado | 403 | Mensaje de error: "No tiene permisos para realizar esta acción". |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error durante el proceso de aprobación. |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ---------------------------------------------------- | -------------- | --------------------------------------------------------------------------- |
| POST | `/api/v1/council/approvals` | Sí | Registra una nueva solicitud de aprobación para un gasto extraordinario. |
| GET | `/api/v1/council/approvals` | Sí | Consulta el listado de solicitudes de aprobación. |
| GET | `/api/v1/council/approvals/{id}` | Sí | Obtiene la información detallada de una solicitud específica. |
| POST | `/api/v1/council/approvals/{id}/vote` | Sí | Permite a un miembro del Consejo registrar su voto de aprobación o rechazo. |
| PATCH | `/api/v1/council/approvals/{id}/status` | Sí | Actualiza el estado de la solicitud según el resultado de la votación. |

## Reglas de negocio

## Reglas de negocio

- RN-001: Solo los administradores autorizados podrán crear solicitudes de aprobación para gastos extraordinarios.
- RN-002: Toda solicitud deberá estar asociada a una copropiedad registrada y a un gasto que no haga parte del presupuesto ordinario.
- RN-003: La solicitud permanecerá en estado **Pendiente de aprobación** hasta que el proceso de votación finalice.
- RN-004: Únicamente los miembros del Consejo de Administración podrán emitir votos de **Aprobado** o **Rechazado**.
- RN-005: Cada miembro del Consejo podrá votar una única vez por cada solicitud de aprobación.
- RN-006: El sistema determinará el resultado de la solicitud conforme a la cantidad de votos registrados según las políticas definidas por la copropiedad.
- RN-007: Una vez finalizada la votación, la solicitud no podrá modificarse y su resultado quedará registrado para fines de auditoría.
- RN-008: El sistema deberá registrar automáticamente la fecha, hora, usuario solicitante y las decisiones emitidas por cada miembro del Consejo durante el proceso de aprobación.
