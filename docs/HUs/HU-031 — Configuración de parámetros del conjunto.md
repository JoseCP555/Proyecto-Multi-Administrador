HU-031 — Configuración de parámetros del conjunto

¿Qué? Historia de usuario que describe la configuración de parámetros generales del conjunto (nombre, logo, datos de contacto).
¿Para qué? Formalizar la necesidad de personalizar la plataforma con la identidad de cada copropiedad administrada.
¿Impacto? Permite que la plataforma se adapte a la identidad visual y datos de cada conjunto, especialmente relevante para administradores multi-conjunto (HU-07). -->

# Identificación

|Campo	|Valor|
| ----------- | ----------- |
|ID|	HU-031|
|Título	|Configuración de parámetros del conjunto|
|Módulo	|Configuración del conjunto|
|Prioridad|	Media|
|Estado|	Por definir|
|RF asociados|	RF-031|

#Historia

Como administrador, quiero configurar los parámetros del conjunto como nombre, logo y datos de contacto,
para personalizar la plataforma con la identidad de cada copropiedad que administro.

# Criterios de aceptación

## CA-31.1 — Edición del nombre del conjunto
- Dado que soy administrador y accedo a la configuración del conjunto,
- cuando edito el nombre,
- entonces el cambio debe guardarse y reflejarse en la plataforma.

## CA-31.2 — Carga de logo
- Dado que estoy configurando el conjunto,
- cuando subo una imagen como logo,
- entonces el sistema debe permitir formatos JPG o PNG con un tamaño máximo de 2 MB.

## CA-31.3 — Validación de formato y tamaño del logo
- Dado que intento subir un logo con formato no permitido o que supera los 2 MB,
- cuando envío el formulario,
- entonces debo ver un mensaje de error indicando el problema.

## CA-31.4 — Edición de dirección y teléfono
- Dado que estoy configurando el conjunto,
- cuando edito la dirección y el teléfono de contacto,
- entonces los cambios deben guardarse correctamente.

## CA-31.5 — Reflejo inmediato de los cambios
- Dado que guardé cambios en la configuración del conjunto,
- cuando navego por la plataforma,
- entonces los cambios (nombre, logo, datos de contacto) deben verse reflejados de inmediato.

## CA-31.6 — Restricción de acceso a la configuración
- Dado que soy residente o miembro del consejo,
- cuando intento acceder a la configuración del conjunto,
- entonces el sistema debe restringir el acceso, ya que esta acción es exclusiva del administrador.

## CA-31.7 — Estado de carga
- Dado que envié cambios en la configuración del conjunto,
- cuando la solicitud está en proceso,
- entonces el botón de guardar debe estar deshabilitado y mostrar un indicador de carga.

## Notas / Pendientes de definición
- Relacionar con HU-07 (gestión de múltiples copropiedades), ya que cada conjunto debe tener su propia configuración independiente.
- Confirmar si existen otros parámetros configurables (ej. moneda, zona horaria, política de reservas).
