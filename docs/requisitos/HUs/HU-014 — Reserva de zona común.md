# HU-014 — Reserva de zona común

¿Qué? Historia de usuario que describe la reserva de una zona común por parte del residente.
¿Para qué? Formalizar la necesidad de usar los espacios del conjunto sin trámites presenciales. 
¿Impacto? Agiliza el acceso a espacios comunes y reduce la carga operativa de la administración.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-014 |
| Título|	Reserva de zona común|
|Módulo|	Reservas|
|Prioridad	|Alta|
|Estado|	Por definir||
|RF asociados	|RF-014 | 

## Historia

Como residente, quiero reservar una zona común desde mi celular o computador, 
para usar los espacios del conjunto sin necesidad de hacer trámites presenciales.

# Criterios de aceptación

## CA-14.1 — Selección de zona, fecha y horario
- Dado que soy residente y accedo a la sección de reservas,
- cuando quiero reservar un espacio,
- entonces debo poder seleccionar la zona común, la fecha y un horario disponible.

## CA-14.2 — Visualización de disponibilidad
- Dado que estoy seleccionando fecha y horario,
- cuando consulto la disponibilidad,
- entonces el sistema debe mostrarme únicamente los horarios libres para la zona elegida.

## CA-14.3 — Confirmación de la reserva
- Dado que completé la selección de zona, fecha y horario disponible,
- cuando envío la solicitud de reserva,
- entonces debo recibir una confirmación de que la reserva quedó registrada (según el flujo de aprobación definido en HU-10).
## CA-14.4 — Visualización en el historial personal
- Dado que realicé una reserva,
- cuando consulto mi historial de reservas,
- entonces debo poder ver la zona, fecha, horario y estado de cada una de mis reservas.

## CA-14.5 — Cancelación de una reserva propia
- Dado que tengo una reserva activa,
- cuando decido cancelarla,
- entonces el espacio y horario deben liberarse y la reserva debe marcarse como cancelada en mi historial.

## CA-14.6 — Validación de horario no disponible
- Dado que intento reservar un horario ya ocupado,
- cuando envío la solicitud,
- entonces debo ver un mensaje de error indicando que el horario no está disponible.

## CA-14.7 — Estado de carga
- Dado que envié una solicitud de reserva o cancelación,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Confirmar si la reserva queda "confirmada" automáticamente o requiere aprobación del administrador (relación con HU-10).
- Definir si existen restricciones por unidad (ej. máximo de reservas simultáneas o por semana).
