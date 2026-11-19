# syntax=docker/dockerfile:1
# Imagen base del laboratorio emulado (Modo L, Parte F4). Una sola imagen con las herramientas de todos los nodos que no son
# celeris-node ni cowrie; cada nodo ejecuta su rol con la configuración que genera infra/gen/lab.py. NO es un producto real:
# fw01-sim y vgw-sim emulan a OPNsense y al VGW de AWS (F4.2).
#   docker build -f lab/images/base/Dockerfile -t celeris-lab/base:dev lab/images/base
FROM debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc
ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'wireshark-common wireshark-common/install-setuid boolean false' | debconf-set-selections \
 && echo 'deb http://deb.debian.org/debian bookworm-backports main' > /etc/apt/sources.list.d/backports.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      iproute2 iputils-ping iptables nftables tcpdump tshark nmap hydra netcat-openbsd socat curl ca-certificates openssl \
      knot-dnsutils unbound chrony nginx libnginx-mod-http-modsecurity modsecurity-crs \
      strongswan-charon strongswan-swanctl libcharon-extra-plugins libstrongswan-extra-plugins libstrongswan-standard-plugins frr \
      openssh-client python3 jq procps psmisc less \
 && apt-get install -y --no-install-recommends -t bookworm-backports suricata \
 && rm -rf /var/lib/apt/lists/*
# Sin demonios al instalar: cada nodo arranca solo lo suyo desde su script de rol.
RUN rm -f /etc/nginx/sites-enabled/default
COPY rol.sh /usr/local/bin/rol
RUN chmod +x /usr/local/bin/rol
ENTRYPOINT ["/usr/local/bin/rol"]
