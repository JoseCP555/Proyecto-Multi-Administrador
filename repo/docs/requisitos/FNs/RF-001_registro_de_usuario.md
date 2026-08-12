# RF-001 — Registro de usuario

## Identificación
| Campo | Valor |
|----------------|-----------------------------------------------|
| **ID** | RF-001 |
| **Nombre** | Registro de usuario |
| **Módulo** | Autenticación y Gestión de Usuarios |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Actor principal** | Usuario (Administrador, Residente, Seguridad, Mantenimiento o Consejero) |
| **Actores secundarios** | Sistema de autenticación, Base de datos, Servicio de correo electrónico |
| **Versión** | 1.0 |
| **Autor** | Equipo de desarrollo |
| **Fecha de creación** | Julio 2026 |
| **Última actualización** | Julio 2026 |
## Descripción

El sistema debe permitir al Administrador configurar y gestionar la
información, usuarios, y finanzas de múltiples copropiedades desde
una única interfaz unificada.

## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
|--------|------|-------------|--------------|
| `full_name` | Texto | Sí | Mínimo 3 caracteres, máximo 100. Solo se permiten letras y espacios. |
| `email` | Texto (Email) | Sí | Debe tener un formato de correo válido, máximo 255 caracteres y ser único en el sistema. |
| `password` | Texto | Sí | Mínimo 8 caracteres, máximo 20. Debe contener al menos una mayúscula, una minúscula, un número y un carácter especial. |
| `confirm_password` | Texto | Sí | Debe coincidir exactamente con el valor del campo `password`. |
| `phone` | Texto | No | Solo números, longitud entre 7 y 15 dígitos. |
| `document_type` | Lista | Sí | Debe seleccionarse un tipo de documento válido (CC, CE, TI, Pasaporte). |
| `document_number` | Texto | Sí | Debe ser único en el sistema y contener únicamente números. |
| `role` | Lista | Sí | Debe corresponder a uno de los roles permitidos (Administrador, Residente, Seguridad, Mantenimiento o Consejero). |
| `accept_terms` | Booleano | Sí | Debe estar marcado para aceptar los términos y condiciones y la política de tratamiento de datos personales. |

## Proceso

1. El usuario accede al formulario de registro desde la plataforma web o aplicación móvil.
2. El usuario ingresa la información solicitada: nombre completo, correo electrónico, contraseña y confirmación de contraseña.
3. El sistema valida que todos los campos obligatorios estén completos.
4. El sistema verifica que el formato del correo electrónico sea válido.
5. El sistema comprueba que el correo electrónico no esté registrado previamente.
6. El sistema valida que la contraseña cumpla con la política de seguridad establecida (longitud mínima, mayúsculas, minúsculas, números y caracteres especiales).
7. El sistema verifica que la contraseña y su confirmación coincidan.
8. La contraseña es cifrada utilizando un algoritmo seguro antes de almacenarse en la base de datos.
9. El sistema crea el nuevo registro del usuario asignándole el rol correspondiente y el estado **Pendiente de verificación**.
10. El sistema genera un token único de verificación con una vigencia de 24 horas.
11. El sistema envía automáticamente un correo electrónico con el enlace de verificación al usuario registrado.
12. El sistema registra la fecha, hora y dirección IP desde donde se realizó el registro para efectos de auditoría.
13. El sistema devuelve una respuesta indicando que el registro fue exitoso y que el usuario debe verificar su correo electrónico para activar la cuenta.
14. Una vez el usuario accede al enlace recibido en el correo, el sistema valida el token y activa la cuenta.
15. Finalmente, el usuario queda habilitado para iniciar sesión y acceder a las funcionalidades correspondientes a su rol.

## Salidas

| Escenario | Código HTTP | Respuesta |
|-------------------------------|------------|-----------------------------------------------------------------------------------------------------------|
| Registro exitoso | 201 | Se crea la cuenta del usuario y se devuelve su información básica (`id`, `nombre`, `correo`, `rol`, `estado`, `fecha_registro`). Además, se envía un correo de verificación. |
| Correo ya registrado | 400 | Mensaje de error: "El correo electrónico ya se encuentra registrado en el sistema." |
| Datos inválidos | 422 | Se devuelve el detalle de los errores de validación encontrados en los campos del formulario. |
| Contraseña no cumple los requisitos | 400 | Mensaje indicando que la contraseña no cumple con la política de seguridad establecida. |
| Error al enviar el correo de verificación | 500 | La cuenta se crea correctamente, pero se informa que no fue posible enviar el correo de verificación y se ofrece la opción de reenviarlo posteriormente. |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error inesperado durante el proceso de registro y que el usuario debe intentarlo nuevamente más tarde. |

## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
|--------|-------------------------------|----------------|--------------------------------------------------------------|
| POST | `/api/v1/auth/register` | No | Registra un nuevo usuario en el sistema. |
| POST | `/api/v1/auth/verify-email` | No | Verifica la cuenta del usuario mediante el token enviado al correo electrónico. |
| POST | `/api/v1/auth/resend-verification` | No | Reenvía el correo de verificación cuando el enlace ha expirado o no fue recibido. |
| GET | `/api/v1/users/{id}` | Sí | Consulta la información del usuario registrado. |
| PUT | `/api/v1/users/{id}` | Sí | Permite actualizar la información básica del usuario registrado. |

## Reglas de negocio

 RN-001: El correo electrónico debe ser único dentro del sistema; no se permitirá el registro de dos usuarios con la misma dirección de correo.

- RN-002: La contraseña debe tener como mínimo 8 caracteres, incluyendo al menos una letra mayúscula, una letra minúscula, un número y un carácter especial.

- RN-003: Ninguna contraseña podrá almacenarse en texto plano; siempre deberá cifrarse utilizando un algoritmo seguro (por ejemplo, bcrypt).

- RN-004: Todos los campos obligatorios del formulario (nombre completo, correo electrónico, contraseña y confirmación de contraseña) deberán estar diligenciados antes de enviar la solicitud de registro.

- RN-005: El sistema verificará que el formato del correo electrónico sea válido antes de permitir el registro.

- RN-006: El usuario deberá aceptar los términos y condiciones y la política de tratamiento de datos personales antes de completar el registro.

- RN-007: Una vez registrado el usuario, el sistema asignará automáticamente el rol correspondiente según el tipo de cuenta seleccionado o definido por el administrador.
