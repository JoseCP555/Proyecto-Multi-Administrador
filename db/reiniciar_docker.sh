#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Multi-Administrador · Reiniciar la base de datos en Docker DESDE CERO
#
# Útil cuando el volumen de PostgreSQL ya existía y por eso `db/init.sql`
# nunca se volvió a ejecutar (Docker solo lo corre con el volumen VACÍO).
#
#   ⚠  BORRA TODOS LOS DATOS de la base (y de Redis).
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

echo "⚠  Esto ELIMINA la base de datos actual (volumen db_data) y la recrea."
read -r -p "   ¿Continuar? [s/N] " respuesta
case "$respuesta" in
  s|S|si|SI|y|Y) ;;
  *) echo "Cancelado."; exit 0 ;;
esac

echo "==> Bajando contenedores y borrando volúmenes..."
docker compose down -v

echo "==> Levantando de nuevo (aplica db/init.sql en un volumen limpio)..."
docker compose up -d --build

echo "==> Esperando a la API..."
for i in $(seq 1 60); do
  if docker compose exec -T backend python -c \
      'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)' \
      >/dev/null 2>&1; then
    echo "OK: backend respondiendo."
    break
  fi
  [ "$i" -eq 60 ] && echo "AVISO: revisa 'docker compose logs -f backend'"
  sleep 3
done

echo
echo "Usuario: admin@multiadmin.com  /  Admin2026!"
echo "Frontend: http://localhost:3000"
