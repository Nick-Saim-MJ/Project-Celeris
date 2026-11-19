# syntax=docker/dockerfile:1
# Imagen OCI de celeris-node (Parte F6, REQ-NF-15): multi-etapa, binario con LTO, imagen final mínima y sin root.
# Contexto de construcción: la raíz del repositorio.
#   docker build -f deploy/image/Dockerfile --build-arg GIT_COMMIT=$(git rev-parse HEAD) -t celeris-node:dev .
#
# Las dos imágenes base van fijadas por digest (índice multi-arquitectura: amd64 y arm64). Para actualizarlas:
#   docker pull rust:1-bookworm && docker inspect --format '{{index .RepoDigests 0}}' rust:1-bookworm
ARG RUST_IMAGE=rust:1-bookworm@sha256:ade39a710ef85f3506cffcfec3e8a24ba090badef1dff2fb798f71d878833fea
ARG RUNTIME_IMAGE=gcr.io/distroless/cc-debian12:nonroot@sha256:9dac0a79194e45a7da0158a9c6da57b217585af0786db3845d1f0ec1a0dd182f

# ---------- Etapa 1: compilación ----------
FROM ${RUST_IMAGE} AS build
# aws-lc-rs (rustls) compila aws-lc con el compilador de C del sistema: cmake y clang evitan las rutas de respaldo
# del script de construcción. tini hace de PID 1 en la imagen final.
RUN apt-get update \
 && apt-get install -y --no-install-recommends cmake clang tini \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /src

# Las dependencias se compilan primero con un main vacío: mientras Cargo.toml y Cargo.lock no cambien, esta capa se reutiliza.
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo 'fn main() {}' > src/main.rs \
 && cargo build --release --locked \
 && rm -rf src target/release/celeris-cache target/release/deps/celeris_cache* target/release/.fingerprint/celeris-cache*

COPY src ./src
# COPY conserva las fechas del contexto, anteriores a las del main vacío: sin `touch`, cargo daría por compilado el binario vacío.
RUN find src -type f -exec touch {} + \
 && cargo build --release --locked \
 && test "$(stat -c %s target/release/celeris-cache)" -gt 1000000 \
 && strip target/release/celeris-cache \
 && install -d -o 65532 -g 65532 /rootfs/data

# ---------- Etapa 2: imagen final ----------
FROM ${RUNTIME_IMAGE}
ARG GIT_COMMIT=desconocido
ARG VERSION=0.1.0
ARG CREATED=
LABEL org.opencontainers.image.title="celeris-node" \
      org.opencontainers.image.description="Nodo de caché HTTP/HTTPS de Celeris Edge (Modo L, A y H del laboratorio de CE0311)" \
      org.opencontainers.image.source="https://github.com/Nick-Saim-MJ/Project-Celeris" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.created="${CREATED}"

COPY --from=build /src/target/release/celeris-cache /usr/local/bin/celeris-cache
COPY --from=build /usr/bin/tini-static /usr/local/bin/tini
# /data guarda los objetos, los registros y la CA; /config recibe config.toml (montado, solo lectura).
COPY --from=build --chown=65532:65532 /rootfs/data /data

USER 65532:65532
WORKDIR /data
VOLUME ["/data"]
# 3128: proxy explícito (F1). 9128: administración y métricas (F12), desactivada por defecto en config.toml.
EXPOSE 3128 9128
# El nodo termina con gracia solo con SIGINT (tokio::signal::ctrl_c); `docker stop` usa esta señal.
STOPSIGNAL SIGINT
ENTRYPOINT ["/usr/local/bin/tini", "-g", "--", "/usr/local/bin/celeris-cache"]
CMD ["/config/config.toml"]
