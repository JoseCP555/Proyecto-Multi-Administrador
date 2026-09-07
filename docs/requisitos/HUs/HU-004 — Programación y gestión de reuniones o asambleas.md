# HU-004 — Programación y gestión de reuniones o asambleas
 ¿Qué? Historia de usuario que describe la creación y gestión de reuniones/asambleas por parte del administrador.
 ¿Para qué? Formalizar la necesidad de organizar los eventos del conjunto con fecha, hora y agenda definidas.
 ¿Impacto? Permite planificar y comunicar formalmente los eventos del conjunto a los residentes. 

## Identificación 

| Campo | Valor |
| ----- | ----- |
| ID | HU-04 |
| Título|	Programación y gestión de reuniones o asambleas
|Módulo	|Reuniones y asambleas
|Prioridad|	Alta
|Estado|	Por definir
|RF asociados	|RF-04 | 

## Historia

Como administrador, quiero programar y gestionar reuniones o asambleas desde el sistema, para organizar los eventos del conjunto con fecha, 
hora y agenda definidas.

# Criterios de aceptación
## CA-04.1 — Formulario de creación de reunión
- Dado que soy administrador y accedo a la sección de reuniones,
- cuando creo una nueva reunión o asamblea,
- entonces debo poder ingresar fecha, hora, lugar y descripción (agenda) del evento.

## CA-04.2 — Validación de campos obligatorios
- Dado que estoy creando una reunión,
- cuando dejo algún campo obligatorio vacío (fecha, hora o lugar) y guardo el evento,
- entonces debo ver un mensaje de error indicando qué campo falta.
## CA-04.3 — Notificación automática a residentes
- Dado que guardé una reunión exitosamente,
- cuando el sistema procesa el guardado,
- entonces debe notificarse automáticamente a los residentes sobre el nuevo evento (ver HU-01).
## CA-04.4 — Edición de reunión existente
- Dado que selecciono una reunión ya programada,
- cuando modifico su fecha, hora, lugar o descripción y guardo los cambios,
- entonces la información debe actualizarse y reflejarse en el sistema.

## CA-04.5 — Cancelación de reunión
- Dado que selecciono una reunión programada,
- cuando la cancelo,
- entonces debe marcarse como cancelada y los residentes deben poder ver este cambio de estado.

## CA-04.6 — Listado de reuniones programadas
- Dado que estoy en la sección de reuniones,
- cuando consulto el listado,
- entonces debo ver todas las reuniones programadas, pasadas y canceladas, con su respectiva fecha y estado.

## CA-04.7 — Estado de carga
- Dado que envié la creación, edición o cancelación de una reunión,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Confirmar si esta historia depende directamente de HU-01 (notificación) o si son independientes y solo se relacionan.
- Definir si se permite adjuntar documentos (actas, agenda) directamente desde la creación de la reunión (relación con HU-03).
