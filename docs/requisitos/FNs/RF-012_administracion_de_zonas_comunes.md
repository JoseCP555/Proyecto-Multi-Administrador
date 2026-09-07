# RF-012 — Administración de zonas comunes

## Identificación


| Campo         | Valor                                  |
| ------------- | -------------------------------------- |
| **ID**        | RF-012                                 |
| **Nombre**    | Gestión de zonas comunes               |
| **Módulo**    | Administración de Zonas Comunes        |
| **Prioridad** | Alta                                   |
| **Estado**    | Pendiente                              |
| **Fecha**     | Febrero 2026                           |
## Descripción

El Administrador debe poder crear, editar y eliminar las zonas
comunes de cada Copropiedad, definiendo sus horarios y reglas de uso

## Entradas

| Campo             | Tipo          | Obligatorio | Validaciones                                                                 |
| ----------------- | ------------- | ----------- | ---------------------------------------------------------------------------- |
| `zone_name`       | Texto         | Sí          | Mínimo 3 caracteres, máximo 100.                                             |
| `description`     | Texto         | No          | Máximo 500 caracteres.                                                       |
| `property_id`     | UUID          | Sí          | Debe corresponder a una copropiedad registrada.                              |
| `opening_time`    | Hora          | Sí          | Debe tener un formato de hora válido (`HH:MM`).                              |
| `closing_time`    | Hora          | Sí          | Debe ser posterior a la hora de apertura.                                    |
| `usage_rules`     | Texto         | Sí          | Máximo 1000 caracteres.                                                      |
| `capacity`        | Entero        | Sí          | Debe ser mayor que cero.      
## Proceso

1. El Administrador inicia sesión en la plataforma y accede al módulo de **Zonas Comunes**.
2. El Administrador selecciona la opción para crear, editar o eliminar una zona común.
3. El frontend solicita la información de la zona, incluyendo nombre, descripción, capacidad, horarios de uso y reglas.
4. El backend valida que el usuario tenga permisos de Administrador y que los datos ingresados cumplan con las reglas de validación.
5. Si se trata de una nueva zona, el sistema registra la información y la asocia a la copropiedad correspondiente.
6. Si se trata de una edición, el sistema actualiza la información de la zona común conservando su historial de cambios.
7. Si se solicita la eliminación, el sistema verifica que la zona no tenga reservas activas antes de eliminarla o desactivarla.
8. El sistema guarda los cambios realizados y actualiza la información disponible para los residentes.
9. El backend devuelve la confirmación de la operación realizada y registra la acción en el historial de auditoría.

## Salidas

| Escenario                              | Código HTTP | Respuesta                                                                                                   |
| -------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------- |
| Zona común creada exitosamente         | 201         | Datos de la zona creada (`zone_id`, `zone_name`, `property_id`, `created_at`).                              |
| Zona común actualizada correctamente   | 200         | Mensaje de confirmación y datos actualizados de la zona común.                                              |
| Zona común eliminada correctamente     | 200         | Mensaje de confirmación de la eliminación o desactivación de la zona común.                                 |
| Zona común no encontrada               | 404         | Mensaje de error: "Zona común no encontrada".                                                               |
| Datos de entrada inválidos             | 422         | Detalle de los errores de validación.                                                                       |
| No es posible eliminar la zona         | 400         | Mensaje de error: "La zona común tiene reservas activas y no puede eliminarse".                             |
| Error interno del servidor             | 500         | Mensaje de error: "No fue posible procesar la operación sobre la zona común".                               |
## Endpoints asociados
| Método | Ruta | Auth requerida | Descripción |
| ------ | -------------------------------------------- | -------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/common-zones` | Sí (Administrador) | Crea una nueva zona común para una copropiedad. |
| GET    | `/api/v1/common-zones` | Sí | Lista las zonas comunes registradas de una copropiedad. |
| GET    | `/api/v1/common-zones/{zone_id}` | Sí | Obtiene la información de una zona común específica. |
| PUT    | `/api/v1/common-zones/{zone_id}` | Sí (Administrador) | Actualiza la información, horarios o reglas de una zona común. |
| DELETE | `/api/v1/common-zones/{zone_id}` | Sí (Administrador) | Elimina o desactiva una zona común del sistema. |
| GET    | `/api/v1/common-zones/{zone_id}/availability` | Sí | Consulta la disponibilidad y horarios de una zona común. |

## Reglas de negocio

- RN-001: Solo los usuarios con rol **Administrador** podrán crear, editar o eliminar zonas comunes.
- RN-002: Toda zona común deberá estar asociada a una única copropiedad registrada en el sistema.
- RN-003: Cada zona común deberá tener un nombre único dentro de la misma copropiedad.
- RN-004: La hora de apertura deberá ser anterior a la hora de cierre establecida para la zona común.
- RN-005: No se permitirá eliminar una zona común que tenga reservas activas o futuras; en su lugar deberá desactivarse.
- RN-006: Las reglas de uso y el horario de disponibilidad deberán estar definidos antes de que la zona común pueda ser utilizada por los residentes.
- RN-007: Solo las zonas comunes activas podrán estar disponibles para consulta y reserva por parte de los residentes.
- RN-008: Toda creación, modificación, eliminación o desactivación de una zona común deberá registrarse en el historial de auditoría del sistema.
- RN-009: La capacidad máxima de la zona común deberá ser mayor que cero y será utilizada para controlar las reservas.
- RN-010: Cualquier modificación en los horarios o reglas de uso deberá aplicarse únicamente a las reservas futuras y no afectará las reservas ya confirmadas.
