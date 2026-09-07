# RF-011 — Gestión de PQRS

## Identificación

| Campo         | Valor                                   |
| ------------- | --------------------------------------- |
| **ID**        | RF-011                                  |
| **Nombre**    | Gestión de PQRS                         |
| **Módulo**    | Atención al Residente                   |
| **Prioridad** | Alta                                    |
| **Estado**    | Pendiente                               |
| **Fecha**     | Febrero 2026                            |

## Descripción

El sistema debe incluir un módulo para el registro y seguimiento de
Peticiones, Quejas, Reclamos y Sugerencias (PQRS) por parte de los
residentes.


## Entradas

| Campo               | Tipo              | Obligatorio | Validaciones                                                                 |
| ------------------- | ----------------- | ----------- | ---------------------------------------------------------------------------- |
| `resident_id`       | UUID              | Sí          | Debe corresponder a un residente registrado y autenticado.                   |
| `pqrs_type`         | Texto             | Sí          | Debe ser un tipo válido (`Petición`, `Queja`, `Reclamo` o `Sugerencia`).     |
| `subject`           | Texto             | Sí          | Mínimo 5 caracteres, máximo 150.                                             |
| `description`       | Texto             | Sí          | Mínimo 10 caracteres, máximo 2000.                                           |
| `attachment`        | Archivo (PDF, JPG, PNG) | No     | Debe ser un formato permitido y no superar el tamaño máximo configurado.      |
| `property_id`       | UUID              | Sí          | Debe corresponder a una copropiedad registrada y asociada al residente.      |
## Proceso

1. El residente inicia sesión en la plataforma y accede al módulo de **PQRS**.
2. El residente selecciona el tipo de solicitud (Petición, Queja, Reclamo o Sugerencia).
3. El residente diligencia el asunto, la descripción y, opcionalmente, adjunta un archivo de soporte.
4. El frontend envía la información al backend para su procesamiento.
5. El backend valida que el residente esté autenticado y que los datos ingresados cumplan con las reglas de validación.
6. El sistema registra la PQRS en la base de datos y genera un número único de radicado.
7. La PQRS queda con estado inicial **Registrada** o **Pendiente de atención** y es asignada al Administrador para su gestión.
8. El Administrador revisa la solicitud, registra observaciones y actualiza su estado (En proceso, Resuelta o Cerrada).
9. El residente puede consultar en cualquier momento el estado y el historial de su PQRS desde la plataforma.
10. El sistema registra todas las actualizaciones realizadas sobre la PQRS para fines de seguimiento y auditoría.

## Salidas

| Escenario                           | Código HTTP | Respuesta                                                                                                    |
| ----------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------ |
| PQRS registrada exitosamente        | 201         | Datos de la PQRS creada (`pqrs_id`, `radicado`, `status`, `created_at`).                                     |
| Consulta de PQRS exitosa            | 200         | Información detallada de la PQRS, incluyendo estado, historial y observaciones.                              |
| PQRS no encontrada                  | 404         | Mensaje de error: "PQRS no encontrada".                                                                      |
| Datos de entrada inválidos          | 422         | Detalle de los errores de validación.                                                                        |
| Archivo adjunto no válido           | 400         | Mensaje de error: "El archivo adjunto no cumple con el formato o tamaño permitido".                          |
| Error al registrar la PQRS          | 500         | Mensaje de error: "No fue posible registrar la PQRS".        
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | -------------------------------------- | -------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/pqrs` | Sí (Residente) | Registra una nueva Petición, Queja, Reclamo o Sugerencia. |
| GET    | `/api/v1/pqrs` | Sí | Lista las PQRS según el rol del usuario y los filtros aplicados. |
| GET    | `/api/v1/pqrs/{pqrs_id}` | Sí | Obtiene el detalle de una PQRS específica. |
| PATCH  | `/api/v1/pqrs/{pqrs_id}/status` | Sí (Administrador) | Actualiza el estado de una PQRS (Pendiente, En proceso, Resuelta o Cerrada). |
| POST   | `/api/v1/pqrs/{pqrs_id}/comments` | Sí | Agrega observaciones o respuestas a una PQRS. |
| GET    | `/api/v1/pqrs/history/{resident_id}` | Sí | Consulta el historial de PQRS registradas por un residente. |
## Reglas de negocio
- RN-001: Solo los residentes autenticados podrán registrar nuevas PQRS en el sistema.
- RN-002: Cada PQRS deberá estar asociada a un único residente y a una copropiedad registrada.
- RN-003: Toda PQRS deberá clasificarse como **Petición**, **Queja**, **Reclamo** o **Sugerencia** antes de ser registrada.
- RN-004: Al registrar una PQRS, el sistema generará automáticamente un número único de radicado para su seguimiento.
- RN-005: Toda PQRS iniciará con el estado **Pendiente** o **Registrada** y solo podrá ser actualizada por un Administrador autorizado.
- RN-006: El residente podrá consultar en cualquier momento el estado y el historial de sus propias PQRS.
- RN-007: Los archivos adjuntos deberán cumplir con los formatos y tamaños permitidos por el sistema.
- RN-008: Todas las actualizaciones, respuestas y cambios de estado de una PQRS deberán quedar registrados en el historial de auditoría.
- RN-009: Un residente solo podrá visualizar las PQRS que él mismo haya registrado.
- RN-010: Una PQRS solo podrá marcarse como **Cerrada** cuando haya sido atendida y exista una respuesta registrada por el Administrador.
