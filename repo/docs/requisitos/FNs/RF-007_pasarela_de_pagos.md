# RF-007 — Integración pasarela de pagos

## Identificación

| Campo         | Valor                               |
| ------------- | ----------------------------------- |
| **ID**        | RF-007                              |
| **Nombre**    | Integración con pasarela de pagos   |
| **Módulo**    | Facturación y Pagos                 |
| **Prioridad** | Alta                                |
| **Estado**    | Pendiente                           |
| **Fecha**     | Febrero 2026                        |
## Descripción

El sistema debe integrar una pasarela de pagos externa para permitir
el pago de cuotas en línea a través de la plataforma.

## Entradas

| Campo                 | Tipo             | Obligatorio | Validaciones                                                                    |
| --------------------- | ---------------- | ----------- | ------------------------------------------------------------------------------- |
| `invoice_id`          | UUID             | Sí          | Debe corresponder a una factura existente y pendiente de pago.                  |
| `resident_id`         | UUID             | Sí          | Debe existir y ser el propietario de la factura.                                |
| `payment_method`      | Texto            | Sí          | Debe corresponder a un método soportado por la pasarela de pagos.               |
| `amount`              | Decimal          | Sí          | Debe ser mayor que cero y coincidir con el valor pendiente de la factura.       |
| `callback_url`        | URL              | Sí          | Debe ser una URL válida para recibir la respuesta de la pasarela de pagos.      |
## Proceso

## Proceso

1. El residente selecciona una factura pendiente de pago desde su estado de cuenta.
2. El frontend envía la solicitud de pago al backend indicando la factura y el método de pago seleccionado.
3. El backend valida que la factura exista, pertenezca al residente y se encuentre en estado **Pendiente**.
4. El sistema crea una transacción de pago y genera la solicitud hacia la pasarela de pagos externa.
5. La pasarela procesa la información y presenta al residente los medios de pago disponibles.
6. El residente completa el proceso de pago en la plataforma de la pasarela.
7. La pasarela notifica al backend el resultado de la transacción mediante un callback o webhook.
8. El backend valida la autenticidad de la respuesta recibida y actualiza el estado de la transacción.
9. Si el pago es exitoso, la factura cambia a estado **Pagada** y el sistema registra el pago realizado.
10. El sistema devuelve la confirmación del resultado de la transacción al residente.
## Salidas

| Escenario                          | Código HTTP | Respuesta                                                                                         |
| ---------------------------------- | ----------- | ------------------------------------------------------------------------------------------------- |
| Pago procesado exitosamente        | 200         | Confirmación del pago y datos de la transacción (`transaction_id`, `invoice_id`, `status`). |
| Factura no encontrada              | 404         | Mensaje de error: "Factura no encontrada".                                                        |
| Factura ya pagada                  | 400         | Mensaje de error: "La factura ya fue pagada".                                                     |
| Pago rechazado por la pasarela     | 402         | Mensaje de error: "El pago fue rechazado por la pasarela de pagos".                               |
| Error de comunicación con la pasarela | 503      | Mensaje de error: "No fue posible establecer comunicación con la pasarela de pagos".              |
| Datos de entrada inválidos         | 422         | Detalle de los errores de validación.         
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ------------------------------------------- | -------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/payments/create` | Sí (Residente) | Crea una transacción de pago y redirige a la pasarela de pagos. |
| POST   | `/api/v1/payments/webhook` | No | Recibe la notificación (callback/webhook) enviada por la pasarela de pagos. |
| GET    | `/api/v1/payments/{transaction_id}` | Sí | Consulta el estado de una transacción de pago. |
| GET    | `/api/v1/payments/history` | Sí | Obtiene el historial de pagos realizados por el residente. |
| GET    | `/api/v1/payments/methods` | Sí | Lista los métodos de pago disponibles ofrecidos por la pasarela. |
## Reglas de negocio

- RN-001: Solo podrán realizar pagos en línea los residentes con facturas en estado `Pendiente`.
- RN-002: Cada transacción de pago deberá estar asociada a una única factura.
- RN-003: El valor enviado a la pasarela de pagos deberá coincidir exactamente con el saldo pendiente de la factura.
- RN-004: El estado de la factura solo cambiará a `Pagada` cuando la pasarela confirme exitosamente la transacción.
- RN-005: Si la pasarela rechaza o cancela el pago, la factura conservará su estado `Pendiente`.
- RN-006: Todas las transacciones deberán registrarse con un identificador único, fecha, hora y estado para fines de auditoría.
- RN-007: Solo se aceptarán las notificaciones (webhooks) provenientes de la pasarela de pagos autorizada y validadas mediante mecanismos de seguridad.
- RN-008: El residente podrá consultar el historial y el estado de sus pagos en cualquier momento.
- RN-009: Si ocurre un error de comunicación con la pasarela, la transacción permanecerá en estado `Pendiente` hasta recibir una confirmación o ser cancelada.
- RN-010: El sistema no permitirá procesar pagos duplicados sobre una factura que ya haya sido pagada.
