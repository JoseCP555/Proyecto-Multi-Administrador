# HU-029 — Historial de auditoría de acciones
¿Qué? Historia de usuario que describe el registro de un historial (log) de todas las acciones realizadas en la plataforma.
¿Para qué? Formalizar la necesidad de tener trazabilidad de los cambios y auditar cualquier acción cuando sea necesario.
¿Impacto? Aporta seguridad, trazabilidad y respaldo ante disputas o revisiones administrativas. -->

# Identificación

|Campo|	Valor|
| ----------- | ----------- |
|ID	|HU-29|
|Título|	Historial de auditoría de acciones|
|Módulo	|Seguridad / Auditoría|
|Prioridad|	Media|
|Estado	|Por definir|
|RF asociados|	RF-29|

## Historia

Como administrador, quiero que el sistema registre un historial de todas las acciones realizadas en la plataforma,
para tener trazabilidad de los cambios y auditar cualquier acción cuando sea necesario.

# Criterios de aceptación

## CA-29.1 — Registro automático de acciones relevantes
- Dado que un usuario realiza una acción relevante en el sistema (crear, editar, eliminar, aprobar, etc.),
- cuando la acción se ejecuta,
- entonces el sistema debe guardar un registro con usuario, acción, fecha y hora.

## CA-29.2 — Visualización del historial por el administrador
- Dado que soy administrador y accedo a la sección de auditoría,
- cuando consulto el historial,
- entonces debo poder ver el listado completo de acciones registradas.

## CA-29.3 — Filtrado del historial
- Dado que estoy consultando el historial de auditoría,
- cuando aplico filtros,
- entonces debo poder filtrar por usuario, tipo de acción o rango de fechas.

## CA-29.4 — Restricción de acceso al historial
- Dado que soy un residente o miembro del consejo,
- cuando intento acceder a la sección de auditoría,
- entonces el sistema debe restringir el acceso, ya que esta sección es exclusiva del administrador.

## CA-29.5 — Inmutabilidad del historial
- Dado que existe un registro en el historial de auditoría,
- cuando cualquier usuario (incluido el administrador desde la interfaz estándar) intenta eliminarlo o modificarlo,
- entonces el sistema debe impedirlo.

## CA-29.6 — Detalle de cada registro
- Dado que selecciono un registro del historial,
- cuando lo consulto,
- entonces debo poder ver el detalle completo de la acción, incluyendo los valores anteriores y nuevos si aplica.

## Notas / Pendientes de definición
- Definir la lista completa de acciones consideradas "relevantes" para efectos de auditoría (ej. ¿se incluyen los inicios de sesión?).
- Confirmar el tiempo de retención del historial de auditoría.
