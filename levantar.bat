@echo off
chcp 65001 >nul
REM Multi-Administrador - arranque con Docker Compose (Windows)
setlocal
cd /d "%~dp0"

echo ==^> Comprobando Docker...
docker info >nul 2>&1
if errorlevel 1 (
  echo ERROR: el daemon de Docker no responde. Abre Docker Desktop y espera a que este listo.
  exit /b 1
)
docker compose version >nul 2>&1
if errorlevel 1 (
  echo ERROR: falta "docker compose" ^(Compose v2^). Actualiza Docker Desktop.
  exit /b 1
)

if not exist ".env" (
  echo ==^> Creando .env desde .env.example
  copy /y ".env.example" ".env" >nul
)

echo ==^> Validando docker-compose.yml
docker compose config >nul
if errorlevel 1 (
  echo ERROR: docker-compose.yml no es valido.
  exit /b 1
)

echo ==^> Construyendo y levantando ^(la primera vez puede tardar unos minutos^)
docker compose up --build -d
if errorlevel 1 (
  echo ERROR: fallo el arranque. Revisa los mensajes anteriores o ejecuta: docker compose logs -f
  exit /b 1
)
docker compose ps

echo ==^> Esperando a que la API este sana...
for /L %%i in (1,1,40) do (
  docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" >nul 2>&1
  if not errorlevel 1 (
    echo OK: backend respondiendo.
    goto :listo
  )
  ping -n 4 127.0.0.1 >nul
)
echo AVISO: el backend aun no responde. Revisa: docker compose logs -f backend

:listo
echo.
echo Frontend : http://localhost:3000
echo API      : http://localhost:3000/api/health   ^(o http://localhost:8000/docs^)
echo Usuario  : admin@multiadmin.com  /  Admin2026!
echo Logs     : docker compose logs -f
echo Parar    : docker compose down         ^(con -v borra tambien la BD^)
endlocal
