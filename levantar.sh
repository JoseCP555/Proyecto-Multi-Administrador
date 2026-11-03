#!/usr/bin/env bash
# Multi-Administrador - arranque con Docker Compose (Linux / macOS / Git Bash)
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Comprobando Docker..."
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: el daemon de Docker no responde. Abre Docker Desktop o inicia el servicio."
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: falta 'docker compose' (Compose v2). Actualiza Docker."
  exit 1
fi

if [ ! -f .env ]; then
  echo "==> Creando .env desde .env.example"
  cp .env.example .env
fi

echo "==> Validando docker-compose.yml"
docker compose config >/dev/null

echo "==> Construyendo y levantando (la primera vez puede tardar unos minutos)"
docker compose up --build -d
docker compose ps

echo "==> Esperando a que la API este sana..."
for i in $(seq 1 60); do
  if docker compose exec -T backend python -c \
      'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)' \
      >/dev/null 2>&1; then
    echo "OK: backend respondiendo."
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "AVISO: el backend aun no responde. Revisa: docker compose logs -f backend"
  fi
  sleep 3
done

echo
echo "Frontend : http://localhost:3000"
echo "API      : http://localhost:3000/api/health  (o http://localhost:8000/docs)"
echo "Usuario  : admin@multiadmin.com  /  Admin2026!"
echo "Logs     : docker compose logs -f"
echo "Parar    : docker compose down        (con -v borra tambien la BD)"
