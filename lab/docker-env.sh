#!/bin/sh
# Se carga con `. lab/docker-env.sh`. Si el docker por defecto es el de Docker Desktop (integración con WSL), o no responde en 5 s, y existe el
# socket del dockerd nativo (lab/docker-nativo.sh), usa ese: containerlab y los contenedores del laboratorio deben vivir en esta distribución.
if [ -z "${DOCKER_HOST:-}" ] && [ -S /run/docker-nativo.sock ]; then
  nombre=$(timeout 5 docker info --format '{{.Name}}' 2>/dev/null || echo sin-respuesta)
  if [ "$nombre" = "docker-desktop" ] || [ "$nombre" = "sin-respuesta" ]; then
    export DOCKER_HOST=unix:///run/docker-nativo.sock
  fi
fi
