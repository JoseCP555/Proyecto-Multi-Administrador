# HU-019 — Consulta de documentos y actas

¿Qué? Historia de usuario que describe la consulta de documentos y actas publicados por la administración, desde la perspectiva del residente. 
¿Para qué? Formalizar la necesidad de revisar la información oficial del conjunto en cualquier momento.
¿Impacto? Da acceso transparente y permanente a la documentación oficial del conjunto.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-019 |
| Título|	Consulta de documentos y actas|
|Módulo	|Documentos|
|Prioridad|	Media|
|Estado|	Por definir|
|RF asociados	 |RF-19 | 

# Historia

Como residente, quiero consultar los documentos y actas publicados por la administración,
para revisar la información oficial del conjunto en cualquier momento.

# Criterios de aceptación

## CA-19.1 — Visualización de documentos publicados
- Dado que soy residente y accedo a la sección de documentos,
- cuando consulto el listado,
- entonces debo ver todos los documentos y actas publicados por la administración.

## CA-19.2 — Descarga de documentos
- Dado que selecciono un documento del listado,
- cuando confirmo la descarga,
- entonces debo poder obtener el archivo (PDF o Word) en mi dispositivo.

## CA-19.3 — Organización de documentos
- Dado que existen múltiples documentos publicados,
- cuando consulto la sección de documentos,
- entonces debo poder verlos organizados, por ejemplo por fecha o tipo de documento, para ubicarlos fácilmente.

## CA-19.4 — Búsqueda de documentos
- Dado que estoy en la sección de documentos,
- cuando utilizo el buscador,
-entonces debo poder encontrar documentos por su título o palabras clave.

## CA-19.5 — Acceso restringido a documentos del propio conjunto
- Dado que soy residente de un conjunto específico,
- cuando consulto la sección de documentos,
- entonces solo debo ver los documentos correspondientes a mi conjunto.

## CA-19.6 — Visualización sin necesidad de descarga
- Dado que selecciono un documento,
- cuando el archivo es compatible (por ejemplo PDF),
- entonces debo poder visualizarlo directamente dentro de la plataforma, sin necesidad de descargarlo primero.

## Notas / Pendientes de definición
- Relacionar directamente con HU-03 (subida de documentos por el administrador), ya que ambas historias forman el mismo flujo end-to-end.
- Confirmar si se requiere control de versiones cuando un documento se actualiza o reemplaza.
