@echo off
chcp 65001 >nul
REM ============================================================================
REM  MULTI-ADMINISTRADOR - INIT.BAT (Windows)
REM  Configura PostgreSQL: crea el rol de aplicación, la base de datos,
REM  aplica el esquema db/init.sql (que incluye roles + permisos RBAC)
REM  y otorga los privilegios correspondientes a cada rol.
REM
REM  Requisitos: PostgreSQL instalado y su carpeta \bin en el PATH
REM             (o ejecuta este script desde C:\Program Files\PostgreSQL\...\bin)
REM ============================================================================

REM ------------- Variables (edita si difieren en tu entorno) ----------------
set "PGHOST=localhost"
set "PGPORT=5432"          REM En Docker usa 5432; en el sandbox local puede ser 5433
set "PG_SUPERUSER=postgres"
set "PG_SUPERPASS=postgres"
set "DB_NAME=multiadmin_db"
set "DB_USER=multiadmin"
set "DB_PASS=multiadmin"
set "SQL_FILE=db\init.sql"
REM --------------------------------------------------------------------------

title Multi-Administrador - Inicializacion de base de datos

echo ============================================================
echo   MULTI-ADMINISTRADOR - Inicializacion de base de datos
echo ============================================================

REM ------------ 1) Verificar que psql esté disponible -------------
where psql >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encontro "psql".
    echo         Instala PostgreSQL y agrega su carpeta \bin al PATH,
    echo         o ejecuta este script desde esa carpeta.
    pause
    exit /b 1
)
echo [OK] psql encontrado.

REM ------------ 2) Credenciales del superusuario -------------------
if "%PG_SUPERPASS%"=="postgres" (
    set /p PG_SUPERPASS=Password del superusuario "%PG_SUPERUSER%": 
)
set "PGPASSWORD=%PG_SUPERPASS%"

REM ------------ 3) Crear el rol de aplicación si no existe --------
echo.
echo [*] Verificando/creando rol "%DB_USER%"...
psql -h %PGHOST% -p %PGPORT% -U %PG_SUPERUSER% -d postgres -v ON_ERROR_STOP=1 ^
    -c "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='%DB_USER%') THEN CREATE ROLE %DB_USER% LOGIN PASSWORD '%DB_PASS%' CREATEDB; END IF; END $$;"
if errorlevel 1 ( echo [ERROR] No se pudo crear el rol. & pause & exit /b 1 )
echo [OK] Rol "%DB_USER%" listo.

REM ------------ 4) Crear la base de datos si no existe -------------
echo.
echo [*] Verificando/creando base de datos "%DB_NAME%"...
for /f "delims=" %%i in ('psql -h %PGHOST% -p %PGPORT% -U %PG_SUPERUSER% -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='%DB_NAME%'"') do set "EXISTS=%%i"
if "%EXISTS%"=="1" (
    echo [OK] La base de datos "%DB_NAME%" ya existe.
) else (
    psql -h %PGHOST% -p %PGPORT% -U %PG_SUPERUSER% -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE %DB_NAME% OWNER %DB_USER%;"
    if errorlevel 1 ( echo [ERROR] No se pudo crear la base de datos. & pause & exit /b 1 )
    echo [OK] Base de datos "%DB_NAME%" creada.
)

REM ------------ 5) Aplicar el esquema (roles + permisos RBAC) ------
echo.
echo [*] Aplicando esquema y permisos desde "%SQL_FILE%"...
if not exist "%SQL_FILE%" (
    echo [ERROR] No se encontro "%SQL_FILE%". Ejecuta el script desde la raiz del proyecto.
    pause
    exit /b 1
)
psql -h %PGHOST% -p %PGPORT% -U %PG_SUPERUSER% -d %DB_NAME% -v ON_ERROR_STOP=1 -f "%SQL_FILE%"
if errorlevel 1 ( echo [ERROR] Error al aplicar el esquema. & pause & exit /b 1 )
echo [OK] Esquema y permisos aplicados.

REM ------------ 6) Otorgar privilegios al rol de aplicación -------
echo.
echo [*] Otorgando privilegios a "%DB_USER%"...
psql -h %PGHOST% -p %PGPORT% -U %PG_SUPERUSER% -d %DB_NAME% -v ON_ERROR_STOP=1 ^
    -c "GRANT ALL PRIVILEGES ON DATABASE %DB_NAME% TO %DB_USER%;" ^
    -c "GRANT ALL ON SCHEMA public TO %DB_USER%;" ^
    -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO %DB_USER%;" ^
    -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO %DB_USER%;" ^
    -c "GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO %DB_USER%;" ^
    -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO %DB_USER%;" ^
    -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO %DB_USER%;"
if errorlevel 1 ( echo [AVISO] Algunos grants fallaron (puede ser solo por permisos ya otorgados). )
echo [OK] Privilegios otorgados.

REM ------------ 7) Verificación final ------------------------------
echo.
echo [*] Verificando conexion como "%DB_USER%"...
set "PGPASSWORD=%DB_PASS%"
psql -h %PGHOST% -p %PGPORT% -U %DB_USER% -d %DB_NAME% -tAc "SELECT 'CONEXION_OK';"
if errorlevel 1 ( echo [ERROR] El rol "%DB_USER%" no puede conectarse. Revisa pg_hba.conf. & pause & exit /b 1 )
echo [OK] Conexion verificada con el rol de aplicacion.

echo.
echo ============================================================
echo   Listo. Datos de conexion:
echo     Host      : %PGHOST%
echo     Puerto    : %PGPORT%
echo     Base      : %DB_NAME%
echo     Usuario   : %DB_USER%
echo     Password  : %DB_PASS%
echo   (Ambos roles y permisos quedaron configurados.)
echo ============================================================
pause
