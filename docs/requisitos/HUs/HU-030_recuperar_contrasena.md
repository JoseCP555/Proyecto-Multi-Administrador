# HU-030 — Recuperación de contraseña

| Campo | Valor |
|---|---|
| **ID** | HU-030 |
| **Rol** | Residente |
| **Módulo** | Autenticación |
| **Permisos** | — |
| **Estado** | ✅ Implementada |

## Historia

> **Como** residente, **quiero** quiero recuperar mi contraseña desde la pantalla de inicio de sesión,
> **para** para poder acceder a la plataforma si olvido mis credenciales sin depender del administrador.

## Criterio de aceptación

> El sistema envía un enlace de recuperación al correo registrado del residente. El enlace expira en 30 minutos y al usarlo permite establecer una nueva contraseña.

## Implementación

### Backend
- `POST /recuperar-password` — genera `token_recuperacion` y `expira_token = ahora + 30 min`, y
  envía el enlace por SMTP (respuesta neutra para evitar enumeración de correos).
- `GET /validar-token-recuperacion/{token}`, `POST /validar-codigo-recuperacion` (código de 6
  dígitos) y `POST /restablecer-password` — validan vigencia y guardan la nueva contraseña.

### Frontend
- `frontend/src/pages/Recuperar.tsx` y `Restablecer.tsx`: solicitud por correo, ingreso del código o
  enlace y formulario de nueva contraseña con los requisitos de seguridad.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_recuperacion_expira_en_30_minutos` — el token generado
  caduca en 30 minutos (±1 min).

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
