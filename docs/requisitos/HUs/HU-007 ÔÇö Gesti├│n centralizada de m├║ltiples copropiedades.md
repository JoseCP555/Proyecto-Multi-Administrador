# HU-07 — Gestión centralizada de múltiples copropiedades

¿Qué? Historia de usuario que describe la administración de varios conjuntos desde un solo panel de control.
¿Para qué? Formalizar la necesidad de administrar de forma centralizada todos los conjuntos a cargo del administrador. 
¿Impacto? Permite escalar el sistema a administradores que gestionan más de un conjunto sin duplicar sesiones.

## Identificación

| Campo | Valor |
| ----- | ----- |
| ID | HU-007 |
| Título|	Gestión centralizada de múltiples copropiedades|
|Módulo	|Administración multi-conjunto|
|Prioridad|	Media|
|Estado	|Por definir|
|RF asociados	|RF-07 | 

## Historia

Como administrador, quiero gestionar múltiples copropiedades desde un solo panel de control, 
para administrar de forma centralizada todos los conjuntos a mi cargo sin cambiar de sesión.

# Criterios de aceptación

## CA-07.1 — Selector de conjunto en el menú principal
- Dado que soy administrador de más de un conjunto,
- cuando accedo al menú principal,
- entonces debo encontrar un selector que me permita elegir entre los conjuntos a mi cargo.

## CA-07.2 — Cambio de conjunto sin cerrar sesión
- Dado que estoy autenticado en la plataforma,
- cuando selecciono un conjunto diferente desde el selector,
- entonces el sistema debe cambiar el contexto de trabajo sin requerir que vuelva a iniciar sesión.

## CA-07.3 — Aislamiento de información entre conjuntos
- Dado que cambié al contexto de un conjunto específico,
- cuando consulto residentes, documentos, finanzas o reuniones,
- entonces solo debo ver la información correspondiente a ese conjunto.

## CA-07.4 — Aislamiento de usuarios entre conjuntos
- Dado que estoy en el contexto de un conjunto,
- cuando consulto el listado de residentes o usuarios,
- entonces solo deben aparecer los usuarios pertenecientes a ese conjunto.

## CA-07.5 — Aislamiento de configuración entre conjuntos
- Dado que cada conjunto tiene su propia configuración,
- cuando modifico ajustes de un conjunto,
- entonces estos cambios no deben afectar la configuración de los demás conjuntos.

## CA-07.6 — Persistencia del conjunto seleccionado
- Dado que seleccioné un conjunto para trabajar,
- cuando navego entre las distintas secciones del sistema,
- entonces el conjunto seleccionado debe mantenerse activo hasta que yo decida cambiarlo.

## CA-07.7 — Acceso restringido a conjuntos no asignados
- Dado que soy administrador de uno o varios conjuntos,
- cuando intento acceder a un conjunto que no tengo asignado,
- entonces el sistema debe impedir el acceso y no mostrarlo en mi selector.

## Notas / Pendientes de definición
- Confirmar si un mismo administrador puede tener diferentes roles según el conjunto (ej. administrador en uno, consejo en otro).
- Definir el flujo para que un administrador solicite o reciba acceso a un nuevo conjunto.
