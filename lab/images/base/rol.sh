#!/bin/sh
# Punto de entrada de los nodos del laboratorio: espera a que containerlab conecte las interfaces (ESPERA_IFACES), ejecuta el
# arranque del nodo (/lab/arranque.sh, generado desde el inventario por infra/gen/lab.py) y deja el contenedor vivo.
for _ in $(seq 1 240); do
  listo=1
  for n in ${ESPERA_IFACES:-}; do ip link show "$n" >/dev/null 2>&1 || listo=0; done
  [ "$listo" = 1 ] && break
  sleep 0.5
done
if [ -f /lab/arranque.sh ]; then sh /lab/arranque.sh > /var/log/arranque.log 2>&1 || echo "arranque terminó con error $?" >> /var/log/arranque.log; fi
[ -e /run/lab-listo ] || touch /run/lab-listo
exec sleep infinity
