# HU-019 — Consulta y descarga de documentos por el residente

| Campo | Valor |
|---|---|
| **ID** | HU-019 |
| **Rol** | Residente |
| **Módulo** | Documentos |
| **Permisos** | `documentos.ver`, `documentos.descargar` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** residente, **quiero** quiero consultar los documentos y actas publicados por la administración,
> **para** para revisar la información oficial del conjunto en cualquier momento.

## Criterio de aceptación

> El residente puede ver y descargar los documentos publicados. Los archivos están organizados por categoría y fecha de publicación.

## Implementación

### Backend
- `GET /documentos` — devuelve los documentos del conjunto ordenados por `fecha_creacion`
  descendente, con `tipo_documento` (categoría), `tamano` y `version`.
- `GET /documentos/{id}/descargar` — descarga real del archivo (permiso `documentos.descargar`).
- `POST /documentos/upload` — (UH-03) sólo PDF/Word y anexos ofimáticos, máximo 20 MB.

### Frontend
- `frontend/src/pages/Dashboard/Documentos.tsx`: listado con categoría y fecha, filtros y botón de
  descarga por archivo; el modal de subida valida formato y tamaño antes de enviar.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_documento_pdf_y_limite_de_20mb` — el residente ve y descarga
  el PDF publicado, se rechazan formatos no permitidos (`415`) y archivos de más de 20 MB (`413`).

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
