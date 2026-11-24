# 6. Diseño de conectividad híbrida

**Tecnología y extremos.** El extremo del campus es FW01 (OPNsense con strongSwan, IPsec con IKEv2 [16] basado en rutas sobre VTI1 y VTI2), detrás del FortiGate, que hace NAT 1:1 de 203.0.113.10 hacia 10.20.0.2 para UDP 500 y 4500 [S-15, S-29]. El extremo de AWS es un Virtual Private Gateway adjunto a la VPC, con dos IP públicas que asigna AWS, una por túnel. Los parámetros completos están en la tabla de la sección 5.4.

**Redes y rutas.** El campus anuncia 10.20.0.0/16 (ASN 65020) y AWS anuncia 10.30.0.0/16 (ASN 64512). El VGW propaga 10.20.0.0/16 a las tablas rt-public y rt-private, de modo que no hay rutas estáticas que mantener. Cuando lleguen las sedes reservadas, el campus podrá anunciar el resumen 10.20.0.0/14 sin cambiar la VPC.

**Redundancia.** Los dos túneles trabajan en activo/pasivo: el VGW usa uno a la vez (sin ECMP) y el túnel 2 se anuncia con *AS-path prepending* para que quede como respaldo. Los temporizadores de BGP (keepalive 10 s, hold 30 s) y DPD (10 s, *restart*) acotan la detección de la falla. La meta de OD-05 es una convergencia **medida** de ≤ 60 s (T05). En el laboratorio emulado se midieron {{dato:t05}}; ese valor se repetirá con el VGW real.

**Tamaño de paquete.** La MTU de las VTI es 1400 y el MSS se ajusta a 1360: el encapsulado IPsec más los 8 bytes del NAT-T cabe en el margen, y se evita la fragmentación que rompería descargas largas por el túnel (T21).

**Controles previstos.**
- En AWS, el Security Group sg-gw solo admite TCP 443 hacia EC2-GW (F29) y solo le permite salir a CTRL01:443 (F30), a SIEM01:1514/1515 (F13) y a TCP 443 de Internet para ACME y actualizaciones. La NACL pública deniega 22 y 3389 desde Internet; EC2-GW se administra por SSM Session Manager o EC2 Instance Connect, sin puerto 22 público.
- En FW01, las reglas de la VTI repiten esa restricción. Si EC2-GW fuera comprometido, no serviría para pivotar hacia el campus (AM-18, T58).
- Las zonas DMZ-SVC y DMZ-HONEY no tienen ruta hacia AWS (T03), y la subred privada app-a no es alcanzable desde Internet (T04).
- CTRL01 solo acepta F30 con el certificado de cliente de EC2-GW: la VPN no es la única barrera.

**Costo.** La operación 24×7 en AWS se estima en ≈ US$ 70 al mes con precios de lista [S-12]: la VPN es la mitad del costo, y el resto son EC2-GW t3.micro, tres IPv4 públicas y unos 300 GB en S3. El detalle corresponde al entregable de centro de datos.

**Matriz de pruebas de conectividad planeadas.** La tabla resume las pruebas que validan la conectividad híbrida y su segmentación. La matriz completa ({{dato:n_pruebas}} pruebas, con comando, precondición, criterio de aprobación y evidencia a capturar) está en `{{dato:matriz_pruebas_xlsx}}`; la sección 7.3 resume las de segmentación del campus. La columna «Modo L» es el resultado de la **emulación** local. Las pruebas que dependen de AWS real o del hardware del campus se ejecutan en los Modos A y H, y por eso figuran como NO_APLICA en L.

{{tabla:pruebas_vpn}}
