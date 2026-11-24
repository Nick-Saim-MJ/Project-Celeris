# 5. Topologías de red (diseño)

El diseño se presenta en seis vistas, cada una con un propósito. Todas se generan desde `infra/inventory.yaml`: cada caja lleva el ID del componente y la herramienta de validación (V-50…V-56) comprueba que las IP rotuladas, la criticidad (borde de 3, 2 o 1 px con el texto ALTA, MEDIA o BAJA) y los colores de zona coincidan con el inventario. Los colores siguen una paleta apta para daltonismo y siempre van acompañados del nombre de la zona. En los diagramas de flujo, la línea continua es tráfico cifrado, la discontinua es tráfico sin cifrar con riesgo aceptado y la punteada con «✖ BLOQUEADO» es tráfico que el firewall deniega.

## 5.1 Topología general de infraestructura de red

La Figura 5.1 muestra los dos entornos completos. En el campus, Internet llega al FortiGate existente (FGT-EXT), que conserva la IP pública 203.0.113.10 (bloque de documentación [10]) [S-15] y entrega a FW01 solo lo que el proyecto necesita por la red de tránsito 10.20.0.0/29 (FortiGate 10.20.0.1, FW01 10.20.0.2). FW01 enruta las {{dato:n_vlan}} VLAN del proyecto sobre un trunk 802.1Q hacia SW-CORE01 y el host ESX01; la capa de acceso existente (SW-ACC) conecta las PCs de los diez laboratorios. El Wi-Fi de estudiantes cuelga del FortiGate y no de FW01. Dentro de esa topología, la zona MGMT (VLAN 10) agrupa la gestión de ESXi, del switch, de IPMI y de la UPS, y solo se administra desde JMP01; las zonas DMZ-SVC (VLAN 40, portal de transparencia PORTAL01, F21) y DMZ-HONEY (VLAN 41, señuelo HNY01, F24 solo en la ventana autorizada) son las que se publican a Internet, y no tienen ningún flujo hacia MGMT ni SERVERS (sección 5.3). En AWS, la VPC 10.30.0.0/16 contiene la subred pública pub-a (EC2-GW 10.30.0.10) y la privada app-a, vacía en operación normal. Los dos túneles VTI1 y VTI2 unen FW01 con el VGW.

{{figura:FIG-5.1|Qué observar: FW01 no reemplaza al FortiGate, queda detrás de él (D-26); el Wi-Fi no pasa por FW01; los túneles VTI1/VTI2 salen por el FortiGate con NAT-T; cada caja tiene su ID e IP, y el panel lateral resume qué aporta cada componente y qué pasa si falla.}}

**Por qué FW01 detrás del FortiGate y no en su lugar (D-26).** El FortiGate ya tiene la IP pública, filtra con FortiGuard para todo el campus y lo opera la DTI [11]. Reemplazarlo obligaría a rediseñar una red ajena y a duplicar un filtrado que la universidad ya paga. Colocar FW01 detrás, en una red de tránsito propia, da al proyecto un firewall que sí controla: separa sus zonas con *deny-all*, termina la VPN y ejecuta Suricata, sin tocar la política del resto del campus. El costo son tres pedidos a la DTI que se registran como supuesto [S-29]: NAT 1:1 de la IP pública hacia 10.20.0.2 solo para UDP 500/4500 y TCP 80/443, una ruta estática a 10.20.0.0/16 vía 10.20.0.2 y la exclusión de EDGE01/02 de la inspección SSL profunda. Sin esa exclusión el nodo no podría verificar el certificado real del origen (sección 5.5).

**Por qué un solo host.** Todas las VM caben en un servidor de 12 núcleos y 96 GB [S-08]: el dimensionamiento detallado corresponde al entregable de centro de datos (CE0331). Un solo host simplifica la operación, pero convierte a ESX01 y a FW01 en puntos únicos de falla; la sección 9 explica cómo se recuperan.

## 5.2 Topología lógica de red — VLAN y subredes

El plan usa la supernet 10.20.0.0/16 para el campus y 10.30.0.0/16 para AWS, ambas del espacio privado de la RFC 1918 [12], sin solapamiento con la red del Wi-Fi (valor provisional 172.16.0.0/16 [S-28]). La convención es que el número de VLAN coincide con el tercer octeto; la única excepción es LAB, que necesita un /22 para diez laboratorios y crecimiento. La puerta de enlace de cada VLAN es la interfaz .1 de FW01, que además presta DNS (Unbound con DNSSEC) y NTP en esa misma dirección (D-28).

{{tabla:vlan}}

