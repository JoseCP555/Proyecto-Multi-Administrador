# RF-008 — Consulta de estado de cuenta

## Identificación

## Identificación

| Campo         | Valor                              |
| ------------- | ---------------------------------- |
| **ID**        | RF-008                             |
| **Nombre**    | Consulta de estado de cuenta       |
| **Módulo**    | Facturación y Pagos                |
| **Prioridad** | Alta                               |
| **Estado**    | Pendiente                          |
| **Fecha**     | Febrero 2026                       |

## Descripción

El Residente debe poder consultar en tiempo real su estado de cuenta
detallado, incluyendo movimientos, saldo pendiente y fechas de
vencimiento.

## Entradas
| Campo              | Tipo          | Obligatorio | Validaciones                                                                 |
| ------------------ | ------------- | ----------- | ---------------------------------------------------------------------------- |
| `resident_id`      | UUID          | Sí          | Debe corresponder a un residente registrado y autenticado.                   |
| `property_id`      | UUID          | Sí          | Debe existir y estar asociada al residente.                                  |
| `period`           | Texto         | No          | Formato `YYYY-MM`; si no se envía, se consulta el período actual.            |
| `invoice_status`   | Texto         | No          | Debe corresponder a un estado válido (`Pendiente`, `Pagada` o `Vencida`).    |

## Proceso

1. El residente inicia sesión en la plataforma.
2. El residente accede al módulo **Estado de cuenta**.
3. El frontend envía la solicitud al backend con el identificador del residente y, opcionalmente, los filtros de consulta.
4. El backend valida que el residente esté autenticado y autorizado para consultar únicamente su información.
5. El sistema obtiene las facturas, pagos, movimientos, saldo pendiente y fechas de vencimiento asociados a la propiedad del residente.
6. El backend calcula el saldo actualizado considerando los pagos registrados y las facturas pendientes.
7. El sistema organiza la información cronológicamente y aplica los filtros solicitados, si existen.
8. El backend devuelve el estado de cuenta actualizado al frontend.
9. El frontend presenta al residente el detalle de movimientos, saldo pendiente y fechas de vencimiento en tiempo real.

## Salidas
| Escenario                              | Código HTTP | Respuesta                                                                                          |
| -------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------- |
| Consulta realizada exitosamente        | 200         | Estado de cuenta con facturas, movimientos, saldo pendiente y fechas de vencimiento. |
| Residente no encontrado                | 404         | Mensaje de error: "Residente no encontrado".                                                       |
| Propiedad no asociada al residente     | 403         | Mensaje de error: "No tiene permisos para consultar esta propiedad".                               |
| Estado de cuenta sin movimientos       | 200         | Estado de cuenta vacío con saldo en cero y sin movimientos registrados.                            |
| Datos de consulta inválidos            | 422         | Detalle de los errores de validación.                                                              |
| Error interno del servidor             | 500         | Mensaje de error: "No fue posible consultar el estado de cuenta".                                  |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ---------------------------------------------- | -------------- | ------------------------------------------------------------ |
| GET    | `/api/v1/account-status` | Sí (Residente) | Obtiene el estado de cuenta actualizado del residente autenticado. |
| GET    | `/api/v1/account-status/{property_id}` | Sí (Residente) | Consulta el estado de cuenta de una propiedad específica del residente. |
| GET    | `/api/v1/account-status/movements` | Sí (Residente) | Lista los movimientos financieros asociados al estado de cuenta. |
| GET    | `/api/v1/account-status/invoices` | Sí (Residente) | Consulta las facturas pendientes, pagadas y vencidas del residente. |
| GET    | `/api/v1/account-status/balance` | Sí (Residente) | Obtiene el saldo pendiente actualizado del residente. |
## Reglas de negocio

---

## Reglas de negocio

- RN-001: Cada residente solo podrá consultar el estado de cuenta de las propiedades que tenga asociadas.
- RN-002: La información del estado de cuenta deberá mostrarse en tiempo real con base en los registros más recientes del sistema.
- RN-003: El saldo pendiente se calculará automáticamente considerando las facturas emitidas, los pagos realizados y los ajustes registrados.
- RN-004: Solo los usuarios autenticados con rol **Residente** podrán acceder a su estado de cuenta.
- RN-005: El estado de cuenta deberá incluir el historial de movimientos, las facturas, los pagos realizados y las fechas de vencimiento.
- RN-006: No se permitirá el acceso a la información financiera de otros residentes o propiedades.
- RN-007: Las facturas vencidas deberán identificarse claramente con su estado correspondiente.
- RN-008: Toda consulta del estado de cuenta deberá registrarse en el historial de auditoría del sistema.
- RN-009: Si no existen movimientos financieros registrados, el sistema mostrará un estado de cuenta con saldo en cero y sin movimientos.
- RN-010: La información presentada deberá reflejar automáticamente cualquier pago, factura o ajuste aprobado en el sistema.
