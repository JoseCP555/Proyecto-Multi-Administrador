# RF-004 — Validación de comprobantes

## Identificación

| Campo | Valor |
|----------------|----------------------------------------------------------------|
| **ID** | RF-004 |
| **Nombre** | Validación de comprobantes de pago |
| **Módulo** | Finanzas y Gestión de Pagos |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Actor principal** | Administrador |
| **Actores secundarios** | Residente, Sistema de notificaciones, Base de datos |
| **Versión** | 1.0 |
| **Autor** | Equipo de desarrollo |
| **Fecha de creación** | Julio 2026 |
| **Última actualización** | Julio 2026 |

## Descripción

El Administrador debe poder revisar, validar y aprobar o rechazar los
comprobantes de pago cargados.

## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
|--------|------------------------------|-------------|------------------------------------------------------------------------|
| `id_comprobante` | Entero | Sí | Debe corresponder a un comprobante existente y en estado **Pendiente de validación**. |
| `id_administrador` | Entero | Sí | Debe pertenecer a un usuario con el rol de Administrador y encontrarse activo. |
| `estado_validacion` | Lista | Sí | Solo permite los valores **Aprobado** o **Rechazado**. |
| `comentarios` | Texto | No | Máximo 500 caracteres. Obligatorio si el comprobante es rechazado. |
| `fecha_validacion` | Fecha y hora | Sí | Se registra automáticamente con la fecha y hora del sistema. |
| `observaciones` | Texto | No | Información adicional sobre la revisión realizada. |
| `token` | Texto (JWT) | Sí | Debe ser un token válido y vigente del administrador autenticado. |
## Proceso

1. El administrador inicia sesión en la plataforma con sus credenciales.
2. El sistema valida la autenticación y verifica que el usuario tenga el rol de Administrador.
3. El administrador accede al módulo **Validación de Comprobantes**.
4. El sistema muestra la lista de comprobantes con estado **Pendiente de validación**.
5. El administrador selecciona el comprobante que desea revisar.
6. El sistema presenta la información del comprobante, la factura asociada y el archivo cargado por el residente.
7. El administrador verifica que la información del comprobante coincida con los datos de la factura y del pago realizado.
8. El administrador selecciona una de las opciones disponibles: **Aprobar** o **Rechazar**.
9. Si el comprobante es rechazado, el administrador deberá registrar el motivo del rechazo mediante un comentario u observación.
10. El sistema actualiza el estado del comprobante según la decisión tomada.
11. Si el comprobante es aprobado, el sistema actualiza automáticamente el estado de la factura a **Pagada**.
12. Si el comprobante es rechazado, la factura permanecerá pendiente de pago y el residente podrá cargar un nuevo comprobante.
13. El sistema envía una notificación al residente informando el resultado de la validación.
14. Finalmente, el sistema registra en el historial de auditoría la fecha, hora, administrador responsable y la decisión tomada sobre el comprobante.

## Salidas

| Escenario | Código HTTP | Respuesta |
|-------------------------------|------------|---------------------------------------------------------------------------------------------------------------|
| Comprobante aprobado correctamente | 200 | El sistema actualiza el estado del comprobante a **Aprobado**, cambia el estado de la factura a **Pagada** y notifica al residente. |
| Comprobante rechazado | 200 | El sistema actualiza el estado del comprobante a **Rechazado**, mantiene la factura pendiente de pago y envía al residente el motivo del rechazo. |
| Comprobante no encontrado | 404 | Mensaje indicando que el comprobante solicitado no existe en el sistema. |
| Comprobante ya validado | 409 | Mensaje indicando que el comprobante ya fue aprobado o rechazado anteriormente y no puede volver a validarse. |
| Usuario sin permisos | 403 | Mensaje indicando que el usuario no tiene autorización para validar comprobantes de pago. |
| Datos inválidos | 422 | Mensaje indicando que la información suministrada para la validación es incorrecta o incompleta. |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error inesperado durante el proceso de validación y que debe intentarse nuevamente más tarde. |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
|--------|--------------------------------------------------|----------------------|--------------------------------------------------------------------------|
| GET | `/api/v1/payments/proofs/pending` | Sí (Administrador) | Consulta la lista de comprobantes pendientes de validación. |
| GET | `/api/v1/payments/proofs/{id}` | Sí (Administrador) | Obtiene la información detallada de un comprobante de pago. |
| PUT | `/api/v1/payments/proofs/{id}/approve` | Sí (Administrador) | Aprueba un comprobante de pago y actualiza el estado de la factura. |
| PUT | `/api/v1/payments/proofs/{id}/reject` | Sí (Administrador) | Rechaza un comprobante de pago indicando el motivo del rechazo. |
| GET | `/api/v1/invoices/{id}` | Sí | Consulta la información de la factura asociada al comprobante. |
| GET | `/api/v1/users/{id}` | Sí | Consulta la información del residente que registró el comprobante. |

## Reglas de negocio


- RN-001: Solo los usuarios con el rol de **Administrador** podrán revisar, aprobar o rechazar los comprobantes de pago registrados por los residentes.

- RN-002: El sistema solo permitirá validar comprobantes que se encuentren en estado **Pendiente de validación**.

- RN-003: El administrador deberá revisar la información del comprobante y verificar que corresponda a la factura asociada antes de emitir una decisión.

- RN-004: El administrador solo podrá seleccionar uno de los siguientes estados de validación: **Aprobado** o **Rechazado**.

- RN-005: Si el comprobante es rechazado, será obligatorio registrar el motivo del rechazo antes de finalizar la validación.

- RN-006: Cuando un comprobante sea aprobado, el sistema actualizará automáticamente el estado de la factura a **Pagada**.

- RN-007: Cuando un comprobante sea rechazado, la factura permanecerá en estado **Pendiente de pago**, permitiendo al residente cargar un nuevo comprobante.

- RN-008: El sistema notificará automáticamente al residente el resultado de la validación, indicando si el comprobante fue aprobado o rechazado.

- RN-009: Un comprobante aprobado o rechazado no podrá volver a ser modificado ni validado nuevamente.

- RN-010: Todas las acciones de validación deberán registrarse en el historial de auditoría, incluyendo el administrador responsable, la fecha, la hora y la decisión tomada.

- RN-011: El sistema deberá garantizar que únicamente el administrador autenticado pueda realizar la validación del comprobante.

- RN-012: El sistema verificará que el comprobante corresponda a la factura seleccionada y que esta pertenezca al residente que realizó el registro.

- RN-013: La información del comprobante deberá conservarse en el sistema para efectos de consulta, auditoría y trazabilidad, incluso después de haber sido validado.

- RN-014: Si ocurre un error durante el proceso de validación, el sistema no modificará el estado del comprobante ni de la factura hasta que la operación se complete correctamente.

- RN-015: Todas las operaciones relacionadas con la validación de comprobantes deberán realizarse median
