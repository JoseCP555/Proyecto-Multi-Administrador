# HU-017 — Consulta de estados de cuenta y pagos

¿Qué? Historia de usuario que describe la consulta de estados de cuenta e historial de pagos por parte del residente.
¿Para qué? Formalizar la necesidad de verificar que los pagos han sido registrados correctamente y conocer la deuda actual. 
¿Impacto? Da transparencia y autonomía al residente sobre su situación financiera con el conjunto.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-017 |
| Título	|Consulta de estados de cuenta y pagos|
|Módulo	|Finanzas|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados	|RF-17 | 

## Historia

Como residente, quiero consultar mis estados de cuenta y el historial de pagos, 
para verificar que mis pagos han sido registrados correctamente y conocer mi deuda actual.

# Criterios de aceptación

## CA-17.1 — Visualización de pagos realizados
- Dado que soy residente autenticado y accedo a mi sección de pagos,
- cuando consulto mi historial,
- entonces debo ver los pagos realizados con su fecha y monto.

## CA-17.2 — Visualización de saldo pendiente
- Dado que consulto mi estado de cuenta,
- cuando reviso la información mostrada,
- entonces debo poder ver claramente mi saldo pendiente actual (si existe deuda).

## CA-17.3 — Información restringida al residente autenticado
- Dado que consulto mis pagos,
- cuando el sistema muestra la información,
- entonces solo debo poder ver los pagos y saldos correspondientes a mi propia unidad, no los de otros residentes.

## CA-17.4 — Exportación en PDF
- Dado que estoy consultando mi historial de pagos,
-cuando selecciono la opción de exportar,
- entonces debo poder descargar un archivo PDF con la información de mi estado de cuenta.

## CA-17.5 — Filtro por período
- Dado que estoy consultando mi historial de pagos,
- cuando aplico un filtro de fecha,
- entonces debo poder ver únicamente los pagos correspondientes al período seleccionado.

## CA-17.6 — Sin movimientos registrados
- Dado que no tengo pagos registrados en el sistema,
- cuando consulto mi historial,
- entonces debo ver un mensaje indicando que no hay movimientos disponibles.

## Notas / Pendientes de definición
- Relacionar con HU-13 (subida de comprobante de pago) para confirmar que los pagos "en revisión" también se reflejen en este historial con su estado correspondiente.
- Definir si se debe mostrar el detalle de la cuota de administración (concepto, mes correspondiente) además del monto total.
