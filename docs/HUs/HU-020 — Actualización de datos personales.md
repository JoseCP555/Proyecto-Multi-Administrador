# HU-020 — Actualización de datos personales

¿Qué? Historia de usuario que describe la actualización de datos personales por parte del residente. 
¿Para qué? Formalizar la necesidad de mantener la información de contacto al día y recibir comunicaciones correctamente.
¿Impacto? Garantiza que las notificaciones, comunicados y comunicaciones lleguen a los datos correctos del residente.

# Identificación

| Campo | Valor |
| ----------- | ----------- |
| ID | HU-020 |
| Título	|Actualización de datos personales|
|Módulo	|Perfil de usuario|
|Prioridad|	Media|
|Estado	|Por definir|
|RF asociados|	RF-20 | 

## Historia

Como residente, quiero actualizar mis datos personales dentro de la plataforma,
para mantener mi información de contacto al día y recibir comunicaciones correctamente.

#Criterios de aceptación

##CA-20.1 — Edición de datos de contacto
- Dado que soy residente y accedo a mi perfil,
- cuando edito mis datos,
- entonces debo poder actualizar mi número de teléfono, correo electrónico y foto de perfil.

## CA-20.2 — Validación de formato de correo
- Dado que estoy actualizando mi correo electrónico,
- cuando ingreso un valor con formato inválido,
- entonces debo ver un mensaje de error indicando que el correo no es válido.

## CA-20.3 — Validación de formato de teléfono
- Dado que estoy actualizando mi número de teléfono,
- cuando ingreso un valor con formato inválido (letras o longitud incorrecta),
- entonces debo ver un mensaje de error indicando que el número no es válido.

## CA-20.4 — Carga de foto de perfil
- Dado que estoy actualizando mi foto de perfil,
- cuando selecciono una imagen,
- entonces el sistema debe permitir formatos de imagen comunes (JPG/PNG) y mostrar una vista previa antes de guardar.

## CA-20.5 — Confirmación de la actualización
- Dado que modifiqué mis datos personales,
- cuando confirmo la actualización,
- entonces los cambios deben guardarse y reflejarse de inmediato en mi perfil.

## CA-20.6 — Estado de carga
- Dado que envié la actualización de mis datos,
- cuando la solicitud está en proceso,
- entonces el botón de guardar debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Confirmar si el cambio de correo electrónico requiere verificación (similar al flujo de HU-001) antes de quedar activo.
- Definir si el nombre completo y el apartamento asignado también son editables por el residente o solo por el administrador (relación con HU-02).
