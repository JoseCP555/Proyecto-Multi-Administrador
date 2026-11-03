# HU-008 — Asignación de roles y permisos
¿Qué? Historia de usuario que describe la asignación de roles y permisos a los usuarios del sistema.
¿Para qué? Formalizar la necesidad de controlar qué acciones puede realizar cada tipo de usuario dentro de la plataforma.
¿Impacto? Garantiza la seguridad y el control de acceso a las funcionalidades del sistema según el tipo de usuario.

# Identificación

| Campo  | Valor |
| -------| ----- |
| ID | HU-008 |
| Título|	Asignación de roles y permisos|
|Módulo|	Administración de usuarios / Seguridad|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados	|RF-08 | 

## Historia

Como administrador, quiero asignar roles y permisos a los usuarios del sistema,
para controlar qué acciones puede realizar cada tipo de usuario dentro de la plataforma.

# Criterios de aceptación
## CA-08.1 — Listado de roles disponibles
- Dado que soy administrador y accedo a la gestión de usuarios,
- cuando consulto las opciones de rol,
- entonces debo poder elegir entre los roles: residente, consejo o administrador.
## CA-08.2 — Asignación de rol a un usuario
- Dado que selecciono un usuario del sistema,
- cuando le asigno un rol específico y guardo el cambio,
- entonces el usuario debe quedar registrado con ese rol.

## CA-08.3 — Cambio inmediato de permisos
- Dado que actualicé el rol de un usuario,
- cuando el cambio se guarda,
- entonces los permisos del usuario deben actualizarse de inmediato, sin requerir que cierre y vuelva a iniciar sesión.

## CA-08.4 — Restricción de acciones según el rol
- Dado que un usuario tiene un rol específico,
- cuando intenta acceder a una funcionalidad no permitida para su rol,
- entonces el sistema debe impedir la acción y mostrar un mensaje indicando que no tiene permisos suficientes.

## CA-08.5 — Validación de rol obligatorio
- Dado que estoy creando o editando un usuario,
- cuando no selecciono ningún rol,
- entonces debo ver un mensaje de error indicando que el rol es obligatorio.

## CA-08.6 — Visualización de permisos por rol
- Dado que estoy en la sección de gestión de roles,
- cuando consulto un rol específico,
- entonces debo poder ver qué acciones o módulos tiene permitidos ese rol.

## CA-08.7 — Estado de carga durante la actualización
- Dado que envié un cambio de rol,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Definir la matriz completa de permisos por rol (qué puede hacer cada uno: residente, consejo, administrador).
- Confirmar si se requiere un registro de auditoría de los cambios de rol realizados.