**Rangos de laboratorio (D-23).** Dentro de la VLAN 30 cada laboratorio tiene un /26 propio. Así el encargado habilita o deshabilita un laboratorio completo desde la consola y el nodo lo aplica por rango (`allowed_clients`, REQ-F-32; T52). Una VLAN por laboratorio daría además aislamiento de capa 2 entre laboratorios, pero exigiría reconfigurar la capa de acceso, que está fuera de alcance [S-14]; queda como opción de crecimiento (sección 9).

{{tabla:rangos_lab}}

**Ruteo.** FW01 enruta entre VLAN (*router-on-a-stick*) y SW-CORE01 trabaja solo en capa 2, de modo que todo tráfico entre zonas cruza una regla registrada (D-17). La ruta por defecto de FW01 apunta a 10.20.0.1 (FortiGate); la red 10.30.0.0/16 se aprende por BGP desde AWS y 10.20.0.0/16 se anuncia hacia AWS. El FortiGate necesita una ruta estática a 10.20.0.0/16 vía 10.20.0.2 para devolver el tráfico del Wi-Fi hacia EDGE y PORTAL01 [S-29]. En AWS, las tablas de rutas son las siguientes:

{{tabla:rutas_aws}}

**Servicios de red base (D-28).** DNS, NTP y DHCP se concentran en FW01 porque una VM aparte no daba redundancia real: si FW01 cae, no hay ruteo entre zonas y un DNS en otra VLAN tampoco sería alcanzable.

{{tabla:servicios_base}}

La Figura 5.2 reúne el plan de direccionamiento, las tablas de rutas y la matriz de comunicación entre zonas. La matriz completa, celda por celda, está en el anexo A; la sección 7.3 la resume con su prueba asociada.

{{figura:FIG-5.2|Qué observar: cada VLAN con su CIDR, puerta de enlace y hosts útiles; los diez /26 y el rango de infraestructura 10.20.35.0/24 dentro de la VLAN 30; la ruta por defecto hacia el FortiGate y las rutas propagadas por BGP en AWS.}}

## 5.3 Diseño de seguridad perimetral y zonas

La Figura 5.3 ordena las zonas por nivel de confianza (la segregación de redes que pide el control 8.22 de ISO/IEC 27002 [13]) y muestra, sobre la misma topología lógica, dónde actúa cada control: el FortiGate en el borde del campus, Suricata y CrowdSec en FW01, el WAF delante del portal y del panel remoto, los señuelos y el SIEM que recibe los eventos. Las amenazas AM-xx aparecen marcadas en el punto donde se mitigan (anexo B).

{{tabla:zonas_confianza}}

La zona AWS figura con confianza «Baja, expuesta», igual que DMZ-SVC, porque EC2-GW recibe tráfico de Internet (F29). Que EC2-GW no guarde datos no vuelve más confiable a su zona: solo reduce el impacto si la comprometen. La decisión está registrada como CI-72 y no cambia ninguna regla: EC2-GW solo puede llegar a CTRL01:443 con mTLS y a SIEM01:1514/1515, tanto por su Security Group como por FW01 (T58).

{{figura:FIG-5.3|Qué observar: las zonas de mayor a menor confianza; los controles de cada capa de defensa; que PORTAL01 no tiene salida a Internet y recibe su certificado de FW01 por F33; y en qué componente se mitiga cada amenaza AM-xx.}}

**Defensa en profundidad.** Ningún control es el único que protege un activo. Si una capa falla, la siguiente sigue actuando: un estudiante que se salte el PAC sigue sin llegar a CTRL01 porque FW01 lo deniega; un equipo de la DMZ comprometido sigue sin salida porque la VLAN no tiene reglas hacia el resto.

{{tabla:defensa}}

## 5.4 Diseño de conectividad VPN híbrida

La VPN es IPsec *site-to-site* basada en rutas (interfaces VTI) entre FW01 y el Virtual Private Gateway de la VPC [14], [15]. Como FW01 está detrás del NAT del FortiGate, usa NAT-T (UDP 4500) y se identifica ante AWS con la IP pública 203.0.113.10. Los parámetros no incluyen secretos: la llave precompartida la genera AWS, se guarda cifrada con SOPS y no aparece en este informe ni en el repositorio.

{{tabla:vpn}}

**Qué transporta y qué no.** La VPN lleva el panel remoto (F30: EC2-GW → CTRL01:443 con mTLS dentro de IPsec) y los eventos de EC2-GW hacia el SIEM (F13). No lleva descargas ni respaldos: los MISS salen por el FortiGate (F8) y el respaldo va cifrado en origen por Internet hacia S3 (F18), porque pasarlos por la VPN agregaría costo y latencia sin ganar protección. Si la VPN cae, el campus no lo nota: solo se pierde el acceso remoto, y el encargado sigue usando ENC01.

