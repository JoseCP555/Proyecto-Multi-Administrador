# HU-023 — Revisión de reportes de pagos y gastos

¿Qué? Historia de usuario que describe la revisión de reportes financieros del conjunto por parte del consejo. 
¿Para qué? Formalizar la necesidad de tomar decisiones informadas sobre el presupuesto de la copropiedad.
¿Impacto? Da transparencia financiera y sustento a las decisiones del consejo sobre el presupuesto

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-023 |
| Título|	Revisión de reportes de pagos y gastos|
|Módulo	|Finanzas / Reportes|
|Prioridad	|Alta|
|Estado|	Por definir|
|RF asociados|	RF-23 | Text |

## Historia

Como miembro del consejo del conjunto, quiero revisar los reportes de pagos y gastos del conjunto,
para tomar decisiones informadas sobre el presupuesto de la copropiedad.

# Criterios de aceptación

## CA-23.1 — Visualización del balance de ingresos y egresos
- Dado que soy miembro del consejo y accedo a la sección de finanzas,
- cuando consulto el balance,
- entonces debo poder ver el resumen de ingresos y egresos del conjunto.

## CA-23.2 — Filtro por período
- Dado que estoy consultando el balance financiero,
- cuando aplico un filtro de período,
- entonces el reporte debe mostrar únicamente los movimientos correspondientes a ese rango de fechas.

## CA-23.3 — Visualización con gráficas resumen
- Dado que consulto el reporte financiero,
- cuando el sistema lo genera,
- entonces debe incluir gráficas resumen que faciliten la interpretación de ingresos y gastos por categoría.

## CA-23.4 — Exportación en PDF
- Dado que estoy consultando el reporte financiero,
- cuando selecciono exportar en PDF,
- entonces debo obtener un archivo con la información y las gráficas del período consultado.

## CA-23.5 — Exportación en Excel
- Dado que estoy consultando el reporte financiero,
- cuando selecciono exportar en Excel,
- entonces debo obtener un archivo con el detalle de los movimientos del período consultado.

## CA-23.6 — Acceso de solo lectura
- Dado que soy miembro del consejo,
- cuando consulto los reportes financieros,
- entonces debo poder verlos y exportarlos, pero no modificar los movimientos registrados (esa acción es exclusiva del administrador, ver HU-05).

## Notas / Pendientes de definición
- Confirmar si el consejo puede dejar comentarios u observaciones sobre el reporte para el administrador.
- Relacionar con HU-05 (registro de ingresos y gastos) y HU-06 (reportes de pagos), ya que esta historia consume la información generada en ambas.
