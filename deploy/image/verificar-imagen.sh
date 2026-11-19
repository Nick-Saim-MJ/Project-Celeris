#!/usr/bin/env bash
# Propiedades que la imagen debe cumplir (Parte F6, REQ-NF-15): usuario no root, sin shell, binario real y etiquetas OCI.
set -uo pipefail
IMAGE=${IMAGE:-celeris-node:dev}
FALLAS=0
ok() { echo "  ok    $1"; }
mal() { echo "  FALLA $1"; FALLAS=$((FALLAS + 1)); }

user=$(docker inspect --format '{{.Config.User}}' "$IMAGE")
case "$user" in ""|0|root|0:*|root:*) mal "la imagen corre como root ($user)";; *) ok "usuario no root ($user)";; esac

rev=$(docker inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$IMAGE")
case "$rev" in ""|desconocido) mal "sin etiqueta org.opencontainers.image.revision";; *) ok "etiqueta de commit: $rev";; esac

for l in title source licenses version; do
  v=$(docker inspect --format "{{index .Config.Labels \"org.opencontainers.image.$l\"}}" "$IMAGE")
  [ -n "$v" ] && ok "etiqueta $l = $v" || mal "falta la etiqueta org.opencontainers.image.$l"
done

if docker run --rm --entrypoint /bin/sh "$IMAGE" -c true >/dev/null 2>&1; then mal "la imagen trae un shell"; else ok "sin shell en la imagen final"; fi

# El binario real pesa varios MB; uno de unos 300 kB es el main vacío del truco de caché del Dockerfile.
bytes=$(docker run --rm --entrypoint /usr/local/bin/tini "$IMAGE" -h >/dev/null 2>&1; docker create -q "$IMAGE" | { read -r id; docker cp "$id":/usr/local/bin/celeris-cache - 2>/dev/null | wc -c; docker rm -f "$id" >/dev/null; })
[ "${bytes:-0}" -gt 5000000 ] && ok "binario celeris-cache de $((bytes / 1048576)) MiB" || mal "el binario mide ${bytes:-0} bytes: parece el main vacío"

# Se niega a arrancar abierto a la red sin clientes permitidos (comportamiento existente que la imagen no debe cambiar).
cfg=$(mktemp); printf 'listen = "0.0.0.0:3128"
allowed_clients = []
' > "$cfg"; chmod 644 "$cfg"
code=$(timeout 30 docker run --rm -v "$cfg":/config/config.toml:ro "$IMAGE" >/dev/null 2>&1; echo $?)
rm -f "$cfg"
[ "$code" = "1" ] && ok "sin clientes permitidos no arranca (salida $code)" || mal "esperaba salida 1 sin allowed_clients, obtuve $code"

[ "$FALLAS" -eq 0 ] && echo "imagen OK" || { echo "$FALLAS verificación(es) fallaron"; exit 1; }
