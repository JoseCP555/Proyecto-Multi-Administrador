## HU-01 — Notificación de asambleas 
¿Qué? Historia de usuario que describe el envío de notificaciones a los residentes sobre las asambleas del conjunto. 
¿Para qué? Formalizar la necesidad del administrador de informar oportunamente a los residentes. ¿Impacto? Asegura la participación 
de los residentes en las asambleas al mantenerlos informados a tiempo. 

# Identificación

| Campo | Valor |
| ----- | ------|
| ID    | HU-001 |
| Título|	Notificación de asambleas|
|Módulo	|Notificaciones|
|Prioridad | 	Alta |
|Estado	|Por definir |
|RF asociados | 	RF-01 |

### Historia

Como administrador, quiero notificar a los residentes sobre las asambleas del conjunto, para asegurar que todos los residentes
participen y estén informados a tiempo.

---

# Criterios de aceptación
## CA-01.1 — Creación de la notificación de asamblea
- Dado que soy administrador y estoy programando una asamblea,
- Cuando completo el formulario de la asamblea (fecha, hora, lugar y tipo: ordinaria/extraordinaria),
- Entonces debo poder generar y enviar la notificación correspondiente a los residentes.


## CA-01.2 — Envío por notificación push
- Dado que confirmé el envío de la notificación de asamblea,
- Cuando el sistema procesa el envío,
- Entonces todos los residentes activos con la app instalada deben recibir una notificación
  push con los datos de la asamblea.

## CA-01.3 — Envío por correo electrónico
- Dado que confirmé el envío de la notificación de asamblea,
- Cuando el sistema procesa el envío,
- Entonces todos los residentes activos deben recibir un correo electrónico con los datos de la asamblea.

## CA-01.4 — Anticipación mínima de 48 horas
- Dado que estoy programando la notificación de una asamblea,
- Cuando intento enviarla con menos de 48 horas de anticipación respecto a la fecha del evento,
- Entonces el sistema debe mostrar una advertencia indicando que la anticipación mínima requerida es de 48 horas.

## CA-01.5 — Alcance a residentes activos únicamente
- Dado que se envía una notificación de asamblea,
- Cuando el sistema determina los destinatarios,
- Entonces solo deben recibir la notificación los residentes con estado "activo" en el sistema.

## CA-01.6 — Contenido de la notificación
- Dado que se genera una notificación de asamblea,
- Cuando el residente la recibe (push o correo),
- Entonces debe incluir como mínimo: tipo de asamblea, fecha, hora, lugar y una breve descripción o agenda.

## CA-01.7 — Confirmación de envío exitoso
- Dado que el sistema terminó de procesar el envío masivo de la notificación,
- Cuando reviso el panel de administración,
- Entonces debo ver un resumen indicando cuántos residentes recibieron la notificación exitosamente.

## CA-01.8 — Manejo de errores en el envío
-Dado que ocurre un error al notificar a uno o más residentes (ej. correo inválido, push fallido),
- Cuando el sistema finaliza el proceso de envío,
- Entonces debo ver un listado de los envíos fallidos con la opción de reintentar.

## CA-01.9 — Estado de carga durante el envío
- Dado que inicié el envío de la notificación de asamblea,
- Cuando la solicitud está en proceso,
- Entonces el botón de envío debe estar deshabilitado y mostrar un indicador de carga hasta finalizar.


## Notas / Pendientes de definición
-  Confirmar si el residente puede desactivar las notificaciones push manteniendo el correo electrónico (o viceversa).
- Definir si existe un límite de asambleas notificadas por mes/periodo.
- Validar el estado inicial ("Por definir") una vez el equipo confirme si la funcionalidad ya está implementada,
  en desarrollo o pendiente.
