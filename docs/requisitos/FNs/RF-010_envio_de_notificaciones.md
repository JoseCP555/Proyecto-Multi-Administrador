# RF-010 — Envío de notificaciones

## Identificación

| Campo         | Valor                                      |
| ------------- | ------------------------------------------ |
| **ID**        | RF-010                                     |
| **Nombre**    | Envío de notificaciones a residentes       |
| **Módulo**    | Comunicaciones                             |
| **Prioridad** | Alta                                       |
| **Estado**    | Pendiente                                  |
| **Fecha**     | Febrero 2026                               |
## Descripción

El sistema debe permitir al Administrador enviar notificaciones push,
email o mensajes a grupos específicos de residentes (ej. morosos, o
por bloque).

## Entradas

| Campo                  | Tipo               | Obligatorio | Validaciones                                                                 |
| ---------------------- | ------------------ | ----------- | ---------------------------------------------------------------------------- |
| `notification_title`   | Texto              | Sí          | Mínimo 3 caracteres, máximo 100.                                             |
| `notification_message` | Texto              | Sí          | Mínimo 5 caracteres, máximo 1000.                                            |
| `notification_type`    | Texto              | Sí          | Debe ser un tipo válido (`Push`, `Email` o `Mensaje`).                       |
| `recipient_group`      | Texto              | Sí          | Debe corresponder a un grupo válido (Todos, Morosos, Bloque, Torre, etc.).   |
| `property_id`          | UUID               | Sí          | Debe corresponder a una copropiedad registrada.                              |
| `block_id`             | UUID               | No          | Obligatorio cuando el grupo seleccionado sea un bloque específico.           |

## Proceso

1. El Administrador inicia sesión y accede al módulo de **Comunicaciones**.
2. El Administrador selecciona el tipo de notificación (Push, Email o Mensaje).
3. El Administrador redacta el título y el contenido de la notificación.
4. El Administrador selecciona el grupo de destinatarios (Todos los residentes, Morosos, Bloque, Torre u otro grupo disponible).
5. El frontend envía la solicitud al backend con la información de la notificación y los destinatarios seleccionados.
6. El backend valida los permisos del Administrador y verifica que los destinatarios existan.
7. El sistema genera la notificación y la distribuye utilizando el canal de comunicación seleccionado.
8. El sistema registra el resultado del envío para cada destinatario (Enviado, Pendiente o Fallido).
9. El backend devuelve la confirmación del envío y el resumen de las notificaciones procesadas.
## Salidas

| Escenario                              | Código HTTP | Respuesta                                                                                                  |
| -------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------- |
| Notificación enviada exitosamente      | 200         | Mensaje de confirmación y resumen del envío (`notification_id`, `total_recipients`, `sent_at`). |
| Grupo de destinatarios no encontrado   | 404         | Mensaje de error: "Grupo de destinatarios no encontrado".                                                  |
| Datos de entrada inválidos             | 422         | Detalle de los errores de validación.                                                                      |
| Sin destinatarios válidos              | 400         | Mensaje de error: "No existen destinatarios para el grupo seleccionado".                                  |
| Error en el envío de la notificación   | 500         | Mensaje de error: "No fue posible enviar la notificación".                                                 |
| Envío parcial                          | 207         | Algunas notificaciones fueron enviadas correctamente y otras presentaron errores durante el proceso.       |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ------------------------------------------- | -------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/notifications` | Sí (Administrador) | Crea y envía una notificación a un grupo de residentes. |
| GET    | `/api/v1/notifications` | Sí (Administrador) | Lista las notificaciones enviadas con filtros por fecha, tipo o estado. |
| GET    | `/api/v1/notifications/{notification_id}` | Sí (Administrador) | Obtiene el detalle de una notificación específica. |
| POST   | `/api/v1/notifications/{notification_id}/resend` | Sí (Administrador) | Reenvía una notificación previamente enviada. |
| GET    | `/api/v1/notifications/history` | Sí (Administrador) | Consulta el historial de notificaciones enviadas. |
| DELETE | `/api/v1/notifications/{notification_id}` | Sí (Administrador) | Elimina una notificación registrada en el sistema. |

## Reglas de negocio

- RN-001: Solo los usuarios con rol **Administrador** podrán crear, enviar, reenviar o eliminar notificaciones.
- RN-002: Toda notificación deberá estar asociada a una copropiedad registrada en el sistema.
- RN-003: El sistema permitirá enviar notificaciones únicamente a grupos de destinatarios válidos (Todos, Morosos, Bloque, Torre u otros definidos).
- RN-004: El contenido de la notificación deberá incluir un título y un mensaje antes de ser enviado.
- RN-005: El sistema enviará las notificaciones únicamente por los canales habilitados (Push, Email o Mensaje).
- RN-006: Cada envío de notificación deberá registrarse con fecha, hora, remitente, destinatarios y estado del envío.
- RN-007: Si uno o varios destinatarios no pueden recibir la notificación, el sistema continuará el envío al resto y registrará los errores correspondientes.
- RN-008: Los residentes solo podrán visualizar las notificaciones dirigidas a ellos o al grupo al que pertenecen.
- RN-009: Toda acción de creación, envío, reenvío o eliminación de notificaciones deberá registrarse en el historial de auditoría.
- RN-010: El sistema conservará el historial de notificaciones enviadas para permitir su consulta y seguimiento por parte del Administrador.
