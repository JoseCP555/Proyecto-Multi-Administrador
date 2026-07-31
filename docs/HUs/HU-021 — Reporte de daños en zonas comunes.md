# HU-021 — Reporte de daños en zonas comunes

¿Qué? Historia de usuario que describe el reporte de daños o novedades en zonas comunes por parte del residente.
¿Para qué? Formalizar la necesidad de informar a la administración de manera ágil sobre problemas que afectan a la comunidad. 
¿Impacto? Agiliza la detección y atención de daños en las zonas comunes del conjunto.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-021 |
| Título	|Reporte de daños en zonas comunes|
|Módulo	|Mantenimiento|
|Prioridad	|Media|
|Estado	|Por definir|
|RF asociados|	RF-21 | 


## Historia

Como residente, quiero reportar un daño o novedad en las zonas comunes del conjunto,
para informar a la administración de manera ágil sobre problemas que afectan a la comunidad.

# Criterios de aceptación

## CA-21.1 — Formulario de reporte de daño
- Dado que soy residente y accedo a la sección de reportes,
- cuando creo un nuevo reporte,
- entonces debo poder describir el daño y adjuntar una o más fotos.

## CA-21.2 — Validación de campos obligatorios
- Dado que estoy creando un reporte de daño,
- cuando dejo la descripción vacía y lo envío,
- entonces debo ver un mensaje de error indicando que la descripción es obligatoria.

## CA-21.3 — Selección de zona afectada
- Dado que estoy reportando un daño,
- cuando completo el formulario,
- entonces debo poder indicar la zona común específica donde ocurrió el daño.

## CA-21.4 — Envío al administrador como tarea pendiente
- Dado que envié un reporte de daño,
- cuando el administrador consulta su panel,
- entonces el reporte debe aparecer listado como tarea pendiente.

## CA-21.5 — Consulta del estado del reporte
- Dado que envié un reporte de daño,
- cuando consulto la sección "Mis reportes",
- entonces debo poder ver su estado (pendiente, en proceso, resuelto).

## CA-21.6 — Notificación al residente sobre actualización del reporte
- Dado que el administrador actualiza el estado de mi reporte,
- cuando el sistema procesa el cambio,
- entonces debo recibir una notificación informándome de la actualización.

## CA-21.7 — Estado de carga durante el envío
- Dado que envié un reporte de daño,
- cuando el archivo y la información están siendo procesados,
- entonces debo ver un indicador de carga hasta que finalice el envío.

## Notas / Pendientes de definición
- Confirmar el límite de tamaño y cantidad de fotos que se pueden adjuntar por reporte.
- Definir si este reporte se integra con el módulo de PQRS (HU-16) o si es un módulo independiente de mantenimiento.