{{figura:FIG-5.4|Qué observar: los dos túneles (VTI1 activo, VTI2 de respaldo con AS-path prepending) cruzan el FortiGate con NAT-T; en AWS, EC2-GW está en pub-a y app-a queda vacía; solo F30 y F13 viajan por la VPN.}}

## 5.5 Diagrama de flujo de información planeado

Cada flujo tiene un ID F-nn que se repite en la regla del firewall (descripción de la regla), en los diagramas y en las pruebas. La tabla incluye el flujo bloqueado F7 porque documentar lo que se deniega es tan importante como lo que se permite. El retorno de una conexión permitida no se lista: FW01 es un firewall con estado.

{{tabla:flujos}}

{{figura:FIG-5.5a|Qué observar: los flujos de los usuarios (F1, F3, F5, F6) y del Wi-Fi (F31, F32), siempre hacia EDGE o el portal; la salida de los nodos (F8) por el FortiGate; F7 bloqueado; el señuelo F24 en claro a propósito.}}

{{figura:FIG-5.5b|Qué observar: el plano de control (F10 con mTLS y firma), los eventos hacia SIEM01 (F13, F14), la administración desde JMP01 (F20), el acceso del encargado (F28 en el campus, F29 y F30 desde fuera) y el respaldo F18 hacia S3.}}

### Cómo se protege cada tramo del trayecto de los datos

El diseño protege los datos tramo por tramo y, donde importa, también de extremo a extremo con una firma que no depende de la red.

**Una descarga (F8 → nodo → F1).** Del origen al nodo, TLS con verificación de certificado contra las raíces públicas; por eso se pide que el FortiGate no inspeccione ese tráfico [S-29] (T07). En el nodo, el contenido se guarda direccionado por SHA-256 y se verifica antes de servirlo. Del nodo a la PC, TLS con la CA del proyecto limitada por *Name Constraints* solo para los dominios aprobados, o el TLS original del sitio en *passthrough*. Los repositorios en HTTP plano (apt y partes de Windows Update) firman sus paquetes y el cliente verifica la firma; un archivo HTTP sin firma propia es un riesgo aceptado y documentado. Hacia Internet, el nodo elimina `X-Forwarded-For`, `Via` y `Forwarded` para que la IP del estudiante no salga (REQ-F-28, T26).

**Un cambio del encargado (el trayecto más sensible).** Desde fuera del campus, TLS 1.3 con certificado público, HSTS, WAF y segundo factor hasta EC2-GW (F29); de EC2-GW a CTRL01, un nuevo TLS con certificado de cliente dentro de IPsec (F30). Aunque la VPN quedara mal configurada, EC2-GW tiene que probar quién es. En CTRL01, segundo factor, RBAC por laboratorio y auditoría de solo inserción. Las acciones críticas (aprobar un dominio a descifrar, rotar llaves, crear usuarios) solo se aceptan con origen campus (REQ-F-37, T54). De CTRL01 al nodo, la configuración viaja firmada con ed25519 por mTLS (F10): quien intercepte F10 no puede inyectar configuración, porque el nodo rechaza lo no firmado o más antiguo (T51).

**Eventos y respaldos.** Los agentes de Wazuh cifran su protocolo (F13) y FW01 envía syslog solo por TLS en 6514 (F14, T28). El respaldo de la consola lo cifra restic en origen, con una llave que no está en AWS, y viaja por HTTPS a un bucket que solo acepta la IP pública del campus, con versionado y Object Lock de 30 días (F18, T40).

**Tramos sin cifrar con riesgo aceptado.** DNS y NTP hacia FW01 (F2) y el PAC (F3) viajan en claro dentro de la LAN. Se compensa con DNSSEC en el resolvedor y con la URL fija del PAC por GPO, que evita el secuestro de WPAD (T60). El señuelo F24 es en claro a propósito.

## 5.6 Matriz de componentes de red

La tabla lista los {{dato:n_componentes}} componentes del inventario que no están retirados, con su IP planeada (una línea por interfaz), zona, función y criticidad. Cubre el 100 % de lo dibujado en las Figuras 1.1 a 5.5b: la validación V-62 cruza los componentes de los `.drawio` con la matriz. EC2-DR y NAT-DR son **temporales**: solo existen durante el simulacro de recuperación (T59) y no se dibujan en las topologías de operación. La matriz XLSX `{{dato:matriz_xlsx}}` agrega, para cada componente, por qué existe, qué aporta, qué pasa si falla, sus flujos, pruebas, amenazas y figuras, y la lista de los {{dato:n_retirados}} componentes retirados en la v0.4.

{{tabla:componentes}}
