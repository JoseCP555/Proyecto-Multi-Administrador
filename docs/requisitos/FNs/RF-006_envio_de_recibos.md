# RF-006 — Envío de recibos electrónicos

## Identificación

| Campo         | Valor                                 |
| ------------- | ------------------------------------- |
| **ID**        | RF-006                                |
| **Nombre**    | Generación y envío de recibo electrónico |
| **Módulo**    | Facturación y Pagos                   |
| **Prioridad** | Alta                                  |
| **Estado**    | Pendiente                             |
| **Fecha**     | Febrero 2026                          |

## Descripción

Tras la aprobación de un pago, el sistema debe generar y enviar
automáticamente un recibo electrónico oficial al residente.

## Entradas

| Campo             | Tipo          | Obligatorio | Validaciones                                                                 |
| ----------------- | ------------- | ----------- | ---------------------------------------------------------------------------- |
| `payment_id`      | UUID          | Sí          | Debe corresponder a un pago aprobado en el sistema.                          |
| `resident_id`     | UUID          | Sí          | Debe existir y estar asociado al pago aprobado.                              |
| `invoice_id`      | UUID          | Sí          | Debe existir y corresponder a la factura pagada.                             |
| `payment_date`    | Fecha/Hora    | Sí          | Debe ser una fecha válida y corresponder al registro del pago.               |
| `payment_amount`  | Decimal       | Sí          | Debe ser mayor que cero y coincidir con el valor registrado del pago.        |
## Proceso

1. El sistema detecta que un pago ha sido aprobado por el Administrador.
2. El backend valida que el pago esté asociado a una factura existente y que su estado sea **Aprobado**.
3. El sistema obtiene la información del residente, la propiedad y la factura correspondiente.
4. Se genera automáticamente un recibo electrónico con un identificador único, incluyendo los datos del pago realizado.
5. El recibo se almacena en el sistema y queda asociado al pago y a la factura correspondiente.
6. El backend genera el documento del recibo en formato PDF.
7. El sistema envía automáticamente el recibo electrónico al correo registrado del residente.
8. Se registra la fecha y hora del envío del recibo para fines de auditoría.
9. La respuesta confirma la generación y el envío exitoso del recibo electrónico.

## Salidas


| Escenario                              | Código HTTP | Respuesta                                                                                              |
| -------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------ |
| Recibo generado y enviado exitosamente | 200         | Mensaje de confirmación y datos del recibo (`receipt_id`, `invoice_id`, `payment_id`, `sent_at`). |
| Pago no aprobado                       | 400         | Mensaje de error: "El pago aún no ha sido aprobado".                                                  |
| Pago o factura no encontrados          | 404         | Mensaje de error: "Pago o factura no encontrados".                                                    |
| Error al generar el recibo             | 500         | Mensaje de error: "No fue posible generar el recibo electrónico".                                     |
| Error al enviar el correo              | 500         | Mensaje de error: "El recibo fue generado, pero no pudo enviarse al correo del residente".            |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ---------------------------------------- | -------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/receipts/generate/{payment_id}` | Sí (Administrador) | Genera el recibo electrónico de un pago aprobado. |
| GET    | `/api/v1/receipts/{receipt_id}` | Sí | Obtiene el detalle de un recibo electrónico. |
| GET    | `/api/v1/receipts/payment/{payment_id}` | Sí | Consulta el recibo asociado a un pago específico. |
| GET    | `/api/v1/receipts/{receipt_id}/pdf` | Sí | Descarga el recibo electrónico en formato PDF. |
| POST   | `/api/v1/receipts/{receipt_id}/send` | Sí (Administrador) | Envía nuevamente el recibo electrónico al correo del residente. |
## Reglas de negocio
---

## Reglas de negocio

- RN-001: El recibo electrónico solo podrá generarse cuando el pago haya sido aprobado por el Administrador.
- RN-002: Cada pago aprobado tendrá un único recibo electrónico asociado.
- RN-003: El recibo deberá contener la información del residente, la propiedad, la factura, el monto pagado y la fecha del pago.
- RN-004: El recibo se generará automáticamente en formato PDF con un identificador único.
- RN-005: El sistema enviará automáticamente el recibo al correo electrónico registrado del residente.
- RN-006: Si el envío del correo falla, el recibo permanecerá almacenado en el sistema y podrá reenviarse posteriormente.
- RN-007: Solo los usuarios autorizados (Administrador y el Residente propietario del recibo) podrán consultar o descargar el recibo electrónico.
- RN-008: Toda generación y envío de recibos deberá registrarse en el historial de auditoría del sistema.
- RN-009: No se permitirá generar múltiples recibos para el mismo pago, salvo mediante un proceso de reenvío o regeneración autorizado.
