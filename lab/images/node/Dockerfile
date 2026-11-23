# syntax=docker/dockerfile:1
# celeris-node para el laboratorio: la imagen base de herramientas + el MISMO binario de la imagen OCI de producción
# (deploy/image/Dockerfile). La imagen OCI no trae shell ni `ip`, y containerlab necesita configurar las interfaces del nodo.
#   docker build -f lab/images/node/Dockerfile -t celeris-lab/node:dev lab/images/node   (necesita celeris-node:dev y celeris-lab/base:dev)
FROM celeris-node:dev AS binario
FROM celeris-lab/base:dev
COPY --from=binario /usr/local/bin/celeris-cache /usr/local/bin/celeris-cache
