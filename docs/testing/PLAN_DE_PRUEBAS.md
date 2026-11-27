# Plan de pruebas — Multi-Administrador

**Identificador:** PLAN-TEST-001  
**Versión:** 1.0  
**Fecha de elaboración:** 26 de noviembre de 2026  
**Línea base revisada:** rama `Main`, commit `48f3ae4`  
**Responsable de coordinación/documentación:** Jose David Caicedo  
**Ejecución:** integrantes del equipo que se registren en cada corrida.

> Este documento define qué se debe probar, en qué entorno y cómo registrar los resultados. **No es un informe de ejecución ni certifica que las pruebas hayan pasado.** Los resultados deben registrarse aparte en `REPORTE_TESTING.md`, con evidencia de cada corrida.

## 1. Objetivo

Planificar las verificaciones del backend y del frontend de Multi-Administrador para detectar errores funcionales, de integración y de permisos antes de presentar la versión. El plan separa pruebas unitarias, pruebas de API, integración y verificación manual; sus cantidades no se deben sumar ni etiquetar como pruebas unitarias sin revisar su naturaleza.

## 2. Alcance

### Incluye

- Funciones internas del backend: seguridad/contraseñas, JWT, lógica del chatbot y formato de datos.
- Flujos funcionales de historias de usuario (HU), ejecutados con `TestClient` y SQLite aislada.
- API desplegada localmente con PostgreSQL y Redis: salud, autenticación, módulos, reportes y operaciones CRUD.
- Control de acceso por rol (RBAC) y respuestas para usuarios autorizados/no autorizados.
- Mensajería, notificaciones y funciones del chatbot según las suites existentes.
- Frontend: comprobación estática de TypeScript, compilación de producción y revisión manual de rutas, formularios y permisos.
- Registro reproducible de resultados, defectos y evidencia.

### Fuera de alcance de la corrida local estándar

- Pruebas en producción o contra datos reales de residentes.
- Envío de correos a personas reales, uso de credenciales SMTP reales o envío de notificaciones externas.
- Pruebas que dependan de un modelo Ollama real, salvo que se programe y documente expresamente una corrida separada.
- Afirmar que todo requisito está cubierto solo porque existe un archivo de pruebas o porque una HU aparece en el nombre/docstring de una suite.

## 3. Base de pruebas revisada

En el commit de referencia se encuentran, entre otros, estos archivos:

| Suite/artefacto | Uso previsto según el código/documentación | Requisitos del entorno |
|---|---|---|
| `backend/tests/test_unit.py` | Funciones de seguridad, JWT, chatbot y enlaces de notificación | Python y dependencias del backend; utiliza configuración aislada para pruebas |
| `backend/tests/test_hus_nuevas.py` | Flujos de API para módulos e historias, mediante `TestClient` | Python, aplicación de pruebas y SQLite; el archivo deshabilita correo/programador |
| `backend/tests/test_api.py` | Pruebas funcionales contra la API en ejecución | API local, base de datos de prueba con datos iniciales; PostgreSQL y Redis según el código |
| `backend/tests/test_rbac.py` | Matriz de permisos y pruebas de acceso por rol | API local, PostgreSQL/Redis y usuarios de prueba; puede crear usuarios y modificar datos de prueba |
| `backend/tests/test_mensajeria.py` | Casos del módulo de mensajería | Revisar fixtures y dependencias antes de ejecutar |
| `backend/tests/test_chatbot_ollama.py` | Casos del chatbot | Revisar configuración/mocks; no asumir que usa Ollama real |
| `backend/tests/test_notificaciones_reales.py` | Notificaciones ligadas a servicios/API | Revisar dependencias y usar únicamente servicios de prueba |
| `frontend/tests_ui_rbac.py` | Comprobación de interfaz/permisos con herramientas UI | Frontend y dependencias indicadas por el proyecto |

La existencia de las suites es una referencia para diseñar la ejecución, no evidencia de una corrida actual. El reporte existente contiene resultados históricos y una ejecución reportada por Kristian el 26/11/2026; se deben conservar con su fecha y procedencia.

## 4. Tipos de prueba y escenarios

