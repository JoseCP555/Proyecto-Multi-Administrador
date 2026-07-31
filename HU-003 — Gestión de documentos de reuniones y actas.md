# HU-003 — Gestión de documentos de reuniones y actas
 ¿Qué? Historia de usuario que describe la carga de documentos (actas, reuniones) por parte del administrador.
 ¿Para qué? Formalizar la necesidad de que residentes y consejo consulten la información oficial del conjunto.
 ¿Impacto? Centraliza la documentación oficial y da transparencia a la gestión del conjunto.

# Identificación

| Campo | Valor |
| ----- | ----- |
| ID    | HU-003|
| Título|	Gestión de documentos de reuniones y actas|
|Módulo	|Documentos|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados|	RF-03 | 


# Historia

Como administrador, quiero subir documentos de reuniones y actas a la plataforma,
para que los residentes y el consejo consulten la información oficial cuando lo necesiten.

# Criterios de aceptación

## CA-03.1 — Formulario de carga de documento
- Dado que soy administrador y accedo a la sección de documentos,
- Cuando subo un nuevo documento,
- Entonces debo poder adjuntar el archivo e ingresar un título y/o descripción asociada.
  
## CA-03.2 — Formatos de archivo permitidos
- Dado que estoy subiendo un documento,
-Cuando selecciono el archivo,
- Entonces el sistema solo debe permitir archivos en formato PDF o Word.

## CA-03.3 — Límite de tamaño de archivo
- Dado que estoy subiendo un documento,
- Cuando el archivo seleccionado supera los 20 MB,
- Entonces debo ver un mensaje de error indicando que el tamaño máximo permitido es 20 MB.

## CA-03.4 — Formato no permitido
- Dado que intento subir un archivo con una extensión distinta a PDF o Word,
- Cuando envío el formulario,
- Entonces debo ver un mensaje de error indicando que el formato no es válido.

## CA-03.5 — Visibilidad del documento en la plataforma
- Dado que subí un documento exitosamente,
- Cuando un residente o miembro del consejo consulta la sección de documentos,
- Entonces el documento debe estar visible y disponible para su descarga o consulta.

## CA-03.6 — Estado de carga durante la subida
- Dado que envié un documento para subir,
- Cuando el archivo está siendo procesado,
- Entonces debo ver un indicador de progreso o carga hasta que finalice la subida.

## CA-03.7 — Eliminación de documentos
- Dado que soy administrador,
- Cuando elimino un documento previamente cargado,
- Entonces este debe dejar de estar visible para los residentes y el consejo.

## CA-03.8 — Organización de documentos
- Dado que existen múltiples documentos cargados,
- Cuando consulto la sección de documentos,
-Entonces debo poder verlos organizados (por ejemplo, por fecha o tipo de documento) para ubicarlos fácilmente.

## Notas / Pendientes de definición
- Confirmar si los residentes pueden subir documentos o solo consultarlos (rol de solo lectura).
- Definir si se requiere versionado de documentos (ej. actas corregidas).
