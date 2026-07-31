# HU-022 — Consulta de acta de la última asamblea

¿Qué? Historia de usuario que describe la consulta del acta y transcripción de la última asamblea por parte del consejo. 
¿Para qué? Formalizar la necesidad de revisar y verificar las decisiones tomadas oficialmente en la reunión. 
¿Impacto? Da respaldo formal y consultable de las decisiones tomadas en las asambleas.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-022 |
| Título	|Consulta de acta de la última asamblea|
|Módulo	|Documentos|
|Prioridad	|Media|
|Estado	|Por definir|
|RF asociados	|RF-22 |

## Historia

Como miembro del consejo del conjunto, quiero ver la transcripción y acta de la última asamblea, 
para revisar y verificar las decisiones tomadas oficialmente en la reunión.

# Criterios de aceptación

## CA-22.1 — Acceso al acta desde la sección de documentos
- Dado que soy miembro del consejo y accedo a la sección de documentos,
- cuando busco el acta de la última asamblea,
- entonces debo poder encontrarla y abrirla directamente.

## CA-22.2 — Formato del documento
- Dado que consulto el acta de la asamblea,
- cuando el sistema la muestra,
- entonces el archivo debe estar disponible en formato PDF.

## CA-22.3 — Restricción de edición para residentes comunes
- Dado que el acta fue publicada,
- cuando un residente común (sin rol de consejo o administrador) intenta editarla,
- entonces el sistema debe impedir la edición, permitiendo únicamente su consulta o descarga.

## CA-22.4 — Descarga del acta
- Dado que estoy consultando el acta de la última asamblea,
- cuando selecciono la opción de descarga,
- entonces debo poder obtener el archivo PDF en mi dispositivo.

## CA-22.5 — Identificación de la asamblea correspondiente
- Dado que existen actas de varias asambleas,
- cuando consulto la sección de documentos,
- entonces debo poder identificar claramente cuál es el acta de la última asamblea (por fecha o etiqueta destacada).

## CA-22.6 — Historial de actas anteriores
- Dado que estoy en la sección de documentos,
- cuando consulto el historial,
- entonces debo poder acceder también a las actas de asambleas anteriores, no solo la más reciente.

## Notas / Pendientes de definición
- Confirmar quién tiene permiso para subir/editar el acta (¿solo administrador?) antes de que quede en modo solo lectura para consejo y residentes.
- Relacionar con HU-03 (gestión de documentos) para definir si el acta se sube como cualquier otro documento o si tiene un flujo propio.
