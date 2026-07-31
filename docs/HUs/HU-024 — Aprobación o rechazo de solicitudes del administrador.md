# HU-024 — Aprobación o rechazo de solicitudes del administrador

¿Qué? Historia de usuario que describe la aprobación o rechazo de solicitudes enviadas por el administrador al consejo.
¿Para qué? Formalizar la necesidad de mantener el control y la transparencia en las decisiones administrativas.
¿Impacto? Añade un mecanismo de control y balance sobre las decisiones del administrador.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-024 |
| Título|	Aprobación o rechazo de solicitudes del administrador|
|Módulo	|Gobernanza / Consejo|
|Prioridad|	Alta|
|Estado	|Por definir|
|RF asociados	|RF-24 |

## Historia

Como miembro del consejo del conjunto, quiero aprobar o rechazar solicitudes enviadas por el administrador, 
para mantener el control y la transparencia en las decisiones administrativas.

# Criterios de aceptación

## CA-24.1 — Visualización de solicitudes pendientes
- Dado que soy miembro del consejo y accedo a mi panel,
- cuando el administrador ha enviado una solicitud,
- entonces debo verla listada con su descripción y estado.

## CA-24.2 — Aprobación de una solicitud
- Dado que consulto una solicitud pendiente,
- cuando la apruebo,
- entonces su estado debe cambiar a "aprobada" y quedar registrada con fecha, hora y el miembro del consejo que tomó la decisión.

## CA-24.3 — Rechazo de una solicitud
- Dado que consulto una solicitud pendiente,
- cuando la rechazo,
- entonces su estado debe cambiar a "rechazada" y quedar registrada con fecha, hora y el miembro del consejo que tomó la decisión.

## CA-24.4 — Notificación al administrador sobre la decisión
- Dado que un miembro del consejo aprueba o rechaza una solicitud,
- cuando el sistema procesa la decisión,
- entonces el administrador debe recibir una notificación con el resultado.

## CA-24.5 — Historial de decisiones
- Dado que estoy en el panel del consejo,
- cuando consulto el historial de solicitudes,
- entonces debo poder ver todas las solicitudes anteriores con su decisión, fecha y responsable.

## CA-24.6 — Restricción de decisión duplicada
- Dado que una solicitud ya fue aprobada o rechazada,
- cuando intento tomar una nueva decisión sobre ella,
- entonces el sistema debe impedirlo, ya que la solicitud ya fue resuelta.

## CA-24.7 — Estado de carga
- Dado que envié la aprobación o rechazo de una solicitud,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Definir qué tipo de acciones del administrador requieren aprobación del consejo (ej. gastos superiores a un monto, cambios de configuración críticos).
- Confirmar si se requiere la aprobación de todos los miembros del consejo o si basta con la mayoría/uno solo.
