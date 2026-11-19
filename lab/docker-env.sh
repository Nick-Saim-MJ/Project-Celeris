#!/bin/sh
# Se carga con `. lab/docker-env.sh`. Si el docker por defecto es el de Docker Desktop (integración con WSL) y existe el socket del dockerd
# nativo (lab/docker-nativo.sh), usa ese: containerlab y los contenedores del laboratorio deben vivir en esta distribución.
if [ -z "${DOCKER_HOST:-}" ] && [ -S /run/docker-nativo.sock ] \
   && [ "$(docker info --format '{{.Name}}' 2>/dev/null)" = "docker-desktop" ]; then
  export DOCKER_HOST=unix:///run/docker-nativo.sock
fi
