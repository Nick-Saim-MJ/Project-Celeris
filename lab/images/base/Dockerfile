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
      openssh-client openssh-server restic chromium gnupg python3 jq procps psmisc less \
 && apt-get install -y --no-install-recommends -t bookworm-backports suricata \
 && rm -rf /var/lib/apt/lists/*
# Agente de Wazuh (F13): misma versión que el manager del laboratorio (siem01). Se instala sin arrancar y sin manager fijo: cada nodo se enrola
# al arrancar (lab/generated/<nodo>/arranque.sh). El repositorio es el oficial de Wazuh; la llave se importa al construir la imagen.
ARG WAZUH_VERSION=4.9.2-1
RUN curl -fsSL https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import \
 && chmod 644 /usr/share/keyrings/wazuh.gpg \
 && echo 'deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main' > /etc/apt/sources.list.d/wazuh.list \
 && apt-get update && WAZUH_MANAGER=127.0.0.1 apt-get install -y --no-install-recommends wazuh-agent=${WAZUH_VERSION} \
 && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd
# CrowdSec (DET-08) con su bouncer de nftables, del repositorio oficial del fabricante (llave importada al construir, sin ejecutar scripts remotos).
# Solo fw01-sim los arranca. No se fija la versión: se registra la que quede instalada en el ensayo.
# Los scripts de instalación de estos paquetes exigen systemd, que un contenedor no tiene: se descargan y se extraen sin ejecutarlos. fw01-sim solo usa
# la API local de CrowdSec (`crowdsec -no-cs`), `cscli` y el bouncer; la configuración la completa su script de arranque.
RUN curl -fsSL https://packagecloud.io/crowdsec/crowdsec/gpgkey | gpg --dearmor -o /usr/share/keyrings/crowdsec.gpg && echo 'deb [signed-by=/usr/share/keyrings/crowdsec.gpg] https://packagecloud.io/crowdsec/crowdsec/debian/ bookworm main' > /etc/apt/sources.list.d/crowdsec.list && apt-get update && cd /tmp && apt-get download crowdsec crowdsec-firewall-bouncer-nftables && mkdir /tmp/pkg && for f in /tmp/*.deb; do dpkg-deb -x "$f" /tmp/pkg; done && cp -a /tmp/pkg/usr/. /usr/local/ && cp -a /tmp/pkg/etc/crowdsec /etc/ && rm -rf /tmp/pkg /tmp/*.deb /var/lib/apt/lists/*
# Sin demonios al instalar: cada nodo arranca solo lo suyo desde su script de rol.
RUN rm -f /etc/nginx/sites-enabled/default
COPY rol.sh /usr/local/bin/rol
RUN chmod +x /usr/local/bin/rol
ENTRYPOINT ["/usr/local/bin/rol"]
