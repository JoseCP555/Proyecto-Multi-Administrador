@echo off
chcp 65001 >nul
REM ============================================================
REM  Sube el proyecto completo a https://github.com/sayethbermudez/Multi.Admin
REM  Ejecutar desde la carpeta raíz del proyecto (donde está este archivo).
REM  Requiere Git instalado. La primera vez pedirá iniciar sesión en GitHub.
REM ============================================================
cd /d "%~dp0"

git --version >nul 2>&1 || (echo [ERROR] Git no está instalado: https://git-scm.com/download/win & pause & exit /b 1)

if not exist ".git" git init
git branch -M main

git config user.name  >nul || git config user.name  "sayethbermudez"
git config user.email >nul || git config user.email "sayethbermudez@users.noreply.github.com"

git remote remove origin >nul 2>&1
git remote add origin https://github.com/sayethbermudez/Multi.Admin.git

echo.
echo [1/3] Agregando archivos (los .env con contraseñas quedan fuera por .gitignore)...
git add -A
git commit -m "Multi.Admin: RBAC, rediseño UI, eventos futuros, verificación de correo y recuperación con código de 6 dígitos" >nul 2>&1 || echo      (sin cambios nuevos que confirmar)

echo [2/3] Subiendo a GitHub (rama main)...
git push -u origin main --force
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo subir. Verifica tu sesión de GitHub o usa un token:
    echo         https://github.com/settings/tokens  (permiso "repo")
    pause & exit /b 1
)

echo [3/3] Listo: https://github.com/sayethbermudez/Multi.Admin
pause