| ID | Tipo | Escenarios mínimos | Criterio esperado |
|---|---|---|---|
| P-01 | Unitaria | Hash y verificación de contraseña; token válido/inválido y expiración; detección de intenciones; formato de moneda; construcción de enlaces de notificación | Cada función devuelve el resultado esperado para entradas válidas, inválidas y límites definidos. Los defectos de tiempo/JWT deben corregirse y volver a probarse. |
| P-02 | Funcional de HU | Flujos de PQRS, reservas, comunicados, visitantes, pagos/comprobantes, votaciones/aprobaciones, auditoría, perfil, documentos y alertas contemplados en la suite de HU | Se cumplen los criterios de aceptación implementados; se verifican también rechazos, conflictos y permisos cuando corresponda. Mapear cada caso a HU y criterio, sin declarar cubiertas las 32 HUs por defecto. |
| P-03 | API/integración | `/health`, raíz, login correcto/incorrecto, registro duplicado, logout/revocación, dashboard, finanzas, listados y CRUD | Códigos HTTP, estructura de respuesta y persistencia corresponden al resultado esperado; operaciones de creación/eliminación se hacen solo con datos de prueba. |
| P-04 | RBAC | Acceso permitido y denegado para cada rol a endpoints y acciones sensibles; intentos sin token, con token inválido y rol insuficiente | Las acciones permitidas funcionan; las denegadas responden como corresponde (por ejemplo, 401/403); no hay exposición de datos de otro usuario o conjunto. |
| P-05 | Mensajería/notificaciones | Crear/consultar mensajes y notificaciones; destinatarios, enlaces y persistencia; revisar fallos de servicio | Resultado verificable en la aplicación de prueba. Sin correo externo real, comprobar el modo de prueba y no afirmar entrega SMTP. |
| P-06 | Chatbot | Saludo, saldo/gastos u otras intenciones cubiertas; historial/aislamiento por usuario y manejo de respuesta general | Respuesta no vacía y consistente con la intención; no revela información para la que el rol no tiene permiso. Registrar si se usó mock o servicio real. |
| P-07 | Frontend | TypeScript, build, login, rutas principales, formularios y visibilidad de acciones por rol; acceso denegado a vistas restringidas | Compilación sin errores y comportamiento visual/funcional conforme a permisos. Guardar captura con ruta, rol y resultado. |
| P-08 | Seguridad básica | No revelar secretos en respuestas/logs; rechazo de permisos; validar que `.env` y datos personales no se suban; revisar valores por defecto peligrosos | No se publican secretos ni datos reales. Hallazgos de configuración se registran como defectos/riesgos y no se ocultan por pasar otras pruebas. |
| P-09 | Compatibilidad/estabilidad manual | Recorrer flujos principales en navegador y verificar mensajes de error, navegación y estado después de guardar | Sin errores bloqueantes durante el recorrido; navegador, resolución, cuenta/rol y pasos deben quedar registrados. |

## 5. Preparación y seguridad del entorno

1. Confirmar rama y commit que se van a evaluar. Registrar el SHA en el resultado.
2. Usar una copia local actualizada del repositorio y las versiones de dependencias definidas por sus archivos de configuración.
3. Para pruebas aisladas, emplear SQLite/fixtures de prueba según cada suite.
4. Para `test_api.py`, `test_rbac.py` u otras suites contra servicios, levantar una instancia local de prueba con PostgreSQL/Redis y verificar que `TEST_API_URL` apunte a esa instancia; el código por defecto puede usar `http://localhost:8041`.
5. Usar solo `.env` local no versionado, credenciales de demostración/prueba y datos ficticios. No copiar contraseñas, tokens, cadenas de conexión ni correos personales al informe, capturas o Git.
6. **No ejecutar pruebas que creen, editen o eliminen datos contra producción ni contra una base con información real.** La suite RBAC puede crear usuarios y hacer cambios directos en SQL para preparar casos; debe correr únicamente contra la base desechable/de prueba.
7. Antes de usar servicios externos, identificar qué suite los requiere. Mantener SMTP deshabilitado o en entorno de captura; no enviar mensajes reales sin autorización y preparación expresa.
8. Guardar la salida íntegra de consola y las capturas pertinentes en una ubicación de evidencias sin secretos. No modificar salidas para aparentar un resultado distinto.

## 6. Orden de ejecución propuesto

Ejecutar fases separadas para aislar fallos y dependencias. Si una suite depende de servicios no disponibles, marcarla **Bloqueada/No ejecutada**, no como aprobada.

### Fase A — revisar entorno y seleccionar suites

Desde PowerShell:

```powershell
cd "C:\Users\LENOVO\Documents\Proyecto-Multi-Administrador-git\backend"
python --version
python -m pytest --version
```

Confirmar en la documentación/configuración cuáles servicios necesita cada suite y que el entorno es de pruebas.

### Fase B — pruebas aisladas

```powershell
python -m pytest tests/test_unit.py -v
python -m pytest tests/test_hus_nuevas.py -v
python -m pytest tests/test_mensajeria.py -v
python -m pytest tests/test_chatbot_ollama.py -v
```

