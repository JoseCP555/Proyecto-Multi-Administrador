# HU-028 — Plataforma responsiva (móvil, tableta y computador)

| Campo | Valor |
|---|---|
| **ID** | HU-028 |
| **Rol** | Administrador (todos los usuarios) |
| **Módulo** | Interfaz |
| **Permisos** | — |
| **Estado** | ✅ Implementada |

## Historia

> **Como** administrador (todos los usuarios), **quiero** quiero que la plataforma esté disponible desde cualquier dispositivo con navegador web,
> **para** para poder administrar el conjunto desde el celular, tableta o computador en cualquier lugar.

## Criterio de aceptación

> La plataforma es responsiva y se adapta a pantallas de distintos tamaños. Las funciones principales están disponibles en móvil sin pérdida de funcionalidad.

## Implementación

### Backend
- API REST sin suposiciones de escritorio: todas las operaciones usadas en escritorio están
  disponibles para el cliente móvil.

### Frontend
- Tailwind CSS con enfoque *mobile first*: barra lateral colapsable con menú móvil
  (`components/layout/Sidebar.tsx`), rejillas `sm/lg` en todos los módulos nuevos, tablas con
  desplazamiento horizontal y modales a pantalla completa en pantallas pequeñas.

### Pruebas
- Verificación visual con Playwright en 1440×950 y en anchos móviles (390×844) sobre los módulos
  `pqrs`, `reservas`, `pagos`, `comunicados`, `visitantes`, `votaciones`, `aprobaciones`, `auditoria`,
  `consejo` y `perfil`, sin errores de consola.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
