# HU-018 — Recepción de notificaciones de eventos y comunicados

¿Qué? Historia de usuario que describe la recepción de notificaciones por parte del residente sobre eventos y comunicados.
¿Para qué? Formalizar la necesidad de estar al tanto de novedades sin revisar la plataforma constantemente. 
¿Impacto? Mantiene informado al residente de manera proactiva, mejorando su participación y respuesta oportuna.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-018 |
| Título	|Recepción de notificaciones de eventos y comunicados|
|Módulo|	Notificaciones|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados	|RF-018 | 

## Historia

Como residente, quiero recibir notificaciones sobre eventos y comunicados del conjunto,
para estar al tanto de novedades importantes sin tener que revisar la plataforma constantemente.

# Criterios de aceptación

## CA-18.1 — Recepción de notificación push
- Dado que el administrador publica un comunicado o evento,
- cuando el sistema procesa la publicación,
- entonces debo recibir una notificación push en la app (si tengo esta opción habilitada).

## CA-18.2 — Recepción de notificación por correo electrónico
- Dado que el administrador publica un comunicado o evento,
- cuando el sistema procesa la publicación,
- entonces debo recibir un correo electrónico con la información correspondiente (si tengo esta opción habilitada).

## CA-18.3 — Configuración de preferencias de notificación
- Dado que soy residente y accedo a mi configuración de perfil,
- cuando ajusto mis preferencias de notificación,
- entonces debo poder activar o desactivar independientemente las notificaciones push y por correo.
## CA-18.4 — Centro de notificaciones dentro de la app
- Dado que he recibido notificaciones,
- cuando accedo al centro de notificaciones dentro de la app,
- entonces debo poder ver un historial de las notificaciones recibidas.

## CA-18.5 — Marcado de notificación como leída
- Dado que tengo notificaciones sin leer,
- cuando abro o reviso una notificación,
- entonces esta debe marcarse como leída y actualizarse el contador de notificaciones pendientes.

## CA-18.6 — Notificaciones desactivadas
- Dado que desactivé un canal de notificación (push o correo),
- cuando se publica un nuevo comunicado o evento,
- entonces no debo recibir notificaciones por ese canal, aunque sí debo poder consultarlo dentro de la plataforma.

## Notas / Pendientes de definición
- Confirmar si existen distintos tipos de notificación configurables por separado (ej. solo PQRS, solo pagos, solo eventos) o si la configuración es general.
- Relacionar con HU-01 (notificación de asambleas) y HU-11 (comunicados), que son los disparadores de estas notificaciones.
