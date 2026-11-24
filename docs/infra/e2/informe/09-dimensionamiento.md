# 9. Dimensionamiento y capacidad

El dimensionamiento compara lo que piden las {{dato:n_vm}} VM de la fase F2 (la más exigente) con lo que tiene ESX01, y el t3.micro de EC2-GW con su carga. Cada cálculo está como fórmula visible en la hoja «Dimensionamiento» de la matriz XLSX, y V-92 y V-107 comprueban que Excel y el código dan el mismo resultado. La holgura se define como la fracción de la capacidad que queda libre; la meta de D2.3 es ≥ 15 %.

{{tabla:dim}}

**CPU.** Las VM suman {{dato:vcpu_f2}} vCPU. FW01, EDGE01 y EDGE02 ({{dato:vcpu_sens}} vCPU) están en la ruta crítica de los datos y se dimensionan a 2:1, que son {{dato:nuc_sens}} núcleos. Las demás ({{dato:vcpu_resto}} vCPU) tienen poca ocupación de CPU y se dimensionan a 4:1, que son {{dato:nuc_resto}} núcleos. El total, {{dato:nucleos_nec}} núcleos, cabe en los {{dato:nucleos_host}} del host con una holgura de {{dato:h_cpu}}. La relación global es de {{dato:rel_cpu}} vCPU por núcleo físico.

**RAM.** {{dato:ram_f2}} GB asignados × 1,1 de sobrecarga de ESXi = {{dato:ram_esxi}} GB; × 1,2 de crecimiento = {{dato:ram_crec}} GB, sobre {{dato:ram_host}} GB del host. La holgura después de la sobrecarga de ESXi es {{dato:h_ram}}; si además se reserva todo el crecimiento del 20 %, quedan {{dato:ram_libre}} GB libres, es decir {{dato:m_ram}}, sobre el 15 % de D2.3. Con SIEM01 en 16 GB el margen era 12,0 % y no cumplía; el equipo lo bajó a 12 GB (CI-78, resuelto) porque Wazuh todo en uno admite hasta 25 agentes con 8 GiB y el diseño tiene ≈ 8.

**Disco.** Las VM sin caché suman {{dato:disco_sin_cache_f2}} GB; con el factor de 1,3 (instantáneas y crecimiento) son {{dato:disco_req}} GB, más ≈ 200 GB de copia local de restic: {{dato:disco_tot}} GB sobre los {{dato:disco_cap}} GB del RAID 1, un uso de {{dato:uso_disco}} y una holgura de {{dato:h_disco}}. Los 500 GB de caché de cada nodo van en su NVMe de 1 TB (holgura de 50 %); el valor es un punto de partida [S-04] que se ajusta con la curva de fallos medida en el piloto. Un ciclo de 3 GB por PC con contenido común ocupa 3 GB, no 120 GB.

**Red.** Un laboratorio de 40 PCs que descarga a la vez necesita ≈ 1 Gbps desde la caché (REQ-NF-02 pide ≥ 900 Mbps agregados con 4 vCPU y 8 GB por nodo, que es lo que tiene cada EDGE). Los dos enlaces de 10 GbE del host lo cubren con holgura, pero el trunk de SW-CORE01 hacia SW-ACC es de 1 GbE [S-14]: iguala el objetivo de un laboratorio y no deja holgura; con varios laboratorios descargando a la vez comparten 1 Gbps (CI-87, abierto). Como los HIT atraviesan FW01 (D-17), en S2 se mide con iperf3 el rendimiento de LAB hacia EDGE con y sin IPS; si FW01 o el enlace de acceso lo limitan, se revisa D-17 o se pide a la DTI un enlace de mayor velocidad.

**SIEM.** SIEM01 recibe ≈ 8 agentes, Suricata, el WAF y el firewall: 12 GB de RAM y 300 GB de disco para ≈ 90 días de eventos. Wazuh todo en uno admite hasta 25 agentes con 8 GiB, así que 12 GB dan holgura para el pico de eventos y para crecer hasta ese límite sin tocar la VM.

**Margen de crecimiento.** El crecimiento previsto es EDGE02 (ya incluido en F2) y hasta 16 laboratorios en el mismo /22. Con la RAM y el disco actuales caben unos {{dato:ram_libre}} GB de RAM y unos {{dato:disco_libre}} GB de disco más antes de agotar el host; el cuello de botella sería la RAM.

**EC2-GW frente a su carga.** La instancia se dimensiona frente a la carga esperada del supuesto S-33 (derivada de S-26: una sesión por laboratorio), que se mide en S2:

{{tabla:gw}}
