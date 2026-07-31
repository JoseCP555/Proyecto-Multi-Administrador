# HU-027 — Autenticación segura de usuarios

¿Qué? Historia de usuario que describe la autenticación de todos los usuarios del sistema mediante usuario y contraseña segura.
¿Para qué? Formalizar la necesidad de proteger la información del conjunto y garantizar que solo usuarios autorizados accedan. 
¿Impacto? Es un requisito de seguridad transversal a toda la plataforma. -->

# Identificación

|Campo|	Valor|
| ----------- | ----------- |
|ID|	HU-27|
|Título	|Autenticación segura de usuarios|
|Módulo|	Autenticación|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados|	RF-27|

## Historia

Como administrador, quiero que el sistema autentique a todos los usuarios con usuario y contraseña segura,
para proteger la información del conjunto y garantizar que solo usuarios autorizados accedan.

# Criterios de aceptación

## CA-27.1 — Inicio de sesión con correo y contraseña
- Dado que soy un usuario registrado,
- cuando ingreso mi correo y contraseña correctos,
- entonces debo poder acceder a la plataforma con los permisos correspondientes a mi rol.

## CA-27.2 — Validación de credenciales incorrectas
- Dado que intento iniciar sesión,
- cuando ingreso un correo o contraseña incorrectos,
- entonces debo ver un mensaje de error genérico que no revele cuál de los dos datos es incorrecto.

## CA-27.3 — Bloqueo tras intentos fallidos
- Dado que he fallado 5 intentos consecutivos de inicio de sesión,
- cuando intento un sexto intento,
- entonces el sistema debe bloquear el acceso por 10 minutos.

## CA-27.4 — Mensaje durante el bloqueo
- Dado que mi cuenta está bloqueada temporalmente,
- cuando intento iniciar sesión durante ese período,
- entonces debo ver un mensaje indicando que la cuenta está bloqueada temporalmente y el tiempo restante o la razón.

## CA-27.5 — Expiración de sesión por inactividad
- Dado que estoy autenticado en la plataforma,
- cuando transcurren 30 minutos sin actividad,
- entonces mi sesión debe cerrarse automáticamente y debo volver a iniciar sesión para continuar.

## CA-27.6 — Requisitos de contraseña segura
- Dado que un usuario crea o cambia su contraseña,
- cuando ingresa el nuevo valor,
- entonces el sistema debe exigir los requisitos mínimos de seguridad definidos (ver CA-001.4 de HU-001: mínimo 8 caracteres, mayúscula, minúscula y número).

## CA-27.7 — Cierre de sesión manual
- Dado que estoy autenticado en la plataforma,
- cuando selecciono la opción de cerrar sesión,
- entonces mi sesión debe finalizar de inmediato y debo ser redirigido a la pantalla de inicio de sesión.

## Notas / Pendientes de definición
- Confirmar si el bloqueo por intentos fallidos es por cuenta, por IP, o ambos.
- Relacionar con HU-001 (registro de cuenta), ya que ambas historias comparten el módulo de Autenticación.
