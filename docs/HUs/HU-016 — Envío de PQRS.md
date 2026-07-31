# HU-016 — Envío de PQRS

¿Qué? Historia de usuario que describe el envío de una PQRS a la administración por parte del residente.
¿Para qué? Formalizar la necesidad de comunicar de forma formal solicitudes, quejas o sugerencias.
¿Impacto? Da un canal formal y trazable de comunicación entre residentes y administración.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-016 |
| Título | Envío de PQRS | 
|Módulo	|PQRS|
|Prioridad|	Alta|
|Estado	|Por definir|
|RF asociados	|RF-16 | 

## Historia

Como residente, quiero enviar una PQRS a la administración desde la plataforma,
para comunicar de forma formal mis solicitudes, quejas o sugerencias al administrador.

# Criterios de aceptación

## CA-16.1 — Formulario de radicación de PQRS
- Dado que soy residente y accedo a la sección de PQRS,
- cuando creo una nueva solicitud,
- entonces debo poder ingresar un título, descripción y el tipo de solicitud.
## CA-16.2 — Clasificación por tipo
- Dado que estoy radicando una PQRS,
- cuando selecciono el tipo,
- entonces debo poder elegir entre: petición, queja, reclamo o sugerencia.
## CA-16.3 — Validación de campos obligatorios
- Dado que estoy completando el formulario de PQRS,
- cuando dejo algún campo obligatorio vacío y lo envío,
- entonces debo ver un mensaje de error indicando qué campo falta.

## CA-16.4 — Confirmación de radicado
- Dado que envié mi PQRS correctamente,
- cuando el sistema la procesa,
- entonces debo recibir una confirmación con un número o identificador de radicado.

## CA-16.5 — Consulta del estado de mi PQRS
- Dado que radiqué una PQRS previamente,
- cuando consulto la sección de "Mis PQRS",
- entonces debo poder ver su estado actual (pendiente, en proceso, cerrada) y la respuesta del administrador si existe.

## CA-16.6 — Notificación de respuesta
- Dado que el administrador respondió o cerró mi PQRS,
- cuando el sistema procesa el cambio,
- entonces debo recibir una notificación indicando la actualización.

## CA-16.7 — Estado de carga
- Dado que envié mi PQRS,
- cuando la solicitud está en proceso,
- entonces el botón de envío debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Relacionar con HU-09 (gestión de PQRS por el administrador), ya que ambas historias forman el mismo flujo end-to-end.
- Confirmar si el residente puede adjuntar imágenes o documentos de soporte a su PQRS.
