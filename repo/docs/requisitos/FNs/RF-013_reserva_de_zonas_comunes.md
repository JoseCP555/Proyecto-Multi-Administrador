# RF-013 — Reserva de zonas comunes

## Identificación

| Campo         | Valor                                   |
| ------------- | --------------------------------------- |
| **ID**        | RF-013                                  |
| **Nombre**    | Reserva de zonas comunes                |
| **Módulo**    | Administración de Zonas Comunes         |
| **Prioridad** | Alta                                    |
| **Estado**    | Pendiente                               |
| **Fecha**     | Febrero 2026                            |

## Descripción

El Residente debe poder consultar la disponibilidad y reservar zonas
comunes a través de la interfaz web o móvil.
## Entradas

| Campo              | Tipo          | Obligatorio | Validaciones                                                                 |
| ------------------ | ------------- | ----------- | ---------------------------------------------------------------------------- |
| `resident_id`      | UUID          | Sí          | Debe corresponder a un residente registrado y autenticado.                   |
| `property_id`      | UUID          | Sí          | Debe corresponder a una copropiedad registrada y asociada al residente.      |
| `zone_id`          | UUID          | Sí          | Debe corresponder a una zona común activa.                                   |
| `reservation_date` | Fecha         | Sí          | Debe ser una fecha válida y no podrá ser anterior a la fecha actual.         |
| `start_time`       | Hora          | Sí          | Debe encontrarse dentro del horario permitido para la zona común.            |
| `end_time`         | Hora          | Sí          | Debe ser posterior a la hora de inicio y estar dentro del horario permitido. |

## Proceso

1. El residente inicia sesión en la plataforma y accede al módulo de **Zonas Comunes**.
2. El sistema muestra la disponibilidad de las zonas comunes junto con sus horarios, capacidad y reglas de uso.
3. El residente selecciona la zona común, la fecha y el horario que desea reservar.
4. El frontend envía la solicitud de reserva al backend.
5. El backend valida que el residente esté autenticado y que la zona común se encuentre activa.
6. El sistema verifica que la fecha y el horario solicitados estén disponibles y que no exista otra reserva para el mismo período.
7. El backend valida que la reserva cumpla con las reglas de uso establecidas para la zona común.
8. Si todas las validaciones son correctas, el sistema registra la reserva y la asocia al residente y a la copropiedad.
9. El sistema actualiza la disponibilidad de la zona común para evitar reservas duplicadas.
10. El backend devuelve la confirmación de la reserva al residente y registra la operación en el historial de auditoría.
## Salidas

| Escenario                                | Código HTTP | Respuesta                                                                                                  |
| ---------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------- |
| Reserva realizada exitosamente           | 201         | Datos de la reserva creada (`reservation_id`, `zone_id`, `resident_id`, `reservation_date`, `status`). |
| Disponibilidad consultada exitosamente   | 200         | Lista de horarios disponibles y reservas existentes para la zona común seleccionada.                       |
| Zona común no encontrada                 | 404         | Mensaje de error: "Zona común no encontrada".                                                              |
| Horario no disponible                    | 409         | Mensaje de error: "El horario seleccionado ya se encuentra reservado".                                    |
| Datos de entrada inválidos               | 422         | Detalle de los errores de validación.                                                                      |
| Error al registrar la reserva            | 500         | Mensaje de error: "No fue posible registrar la reserva de la zona común".                                 |

## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ---------------------------------------------- | -------------- | ------------------------------------------------------------ |
| GET    | `/api/v1/common-zones/availability` | Sí | Consulta la disponibilidad de las zonas comunes. |
| GET    | `/api/v1/common-zones/{zone_id}/availability` | Sí | Obtiene los horarios disponibles de una zona común específica. |
| POST   | `/api/v1/reservations` | Sí (Residente) | Registra una nueva reserva de una zona común. |
| GET    | `/api/v1/reservations` | Sí | Lista las reservas del residente autenticado. |
| GET    | `/api/v1/reservations/{reservation_id}` | Sí | Obtiene el detalle de una reserva específica. |
| DELETE | `/api/v1/reservations/{reservation_id}` | Sí (Residente) | Cancela una reserva realizada por el residente. |

## Reglas de negocio

- RN-001: Solo los residentes activos pueden realizar reservas.
- RN-002: Una zona común no puede tener reservas superpuestas.
- RN-003: Las reservas deben realizarse dentro de los horarios configurados por el administrador.
- RN-004: El sistema debe registrar la fecha y hora de creación de la reserva.
- RN-005: El residente solo puede cancelar una reserva antes de su horario de inicio.
- RN-006: El administrador puede visualizar todas las reservas realizadas.
