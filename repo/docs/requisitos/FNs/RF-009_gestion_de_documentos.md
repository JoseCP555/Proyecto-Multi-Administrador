# RF-009 — Gestión de documentos

## Identificación


| Campo         | Valor                                    |
| ------------- | ---------------------------------------- |
| **ID**        | RF-009                                   |
| **Nombre**    | Gestión de documentos oficiales          |
| **Módulo**    | Gestión Documental                       |
| **Prioridad** | Alta                                     |
| **Estado**    | Pendiente                                |
| **Fecha**     | Febrero 2026                             |
## Descripción

El sistema debe permitir al Administrador subir y clasificar
documentos oficiales (Reglamento PH, Actas, Balances) para su
consulta por los residentes.

## Entradas

| Campo                | Tipo              | Obligatorio | Validaciones                                                                 |
| -------------------- | ----------------- | ----------- | ---------------------------------------------------------------------------- |
| `document_name`      | Texto             | Sí          | Mínimo 3 caracteres, máximo 255.                                             |
| `document_type`      | Texto             | Sí          | Debe corresponder a una categoría válida (`Reglamento PH`, `Acta`, `Balance` u otra definida por el sistema). |
| `file`               | Archivo (PDF, DOCX) | Sí        | Debe ser un formato permitido y no exceder el tamaño máximo configurado.     |
| `property_id`        | UUID              | Sí          | Debe corresponder a una copropiedad registrada.                              |
| `description`        | Texto             | No          | Máximo 500 caracteres. 
## Proceso

1. El Administrador inicia sesión en la plataforma y accede al módulo de **Gestión Documental**.
2. El Administrador selecciona la opción para cargar un nuevo documento oficial.
3. El frontend solicita el nombre, la categoría, la descripción (opcional), la copropiedad y el archivo correspondiente.
4. El backend valida que el usuario tenga permisos de Administrador y que el archivo cumpla con el formato y tamaño permitidos.
5. El sistema almacena el documento en el repositorio de archivos y registra su información en la base de datos.
6. El documento queda clasificado según su tipo (Reglamento PH, Acta, Balance u otra categoría definida).
7. El sistema asocia el documento a la copropiedad correspondiente y lo marca como disponible para consulta.
8. Los residentes autenticados pueden consultar y descargar únicamente los documentos publicados para su copropiedad.
9. El sistema registra la carga del documento y las consultas realizadas para fines de auditoría.

## Salidas

| Escenario                              | Código HTTP | Respuesta                                                                                              |
| -------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------ |
| Documento cargado exitosamente         | 201         | Datos del documento registrado (`document_id`, `document_name`, `document_type`, `property_id`, `created_at`). |
| Documento actualizado correctamente    | 200         | Mensaje de confirmación y datos actualizados del documento.                                            |
| Documento no encontrado                | 404         | Mensaje de error: "Documento no encontrado".                                                           |
| Archivo con formato no permitido       | 400         | Mensaje de error: "El formato del archivo no es válido".                                               |
| Archivo excede el tamaño permitido     | 400         | Mensaje de error: "El archivo supera el tamaño máximo permitido".                                      |
| Datos inválidos                        | 422         | Detalle de los errores de validación.                                                                  |
| Error al almacenar el documento        | 500         | Mensaje de error: "No fue posible almacenar el documento".                                             |
## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ------------------------------------------ | -------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/documents` | Sí (Administrador) | Carga un nuevo documento oficial al sistema. |
| GET    | `/api/v1/documents` | Sí | Lista los documentos disponibles según la copropiedad y los permisos del usuario. |
| GET    | `/api/v1/documents/{document_id}` | Sí | Obtiene la información de un documento específico. |
| PUT    | `/api/v1/documents/{document_id}` | Sí (Administrador) | Actualiza la información o el archivo de un documento oficial. |
| DELETE | `/api/v1/documents/{document_id}` | Sí (Administrador) | Elimina un documento oficial del sistema. |
| GET    | `/api/v1/documents/{document_id}/download` | Sí | Descarga el documento oficial seleccionado. |
## Reglas de negocio

---

## Reglas de negocio

- RN-001: Solo los usuarios con rol **Administrador** podrán cargar, actualizar o eliminar documentos oficiales.
- RN-002: Todo documento deberá estar asociado a una copropiedad registrada en el sistema.
- RN-003: Cada documento deberá clasificarse en una categoría válida (Reglamento PH, Acta, Balance u otra definida por el sistema).
- RN-004: Solo se aceptarán archivos en los formatos permitidos por el sistema y que no superen el tamaño máximo configurado.
- RN-005: Los residentes únicamente podrán consultar y descargar los documentos publicados para la copropiedad a la que pertenecen.
- RN-006: El sistema conservará la fecha de carga, el autor y la última actualización de cada documento.
- RN-007: No se permitirá eliminar un documento que esté marcado como obligatorio o vigente sin una autorización administrativa.
- RN-008: Toda carga, modificación, eliminación y descarga de documentos deberá registrarse en el historial de auditoría del sistema.
- RN-009: Los documentos deberán almacenarse de forma segura para garantizar su integridad y disponibilidad.
- RN-010: Los documentos publicados estarán disponibles para consulta de los residentes hasta que sean reemplazados, archivados o eliminados por un Administrador.
