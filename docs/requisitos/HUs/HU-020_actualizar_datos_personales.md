# HU-020 — Actualización de datos personales

| Campo | Valor |
|---|---|
| **ID** | HU-020 |
| **Rol** | Residente |
| **Módulo** | Mi perfil |
| **Permisos** | `perfil.ver`, `perfil.editar` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** residente, **quiero** quiero actualizar mis datos personales dentro de la plataforma,
> **para** para mantener mi información de contacto al día y recibir comunicaciones correctamente.

## Criterio de aceptación

> El residente puede editar su número de teléfono, correo electrónico y foto de perfil. Los cambios quedan guardados al confirmar la actualización.

## Implementación

### Backend
- `GET /perfil` — datos del usuario autenticado (incluye `telefono`, `correo`, `foto`,
  `correo_verificado`).
- `PUT /perfil` — actualiza nombre, teléfono, correo y foto (data URI JPEG/PNG hasta 2 MB); valida
  que el correo no esté en uso y marca `correo_verificado = false` si cambia.
- `PUT /perfil/password` — cambio de contraseña con verificación de la actual.
  `GET /perfil/actividad` — últimas acciones del usuario.

### Frontend
- `frontend/src/pages/Dashboard/Perfil.tsx`: formulario de datos, subida de foto con vista previa,
  cambio de contraseña y aviso de verificación de correo.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_actualizar_perfil` — actualiza teléfono y foto y comprueba
  que quedan persistidos.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
