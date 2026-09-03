#!/usr/bin/env bash
# Uso: DOCKER_USER=tu_usuario ./docker-push.sh
# o simplemente: ./docker-push.sh   (te lo pedirá por consola)

set -e

if [ -z "$DOCKER_USER" ]; then
  read -rp "Usuario de Docker Hub: " DOCKER_USER
fi

echo "Iniciando sesión en Docker Hub..."
docker login

echo "Construyendo imágenes para el usuario: $DOCKER_USER"
docker build -t "$DOCKER_USER/multiadmin-backend:latest" ./back
docker build -t "$DOCKER_USER/multiadmin-frontend:latest" ./React

echo "Subiendo imágenes..."
docker push "$DOCKER_USER/multiadmin-backend:latest"
docker push "$DOCKER_USER/multiadmin-frontend:latest"

echo "Listo. Imágenes disponibles en:"
echo "  https://hub.docker.com/r/$DOCKER_USER/multiadmin-backend"
echo "  https://hub.docker.com/r/$DOCKER_USER/multiadmin-frontend"
