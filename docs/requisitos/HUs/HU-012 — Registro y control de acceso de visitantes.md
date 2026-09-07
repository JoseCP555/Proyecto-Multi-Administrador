# HU-012 — Registro y control de acceso de visitantes

¿Qué? Historia de usuario que describe el registro y control del ingreso de visitantes al conjunto por parte del administrador.
¿Para qué? Formalizar la necesidad de llevar un registro de seguridad de las personas que ingresan a la copropiedad.
¿Impacto? Fortalece la seguridad del conjunto mediante un historial consultable de visitantes. 

## Identificación

| Campo | Valor |
| ----- | ------|
| ID | HU-12 |
| Título|	Registro y control de acceso de visitantes|
|Módulo	|Seguridad|
|Prioridad|	Alta|
|Estado	|Por definir|
|RF asociados|	RF-12 | 

## Historia

Como administrador, quiero registrar y controlar el acceso de visitantes al conjunto,
para llevar un registro de seguridad de las personas que ingresan a la copropiedad.

# Criterios de aceptación

## CA-12.1 — Formulario de registro de visitante
- Dado que soy administrador (o personal de portería) y accedo a la sección de visitantes,
- cuando registro el ingreso de una persona,
- entonces debo poder ingresar nombre, documento, apartamento visitado y hora de ingreso.

## CA-12.2 — Validación de campos obligatorios
- Dado que estoy registrando un visitante,
- cuando dejo algún campo obligatorio vacío y envío el formulario,
- entonces debo ver un mensaje de error indicando qué campo falta.

## CA-12.3 — Registro de hora de salida
- Dado que un visitante previamente registrado abandona el conjunto,
- cuando registro su salida,
-entonces el sistema debe guardar la hora de salida asociada a su ingreso.

## CA-12.4 — Historial consultable con filtros
- Dado que estoy en la sección de visitantes,
- cuando consulto el historial de ingresos,
- entonces debo poder filtrarlo por fecha, apartamento o nombre del visitante.

## CA-12.5 — Listado de visitantes activos
- Dado que estoy en la sección de visitantes,
- cuando consulto el listado actual,
- entonces debo poder ver quiénes se encuentran actualmente dentro del conjunto (sin hora de salida registrada).

## CA-12.6 — Estado de carga
- Dado que envié el registro de ingreso o salida de un visitante,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Confirmar si los residentes pueden pre-autorizar visitantes desde su cuenta.
- Definir si se requiere fotografía o firma digital del visitante como parte del registro.
