#!/bin/bash
# AWS EMULADO: PLANO DE CONTROL, SIN TRÁFICO. Todo contra el AWS Emulator local con credenciales ficticias; nada contra una cuenta real.
#   demo.sh levantar     construye la imagen (si falta) y arranca el emulador limpio en 127.0.0.1:9297
#   demo.sh aplicar      tofu init + apply del entorno demo contra el emulador
#   demo.sh evidencias   describe-* → evidencias/<fecha>-E/ (sin secretos) y comparación con el inventario
#   demo.sh destruir     tofu destroy contra el emulador
#   demo.sh bajar        detiene el emulador (su estado vive solo en memoria)
#   demo.sh todo         levantar + aplicar + evidencias
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$AQUI/../../.." && pwd)"
PUERTO="${EMULADOR_PUERTO:-9297}"
ESTADO="${EMULADOR_ESTADO:-$HOME/.aws-emulator-lab}"        # fuera del repo: ahí deja el emulador su ca.pem
NOMBRE=celeris-aws-emulator
CA="$ESTADO/$PUERTO/ca.pem"

entorno_aws() {
  export AWS_ENDPOINT_URL="https://127.0.0.1:$PUERTO" AWS_CA_BUNDLE="$CA" AWS_ACCESS_KEY_ID=ficticia AWS_SECRET_ACCESS_KEY=ficticia
  export AWS_DEFAULT_REGION=us-east-1 AWS_REGION=us-east-1 AWS_EC2_METADATA_DISABLED=true AWS_DISABLE_HOST_PREFIX_INJECTION=true AWS_PAGER=
  unset AWS_PROFILE AWS_SESSION_TOKEN
}

levantar() {
  command -v docker >/dev/null || { echo "falta docker" >&2; exit 1; }
  if ! docker image inspect aws-emulator >/dev/null 2>&1; then
    echo "Construyendo la imagen aws-emulator (el Dockerfile baja el RPM oficial de downloads.aws.com)…"
    docker build -q -t aws-emulator "$AQUI"
  fi
  mkdir -p "$ESTADO" && chmod 777 "$ESTADO"
  docker rm -f "$NOMBRE" >/dev/null 2>&1 || true
  docker run -d --name "$NOMBRE" --memory=2g --memory-swap=2g -p "127.0.0.1:$PUERTO:$PUERTO" -v "$ESTADO:/home/emulator/.aws/emulator" \
    aws-emulator -p "$PUERTO" -a off >/dev/null
  for _ in $(seq 1 30); do
    curl -fs --cacert "$CA" "https://127.0.0.1:$PUERTO/__admin/health" >/dev/null 2>&1 && { echo "AWS Emulator listo en https://127.0.0.1:$PUERTO (estado vacío)"; return; }
    sleep 1
  done
  echo "el emulador no respondió" >&2; exit 1
}

# El estado queda FUERA del repositorio: contiene las llaves precompartidas de la VPN.
tofu_demo() { (cd "$RAIZ/deploy/opentofu/envs/demo" && tofu "$@" -state="$ESTADO/demo.tfstate" -var "ca_emulador=$CA" -var "endpoint_emulador=https://127.0.0.1:$PUERTO"); }

case "${1:-}" in
  levantar) levantar ;;
  aplicar)
    (cd "$RAIZ/deploy/opentofu/envs/demo" && tofu init -input=false >/dev/null)
    tofu_demo apply -input=false -auto-approve ;;
  evidencias) entorno_aws; python3 "$AQUI/evidencias.py" "${@:2}" ;;
  destruir) tofu_demo destroy -input=false -auto-approve ;;
  bajar) docker rm -f "$NOMBRE" >/dev/null 2>&1 || true; echo "emulador detenido" ;;
  todo) levantar; "$0" aplicar; "$0" evidencias ;;
  *) sed -n '2,10p' "$0"; exit 2 ;;
esac
