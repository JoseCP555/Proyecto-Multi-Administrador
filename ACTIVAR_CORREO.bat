@echo off
setlocal
cd /d "%~dp0"
echo Abre Docker Desktop antes de continuar. No se borraran tus datos.
docker compose run --build --rm --no-deps -v "%CD%:/workspace" backend python /workspace/configurar_gmail.py
if errorlevel 1 goto fallo
docker compose up -d --build backend frontend
if errorlevel 1 goto fallo
docker compose exec backend python probar_correo.py --interactivo
if errorlevel 1 goto fallo
echo Ahora solicita Reenviar codigo en la aplicacion.
pause
exit /b 0
:fallo
echo No se completo la activacion. Revisa el mensaje anterior.
pause
exit /b 1
