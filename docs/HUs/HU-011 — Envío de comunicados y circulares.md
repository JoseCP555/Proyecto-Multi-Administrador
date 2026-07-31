#HU-011 — Envío de comunicados y circulares

¿Qué? Historia de usuario que describe el envío de comunicados y circulares masivas a los residentes por parte del administrador. 
¿Para qué? Formalizar la necesidad de informar sobre novedades, normas o eventos importantes del conjunto.
¿Impacto? Centraliza la comunicación oficial entre administración y residentes. 

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-011 |
| Título|	Envío de comunicados y circulares|
|Módulo	|Comunicados|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados	|RF-11 | 

## Historia

Como administrador, quiero enviar comunicados y circulares masivas a los residentes,
para informar sobre novedades, normas o eventos importantes del conjunto.

# Criterios de aceptación

## CA-11.1 — Formulario de creación de comunicado
- Dado que soy administrador y accedo a la sección de comunicados,
- cuando creo un nuevo comunicado,
- entonces debo poder ingresar un título y contenido del mensaje.

## CA-11.2 — Envío por notificación push
- Dado que publiqué un comunicado,
- cuando el sistema procesa el envío,
- entonces todos los residentes activos deben recibir una notificación push con el comunicado.

## CA-11.3 — Envío por correo electrónico
- Dado que publiqué un comunicado,
- cuando el sistema procesa el envío,
- entonces todos los residentes activos deben recibir un correo electrónico con el comunicado.

## CA-11.4 — Almacenamiento en la sección de comunicados
- Dado que publiqué un comunicado,
- cuando un residente o el administrador consulta la sección de comunicados,
- entonces el comunicado debe quedar guardado y disponible para consulta posterior.

## CA-11.5 — Validación de campos obligatorios
- Dado que estoy creando un comunicado,
- cuando dejo el título o el contenido vacío y envío el formulario,
- entonces debo ver un mensaje de error indicando qué campo falta.

## CA-11.6 — Estado de carga durante el envío
- Dado que envié un comunicado,
- cuando la solicitud está en proceso,
- entonces el botón de envío debe estar deshabilitado y mostrar un indicador de carga.

## CA-11.7 — Historial de comunicados enviados
- Dado que estoy en la sección de comunicados,
- cuando consulto el historial,
- entonces debo ver todos los comunicados enviados previamente, ordenados por fecha.

## Notas / Pendientes de definición
- Confirmar si se pueden adjuntar archivos (imágenes, documentos) a un comunicado.
- Definir si existe segmentación de destinatarios (ej. enviar solo a un bloque o torre específica).
