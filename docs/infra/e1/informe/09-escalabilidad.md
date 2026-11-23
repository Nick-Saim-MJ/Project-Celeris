# 9. Consideraciones de escalabilidad y disponibilidad

### Crecimiento sin perder la segmentación

**Laboratorios.** La VLAN 30 (10.20.32.0/22) admite 16 rangos /26. Hoy se usan 10, y 10.20.34.128/25 queda reservado para los laboratorios 11 y 12. El bloque contiguo 10.20.36.0/22 está reservado para ampliar LAB a /21 sin renumerar. Cada laboratorio nuevo es un rango /26 más en `allowed_clients` y en el DHCP: no exige reglas nuevas en FW01.

**Zonas y sedes.** Cada VLAN de servicios es un /24 con menos de diez direcciones en uso: hay espacio para más servidores sin cambiar el plan. Las sedes futuras tienen bloques reservados (10.21.0.0/16 Lima y 10.22.0.0/16 Tarapoto), y el resumen 10.20.0.0/14 permite anunciarlas por la misma VPN. En AWS, 10.30.128.0/17 queda reservado para crecimiento.

**Nodos de caché.** Se agregan como EDGE03 en adelante, en la misma VLAN 60. El PAC los incorpora como un destino más, sin cambiar la configuración de las PCs.

**Opciones registradas para más adelante.** VLAN por laboratorio, 802.1X y QoS (fq_codel, con una clase baja para las precargas). Un segundo FW01 en CARP y un segundo ISP con *gateway group*. Si crecen las VPC o el ancho de banda, pasar del VGW a un Transit Gateway. Ninguna de estas opciones cambia el modelo de zonas: se agregan dentro de él.

### Disponibilidad: qué pasa si falla una pieza

{{tabla:continuidad}}

**Si cae FW01.** Se pierden el ruteo entre VLAN, la salida a Internet de las zonas del proyecto, la VPN, el DNS y el NTP (AM-12). Mientras FW01 está caído, las PCs de los laboratorios no alcanzan los nodos ni Internet, porque tanto F1 como F6 cruzan FW01: el PAC no reemplaza al ruteo, y la única recuperación es restaurar FW01. Para eso existe el puerto de emergencia BRK01: un puerto de SW-CORE01 en la VLAN 10, rotulado y deshabilitado por defecto, desde el que una laptop (10.20.10.250) alcanza ESXi, IPMI y la consola DCUI para restaurar FW01 desde el XML versionado en Git. RTO de 1 h (T25). La redundancia real (CARP) queda como opción futura.

**Si cae EDGE01.** El PAC envía las peticiones a EDGE02 y, si ambos caen, a `DIRECT`, solo durante el piloto (F6). En el laboratorio emulado el cambio a EDGE02 tardó {{dato:t09}} (T09). El contenido de la caché no se respalda: se vuelve a llenar.

**Si cae la VPN.** Solo se pierde el panel remoto: el encargado sigue trabajando desde ENC01 dentro del campus (F28) y las descargas no dependen de AWS. Si cae un solo túnel, el tráfico pasa al otro con la convergencia medida en T05.

**Si cae CTRL01.** El nodo sigue con la última configuración válida y no se pueden hacer cambios. La consola se restaura desde la copia local o desde S3, incluso en una EC2 temporal en app-a, con RTO de 2 h y RPO de 15 min (T59).
