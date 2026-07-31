# HU-015 — Consulta de calendario general del conjunto

¿Qué? Historia de usuario que describe la consulta del calendario general de eventos por parte del residente.
¿Para qué? Formalizar la necesidad de enterarse de actividades, reuniones y fechas importantes de la copropiedad.
¿Impacto? Mejora la comunicación y participación de los residentes en las actividades del conjunto.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID	| HU-15| 
|Título	|Consulta de calendario general del conjunto|
|Módulo	|Reuniones y asambleas / Calendario|
|Prioridad	|Media|
|Estado	|Por definir|
|RF asociados	|RF-15 |

## Historia

Como residente, quiero ver el calendario general del conjunto con todos los eventos,
para enterarme de actividades, reuniones y fechas importantes de la copropiedad.

# Criterios de aceptación

## CA-15.1 — Visualización del calendario de eventos
- Dado que soy residente y accedo a la sección de calendario,
- cuando consulto el calendario,
- entonces debo ver todos los eventos publicados por el administrador (reuniones, asambleas, actividades).
## CA-15.2 — Filtro por tipo de evento
- Dado que estoy consultando el calendario,
- cuando aplico un filtro,
- entonces debo poder filtrar los eventos por tipo (ej. asamblea, actividad social, mantenimiento).

## CA-15.3 — Detalle de un evento
- Dado que selecciono un evento del calendario,
- cuando lo abro,
- entonces debo ver su fecha, hora, lugar y descripción completa.

## CA-15.4 — Navegación entre fechas
- Dado que estoy en el calendario,
- cuando navego entre meses o semanas,
- entonces debo poder ver los eventos correspondientes a ese período.

## CA-15.5 — Diferenciación visual por tipo de evento
- Dado que el calendario muestra distintos tipos de eventos,
- cuando los visualizo,
- entonces debo poder identificarlos visualmente (por ejemplo, con colores o íconos distintos según el tipo).

## CA-15.6 — Sincronización con eventos creados por el administrador
- Dado que el administrador crea o modifica un evento (ver HU-04),
- cuando consulto el calendario como residente,
- entonces debo ver reflejado el evento nuevo o actualizado sin demoras significativas.

## Notas / Pendientes de definición
- Confirmar si el residente puede exportar el calendario a una aplicación externa (Google Calendar, Outlook, etc.).
- Definir si el residente puede marcar eventos como "de interés" o recibir recordatorios personalizados.
