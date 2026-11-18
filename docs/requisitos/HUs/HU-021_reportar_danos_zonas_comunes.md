# HU-021 — Reporte de daño o novedad en zonas comunes

| Campo | Valor |
|---|---|
| **ID** | HU-021 |
| **Rol** | Residente |
| **Módulo** | Mantenimiento |
| **Permisos** | `mantenimiento.crear`, `mantenimiento.ver` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** residente, **quiero** quiero reportar un daño o novedad en las zonas comunes del conjunto,
> **para** para informar a la administración de manera ágil sobre problemas que afectan a la comunidad.

## Criterio de aceptación

> El residente puede describir el daño, adjuntar fotos y enviarlo al administrador. El reporte aparece en el panel del administrador como tarea pendiente.

## Implementación

### Backend
- `POST /mantenimiento/evidencia` — guarda una foto (PNG/JPG/WEBP/PDF, máx. 10 MB) y devuelve su
  nombre para adjuntarla al reporte.
- `POST /mantenimiento` — crea la tarea con `categoria` (`unidad|zona_comun|otro`),
  `evidencias` (lista separada por comas) y `prioridad`; por defecto `estado = "pendiente"` y se
  notifica al administrador.
- `GET /mantenimiento/evidencias/{nombre}` — sirve la foto con permiso de mantenimiento.

### Frontend
- `frontend/src/pages/Dashboard/Mantenimiento.tsx`: formulario con categoría, selección múltiple de
  fotos (subida previa a `/mantenimiento/evidencia`) y columna **Categoría** con enlaces a las
  evidencias; el administrador cambia estado y prioridad desde la misma tabla.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_mantenimiento_con_categoria_y_evidencia` — subida de foto,
  creación de la tarea como pendiente, visibilidad en el panel del administrador y rechazo de formatos
  no permitidos.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
