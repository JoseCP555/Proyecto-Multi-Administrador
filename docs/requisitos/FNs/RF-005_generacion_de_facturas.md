# RF-005 — Generación de facturas

## Identificación

| Campo | Valor |
|----------------|----------------------------------------------------------------|
| **ID** | RF-005 |
| **Nombre** | Generación de facturas de administración |
| **Módulo** | Facturación y Finanzas |
| **Prioridad** | Alta |
| **Estado** | Pendiente |
| **Actor principal** | Administrador |
| **Actores secundarios** | Residente, Sistema de facturación, Base de datos |
| **Versión** | 1.0 |
| **Autor** | Equipo de desarrollo |
| **Fecha de creación** | Julio 2026 |
| **Última actualización** | Julio 2026 |

## Descripción

El sistema debe generar automáticamente las facturas de
administración periódicas (mensuales) basadas en la configuración de
la cuota de cada Propiedad.


## Entradas

| Campo | Tipo | Obligatorio | Validaciones |
|--------|----------------|-------------|------------------------------------------------------------------------|
| `id_residente` | Entero | Sí | Debe corresponder a un residente registrado y activo en el sistema. |
| `periodo_facturacion` | Fecha (Mes/Año) | Sí | Debe ser un período válido y no estar facturado previamente. |
| `valor_administracion` | Decimal | Sí | Debe ser mayor que cero y corresponder a la cuota de administración definida. |
| `conceptos_adicionales` | Lista | No | Deben existir y estar autorizados por la administración (multas, intereses, cuotas extraordinarias, etc.). |
| `fecha_vencimiento` | Fecha | Sí | Debe ser posterior a la fecha de generación de la factura. |
| `estado_factura` | Lista | Sí | Se asignará inicialmente el estado **Pendiente de pago**. |
| `id_administrador` | Entero | Sí | Debe corresponder a un usuario con el rol de Administrador y encontrarse activo. |
| `token` | Texto (JWT) | Sí | Debe ser un token válido y vigente del administrador autenticado. |

## Proceso

1. El administrador inicia sesión en la plataforma con sus credenciales.
2. El sistema valida la autenticación y verifica que el usuario tenga el rol de Administrador.
3. El administrador accede al módulo **Facturación**.
4. El sistema muestra la lista de residentes registrados y activos.
5. El administrador selecciona el residente o el conjunto de residentes para quienes se generará la factura.
6. El administrador define el período de facturación (mes y año), la fecha de vencimiento y los conceptos que serán incluidos en la factura.
7. El sistema calcula automáticamente el valor total de la factura, incluyendo la cuota de administración y los conceptos adicionales, como multas, intereses o cuotas extraordinarias, si existen.
8. El sistema verifica que no exista una factura previamente generada para el mismo residente y período de facturación.
9. Si la validación es correcta, el sistema genera la factura con un número único e irrepetible.
10. El sistema almacena la factura en la base de datos con estado **Pendiente de pago**.
11. El sistema genera la factura en formato digital (PDF) para su consulta y descarga.
12. El sistema envía una notificación al residente informando que la factura se encuentra disponible.
13. El residente podrá consultar, descargar e imprimir la factura desde su estado de cuenta.
14. Finalmente, el sistema registra en el historial de auditoría la fecha, hora, usuario responsable y la información relacionada con la generación de la factura.
## Salidas

| Escenario | Código HTTP | Respuesta |
|-------------------------------|------------|--------------------------------------------------------------------------------------------------------------------|
| Factura generada correctamente | 201 | El sistema genera la factura, le asigna un número único, la almacena en la base de datos con estado **Pendiente de pago** y la pone a disposición del residente en formato PDF. |
| Factura ya existente | 409 | Mensaje indicando que ya existe una factura generada para el residente en el período de facturación seleccionado. |
| Residente no encontrado | 404 | Mensaje indicando que el residente seleccionado no existe o no se encuentra registrado en el sistema. |
| Datos de facturación inválidos | 422 | Mensaje indicando que uno o más datos ingresados son incorrectos o están incompletos. |
| Usuario sin permisos | 403 | Mensaje indicando que el usuario no tiene autorización para generar facturas de administración. |
| Error al generar la factura | 500 | Mensaje indicando que ocurrió un error durante la generación de la factura y que la operación no pudo completarse. |
| Error interno del servidor | 500 | Mensaje indicando que ocurrió un error inesperado en el sistema y se recomienda intentar nuevamente más tarde. |

## Endpoints asociados

| Método | Ruta | Auth requerida | Descripción |
| ------ | ------------------------------- | -------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/invoices/generate-monthly` | Sí (Administrador) | Genera automáticamente las facturas mensuales de todas las propiedades activas. |
| GET    | `/api/v1/invoices` | Sí | Lista las facturas generadas con filtros por mes, año, estado o copropiedad. |
| GET    | `/api/v1/invoices/{invoice_id}` | Sí | Obtiene la información detallada de una factura específica. |
| GET    | `/api/v1/invoices/property/{property_id}` | Sí | Consulta el historial de facturas de una propiedad. |
| PATCH  | `/api/v1/invoices/{invoice_id}/status` | Sí (Administrador) | Actualiza el estado de una factura (Pendiente, Pagada, Vencida o Anulada). |
| POST   | `/api/v1/invoices/{invoice_id}/regenerate` | Sí (Administrador) | Regenera una factura cuando se modifica la cuota de administración o es necesario corregirla. |
| GET    | `/api/v1/invoices/{invoice_id}/pdf` | Sí | Descarga la factura en formato PDF. |

## Reglas de negocio
- RN-001: El sistema solo podrá generar facturas para propiedades activas y asociadas a una copropiedad registrada.
- RN-002: Cada propiedad debe tener una cuota de administración configurada antes de generar la factura mensual.
- RN-003: Solo se podrá generar una factura por propiedad para el mismo período (mes y año).
- RN-004: El sistema calculará automáticamente el valor de la factura según la cuota de administración vigente para la propiedad.
- RN-005: La fecha de vencimiento de la factura se establecerá automáticamente de acuerdo con la configuración definida por la administración.
- RN-006: Las facturas generadas tendrán inicialmente el estado `Pendiente`.
- RN-007: Solo los usuarios con rol **Administrador** podrán generar, regenerar o anular facturas.
- RN-008: Si cambia la cuota de administración después de emitida una factura, esta no se modificará automáticamente; deberá regenerarse o emitirse una nueva según la política de la copropiedad.
- RN-009: Toda factura generada deberá quedar registrada con su fecha de creación, período facturado y propiedad asociada.
- RN-010: El sistema deberá impedir la eliminación de facturas que ya hayan sido pagadas o que tengan un recibo asociado.
