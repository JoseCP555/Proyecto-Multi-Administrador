# RF-002 — Control de acceso por roles

## Identificación
| Campo | Valor |
|----------------|-----------------------------------------------------------|
| **ID** | RF-002 |
| **Nombre** | Control de acceso basado en roles |
| **Módulo** | Seguridad y Autenticación |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Actor principal** | Usuario autenticado (Administrador, Residente, Seguridad, Mantenimiento y Consejero) |
| **Actores secundarios** | Sistema de autenticación, Base de datos, Administrador del sistema |
| **Versión** | 1.0 |
| **Autor** | Equipo de desarrollo |
| **Fecha de creación** | Julio 2026 |
| **Última actualización** | Julio 2026 |

## Descripción

El sistema debe implementar un control de acceso basado en roles
(Administrador, Residente, Seguridad, Mantenimiento y Consejero) 

## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
|--------|------|-------------|--------------|
| `email` | Texto (Email) | Sí | Debe corresponder a un correo registrado y tener un formato válido. |
| `password` | Texto | Sí | Debe coincidir con la contraseña almacenada para el usuario. |
| `rol` | Lista | Sí | Debe ser uno de los roles permitidos: Administrador, Residente, Seguridad, Mantenimiento o Consejero. |
| `token` | Texto (JWT) | Sí | Debe ser un token válido, no expirado y generado por el sistema. |
| `permiso` | Texto | Sí | Debe corresponder a un permiso existente dentro del sistema. |
| `id_usuario` | Entero | Sí | Debe existir en la base de datos y encontrarse activo. |
| `estado_usuario` | Booleano | Sí | El usuario debe estar activo y con la cuenta verificada para acceder al sistema. |

## Proceso

1. El usuario accede al formulario de inicio de sesión de la plataforma.
2. El usuario ingresa su correo electrónico y contraseña.
3. El sistema valida que los campos obligatorios hayan sido diligenciados correctamente.
4. El sistema verifica que el correo electrónico exista y que la contraseña corresponda al usuario registrado.
5. El sistema comprueba que la cuenta se encuentre activa y que el correo electrónico haya sido verificado.
6. Una vez autenticado, el sistema identifica el rol asignado al usuario (Administrador, Residente, Seguridad, Mantenimiento o Consejero).
7. El sistema consulta los permisos asociados al rol del usuario en la base de datos.
8. El sistema genera un token de autenticación (JWT) con la información del usuario y sus permisos.
9. El sistema habilita únicamente los módulos, menús y funcionalidades permitidas para el rol identificado.
10. Si el usuario intenta acceder a una funcionalidad para la que no posee permisos, el sistema bloqueará el acceso y mostrará un mensaje de autorización insuficiente.
11. El sistema registra en el historial de auditoría la fecha, hora, usuario, dirección IP y acción realizada durante el inicio de sesión.
12. El usuario podrá utilizar únicamente las funcionalidades autorizadas hasta que cierre sesión o el token de autenticación expire.
13. Al finalizar la sesión, el sistema invalidará el token y cerrará el acceso a todos los recursos protegidos.


## Salidas

| Escenario | Código HTTP | Respuesta |
|-------------------------------|------------|--------------------------------------------------------------------------------------------------------------|
| Inicio de sesión exitoso | 200 | Se concede el acceso al sistema y se muestra la interfaz correspondiente al rol del usuario. Se genera un token de autenticación válido. |
| Credenciales incorrectas | 401 | Mensaje de error: "Correo electrónico o contraseña incorrectos." |
| Usuario no registrado | 404 | Mensaje indicando que el usuario no existe en el sistema. |
| Cuenta inactiva | 403 | Mensaje indicando que la cuenta se encuentra deshabilitada y no puede acceder al sistema. |
| Correo no verificado | 403 | Mensaje indicando que el usuario debe verificar su correo electrónico antes de iniciar sesión. |
| Acceso denegado por permisos | 403 | Mensaje indicando que el usuario no tiene autorización para acceder al módulo o funcionalidad solicitada. |
| Token expirado o inválido | 401 | Mensaje indicando que la sesión ha expirado y el usuario debe iniciar sesión nuevamente. |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error inesperado durante la autenticación y se recomienda intentar nuevamente más tarde. |

## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
|--------|----------------------------------|----------------|---------------------------------------------------------------|
| POST | `/api/v1/auth/login` | No | Autentica al usuario y genera un token de acceso (JWT). |
| POST | `/api/v1/auth/logout` | Sí | Cierra la sesión del usuario e invalida el token de autenticación. |
| GET | `/api/v1/users/me` | Sí | Obtiene la información del usuario autenticado, incluyendo su rol y permisos. |
| GET | `/api/v1/roles` | Sí | Consulta la lista de roles disponibles en el sistema. |
| GET | `/api/v1/roles/{id}/permissions` | Sí | Obtiene los permisos asociados a un rol específico. |
| PUT | `/api/v1/users/{id}/role` | Sí (Administrador) | Permite asignar o modificar el rol de un usuario. |
| GET | `/api/v1/auth/validate-token` | Sí | Verifica que el token de autenticación sea válido y no haya expirado. |
## Reglas de negocio

- RN-001: Cada usuario del sistema debe tener asignado un único rol activo (Administrador, Residente, Seguridad, Mantenimiento o Consejero).

- RN-002: Los permisos de acceso a módulos, funcionalidades y recursos dependerán exclusivamente del rol asignado al usuario.

- RN-003: Solo el Administrador podrá crear, modificar, asignar o eliminar roles y permisos dentro del sistema.

- RN-004: Un usuario no podrá acceder a funcionalidades que no correspondan a su rol; el sistema bloqueará automáticamente cualquier intento de acceso no autorizado.

- RN-005: Para acceder al sistema, el usuario deberá tener una cuenta activa y un correo electrónico previamente verificado.

- RN-006: Toda autenticación exitosa generará un token de acceso (JWT) con tiempo de expiración definido por la configuración del sistema.

- RN-007: Si el token de autenticación expira o es inválido, el usuario deberá iniciar sesión nuevamente para continuar utilizando la plataforma.

- RN-008: El sistema registrará en un historial de auditoría todos los intentos de inicio de sesión, accesos, cierres de sesión y accesos denegados.

- RN-009: Después de cinco (5) intentos fallidos consecutivos de inicio de sesión, la cuenta será bloqueada temporalmente por un período de 15 minutos.

- RN-010: El sistema deberá cerrar automáticamente la sesión del usuario después de un período de inactividad de 30 minutos.

- RN-011: Los cambios realizados sobre los roles y permisos deberán registrarse indicando el usuario que realizó la modificación, la fecha y la hora.

- RN-012: Ningún usuario podrá modificar sus propios permisos o cambiar el rol que tiene asignado.

- RN-013: El sistema verificará los permisos del usuario antes de ejecutar cualquier operación que requiera autorización.

- RN-014: Los permisos asignados a un rol se aplicarán inmediatamente después de que el usuario inicie una nueva sesión.

- RN-015: Todas las comunicaciones relacionadas con la autenticación y autorización deberán realizarse mediante conexiones seguras (HTTPS).

