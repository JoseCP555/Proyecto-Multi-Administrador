# HU-009 — Gestión de PQRS
¿Qué? Historia de usuario que describe la recepción y gestión de PQRS (peticiones, quejas, reclamos y solicitudes) por parte del administrador.
¿Para qué? Formalizar la necesidad de dar respuesta oportuna a las solicitudes de los residentes. 
¿Impacto? Centraliza y da trazabilidad a la comunicación formal entre residentes y administración. 

## Identificación

| Campo | Valor |
| ----- | ----- |
| ID | HU-009 |
| Título|	Gestión de PQRS |
|Módulo	|PQRS|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados	|RF-09 |

## Historia

Como administrador, quiero recibir y gestionar las PQRS enviadas por los residentes, para dar respuesta oportuna a las solicitudes,
peticiones, quejas y reclamos del conjunto.

# Criterios de aceptación

## CA-09.1 — Visualización de PQRS recibidas
- Dado que soy administrador y accedo al panel de PQRS,
- cuando un residente ha enviado una solicitud,
- entonces debo verla listada en el panel con su tipo, fecha y estado.

## CA-09.2 — Estados de una PQRS
- Dado que consulto una PQRS en el panel,
- cuando reviso su estado,
- entonces este debe ser uno de los siguientes: pendiente, en proceso o cerrada.

## CA-09.3 — Respuesta a una PQRS
- Dado que selecciono una PQRS pendiente o en proceso,
- cuando redacto y envío una respuesta,
- entonces el residente que la radicó debe poder ver la respuesta y el estado debe actualizarse a "en proceso" (si aún no se cierra).
## CA-09.4 — Cierre de una PQRS
- Dado que una PQRS ya fue atendida,
- cuando el administrador la marca como cerrada,
- entonces su estado debe cambiar a "cerrada" y no debe permitir más respuestas del administrador salvo que se reabra.

## CA-09.5 — Filtrado y búsqueda de PQRS
- Dado que estoy en el panel de PQRS,
- cuando aplico filtros,
- entonces debo poder filtrar por estado, tipo de solicitud, fecha o residente.

## CA-09.6 — Notificación al residente sobre cambios de estado
- Dado que el estado o la respuesta de una PQRS cambia,
- cuando el sistema procesa la actualización,
- entonces el residente que la radicó debe recibir una notificación del cambio.

## CA-09.7 — Estado de carga
- Dado que envié una respuesta o cambio de estado de una PQRS,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Confirmar si un administrador puede reabrir una PQRS cerrada.
- Relacionar con HU-16 (envío de PQRS por parte del residente), ya que ambas historias forman el mismo flujo end-to-end.
Notas / Pendientes de definición
Confirmar si un administrador puede reabrir una PQRS cerrada.
Relacionar con HU-16 (envío de PQRS por parte del residente), ya que ambas historias forman el mismo flujo end-to-end.
