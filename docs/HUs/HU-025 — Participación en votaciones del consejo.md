# HU-025 — Participación en votaciones del consejo

¿Qué? Historia de usuario que describe la participación en votaciones sobre decisiones del conjunto por parte del consejo.
¿Para qué? Formalizar la necesidad de tomar decisiones colectivas de forma ágil sin reuniones presenciales.
¿Impacto? Agiliza la toma de decisiones colegiadas y deja trazabilidad de los resultados.4

# Identificación

|Campo	|Valor|
| ----------- | ----------- |
|ID	|HU-25|
|Título|	Participación en votaciones del consejo|
|Módulo	|Gobernanza / Consejo|
|Prioridad|	Media|
|Estado	|Por definir|
|RF asociados|	RF-25|

# Historia

Como miembro del consejo del conjunto, quiero participar en votaciones sobre decisiones del conjunto desde la plataforma,
para tomar decisiones colectivas de forma ágil sin necesidad de reuniones presenciales.

# Criterios de aceptación

## CA-25.1 — Creación de votación por el administrador
- Dado que el administrador necesita someter una decisión a votación,
- cuando crea la votación,
- entonces debe poder definir la pregunta, las opciones de respuesta y el plazo (fecha/hora de cierre).

## CA-25.2 — Visualización de votaciones activas
- Dado que soy miembro del consejo,
- cuando accedo a la sección de votaciones,
- entonces debo ver las votaciones activas con su pregunta, opciones y plazo restante.

## CA-25.3 — Emisión de voto
- Dado que consulto una votación activa,
- cuando selecciono una opción y confirmo mi voto,
- entonces mi voto debe registrarse en el sistema.

## CA-25.4 — Restricción de un solo voto por miembro
- Dado que ya emití mi voto en una votación,
- cuando intento votar nuevamente en la misma votación,
- entonces el sistema debe impedirlo, indicando que ya ejercí mi voto.

## CA-25.5 — Cierre automático de la votación
- Dado que una votación alcanza su plazo definido,
- cuando se cumple la fecha/hora límite,
- entonces el sistema debe cerrarla automáticamente y no permitir más votos.

## CA-25.6 — Visualización de resultados al cierre
- Dado que una votación se cerró,
- cuando consulto sus resultados,
- entonces debo ver el conteo de votos por cada opción.

## CA-25.7 — Confidencialidad del voto durante la votación
-Dado que una votación está activa,
-cuando consulto sus resultados parciales,
-entonces el sistema no debe revelar quién votó por cada opción hasta el cierre (según se defina la política de transparencia).

## Notas / Pendientes de definición
- Confirmar si los resultados deben mostrar el detalle de quién votó qué, o solo el conteo agregado, incluso después del cierre.
- Definir si un miembro del consejo puede cambiar su voto antes de que cierre la votación.
