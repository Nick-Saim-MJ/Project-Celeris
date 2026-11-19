#!/bin/sh
# GENERADO por infra/gen desde infra/inventory.yaml — no editar a mano. EMULADO (Modo L, Parte F4.2): no es el producto real.
set -eu
ip tunnel add vti1 mode vti local 203.0.113.10 remote 198.51.100.21 key 1
ip addr add 169.254.10.2/30 dev vti1
ip link set vti1 mtu 1400 up
sysctl -qw net.ipv4.conf.vti1.disable_policy=1 net.ipv4.conf.vti1.rp_filter=0
ip tunnel add vti2 mode vti local 203.0.113.10 remote 198.51.100.22 key 2
ip addr add 169.254.11.2/30 dev vti2
ip link set vti2 mtu 1400 up
sysctl -qw net.ipv4.conf.vti2.disable_policy=1 net.ipv4.conf.vti2.rp_filter=0
