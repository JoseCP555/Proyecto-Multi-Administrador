# HU-026 — Alertas de movimientos financieros significativos

 ¿Qué? Historia de usuario que describe la recepción de alertas por movimientos financieros significativos por parte del consejo. 
 ¿Para qué? Formalizar la necesidad de supervisar el manejo del dinero del conjunto y detectar irregularidades oportunamente.
 ¿Impacto? Fortalece el control financiero y la transparencia entre administración y consejo. -->

# Identificación

|Campo|	Valor|
| ----------- | ----------- |
|ID	|HU-026|
|Título	|Alertas de movimientos financieros significativos|
|Módulo	|Finanzas / Notificaciones|
|Prioridad|	Alta|
|Estado	|Por definir|
|RF asociados|	RF-26|

## Historia

Como miembro del consejo del conjunto, quiero recibir alertas cuando se registren movimientos financieros significativos,
para supervisar el manejo del dinero del conjunto y detectar irregularidades oportunamente.

# Criterios de aceptación

## CA-26.1 — Configuración del umbral de alerta
- Dado que soy administrador (o rol autorizado) y accedo a la configuración financiera,
- cuando defino el umbral de alerta,
- entonces el sistema debe guardar ese valor como referencia para notificar movimientos significativos.

## CA-26.2 — Generación de alerta al superar el umbral
- Dado que se registra un gasto en el sistema (ver HU-05),
- cuando el monto del gasto supera el umbral configurado,
- entonces el sistema debe generar una alerta dirigida al consejo.

## CA-26.3 — Contenido de la alerta
- Dado que se genera una alerta de movimiento significativo,
- cuando el consejo la recibe,
- entonces debe incluir el monto, la categoría del gasto y el administrador que registró el movimiento.

## CA-26.4 — Canal de notificación
- Dado que se genera una alerta,
- cuando el sistema la envía,
- entonces debe llegar al consejo por los canales configurados (push y/o correo electrónico, según preferencias de HU-18).

## CA-26.5 — Historial de alertas
- Dado que soy miembro del consejo,
- cuando accedo a la sección de alertas financieras,
- entonces debo poder consultar el historial de alertas generadas anteriormente.

##CA-26.6 — Movimientos por debajo del umbral
- Dado que se registra un gasto que no supera el umbral configurado,
- cuando el sistema procesa el movimiento,
-entonces no debe generarse ninguna alerta al consejo.

## Notas / Pendientes de definición
- Confirmar si el umbral aplica solo a gastos o también a ingresos inusuales.
- Definir si el umbral es un valor fijo o si puede configurarse también por categoría de gasto.
