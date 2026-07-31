# HU-013 — Subida de comprobante de pago

¿Qué? Historia de usuario que describe la subida del comprobante de pago de administración por parte del residente.
¿Para qué? Formalizar la necesidad de confirmar que el pago se realizó a tiempo y contar con un registro digital.
¿Impacto? Agiliza la conciliación de pagos entre residente y administración.

# Identificación

| Campo | Valor |
| ------| ----- |
| ID | HU-013 |
| Título	|Subida de comprobante de pago  |
|Módulo	|Finanzas | 
|Prioridad	|Alta  |
|Estado	|Por definir|
|RF asociados|	RF-13 |

## Historia

Como residente, quiero subir mi comprobante de pago de administración desde la app,
para confirmar que realicé el pago a tiempo y tener un registro digital.

# Criterios de aceptación

## CA-13.1 — Formulario de carga de comprobante
- Dado que soy residente y accedo a la sección de pagos,
- cuando subo un comprobante de pago,
- entonces debo poder adjuntar una imagen o un archivo PDF del comprobante.

## CA-13.2 — Formatos permitidos
- Dado que estoy subiendo un comprobante,
- cuando selecciono el archivo,
- entonces el sistema solo debe permitir imágenes (JPG/PNG) o archivos PDF.


## CA-13.3 — Estado inicial "En revisión"
- Dado que subí mi comprobante de pago,
- cuando consulto el estado de mi pago,
- entonces este debe mostrarse como "En revisión" hasta que el administrador lo confirme.

## CA-13.4 — Confirmación del pago por el administrador
- Dado que el administrador revisa un comprobante subido,
- cuando lo aprueba,
- entonces el estado del pago debe actualizarse a "Confirmado" y reflejarse en el historial del residente.

## CA-13.5 — Rechazo del comprobante
- Dado que el administrador revisa un comprobante subido,
- cuando lo rechaza (por ilegible, monto incorrecto, etc.),
- entonces el estado debe actualizarse a "Rechazado" y el residente debe recibir una notificación con el motivo.

## CA-13.6 — Notificación al residente sobre el resultado de la revisión
- Dado que el administrador confirma o rechaza un comprobante,
- cuando el sistema procesa el cambio de estado,
- entonces el residente debe recibir una notificación del resultado.

## CA-13.7 — Estado de carga durante la subida
- Dado que envié un comprobante de pago,
- cuando el archivo está siendo procesado,
- entonces debo ver un indicador de carga hasta que finalice la subida.

## Notas / Pendientes de definición
- Confirmar si existe un límite de tamaño para el archivo del comprobante.
- Relacionar con HU-05 (registro de ingresos) para definir si la confirmación del comprobante genera automáticamente el movimiento financiero.
