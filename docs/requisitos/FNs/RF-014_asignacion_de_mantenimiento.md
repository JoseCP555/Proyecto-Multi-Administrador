# RF-014 — Asignación de mantenimiento

## Identificación

| Campo | Valor |
| ------------- | ---------------------------------------- |
| **ID** | RF-014 |
| **Nombre** | Gestión de tareas de mantenimiento |
| **Módulo** | Mantenimiento |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Fecha** | Julio 2026 |

## Descripción

El Administrador debe poder asignar tareas de mantenimiento al
personal y monitorear su estado (Pendiente, En Proceso, Finalizado).

## Entradas


| Campo | Tipo | Obligatorio | Validaciones |
| ---------------- | -------- | ----------- | ------------------------------------------------------------------ |
| `employee_id` | UUID | Sí | Debe corresponder a un empleado registrado y activo. |
| `property_id` | UUID | Sí | Debe pertenecer a una copropiedad existente. |
| `title` | Texto | Sí | Mínimo 5 caracteres, máximo 100. |
| `description` | Texto | Sí | Mínimo 10 caracteres, máximo 1000. |
| `priority` | Enum | Sí | Valores permitidos: Baja, Media, Alta, Crítica. |
| `status` | Enum | Sí | Valores permitidos: Pendiente, En Proceso, Finalizado. |
| `due_date` | Fecha | Sí | Debe ser igual o posterior a la fecha actual. |
| `attachments` | Archivo | No | Solo PDF, JPG o PNG. Tamaño máximo 10 MB por archivo. |
## Proceso

1. El administrador accede al módulo de mantenimiento.
2. El sistema muestra el listado de tareas registradas y la opción para crear una nueva.
3. El administrador ingresa la información de la tarea (título, descripción, prioridad, empleado asignado y fecha límite).
4. El sistema valida que todos los campos obligatorios sean correctos.
5. El sistema verifica que el empleado asignado se encuentre activo y pertenezca a la copropiedad correspondiente.
6. El sistema registra la tarea con estado inicial **Pendiente**.
7. El personal de mantenimiento consulta las tareas que tiene asignadas.
8. El personal puede actualizar el estado de la tarea a **En Proceso** cuando inicia la actividad.
9. Una vez finalizada la labor, el personal cambia el estado a **Finalizado**, pudiendo adjuntar observaciones o evidencias.
10. El sistema actualiza el historial de la tarea y permite al administrador monitorear su estado en tiempo real.
11. El sistema registra la fecha y hora de cada cambio de estado para fines de seguimiento y auditoría.

## Salidas

| Escenario | Código HTTP | Respuesta |
| ------------------------------ | ----------- | -------------------------------------------------------------------------- |
| Tarea creada exitosamente | 201 | Datos completos de la tarea creada (`id`, `title`, `status`, `employee_id`, `due_date`, `created_at`). |
| Estado de la tarea actualizado | 200 | Datos de la tarea con el nuevo estado (`Pendiente`, `En Proceso` o `Finalizado`). |
| Empleado no encontrado o inactivo | 404 | Mensaje de error: "Empleado no encontrado o inactivo". |
| Datos inválidos | 422 | Detalle de los errores de validación. |
| Usuario no autorizado | 403 | Mensaje de error: "No tiene permisos para realizar esta acción". |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ---------------------------------- | -------------- | ----------------------------------------------------------- |
| GET | `/api/v1/maintenance/tasks` | Sí | Obtiene el listado de tareas de mantenimiento. |
| POST | `/api/v1/maintenance/tasks` | Sí | Crea una nueva tarea de mantenimiento. |
| GET | `/api/v1/maintenance/tasks/{id}` | Sí | Consulta la información de una tarea específica. |
| PUT | `/api/v1/maintenance/tasks/{id}` | Sí | Actualiza la información de una tarea existente. |
| PATCH | `/api/v1/maintenance/tasks/{id}/status` | Sí | Actualiza el estado de la tarea (Pendiente, En Proceso o Finalizado). |
| DELETE | `/api/v1/maintenance/tasks/{id}` | Sí | Elimina una tarea de mantenimiento. |
## Reglas de negocio

- RN-001: Solo los administradores autorizados pueden crear, editar, asignar o eliminar tareas de mantenimiento.
- RN-002: Toda tarea debe estar asignada a un empleado de mantenimiento activo antes de iniciar su ejecución.
- RN-003: El estado inicial de toda tarea será **Pendiente**.
- RN-004: Una tarea solo puede cambiar de **Pendiente** a **En Proceso**, y de **En Proceso** a **Finalizado**.
- RN-005: No se podrá marcar una tarea como **Finalizado** sin que previamente haya estado **En Proceso**.
- RN-006: Cada cambio de estado debe registrar automáticamente la fecha, hora y el usuario que realizó la modificación.
- RN-007: El sistema debe conservar el historial de las tareas para fines de seguimiento y auditoría.
- RN-008: El personal de mantenimiento solo podrá visualizar y actualizar las tareas que le hayan sido asignadas.
