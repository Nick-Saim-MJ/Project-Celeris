#!/bin/sh
# Prepara un socket propio para el dockerd nativo de WSL cuando Docker Desktop tiene activada la integración con la distribución.
#
# Con esa integración, Docker Desktop reemplaza /var/run/docker.sock por su proxy: los contenedores corren en OTRA distribución y containerlab no
# encuentra sus espacios de red ni los puentes (error «Failed to lookup link br-…»). El laboratorio necesita el dockerd de esta distribución.
# Este script (como root, una sola vez por equipo) agrega un socket /run/docker-nativo.sock al servicio docker; lab/docker-env.sh lo usa solo
# cuando detecta Docker Desktop, y no se toca nada de Docker Desktop ni de sus contenedores. Alternativa: desactivar la integración de WSL
# de esa distribución en Docker Desktop (Settings → Resources → WSL integration).
set -eu
[ "$(id -u)" = 0 ] || { echo "ejecute como root (sudo sh lab/docker-nativo.sh)" >&2; exit 2; }
command -v systemctl >/dev/null || { echo "falta systemd en esta distribución (WSL: [boot] systemd=true en /etc/wsl.conf)" >&2; exit 2; }
if [ -S /run/docker-nativo.sock ]; then echo "ya existe /run/docker-nativo.sock"; exit 0; fi
destino=/etc/systemd/system/docker.service.d
mkdir -p "$destino"
# Se parte del ExecStart que ya trae el paquete (rutas y opciones de containerd) y se le agrega el socket.
base=$(systemctl cat docker.service | sed -n 's/^ExecStart=\(\/usr\/bin\/dockerd .*\)$/\1/p' | head -1)
[ -n "$base" ] || { echo "no se encontró el ExecStart de docker.service" >&2; exit 2; }
printf '[Service]\nExecStart=\nExecStart=%s -H unix:///run/docker-nativo.sock\n' "$base" > "$destino/celeris-socket-nativo.conf"
systemctl daemon-reload
systemctl restart docker
for _ in $(seq 1 30); do [ -S /run/docker-nativo.sock ] && break; sleep 1; done
[ -S /run/docker-nativo.sock ] && echo "listo: /run/docker-nativo.sock" || { echo "el socket no apareció" >&2; exit 1; }
