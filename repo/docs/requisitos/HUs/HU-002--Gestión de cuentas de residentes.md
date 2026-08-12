# HU-02 — Gestión de cuentas de residentes

 ¿Qué? Historia de usuario que describe la creación, edición y eliminación de cuentas de residentes por parte del administrador.
 ¿Para qué? Formalizar la necesidad de dar acceso controlado al sistema y mantener el directorio actualizado.
 ¿Impacto? Es la base del directorio de residentes; sin esta gestión no hay control de quién accede al sistema. 

## Identificación

| Campo | Valor |
| ----- | ----- |
| ID    | HU-02 |
| Título|	Gestión de cuentas de residentes|
|Módulo	|Administración de usuarios|
|Prioridad|	Alta|
|Estado	|Por definir|
|RF asociados	|RF-02 |


## Historia
Como administrador, quiero crear, editar y eliminar cuentas de residentes desde la plataforma,
para dar acceso controlado al sistema y mantener el directorio actualizado.


# Criterios de aceptación

## CA-02.1 — Formulario de creación de residente
- Dado que soy administrador y accedo a la sección de residentes,
- Cuando creo una nueva cuenta,
- Entonces debo poder ingresar nombre, apartamento, correo electrónico y rol del residente.

## CA-02.2 — Validación de campos obligatorios
- Dado que estoy creando o editando una cuenta de residente,
- Cuando dejo algún campo obligatorio vacío y envío el formulario,
- Entonces debo ver un mensaje de error indicando qué campo falta.

## CA-02.3 — Validación de correo duplicado
-Dado que intento registrar un residente con un correo ya existente en el sistema,
- Cuando envío el formulario,
- Entonces debo ver un mensaje de error indicando que el correo ya está registrado.

## CA-02.4 — Edición de residente existente
- Dado que selecciono un residente ya registrado,
- Cuando modifico sus datos (nombre, apartamento, correo o rol) y guardo los cambios,
- Entonces la información debe actualizarse y reflejarse de inmediato en el sistema.

## CA-02.5 — Eliminación de residente con confirmación
- Dado que selecciono un residente para eliminar,
- Cuando confirmo la acción en el diálogo de confirmación,
- Entonces la cuenta debe eliminarse (o desactivarse) y dejar de tener acceso al sistema.

## CA-02.6 — Reflejo inmediato de cambios
- Dado que realicé una creación, edición o eliminación de un residente,
-Cuando consulto el listado de residentes,
- Entonces los cambios deben verse reflejados sin necesidad de recargar manualmente ni esperar procesos externos.

## CA-02.7 — Estado de carga durante las operaciones
- Dado que envié una acción de creación, edición o eliminación,
-Cuando la solicitud está en proceso,
- Entonces el botón correspondiente debe estar deshabilitado y mostrar un indicador de carga.

## CA-02.8 — Listado y búsqueda de residentes
- Dado que estoy en la sección de residentes,
- Cuando consulto el listado,
- Entonces debo poder ver todos los residentes registrados y buscarlos por nombre, apartamento o correo.

## Notas / Pendientes de definición
- Definir si la eliminación es física (borrado permanente) o lógica (desactivación con posibilidad de reactivar).
- Confirmar los roles disponibles y si esta historia incluye la asignación de rol (relacionar con HU-08).
