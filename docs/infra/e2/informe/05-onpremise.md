# 5. Arquitectura on-premise — diseño (VMware ESXi)

## 5.1 Topología física propuesta

El centro de datos del campus es un rack de 12U con cuatro grupos de equipos: la distribución (patch panel, organizador y SW-CORE01), el servidor ESX01, el respaldo eléctrico (UPS01 con su PDU) y los enlaces hacia el FortiGate y la capa de acceso. La tabla siguiente es la disposición de D2.4; la Figura 5.1 la dibuja.

{{tabla:rack}}

**ESX01.** Un servidor 2U con 12 núcleos y 96 GB de RAM [S-08]. El almacenamiento tiene dos medios con propósitos distintos: dos SSD de 1,92 TB en RAID 1 por hardware para las VM y la copia local de respaldo, y dos NVMe de 1 TB sin RAID, uno por nodo de caché. La caché se reconstruye sola desde Internet, por eso no se protege con RAID ni con copia; los discos de las VM sí, porque contienen la base de la consola y la configuración del firewall.

{{tabla:host}}

**Red física.** Las cuatro NIC se reparten por función. Dos de 10 GbE (vmnic0 y vmnic1) forman el trunk 802.1Q hacia SW-CORE01: un laboratorio de 40 PCs que descarga a la vez necesita ≈ 1 Gbps desde la caché y los HIT atraviesan FW01 (D-17), de modo que el trunk debe tener holgura. Una de 1 GbE (vmnic2) va dedicada al FortiGate y lleva solo la red de tránsito 10.20.0.0/29, separada del trunk de las zonas; así un error de VLAN no puede mezclar el tráfico externo con el interno. La cuarta (vmnic3) queda libre, sin enlace, para crecer sin rediseñar. SW-CORE01 es el único switch del diseño: si cae, ESX01 pierde la capa de acceso; se mitiga con su configuración en Git y es parte del riesgo de la sección 10. El enlace de SW-CORE01 hacia la capa de acceso existente (SW-ACC) es un trunk de 1 GbE [S-14] (CI-80): limita a ≈ 1 Gbps lo que llega a los laboratorios, justo lo que pide un laboratorio a la vez y sin holgura para varios; es el cuello de botella del diseño y se registra como CI-87.

{{tabla:nic}}

**Gestión fuera de banda y emergencia.** IPMI01 (iDRAC/iLO, 10.20.10.11) permite encender, apagar y ver la consola del servidor aunque ESXi o FW01 no respondan. BRK01 es un puerto de SW-CORE01 en la VLAN 10, apagado por defecto y rotulado: si FW01 cae y no hay ruteo entre VLAN, una laptop (10.20.10.250) en ese puerto alcanza ESXi (10.20.10.10) e IPMI01 para restaurar FW01 desde su XML en Git, con RTO de 1 h.

**Energía.** UPS01 es una UPS online de 1,5 kVA con tarjeta de red (10.20.10.40). El consumo de ESX01 es de ≈ {{dato:consumo_w}} W (D2.4 decía ≈ 400 W; manda el inventario, CI-77) y la autonomía de {{dato:autonomia}} min está por confirmar con el fabricante. No está pensada para operar durante un corte largo sino para un apagado ordenado: JMP01 es el servidor NUT, lee UPS01 y apaga por SSH las VM y luego ESXi. El orden de arranque es FW01, CTRL01, EDGE01 y EDGE02, SIEM01 y el resto: primero el firewall, porque sin él no hay ruteo; luego la consola, que el nodo necesita para su configuración.

**Rack.** ESX01 es un equipo de 2U y ocupa U6–U7 (CI-79). Quedan libres U8–U9, entre el organizador y el servidor, y U4–U5, entre el servidor y la UPS; D2.4 no les asigna uso. La figura rotula las U reales, pero dibuja más alta la fila del servidor para mostrar sus NIC y datastores.

{{figura:DC-1|Qué observar: el rack de 12U con la U12 arriba; ESX01 con sus cuatro NIC, sus tres datastores, IPMI01 y JMP01 (servidor NUT) dentro; los cables 10 GbE de vmnic0 y vmnic1 a SW-CORE01, el de 1 GbE de vmnic2 al FortiGate, el puerto break-glass BRK01 y la alimentación UPS01 → PDU → ESX01.}}

## 5.2 Diseño del hipervisor

**Por qué ESXi gratuito.** El host es uno solo, no hay presupuesto de licencias y el proyecto no necesita vMotion, DRS ni HA entre hosts. Proxmox VE es la alternativa si se necesitara API para IaC o un clúster (D4). El costo es aceptar tres límites que condicionan el diseño [8]:

{{tabla:limites_esxi}}

**vSwitch y port groups.** vSwitch0 tiene dos uplinks con teaming por puerto virtual de origen (activo/activo): reparte las VM entre los enlaces y, si uno cae, sus VM pasan al otro. Un vSwitch estándar no soporta LACP [2], que exigiría un vDS y vCenter. Cada VLAN del proyecto tiene su port group; PG-FW-TRUNK (VLAN 4095) entrega a FW01 todas las VLAN etiquetadas, y FW01 enruta entre ellas con una subinterfaz por VLAN. vSwitch1 usa solo vmnic2 y tiene un único port group, PG-TRANSITO, al que solo se conecta FW01: la red de tránsito 10.20.0.0/29 hacia el FortiGate no comparte vSwitch con ninguna otra VM. En todos los port groups, el modo promiscuo, los cambios de MAC y las transmisiones falsificadas están en **rechazar**; en la v0.4 no hay port groups de captura (no hay IDS01) ni vSwitch de almacenamiento (no hay NAS01), de modo que no existe ninguna excepción.

{{tabla:vswitch}}

**Máquinas virtuales.** Son las 11 del inventario (V-91 comprueba que son las mismas, con los mismos recursos). La fase F1 son las 10 primeras; EDGE02 llega en F2. El disco de EDGE01 y EDGE02 incluye 500 GB de caché, que va en su NVMe y no en DS-VM. Ninguna VM supera 8 vCPU.

{{tabla:vms}}

ENC01 es una PC física del laboratorio y no una VM; la validación del cliente se hace además en 2 o 3 PCs reales.

{{figura:DC-2|Qué observar: cada port group lleva su VLAN y el color de su zona; cada VM cuelga del port group de su zona con sus vCPU y su RAM; FW01 tiene dos vNIC (PG-FW-TRUNK y PG-TRANSITO); los nodos de caché usan sus propios NVMe y las demás VM usan DS-VM.}}
