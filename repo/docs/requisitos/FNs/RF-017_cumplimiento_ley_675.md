# RF-017 — Cumplimiento Ley 675

## Identificación

| Campo | Valor |
| ------------- | -------------------------------------------------------------- |
| **ID** | RF-017 |
| **Nombre** | Registro de datos y eventos para cumplimiento de la Ley 675 |
| **Módulo** | Cumplimiento Normativo |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Fecha** | Julio 2026 |

## Descripción

El sistema debe incluir campos y funcionalidades que permitan el
registro de datos y eventos requeridos para el cumplimiento de la Ley
675 de Propiedad Horizontal de Colombia.

## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
| --------------------- | -------- | ----------- | ------------------------------------------------------------------------- |
| `property_id` | UUID | Sí | Debe corresponder a una copropiedad registrada. |
| `event_type` | Enum | Sí | Debe corresponder a un evento definido por la Ley 675. |
| `event_date` | Fecha | Sí | No puede ser una fecha futura. |
| `description` | Texto | Sí | Mínimo 10 caracteres, máximo 1000. |
| `responsible_user` | UUID | Sí | Debe corresponder a un usuario autorizado. |
| `support_document` | Archivo | No | Formatos permitidos: PDF, JPG o PNG. Tamaño máximo 10 MB. |
| `observations` | Texto | No | Máximo 500 caracteres. |
## Proceso

## Proceso

1. El usuario autorizado accede al módulo de cumplimiento normativo.
2. El sistema muestra el formulario para registrar un nuevo dato o evento relacionado con la Ley 675 de Propiedad Horizontal.
3. El usuario selecciona la copropiedad e ingresa la información requerida del evento.
4. El sistema valida que los campos obligatorios estén completos y que la información cumpla con las reglas establecidas.
5. El sistema verifica que el usuario tenga permisos para registrar o modificar información normativa.
6. El sistema almacena el registro del evento en la base de datos junto con la fecha, hora y usuario responsable.
7. Si el usuario adjunta documentos de soporte, el sistema valida el formato y tamaño del archivo antes de almacenarlo.
8. El sistema actualiza el historial de eventos asociados a la copropiedad.
9. El sistema permite consultar, modificar o complementar la información registrada, manteniendo un historial de cambios.
10. El sistema confirma el registro exitoso del dato o evento y lo deja disponible para futuras consultas y auditorías.

## Salidas

## Salidas

| Escenario | Código HTTP | Respuesta |
| --------------------------------------- | ----------- | ------------------------------------------------------------------------------------------- |
| Registro exitoso del evento | 201 | Datos del evento registrados correctamente (`id`, `event_type`, `property_id`, `event_date`, `created_at`). |
| Actualización exitosa del registro | 200 | Información del evento actualizada correctamente. |
| Datos inválidos | 422 | Detalle de los errores de validación de los campos ingresados. |
| Usuario no autorizado | 403 | Mensaje de error: "No tiene permisos para registrar o modificar esta información". |
| Evento no encontrado | 404 | Mensaje de error: "El registro solicitado no existe". |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error durante el registro o actualización del evento. |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ------------------------------------------ | -------------- | ------------------------------------------------------------------------- |
| POST | `/api/v1/compliance/events` | Sí | Registra un nuevo dato o evento relacionado con la Ley 675. |
| GET | `/api/v1/compliance/events` | Sí | Consulta el listado de eventos registrados. |
| GET | `/api/v1/compliance/events/{id}` | Sí | Obtiene la información de un evento específico. |
| PUT | `/api/v1/compliance/events/{id}` | Sí | Actualiza la información de un evento registrado. |
| DELETE | `/api/v1/compliance/events/{id}` | Sí | Elimina un registro de evento cuando esté permitido por las políticas del sistema. |
## Reglas de negocio

- RN-001: Solo los usuarios con permisos de administrador podrán registrar, modificar o eliminar información relacionada con el cumplimiento de la Ley 675.
- RN-002: Todo evento registrado debe estar asociado a una copropiedad existente y activa.
- RN-003: Cada registro debe almacenar automáticamente la fecha, hora y el usuario responsable de la operación.
- RN-004: Los documentos de soporte adjuntos deben cumplir con los formatos y tamaños permitidos por el sistema.
- RN-005: Ningún registro podrá eliminarse físicamente; cuando sea necesario, deberá marcarse como inactivo para conservar el historial de auditoría.
- RN-006: Toda modificación de un registro debe quedar registrada en un historial de cambios, indicando el usuario, la fecha y la información modificada.
- RN-007: La información registrada debe mantenerse disponible para consultas, auditorías y procesos de verificación del cumplimiento de la Ley 675.
- RN-008: El sistema debe garantizar la integridad y trazabilidad de todos los datos y eventos registrados relacionados con el cumplimiento normativo.
