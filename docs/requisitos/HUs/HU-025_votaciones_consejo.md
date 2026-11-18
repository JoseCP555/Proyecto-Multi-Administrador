# HU-025 — Votaciones del consejo

| Campo | Valor |
|---|---|
| **ID** | HU-025 |
| **Rol** | Consejo del conjunto |
| **Módulo** | Votaciones |
| **Permisos** | `votaciones.ver`, `votaciones.crear`, `votaciones.votar`, `votaciones.cerrar` |
| **Estado** | ✅ Implementada |

## Historia

> **Como** consejo del conjunto, **quiero** quiero participar en votaciones sobre decisiones del conjunto desde la plataforma,
> **para** para tomar decisiones colectivas de forma ágil sin necesidad de reuniones presenciales.

## Criterio de aceptación

> El administrador crea la votación con opciones y plazo. Cada miembro del consejo vota una sola vez y el sistema muestra los resultados al cierre de la votación.

## Implementación

### Backend
- `POST /votaciones` — crea la votación con pregunta, opciones (`opciones: [{texto}]`) y fecha de
  cierre; notifica al consejo.
- `POST /votaciones/{id}/voto` — registra el voto del usuario autenticado; un segundo intento
  devuelve `409` («Ya registraste tu voto en esta votación»).
- `PUT /votaciones/{id}/cerrar` — cierra la votación; a partir de ahí `GET /votaciones` devuelve los
  porcentajes por opción. `GET /votaciones/{id}` entrega el detalle con resultados.

### Frontend
- `frontend/src/pages/Dashboard/Votaciones.tsx`: creación con opciones dinámicas, botón **Votar**
  por opción, estado (`abierta`/`cerrada`), fecha límite, número de votos y barras de resultados tras
  el cierre.

### Pruebas
- `backend/tests/test_hus_nuevas.py::test_votacion_un_solo_voto` — un voto por usuario (`409` en el
  segundo intento) y resultados porcentuales tras cerrar.

---

Ver también: [`docs/IMPLEMENTACION_HUs.md`](../../IMPLEMENTACION_HUs.md) (tabla completa de las 32 historias) y [`REPORTE_TESTING.md`](../../../REPORTE_TESTING.md).
