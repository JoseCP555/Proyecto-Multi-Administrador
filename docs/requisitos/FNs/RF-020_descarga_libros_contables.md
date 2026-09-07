# RF-020 — Descarga de libros contables

## Identificación

| Campo | Valor |
| ------------- | ------------------------------------------------------------ |
| **ID** | RF-020 |
| **Nombre** | Descarga de libros contables y financieros |
| **Módulo** | Reportes Financieros |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Fecha** | Julio 2026 |

## Descripción
El sistema debe permitir al Consejo la descarga de los libros
contables y financieros para fines de vigilancia y auditoría.
## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
| --------------------- | -------- | ----------- | ------------------------------------------------------------------------ |
| `property_id` | UUID | Sí | Debe corresponder a una copropiedad registrada. |
| `book_type` | Enum | Sí | Valores permitidos: Libro Diario, Libro Mayor, Balance General, Estado de Resultados, Flujo de Caja. |
| `report_period` | Fecha | Sí | Debe corresponder a un período contable válido. |
| `export_format` | Enum | Sí | Valores permitidos: PDF, Excel, CSV. |
| `council_member_id` | UUID | Sí | Debe corresponder a un miembro activo del Consejo de Administración. |
| `download_reason` | Texto | No | Máximo 500 caracteres. Se utiliza para registrar el motivo de la descarga en auditoría. |

## Proceso

1. El miembro del Consejo de Administración inicia sesión en el sistema.
2. El sistema verifica que el usuario tenga el rol **Consejero** y permisos para consultar información financiera.
3. El usuario accede al módulo de libros contables y financieros.
4. El sistema muestra los libros disponibles para descarga según la copropiedad y el período seleccionado.
5. El usuario selecciona el tipo de libro, el período contable y el formato de descarga.
6. El sistema valida que existan registros para los parámetros seleccionados.
7. El sistema genera el libro contable o financiero en el formato solicitado (PDF, Excel o CSV).
8. El sistema registra la solicitud de descarga, incluyendo el usuario, la fecha, la hora y el tipo de documento descargado.
9. El sistema pone el archivo a disposición del usuario para su descarga.
10. El sistema confirma que la descarga se realizó correctamente.
## Salidas

| Escenario | Código HTTP | Respuesta |
| ------------------------------------------ | ----------- | -------------------------------------------------------------------------------------------- |
| Descarga preparada exitosamente | 200 | Archivo del libro contable o financiero generado correctamente en el formato solicitado. |
| No existen registros para el período | 204 | Mensaje indicando que no se encontraron datos para generar el libro solicitado. |
| Parámetros inválidos | 422 | Detalle de los errores de validación de los datos ingresados. |
| Usuario no autorizado | 403 | Mensaje de error: "No tiene permisos para descargar este documento". |
| Libro contable no encontrado | 404 | Mensaje de error: "El libro contable solicitado no existe". |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error durante la generación o descarga del documento. |

## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | -------------------------------------------------- | -------------- | --------------------------------------------------------------------------- |
| GET | `/api/v1/accounting-books` | Sí | Consulta el listado de libros contables y financieros disponibles. |
| GET | `/api/v1/accounting-books/{id}` | Sí | Obtiene la información de un libro contable o financiero específico. |
| GET | `/api/v1/accounting-books/export` | Sí | Genera y descarga el libro contable o financiero en formato PDF, Excel o CSV. |
| GET | `/api/v1/accounting-books/download/{id}` | Sí | Descarga un libro contable o financiero previamente generado. |
## Reglas de negocio

- RN-001: Solo los miembros del Consejo de Administración con permisos vigentes podrán descargar los libros contables y financieros de la copropiedad.
- RN-002: El sistema permitirá descargar únicamente la información correspondiente a la copropiedad a la que pertenece el consejero.
- RN-003: Los libros contables y financieros deberán contener información actualizada e íntegra al momento de su generación.
- RN-004: El sistema solo permitirá la descarga de los documentos en los formatos autorizados (PDF, Excel y CSV).
- RN-005: Toda descarga deberá registrarse en el historial de auditoría, indicando el usuario, la fecha, la hora, el tipo de documento y el período consultado.
- RN-006: El sistema no permitirá la modificación de los libros contables desde el módulo de consulta; el acceso será exclusivamente de solo lectura.
- RN-007: Si no existen registros para el período seleccionado, el sistema no generará el archivo y notificará al usuario.
- RN-008: El acceso a los libros contables y financieros estará restringido según los permisos asignados al rol **Consejero**, garantizando la confidencialidad de la información.
