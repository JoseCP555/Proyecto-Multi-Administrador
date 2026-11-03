# HU-010 — Gestión de reservas de zonas comunes
¿Qué? Historia de usuario que describe la gestión (aprobación, rechazo, cancelación) de reservas de zonas comunes por parte del administrador.
¿Para qué? Formalizar la necesidad de organizar el uso de espacios compartidos y evitar conflictos entre residentes.
¿Impacto? Evita conflictos de uso simultáneo de espacios comunes y da control al administrador sobre su asignación. 

# Identificación

| Campo | Valor |
| ------| ----- |
| ID | HU-010 |
| Título	|Gestión de reservas de zonas comunes|
|Módulo	|Reservas|
|Prioridad|	Alta|
|Estado	|Por definir|
|RF asociados	|RF-010 | 

## Historia

Como administrador, quiero gestionar las reservas de zonas comunes del conjunto, 
para organizar el uso de espacios compartidos y evitar conflictos entre residentes.

# Criterios de aceptación

## CA-10.1 — Visualización de reservas solicitadas
- Dado que soy administrador y accedo al panel de reservas,
- cuando un residente ha solicitado una reserva,
- entonces debo verla listada con zona, fecha, horario y residente solicitante.

##CA-10.2 — Aprobación de reserva
- Dado que consulto una reserva pendiente,
- cuando la apruebo,
- entonces su estado debe cambiar a "aprobada" y el residente debe recibir una confirmación.

## CA-10.3 — Rechazo de reserva
- Dado que consulto una reserva pendiente,
- cuando la rechazo,
- entonces su estado debe cambiar a "rechazada" y el residente debe recibir una notificación del motivo (si se especifica).

## CA-10.4 — Cancelación de reserva ya aprobada
- Dado que existe una reserva previamente aprobada,
- cuando el administrador la cancela,
- entonces el espacio y horario deben liberarse y el residente debe ser notificado.

## CA-10.5 — Prevención de reservas duplicadas
- Dado que existe una reserva aprobada para una zona en un horario específico,
- cuando otro residente intenta reservar la misma zona en el mismo horario,
- entonces el sistema debe impedirlo y mostrar un mensaje indicando que el espacio ya está reservado.

## CA-10.6 — Configuración de zonas comunes disponibles
- Dado que soy administrador,
- cuando accedo a la configuración de zonas comunes,
- entonces debo poder definir qué espacios están disponibles para reserva y sus horarios habilitados.

## CA-10.7 — Estado de carga
- Dado que envié una acción de aprobar, rechazar o cancelar una reserva,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Relacionar con HU-14 (reserva de zona común por parte del residente), ya que ambas historias forman el mismo flujo end-to-end.
- Definir si existen límites de reservas por residente (ej. máximo de reservas activas por semana).
