# HU-027 — Autenticación segura: bloqueo y expiración de sesión

| Campo | Valor |
|---|---|
| **ID** | HU-027 |
| **Rol** | Administrador (todos los usuarios) |
| **Módulo** | Autenticación |
| **Permisos** | — |
| **Estado** | ✅ Implementada |

## Historia

> **Como** administrador (todos los usuarios), **quiero** quiero que el sistema autentique a todos los usuarios con correo y contraseña,
> **para** para proteger la información del conjunto y garantizar que solo usuarios autorizados accedan.

## Criterio de aceptación

> El sistema requiere correo y contraseña para iniciar sesión. Tras 5 intentos fallidos, bloquea el acceso por 10 minutos. La sesión expira tras 30 minutos de inactividad.

## Implementación

### Backend
- `POST /login` — valida credenciales, devuelve `codigo = "cuenta_bloqueada"` con los minutos
  restantes cuando el bloqueo está activo e informa los intentos restantes.
- `app/routers/auth.py`: `MAX_INTENTOS_LOGIN = 5` y `BLOQUEO_MINUTOS = 10`, contador en Redis (con
  respaldo en memoria).
- JWT con `ACCESS_TOKEN_EXPIRE_MINUTES = 30` (`exp - iat = 1800 s`) y lista negra de tokens al
  cerrar sesión (`POST /logout`).

### Frontend
- `frontend/src/context/AuthContext.tsx`: temporizador de inactividad de 30 minutos que se reinicia
  con `mousemove`, `mousedown`, `keydown`, `scroll`, `touchstart` y `click`; al expirar llama a
  `/logout`, limpia el token y redirige a `/login?sesion=expirada`. `Login.tsx` muestra el banner de
  sesión expirada y el mensaje real del backend (intentos restantes o bloqueo).

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_bloqueo_tras_cinco_intentos` (bloqueo con
  `codigo = "cuenta_bloqueada"`) y `::test_token_expira_en_30_minutos` (JWT de 30 minutos).

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
