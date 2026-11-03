#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Multi-Administrador · Crear/preparar la base de datos en PostgreSQL
# (equivalente a db/crear_bd.py, pero sin recordar los argumentos)
#
#   ./db/crear_bd.sh              # crea la base si no existe y aplica init.sql
#   ./db/crear_bd.sh --recrear    # BORRA la base y la vuelve a crear
#
# Lee DATABASE_URL del .env (raíz o backend) o de las variables del sistema.
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PYTHON:-python3}
command -v "$PY" >/dev/null 2>&1 || PY=python

if [ -x "backend/.venv/bin/python" ]; then
  PY="backend/.venv/bin/python"
fi

echo "==> Python: $($PY --version 2>&1)"
"$PY" db/crear_bd.py "$@"
