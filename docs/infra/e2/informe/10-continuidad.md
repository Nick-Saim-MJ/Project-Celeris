# 10. Consideraciones de disponibilidad y continuidad en el diseño

El diseño contempla la disponibilidad a nivel de diseño, sin implementarla. Los RTO y RPO son objetivos preliminares que se validan en el entregable de implementación de S2; la consola se valida con el simulacro T59. La criticidad de cada servicio es la del componente más crítico que lo presta, y ningún servicio de la clase Alta supera el RTO de 4 h ni el RPO de 24 h, el mayor de la tabla (SIEM).

{{tabla:continuidad}}

**Redundancia.** El almacenamiento de las VM está en RAID 1 por hardware; los nodos de caché tienen un datastore cada uno y no se protegen porque se reconstruyen. La navegación de los laboratorios no depende de un equipo: EDGE01, EDGE02 y la salida `DIRECT` del PAC dan un RTO de ≈ 0 (la prueba T09 midió 8,7 s en el Modo L, que es emulado). La red tiene un solo switch y un solo host; son los puntos únicos de falla que se declaran más abajo.

**Estrategia de respaldo y regla 3-2-1-1-0.** La consola y su base se respaldan con pgBackRest y restic: una copia local en DS-VM y una copia en S3. El respaldo corre dentro de cada VM porque ESXi gratuito no ofrece VADP. La regla se cumple así:

{{tabla:regla_respaldo}}

- **3 copias:** el original, la copia local y la de S3.
- **2 medios:** el datastore RAID (SSD) y el almacenamiento de objetos de S3.
- **1 fuera del sitio:** S3, a donde el respaldo llega cifrado en origen (F18).
- **1 inmutable:** Object Lock de 30 días en modo compliance; nadie del campus, ni un administrador comprometido, puede borrarla.
- **0 errores:** una restauración mensual cronometrada sin errores, y el simulacro T59 que mide el RTO real de la consola.

La copia local comparte datastore con el original: protege contra el borrado o la corrupción dentro de la VM, no contra la pérdida del host. Para eso está la copia de S3.

**Punto único de falla: el host ESX01 (escenario «cae ESX01», CT-09).** Un solo host por presupuesto significa que si cae, caen todas las VM, incluido FW01. El diseño responde así: los laboratorios pasan a `DIRECT` por el PAC, es decir, navegación sin caché, y la consola y la caché se recuperan al reponer el host, restaurando desde S3 (T59): la consola con los 2 h de RTO y los 15 min de RPO de CT-03 contados desde que el host nuevo está disponible, y los nodos de caché desde la imagen OCI, con la caché llenándose sola. El plazo de reposición del servidor es el supuesto S-34, por confirmar con la DTI; hasta entonces no se compromete un RTO del host. Condición: `DIRECT` solo mantiene la navegación si la salida de los laboratorios hacia el FortiGate sigue existiendo, y hoy depende de FW01, que es una VM de ESX01 y la puerta de enlace de la VLAN 30 (AM-12); esa dependencia se registra como CI-88 (abierto). Se mitiga en capas antes de llegar a ese escenario: la UPS01 con apagado ordenado por NUT evita corromper los datastores en un corte; el RAID 1 tolera la falla de un SSD; las VM son reconstruibles desde plantillas e IaC; BRK01 e IPMI01 permiten recuperar FW01 sin ruteo y sin ESXi. La alta disponibilidad entre hosts con CARP queda como hoja de ruta (H3).

**Qué se valida en S2.** T59 (restaurar la consola desde S3 en una EC2 temporal y medir el RTO de restauración), T09 (el cambio a `DIRECT`), T25 (break-glass con FW01 apagado) y la restauración mensual cronometrada; con la DTI, el plazo de reposición del servidor (S-34) y la salida de los laboratorios sin FW01 (CI-88).
