# 7. Mecanismo de integración híbrida

El mecanismo es la VPN IPsec site-to-site del Entregable 1 [12], **sin cambios**: FW01 (detrás del FortiGate FGT-EXT, con NAT-T) se une con el VGW de la VPC en dos túneles activo/pasivo con BGP. Este informe no la rediseña: reutiliza la Figura 5.4 de CE0311 y su sección 5.4 (cifrados, DPD, MTU, convergencia y pruebas), y la tabla sale del mismo inventario.

{{tabla:vpn_dc}}

**Coherencia entre los dos entregables.** Las redes anunciadas son las mismas: el campus anuncia 10.20.0.0/16 y el VGW, 10.30.0.0/16; las dos tablas de rutas de la sección 6.2 reciben 10.20.0.0/16 del VGW, y el CIDR de la VPC es lo que el VGW anuncia al campus. Los extremos también: FW01 con la identidad IKE 203.0.113.10 (IP de documentación, RFC 5737 [13]) [S-15, S-29] y el VGW con dos IP públicas de AWS. V-94 lo comprueba.

**Qué transporta y qué no.** Por la VPN van el panel remoto (F30: EC2-GW hacia CTRL01:443, con mTLS dentro de IPsec) y los eventos de EC2-GW hacia SIEM01 (F13). No van las descargas ni los respaldos: el respaldo a S3 (F18) sale cifrado en origen por Internet. Por eso, si la VPN cae, el panel remoto deja de funcionar pero el campus, los nodos y los respaldos siguen; ENC01 es el acceso alternativo.

{{figura:FIG-5.4|Qué observar: es la figura del Entregable 1, sin modificar. FW01 detrás de FGT-EXT, los túneles VTI1 y VTI2, el VGW y EC2-GW dentro de la VPC; las redes 10.20.0.0/16 y 10.30.0.0/16 anunciadas por BGP son las mismas que las tablas de rutas de la Figura 6.1.}}
