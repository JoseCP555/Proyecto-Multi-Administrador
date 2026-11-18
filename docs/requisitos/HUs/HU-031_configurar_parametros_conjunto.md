# HU-031 — Configuración de los parámetros del conjunto

| Campo | Valor |
|---|---|
| **ID** | HU-031 |
| **Rol** | Administrador |
| **Módulo** | Conjuntos / Configuración |
| **Permisos** | `conjuntos.editar` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** administrador, **quiero** quiero configurar los parámetros del conjunto como nombre, logo y datos de contacto,
> **para** para personalizar la plataforma con la identidad de cada copropiedad que administro.

## Criterio de aceptación

> El administrador puede editar el nombre, logo (imagen JPG/PNG hasta 2 MB), dirección y teléfono del conjunto. Los cambios se reflejan en la plataforma inmediatamente.

## Implementación

### Backend
- `PUT /conjuntos/{id}` — nombre, dirección, teléfono, correo, cuota, día de cobro, reglas,
  horario de silencio, color y `umbral_gasto`.
- `POST /conjuntos/{id}/logo` (y `POST /logos`) — acepta JPG/PNG hasta 2 MB, valida el tipo real
  del archivo y devuelve la URL pública; `DELETE` para quitarlo.

### Frontend
- `frontend/src/pages/Dashboard/Conjuntos.tsx`: formulario completo, subida de logo con vista previa,
  selector de color y umbral de gastos; el nombre, logo y color se refrescan en la barra superior, las
  tarjetas y el tema del conjunto sin recargar la sesión.

### Pruebas
- Verificado por API (`PUT /conjuntos/{id}` con `umbral_gasto` y logo) y en la interfaz: el logo y el
  nombre actualizados aparecen en el selector **Cambiar conjunto** tras guardar.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
