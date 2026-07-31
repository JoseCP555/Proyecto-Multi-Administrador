# HU-006 — Generación de reportes de pagos
¿Qué? Historia de usuario que describe la generación de reportes de cartera (pagos pendientes y al día) por unidad.
¿Para qué? Formalizar la necesidad de hacer seguimiento a la cartera del conjunto y tomar acciones oportunas. 
¿Impacto? Permite al administrador identificar morosidad y tomar decisiones de cobro basadas en datos. 

# Identificación

| Campo | Valor |
| ----- | ----- |
| ID | HU-06 |
| Título|	Generación de reportes de pagos|
|Módulo	|Finanzas / Reportes|
|Prioridad|	Alta|
|Estado	|Por definir|
|RF asociados	|RF-06 | 

## Historia

Como administrador, quiero generar reportes de pagos pendientes y al día por unidad,
para hacer seguimiento a la cartera del conjunto y tomar acciones oportunas.

# Criterios de aceptación

## CA-06.1 — Selección de período para el reporte
- Dado que soy administrador y accedo a la sección de reportes,
- cuando solicito un reporte de cartera,
- entonces debo poder seleccionar el período (mes, rango de fechas) sobre el cual se generará.

## CA-06.2 — Generación de listado por unidad
- Dado que solicité un reporte de cartera,
- cuando el sistema lo genera,
- entonces debe mostrar el estado de pago (pendiente o al día) de cada unidad para el período seleccionado.

## CA-06.3 — Exportación en PDF
- Dado que el reporte fue generado,
- cuando selecciono la opción de descarga en PDF,
- entonces debo obtener un archivo PDF con la información completa del reporte.

## CA-06.4 — Exportación en Excel
- Dado que el reporte fue generado,
- cuando selecciono la opción de descarga en Excel,
- entonces debo obtener un archivo Excel con la información completa del reporte.

## CA-06.5 — Diferenciación visual entre estados de pago
- Dado que consulto el reporte generado,
- cuando reviso el listado de unidades,
- entonces debo poder identificar claramente cuáles unidades están al día y cuáles tienen pagos pendientes.

## CA-06.6 — Estado de carga durante la generación
- Dado que solicité la generación de un reporte,
- cuando el sistema lo está procesando,
- entonces debo ver un indicador de carga hasta que el reporte esté listo para descargar.

## CA-06.7 — Período sin datos
- Dado que selecciono un período sin movimientos registrados,
- cuando solicito el reporte,
- entonces debo ver un mensaje indicando que no hay datos disponibles para ese período.

## Notas / Pendientes de definición
- Confirmar si el reporte debe incluir el monto adeudado por unidad, además del estado (pendiente/al día).
- Definir si los residentes pueden consultar su propio estado de cartera desde su perfil.
