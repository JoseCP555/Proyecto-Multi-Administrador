#!/usr/bin/env bash
# Sube el proyecto completo a https://github.com/sayethbermudez/Multi.Admin (Linux / macOS / Git Bash)
set -e
cd "$(dirname "$0")"
[ -d .git ] || git init
git branch -M main
git config user.name  >/dev/null || git config user.name  "sayethbermudez"
git config user.email >/dev/null || git config user.email "sayethbermudez@users.noreply.github.com"
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/sayethbermudez/Multi.Admin.git
echo "[1/3] Agregando archivos (.env excluidos por .gitignore)..."
git add -A
git commit -m "Multi.Admin: RBAC, rediseño UI, eventos futuros, verificación de correo y recuperación con código de 6 dígitos" || echo "   (sin cambios nuevos)"
echo "[2/3] Subiendo a GitHub..."
git push -u origin main --force
echo "[3/3] Listo: https://github.com/sayethbermudez/Multi.Admin"
