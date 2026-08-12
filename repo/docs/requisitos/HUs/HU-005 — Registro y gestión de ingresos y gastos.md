# HU-005 — Registro y gestión de ingresos y gastos

¿Qué? Historia de usuario que describe el registro de movimientos financieros del conjunto por parte del administrador.
¿Para qué? Formalizar la necesidad de llevar un control financiero transparente de la copropiedad. 
¿Impacto? Es la base de la transparencia financiera del conjunto ante residentes y consejo. 

## Identificación

| Campo | Valor |
| ------| ----- |
| ID | HU-005 |
| Título	|Registro y gestión de ingresos y gastos|
|Módulo	|Finanzas|
|Prioridad|	Alta|
|Estado	|Por definir|
|RF asociados	|RF-05 | 

## Historia

Como administrador, quiero registrar y gestionar los ingresos y gastos del conjunto, para llevar un control financiero transparente de la copropiedad.

# Criterios de aceptación

##CA-05.1 — Formulario de registro de movimiento
- Dado que soy administrador y accedo a la sección de finanzas,
-cuando registro un nuevo movimiento,
- entonces debo poder ingresar fecha, categoría, monto y tipo de movimiento (ingreso o gasto).

## CA-05.2 — Validación de campos obligatorios
- Dado que estoy registrando un movimiento financiero,
 cuando dejo algún campo obligatorio vacío o el monto es inválido (negativo o no numérico),
- entonces debo ver un mensaje de error indicando el problema.

## CA-05.3 — Actualización del balance en tiempo real
- Dado que registré un ingreso o gasto,
- cuando el sistema procesa el movimiento,
- entonces el balance general del conjunto debe actualizarse de inmediato reflejando el nuevo monto.

## CA-05.4 — Edición de movimiento existente
- Dado que selecciono un movimiento previamente registrado,
- cuando modifico sus datos y guardo los cambios,
- entonces la información y el balance deben actualizarse en consecuencia.

## CA-05.5 — Eliminación de movimiento
- Dado que selecciono un movimiento registrado por error,
-cuando lo elimino y confirmo la acción,
- entonces el movimiento debe desaparecer del listado y el balance debe recalcularse.

## CA-05.6 — Listado histórico filtrable
- Dado que estoy en la sección de finanzas,
- cuando consulto el histórico de movimientos,
- entonces debo poder filtrarlos por fecha, categoría y tipo (ingreso/gasto).

## CA-05.7 — Categorías predefinidas
- Dado que estoy registrando un movimiento,
- cuando selecciono la categoría,
- entonces debo elegir entre una lista predefinida (ej. cuota de administración, mantenimiento, servicios públicos, otros).

## CA-05.8 — Estado de carga
- Dado que envié el registro, edición o eliminación de un movimiento,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Confirmar si esta historia incluye la generación de reportes financieros o si eso corresponde únicamente a HU-06.
- Definir si se requiere adjuntar soportes (facturas, comprobantes) a cada movimiento.
