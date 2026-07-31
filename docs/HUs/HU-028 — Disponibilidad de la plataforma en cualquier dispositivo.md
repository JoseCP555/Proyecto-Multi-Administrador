# HU-028 — Disponibilidad de la plataforma en cualquier dispositivo
¿Qué? Historia de usuario que describe la disponibilidad de la plataforma desde cualquier dispositivo con navegador web. 
¿Para qué? Formalizar la necesidad de administrar el conjunto desde el celular, tableta o computador en cualquier lugar. 
¿Impacto? Es un requisito no funcional transversal que garantiza accesibilidad y usabilidad multiplataforma. 

# Identificación

|Campo|	Valor|
| ----------- | ----------- |
|ID|	HU-028|
|Título	|Disponibilidad de la plataforma en cualquier dispositivo|
|Módulo|	Plataforma / Responsive Design|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados|	RF-28|

## Historia

Como administrador, quiero que la plataforma esté disponible desde cualquier dispositivo con navegador web,
para poder administrar el conjunto desde el celular, tableta o computador en cualquier lugar.

# Criterios de aceptación

## CA-28.1 — Diseño responsivo
- Dado que accedo a la plataforma desde distintos dispositivos,
- cuando la interfaz se carga,
- entonces debe adaptarse correctamente a pantallas de distintos tamaños (móvil, tableta, escritorio).

## CA-28.2 — Funciones principales disponibles en móvil
- Dado que accedo desde un dispositivo móvil,
- cuando utilizo las funciones principales del sistema (residentes, documentos, reuniones, finanzas, PQRS, notificaciones),
- entonces debo poder usarlas sin pérdida de funcionalidad respecto a la versión de escritorio.

## CA-28.3 — Compatibilidad con navegadores comunes
- Dado que accedo a la plataforma,
- cuando utilizo un navegador web estándar (Chrome, Safari, Firefox, Edge),
- entonces el sistema debe funcionar correctamente sin requerir instalación adicional.

## CA-28.4 — Navegación adaptada a pantallas táctiles
- Dado que accedo desde un dispositivo con pantalla táctil,
- cuando interactúo con los elementos de la interfaz (botones, menús, formularios),
- entonces estos deben ser fácilmente utilizables mediante toques (tamaño y espaciado adecuados).

## CA-28.5 — Sin necesidad de aplicación nativa
- Dado que quiero acceder a la plataforma desde un dispositivo nuevo,
- cuando ingreso la URL en el navegador,
- entonces debo poder utilizar el sistema completo sin necesidad de instalar una aplicación nativa.

## Notas / Pendientes de definición
- Confirmar el listado de navegadores y versiones mínimas soportadas oficialmente.
- Definir si existirá también una aplicación móvil nativa a futuro o si el enfoque será exclusivamente web responsivo (PWA).
