# HU-032 — Notificación de PQRS de zona común al consejo

¿Qué? Historia de usuario que describe la notificación al consejo cuando un residente envía una PQRS relacionada con zonas comunes. 
¿Para qué? Formalizar la necesidad de que el consejo esté informado de situaciones que requieren atención colectiva. 
¿Impacto? Involucra al consejo en decisiones sobre zonas comunes que afectan a toda la comunidad. -->

# Identificación

|Campo|	Valor|
| ----------- | ----------- |
|ID	|HU-032|
|Título	|Notificación de PQRS de zona común al consejo|
|Módulo	|PQRS / Notificaciones|
|Prioridad |	Media|
|Estado	|Por definir|
|RF asociados|	RF-32|

# Historia

Como miembro del consejo del conjunto, quiero recibir notificaciones cuando un residente envíe una PQRS relacionada con zonas comunes,
para estar informado de situaciones que requieren atención colectiva del consejo.

# Criterios de aceptación

## CA-32.1 — Clasificación de PQRS por categoría "zona común"
- Dado que un residente radica una PQRS (ver HU-16),
- cuando la clasifica como relacionada con "zona común",
- entonces el sistema debe identificarla como elegible para notificar al consejo.

## CA-32.2 — Envío de la notificación al consejo
- Dado que se radica una PQRS categorizada como "zona común",
- cuando el sistema procesa el registro,
- entonces debe notificar a todos los miembros del consejo.

## CA-32.3 — Contenido de la notificación
- Dado que el consejo recibe la notificación,
- cuando la revisa,
- entonces debe incluir un resumen de la PQRS y un enlace directo al caso.

## CA-32.4 — Acceso al caso desde el enlace
- Dado que un miembro del consejo hace clic en el enlace de la notificación,
- cuando el enlace es válido,
- entonces debe ser dirigido directamente al detalle de la PQRS correspondiente.

## CA-32.5 — PQRS no relacionadas con zona común
- Dado que un residente radica una PQRS que no está categorizada como "zona común",
- cuando el sistema procesa el registro,
- entonces no debe notificarse al consejo (solo al administrador, según HU-09).

## CA-32.6 — Canal de notificación
- Dado que se genera una notificación de PQRS de zona común,
- cuando el sistema la envía,
- entonces debe llegar al consejo por los canales configurados en sus preferencias de notificación (ver HU-18).

## Notas / Pendientes de definición
- Confirmar si el consejo puede responder directamente a la PQRS o si su rol es solo de consulta y seguimiento (mientras la respuesta formal la da el administrador según HU-09).
- Definir si existen otras categorías de PQRS que también deban notificar al consejo, además de "zona común".
