#!/bin/sh
# GENERADO por infra/gen desde infra/inventory.yaml — no editar a mano. EMULADO (Modo L, Parte F4.2): no es el producto real.
set -eu
ip link add vti1 type xfrm dev lo if_id 1
ip addr add 169.254.10.1/30 dev vti1
ip link set vti1 mtu 1400 up
ip link add vti2 type xfrm dev lo if_id 2
ip addr add 169.254.11.1/30 dev vti2
ip link set vti2 mtu 1400 up
