# HU-022 — Consulta del acta de la última asamblea por el consejo

| Campo | Valor |
|---|---|
| **ID** | HU-022 |
| **Rol** | Consejo del conjunto |
| **Módulo** | Documentos / Panel del consejo |
| **Permisos** | `documentos.ver`, `documentos.descargar` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** consejo del conjunto, **quiero** quiero ver la transcripción y acta de la última asamblea,
> **para** para revisar y verificar las decisiones tomadas oficialmente en la reunión.

## Criterio de aceptación

> El consejo accede al documento del acta desde la sección de documentos. El archivo está disponible en PDF y no puede ser editado por el residente común.

## Implementación

### Backend
- `GET /documentos` + `tipo_documento = acta` — el acta publicada se lista para el consejo y para
  los residentes; `GET /documentos/{id}/descargar` entrega el PDF.
- `PUT /documentos/{id}` exige `documentos.editar` (sólo administración): el residente recibe `403`,
  de modo que el acta es de sólo lectura para él.

### Frontend
- `frontend/src/pages/Dashboard/Consejo.tsx`: bloque **Actas y documentos oficiales** con versión y
  botón de descarga; en `Documentos.tsx` los residentes ven el archivo sin acciones de edición.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_acta_y_reporte_del_consejo` — el acta es visible para el
  consejo y el residente, y el residente recibe `403` al intentar editarla.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
