#!/usr/bin/env bash
# Ejecuta e2e/run.sh con el binario DENTRO de la imagen celeris-node (no con target/release).
# Cada proxy de la prueba se lanza como `docker run` en la red del anfitrión; los archivos de la prueba (CA, datos, registros)
# quedan en una copia temporal de e2e/ dentro del sistema de archivos de Linux, porque las rutas montadas de Windows (/mnt/*)
# no conservan los permisos de las llaves.
#   IMAGE=celeris-node:dev deploy/image/e2e-en-contenedor.sh
set -euo pipefail
IMAGE=${IMAGE:-celeris-node:dev}
RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d /tmp/celeris-e2e.XXXXXX)
trap 'rm -rf "$TMP"' EXIT
cp -r "$RAIZ/e2e" "$TMP/e2e"
cat > "$TMP/celeris-en-contenedor" <<WRAP
#!/usr/bin/env bash
exec docker run --rm --network host -e RUST_LOG --user $(id -u):$(id -g) -v "\$PWD":/work -w /work $IMAGE "\$@"
WRAP
chmod +x "$TMP/celeris-en-contenedor"
echo "imagen: $IMAGE  ($(docker image inspect --format '{{.Id}}' "$IMAGE" | cut -c1-19))"
cd "$TMP/e2e"
CELERIS_BIN="$TMP/celeris-en-contenedor" bash ./run.sh
