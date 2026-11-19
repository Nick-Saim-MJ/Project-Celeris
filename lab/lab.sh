#!/usr/bin/env bash
# Levanta y destruye el laboratorio emulado (Modo L, Parte F4). Necesita Linux con Docker y containerlab (en Windows: WSL2).
#   lab/lab.sh up      genera la topología, construye las imágenes que falten, crea los puentes y despliega
#   lab/lab.sh down    destruye los contenedores y los puentes
#   lab/lab.sh estado  lista los nodos y si terminaron su arranque
# Si el anfitrión no tiene Docker o containerlab, se detiene: no simula nada.
set -euo pipefail
cd "$(dirname "$0")/.."
. lab/docker-env.sh
TOPO=lab/celeris.clab.yml
PREFIJO=clab-celeris

falta() { echo "ERROR: falta $1. Ejecute lab/entorno.sh para ver el estado del entorno." >&2; exit 2; }
requisitos() {
  command -v docker >/dev/null || falta docker
  docker info >/dev/null 2>&1 || falta "el demonio de Docker"
  command -v containerlab >/dev/null || falta containerlab
  command -v python3 >/dev/null || falta python3
}
nodos() { grep -E '^    [a-z0-9-]+:$' "$TOPO" | tr -d ' :' | grep -vE '^br-'; }

construir() {
  docker image inspect celeris-lab/base:dev >/dev/null 2>&1 || docker build -q -f lab/images/base/Dockerfile -t celeris-lab/base:dev lab/images/base
  docker image inspect celeris-node:dev >/dev/null 2>&1 || make image
  docker image inspect celeris-lab/node:dev >/dev/null 2>&1 || docker build -q -f lab/images/node/Dockerfile -t celeris-lab/node:dev lab/images/node
}

# Configuración del manager de Wazuh (siem01): se parte de la del propio imagen fijada por digest y se le agrega el syslog TCP de bucle local
# que usa el receptor TLS de siem01 (F14, 6514). Queda en lab/.run/ (fuera de git) y se rehace si falta.
wazuh_config() {
  local destino=lab/.run/wazuh/ossec.conf imagen
  mkdir -p lab/.run/wazuh lab/.run/cowrie-log
  chmod 777 lab/.run/cowrie-log
  touch lab/.run/cowrie-log/cowrie.json; chmod 666 lab/.run/cowrie-log/cowrie.json   # el agente de hny01 lo lee desde el arranque
  [ -s "$destino" ] && return 0
  imagen=$(grep -oE 'wazuh/wazuh-manager@sha256:[0-9a-f]{64}' "$TOPO" | head -1)
  [ -n "$imagen" ] || { echo "ERROR: la topología no trae la imagen del manager de Wazuh" >&2; return 1; }
  docker run --rm --entrypoint cat "$imagen" /var/ossec/data_tmp/permanent/var/ossec/etc/ossec.conf > "$destino"
  cat >> "$destino" <<'XML'

<ossec_config>
  <!-- Laboratorio (F14): syslog solo por TCP y solo desde el receptor TLS de siem01, que escucha en 6514; sin UDP 514 -->
  <remote>
    <connection>syslog</connection>
    <port>514</port>
    <protocol>tcp</protocol>
    <allowed-ips>127.0.0.1</allowed-ips>
    <local_ip>127.0.0.1</local_ip>
  </remote>
</ossec_config>
XML
}

# El manager tarda en arrancar (varios servicios): hasta que acepta altas de agentes (1515) no se da el laboratorio por listo.
esperar_manager() {
  for _ in $(seq 1 240); do
    docker exec "$PREFIJO-siem01" nc -z 127.0.0.1 1515 2>/dev/null && { echo "manager de Wazuh listo"; return 0; }
    sleep 1
  done
  echo "ERROR: el manager de Wazuh no aceptó altas en 240 s (docker logs $PREFIJO-siem01-wazuh)" >&2
  return 1
}

# Los agentes se enrolan al arrancar y reintentan con espera: se da el laboratorio por listo cuando todos están activos en el manager.
esperar_agentes() {
  local esperados activos
  esperados=$(ls lab/generated/*/agente.sh 2>/dev/null | wc -l)
  for _ in $(seq 1 180); do
    activos=$(docker exec "$PREFIJO-siem01-wazuh" /var/ossec/bin/agent_control -l 2>/dev/null | grep -c "Active$")
    [ "$activos" -ge $((esperados + 1)) ] && { echo "agentes de Wazuh activos: $esperados"; return 0; }
    sleep 2
  done
  echo "aviso: solo $((activos - 1)) de $esperados agentes de Wazuh están activos" >&2
  return 0
}

esperar() {
  local pendientes n
  for _ in $(seq 1 90); do
    pendientes=""
    for n in $(nodos); do
      [ "$n" = hny01-cowrie ] && continue
      [ "$n" = siem01-wazuh ] && continue
      docker exec "$PREFIJO-$n" test -f /run/lab-listo 2>/dev/null || pendientes="$pendientes $n"
    done
    [ -z "$pendientes" ] && { esperar_manager && esperar_agentes && echo "laboratorio listo"; return $?; }
    sleep 1
  done
  echo "ERROR: nodos que no terminaron su arranque:$pendientes (revise docker exec $PREFIJO-<nodo> cat /var/log/arranque.log)" >&2
  return 1
}

case "${1:-}" in
  up)
    requisitos
    python3 infra/genera.py lab >/dev/null
    construir
    wazuh_config
    sh lab/generated/puentes.sh up
    containerlab deploy -t "$TOPO" --reconfigure
    sh lab/generated/espejo.sh || echo "aviso: el espejo hacia ids01 no se pudo configurar" >&2
    esperar
    ;;
  down)
    command -v containerlab >/dev/null || falta containerlab
    containerlab destroy -t "$TOPO" --cleanup || true
    [ -f lab/generated/puentes.sh ] && sh lab/generated/puentes.sh down
    ;;
  estado)
    requisitos
    for n in $(nodos); do
      printf '%-14s ' "$n"
      docker inspect -f '{{.State.Status}}' "$PREFIJO-$n" 2>/dev/null | tr '\n' ' '
      docker exec "$PREFIJO-$n" test -f /run/lab-listo 2>/dev/null && echo listo || echo "-"
    done
    ;;
  *) echo "uso: $0 up|down|estado" >&2; exit 2 ;;
esac
