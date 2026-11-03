@echo off
REM ---------------------------------------------------------------------------
REM  Multi-Administrador - Crear/preparar la base de datos en PostgreSQL
REM
REM    db\crear_bd.bat              -> crea la base y aplica db\init.sql
REM    db\crear_bd.bat --recrear    -> BORRA la base y la vuelve a crear
REM
REM  Requiere Python instalado. Lee DATABASE_URL del .env si existe.
REM ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0.."

if exist "backend\.venv\Scripts\python.exe" (
    set "PY=backend\.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo ==^> Usando %PY%
%PY% db\crear_bd.py %*
if errorlevel 1 (
    echo.
    echo ERROR: no se pudo preparar la base de datos.
    pause
    exit /b 1
)
echo.
pause
