# RF-003 — Carga de comprobantes de pago

## Identificación

| Campo | Valor |
|----------------|--------------------------------------------------------------|
| **ID** | RF-003 |
| **Nombre** | Carga de comprobantes de pago |
| **Módulo** | Finanzas y Estado de Cuenta |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Actor principal** | Residente |
| **Actores secundarios** | Administrador, Sistema de gestión documental, Base de datos |
| **Versión** | 1.0 |
| **Autor** | Equipo de desarrollo |
| **Fecha de creación** | Julio 2026 |
| **Última actualización** | Julio 2026 |

## Descripción

El Residente debe poder cargar comprobantes de pago en formato
PDF o imagen a su estado de cuenta personal para su validación

## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
|--------|----------------|-------------|-----------------------------------------------------------------------|
| `id_factura` | Entero | Sí | Debe corresponder a una factura existente y pendiente de pago. |
| `id_residente` | Entero | Sí | Debe pertenecer a un residente registrado y activo en el sistema. |
| `comprobante_pago` | Archivo (PDF, JPG, JPEG, PNG) | Sí | Solo se permiten archivos PDF o imágenes con un tamaño máximo de 10 MB. |
| `fecha_pago` | Fecha | Sí | No puede ser una fecha posterior a la fecha actual. |
| `valor_pagado` | Decimal | Sí | Debe ser mayor que cero y corresponder al valor de la factura o al pago realizado. |
| `entidad_bancaria` | Texto | No | Máximo 100 caracteres. |
| `numero_transaccion` | Texto | Sí | Debe ser único para evitar registros duplicados. |
| `observaciones` | Texto | No | Máximo 500 caracteres. |

## Proceso
1. El residente inicia sesión en la plataforma utilizando sus credenciales.
2. El sistema valida la autenticación y verifica que el usuario tenga el rol de Residente.
3. El residente accede al módulo **Estado de Cuenta**.
4. El sistema muestra las facturas pendientes y permite seleccionar aquella para la cual desea registrar el pago.
5. El residente selecciona la factura correspondiente y hace clic en la opción **Cargar comprobante de pago**.
6. El sistema despliega un formulario donde el residente ingresa la información requerida y adjunta el comprobante en formato PDF, JPG, JPEG o PNG.
7. El sistema valida que todos los campos obligatorios estén completos.
8. El sistema verifica que el archivo tenga un formato permitido y que no exceda el tamaño máximo establecido.
9. El sistema comprueba que la factura exista, pertenezca al residente y se encuentre pendiente de validación.
10. Si las validaciones son correctas, el sistema almacena el comprobante de forma segura en el servidor.
11. El sistema registra la información del pago en la base de datos y cambia el estado del comprobante a **Pendiente de validación**.
12. El sistema notifica al administrador que existe un nuevo comprobante pendiente de revisión.
13. El sistema confirma al residente que el comprobante fue cargado correctamente y que será revisado por la administración.
14. Finalmente, el comprobante queda disponible para el proceso de validación por parte del administrador.

## Salidas

| Escenario | Código HTTP | Respuesta |
|-------------------------------|------------|--------------------------------------------------------------------------------------------------------------|
| Comprobante cargado exitosamente | 201 | El sistema registra el comprobante, lo asocia a la factura correspondiente y cambia su estado a **Pendiente de validación**. Se muestra un mensaje de confirmación al residente. |
| Factura no encontrada | 404 | Mensaje indicando que la factura seleccionada no existe o no pertenece al residente. |
| Archivo con formato no permitido | 400 | Mensaje indicando que solo se aceptan archivos en formato PDF, JPG, JPEG o PNG. |
| Archivo excede el tamaño permitido | 413 | Mensaje indicando que el archivo supera el tamaño máximo permitido por el sistema. |
| Datos incompletos | 422 | Mensaje indicando los campos obligatorios que faltan por diligenciar. |
| Comprobante ya registrado | 409 | Mensaje indicando que la factura ya tiene un comprobante asociado y no puede registrarse otro hasta finalizar la validación. |
| Usuario sin autorización | 403 | Mensaje indicando que el usuario no tiene permisos para cargar comprobantes sobre la factura seleccionada. |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error inesperado durante el registro del comprobante y que debe intentarse nuevamente más tarde. |
## Endpoints asociados

Método | Ruta | Auth requerida | Descripción |
|--------|-----------------------------------------------|----------------|--------------------------------------------------------------------------|
| POST | `/api/v1/payments/proofs` | Sí (Residente) | Permite registrar y cargar un comprobante de pago asociado a una factura. |
| GET | `/api/v1/payments/proofs` | Sí | Consulta la lista de comprobantes registrados por el residente. |
| GET | `/api/v1/payments/proofs/{id}` | Sí | Obtiene la información detallada de un comprobante de pago específico. |
| PUT | `/api/v1/payments/proofs/{id}` | Sí (Residente) | Permite actualizar un comprobante antes de que sea validado por el administrador. |
| DELETE | `/api/v1/payments/proofs/{id}` | Sí (Residente) | Elimina un comprobante siempre que aún no haya sido revisado por el administrador. |
| GET | `/api/v1/invoices/{id}` | Sí | Consulta la información de la factura a la que pertenece el comprobante de pago. |
## Reglas de negocio

- RN-002: El comprobante de pago deberá estar asociado a una factura de administración existente y pendiente de validación.

- RN-003: El sistema solo permitirá cargar archivos en formato **PDF, JPG, JPEG o PNG**.

- RN-004: El tamaño máximo permitido para el archivo del comprobante será de **10 MB**.

- RN-005: Cada factura podrá tener un único comprobante de pago activo; no se permitirá registrar otro mientras el anterior se encuentre pendiente de validación.

- RN-006: El sistema verificará que el comprobante pertenezca al residente propietario de la factura antes de permitir su registro.

- RN-007: Una vez cargado el comprobante, su estado cambiará automáticamente a **Pendiente de validación**.

- RN-008: El sistema notificará automáticamente al administrador sobre la existencia de un nuevo comprobante pendiente de revisión.

- RN-009: El residente podrá modificar o eliminar el comprobante únicamente mientras este no haya sido revisado por el administrador.

- RN-010: Si el comprobante es aprobado, el sistema actualizará automáticamente el estado de la factura a **Pagada**.

- RN-011: Si el comprobante es rechazado, el sistema notificará al residente indicando el motivo del rechazo y permitirá registrar un nuevo comprobante.

- RN-012: Todas las acciones relacionadas con la carga, modificación, eliminación y validación de comprobantes deberán registrarse en el historial de auditoría del sistema.

- RN-013: El sistema verificará la integridad del archivo antes de almacenarlo para evitar archivos corruptos o inválidos.

- RN-014: Los comprobantes deberán almacenarse de forma segura y solo podrán ser consultados por el residente propietario y los administradores autorizados.

- RN-015: El sistema registrará la fecha y hora de la carga del comprobante, el usuario responsable y la dirección IP desde la cual se realizó la operación para efectos de auditoría y trazabilidad.
