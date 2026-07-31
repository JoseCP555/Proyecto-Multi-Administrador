# HU-030 — Recuperación de contraseña

¿Qué? Historia de usuario que describe la recuperación de contraseña desde la pantalla de inicio de sesión. 
¿Para qué? Formalizar la necesidad de acceder a la plataforma si el usuario olvidó sus credenciales, sin depender del administrador.
¿Impacto? Reduce la carga operativa del administrador y mejora la autonomía del usuario. -->

#Identificación

|Campo|	Valor|
| ----------- | ----------- |
|ID|	HU-030|
|Título	|Recuperación de contraseña|
|Módulo|	Autenticación|
|Prioridad	|Alta|
|Estado	|Por definir|
|RF asociados|	RF-30|

##Historia

Como residente, quiero recuperar mi contraseña desde la pantalla de inicio de sesión,
para poder acceder a la plataforma si olvidé mis credenciales sin depender del administrador.

# Criterios de aceptación

## CA-30.1 — Enlace de "¿Olvidaste tu contraseña?"
- Dado que estoy en la pantalla de inicio de sesión,
- cuando olvido mi contraseña,
- entonces debo encontrar un enlace o botón para iniciar el proceso de recuperación.

## CA-30.2 — Solicitud de recuperación por correo
- Dado que inicié el proceso de recuperación,
- cuando ingreso mi correo electrónico registrado y lo envío,
- entonces el sistema debe enviar un enlace de recuperación a ese correo.

## CA-30.3 — Expiración del enlace de recuperación
- Dado que recibí un enlace de recuperación,
- cuando intento usarlo después de 30 minutos de haber sido generado,
- entonces el sistema debe rechazarlo e indicar que el enlace expiró, ofreciendo la opción de solicitar uno nuevo.

## CA-30.4 — Establecimiento de nueva contraseña
- Dado que hago clic en un enlace de recuperación válido (no expirado, no usado),
- cuando ingreso una nueva contraseña que cumple los requisitos de seguridad,
- entonces mi contraseña debe actualizarse y debo poder iniciar sesión con la nueva credencial.

## CA-30.5 — Correo no registrado
- Dado que solicito la recuperación de contraseña,
- cuando ingreso un correo que no está registrado en el sistema,
- entonces el sistema debe mostrar un mensaje genérico (sin confirmar ni negar la existencia del correo) por motivos de seguridad.

## CA-30.6 — Invalidación de enlaces anteriores
- Dado que solicito un nuevo enlace de recuperación,
- cuando el sistema genera el nuevo enlace,
- entonces cualquier enlace de recuperación anterior para esa cuenta debe quedar invalidado.

## CA-30.7 — Estado de carga
- Dado que envié una solicitud de recuperación o una nueva contraseña,
- cuando la solicitud está en proceso,
- entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Relacionar con HU-001 (registro de cuenta) y HU-27 (autenticación segura), ya que comparten el módulo de Autenticación.
- Confirmar si el enlace de recuperación es de un solo uso.