Registrar cada comando por separado, código de salida y resumen de pytest. No sumar todos los casos como unitarios: `test_hus_nuevas.py` usa `TestClient` para flujos HTTP de la aplicación.

### Fase C — API e integración local

Con servicios de prueba y API levantados conforme a la configuración del repositorio:

```powershell
python -m pytest tests/test_api.py -v
```

### Fase D — autorización y notificaciones

Después de verificar los requisitos concretos de cada suite y la URL de la API local:

```powershell
$env:TEST_API_URL = "http://localhost:8041"
python -m pytest tests/test_rbac.py -v
python -m pytest tests/test_notificaciones_reales.py -v
Remove-Item Env:TEST_API_URL
```

Si la URL local es distinta, sustituirla por la real y documentarla. Revisar si los casos requieren servicios de correo u otros servicios antes de ejecutarlos.

### Fase E — frontend

Desde la carpeta `frontend`, usar los comandos definidos por el proyecto. El reporte existente documenta estas comprobaciones:

```powershell
npx tsc --noEmit
npm run build
```

Si existe una suite UI y están instaladas sus dependencias:

```powershell
python -m pytest tests_ui_rbac.py -v
```

Realizar además revisión manual con cuentas de prueba por rol y registrar navegador, rutas visitadas y capturas. No afirmar pruebas visuales si solo se ejecutó el build.

## 7. Criterios de entrada, salida y decisión

### Entrada

- Rama/commit identificados.
- Entorno de pruebas aislado y dependencias disponibles.
- Servicios que requiere la fase levantados y verificados.
- Datos/cuentas ficticios y evidencia sin secretos.

### Salida

- Cada caso ejecutado tiene resultado y evidencia suficiente para repetirlo.
- Todos los fallos y bloqueos están registrados con severidad, pasos, resultado esperado/obtenido y responsable asignado por el equipo.
- Las pruebas no ejecutadas se listan expresamente; no se presentan como aprobadas.
- Una corrección se considera verificada solo después de repetir el caso que falló y guardar la nueva salida.

### Regla para aprobar la entrega

La entrega de pruebas no se declara aprobada si quedan defectos bloqueantes/altos sin decisión documentada, fallos sin analizar, suites críticas no ejecutadas o requisitos de cobertura sin evidencia. Si la pauta académica exige **20 pruebas unitarias distintas**, se deben identificar y ejecutar veinte casos que realmente prueben unidades aisladas; no contar automáticamente pruebas de API, integración, UI ni el total de pytest como unitarias. El estado actual de esa exigencia debe verificarse con el docente y el equipo.

## 8. Hallazgos conocidos que deben entrar al ciclo

Según los resultados que Kristian reportó para el 26/11/2026, se ejecutaron 51 casos de varias suites: 49 pasaron y 2 fallaron. En particular, se reportaron fallos en `test_segundos_restantes` y `test_token_expira_en_30_minutos`, relacionados con expiración JWT. Ese resultado está reportado, no vuelto a ejecutar aquí. La corrección propuesta debe revisarse en el código, probarse y documentarse antes de cambiar el defecto a cerrado.

El mismo reporte indicó que quedaron pendientes suites que requieren API/servicios. Consultar `REPORTE_TESTING.md` para el detalle de esa corrida. Este plan no cambia el estado de esos casos ni reemplaza la evidencia faltante.

## 9. Formato para registrar cada corrida

Copiar esta ficha por fase o ejecución en `REPORTE_TESTING.md`:

| Campo | Registro |
|---|---|
| Fecha y hora / zona horaria |  |
| Responsable |  |
| Rama y SHA |  |
| Sistema operativo / versiones |  |
| Entorno (SQLite, PostgreSQL, Redis, mock, etc.) |  |
| Comando exacto |  |
| Suite y cantidad de casos ejecutados |  |
| Pasaron / fallaron / omitidos o bloqueados |  |
| Fallos: ID, esperado y obtenido |  |
| Evidencia (ruta de salida/captura, sin secretos) |  |
| Defectos/issues relacionados y estado |  |

## 10. Referencias del repositorio

- `backend/tests/` — suites automatizadas.
- `backend/tests/conftest.py` — configuración común de pytest y limpieza de rate-limit.
- `docs/IMPLEMENTACION_HUs.md` y `docs/requisitos/HUs/` — implementación y requisitos de historias.
- `REPORTE_TESTING.md` — resultados históricos/reportados; mantenerlo separado de este plan.
- `docker-compose.yml` y archivos `.env.example` — configuración declarada; revisar con cuidado y nunca incluir el `.env` real.
