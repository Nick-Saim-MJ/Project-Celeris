# Control de versiones

{{tabla:control_versiones}}

Este informe se genera con `make informe-dc` desde la fuente única del repositorio: `infra/centro_datos.yaml` (centro de datos, transcrito de CE03 D2.3–D2.9) e `infra/inventory.yaml` (IP, VLAN, zonas, componentes y reglas, compartido con el Entregable 1). Las tablas de VM, vSwitch, rack, rutas, Security Groups, dimensionamiento, costo, RTO/RPO y la matriz de componentes no se escriben a mano: si un dato cambia, el informe, los diagramas y la matriz XLSX cambian juntos. La huella indicada arriba identifica la versión exacta de esos datos.

Las contradicciones y vacíos hallados en los documentos base se registran como CI-77 a CI-88 en `docs/infra/e1/CAMBIOS-INVENTARIO.md`; la sección 11 y el anexo A dicen cuáles siguen abiertos y qué efecto tienen sobre el diseño.

# Glosario

| Término | Significado en este informe |
| --- | --- |
| Hipervisor (ESXi) | Programa que reparte los núcleos, la RAM y el disco de un servidor físico entre varias máquinas virtuales (VM). Aquí, VMware ESXi 8.0U3e en su edición gratuita. |
| vSwitch y port group | El vSwitch es un switch virtual dentro de ESXi; cada port group es un segmento suyo con su VLAN, y cada VM se conecta a uno. |
| NIC teaming | Dos o más tarjetas de red físicas en un mismo vSwitch para tolerar la caída de una. Aquí, por puerto virtual de origen (sin LACP). |
| Datastore | Almacenamiento donde ESXi guarda los discos de las VM. |
| Sobreasignación (2:1, 4:1) | Asignar más vCPU que núcleos físicos. Es aceptable cuando la carga real es baja: 2:1 son dos vCPU por núcleo. |
| VPC, subred, NACL, Security Group | Red virtual de AWS, sus segmentos, el filtro sin estado de cada subred y el firewall con estado de cada instancia. |
| IGW, VGW, NAT | Puerta de la VPC a Internet, extremo AWS de la VPN y traductor de direcciones para salir desde una subred privada. |
| Gateway Endpoint de S3 | Ruta privada desde la VPC a S3 sin pasar por Internet ni por NAT, sin costo por hora. |
| RTO y RPO | Tiempo máximo para recuperar un servicio y cantidad máxima de datos que se pueden perder. |
| 3-2-1-1-0 | Tres copias, en dos medios, una fuera del sitio, una inmutable y cero errores al verificar la restauración. |
| Object Lock | Bloqueo de S3 que impide borrar o modificar un objeto durante un plazo; en modo compliance ni el administrador de la cuenta puede saltarlo. |
| VADP | API de respaldo de VMware que usan los programas de copia de VM; la edición gratuita de ESXi no la ofrece. |
| NUT | Servicio que lee el estado de la UPS y ordena el apagado de los equipos. Aquí corre en JMP01. |
| Break-glass | Acceso de emergencia que funciona aunque caiga el firewall (BRK01). |
