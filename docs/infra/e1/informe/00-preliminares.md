# Control de versiones

{{tabla:control_versiones}}

Este informe se genera con `make informe` desde la fuente única del repositorio (`infra/inventory.yaml`, `infra/pruebas.yaml` e `infra/trazabilidad.yaml`). Las tablas de direccionamiento, componentes, flujos, pruebas, amenazas, detecciones y supuestos no se escriben a mano: si un dato cambia en el inventario, el informe, los diagramas y las matrices XLSX cambian juntos. El commit indicado arriba identifica la versión exacta de esos datos.

Las contradicciones y vacíos encontrados en los documentos base se registran como CI-nn en `docs/infra/e1/CAMBIOS-INVENTARIO.md`. CI-72 (nivel de confianza de la zona AWS, ahora «Baja, expuesta») y CI-74 (motivo del retiro de cuatro subredes de AWS, D-28) están resueltos; ninguno cambia una IP, un puerto ni una regla de este diseño.

# Glosario

| Término | Significado en este informe |
| --- | --- |
| Nodo de caché (EDGE01, EDGE02) | Servidor del campus que actúa como proxy: descarga un archivo una vez desde Internet y entrega la copia por la LAN a las PCs que lo pidan. |
| Consola (CTRL01) | Aplicación web del encargado de laboratorio (SPA, API y base de datos PostgreSQL local). Decide qué se guarda en la caché y qué laboratorio tiene acceso, y firma la configuración de los nodos. |
| Configuración firmada | Archivo de configuración que la consola firma con una llave ed25519. El nodo solo aplica lo que trae una firma válida y más reciente que la vigente. |
| PAC | Archivo `wpad.dat` que indica al navegador qué proxy usar. Aquí se distribuye por GPO con una URL fija, sin autodescubrimiento. |
| `DIRECT` | Salida directa a Internet sin pasar por el nodo. El PAC la usa como último recurso; solo existe durante el piloto (F6). |
| Descifrado selectivo | El nodo abre el HTTPS solo de dominios aprobados y solo en PCs institucionales con la CA del proyecto instalada. El resto pasa cifrado (*passthrough*). |
| BYOD | Equipos personales de los estudiantes conectados al Wi-Fi de la DTI (zona WIFI-EST). |
| FortiGate (FGT-EXT) y FortiGuard | Firewall perimetral existente del campus y su servicio de filtrado web por categorías. No forman parte del alcance; el diseño se apoya en ellos. |
| Zona | Conjunto de equipos con el mismo nivel de confianza y las mismas reglas. En el campus, cada zona interna es una VLAN. |
| DMZ | Zona que aloja servicios alcanzables desde redes menos confiables. Este diseño separa la de servicios (DMZ-SVC) de la de señuelos (DMZ-HONEY). |
| VTI | Interfaz de túnel virtual. Permite una VPN basada en rutas, en la que BGP decide por qué túnel va el tráfico. |
| BGP | Protocolo de ruteo dinámico (RFC 4271) [1]. Aquí intercambia las redes del campus y de AWS por la VPN. |
| NAT-T | Encapsulado de IPsec en UDP 4500 que permite cruzar un equipo que hace NAT, como el FortiGate (RFC 3948) [2]. |
| mTLS | TLS en el que cliente y servidor presentan certificado; el servidor sabe con certeza qué equipo lo llama. |
| WAF | Firewall de aplicaciones web (Coraza [3] con OWASP CRS [4]). Filtra inyecciones y ataques web conocidos. |
| IDS / IPS | Sistema que detecta (IDS) o además bloquea (IPS) tráfico malicioso. Aquí es Suricata [5] dentro de FW01. |
| Honeypot / canary | Servicio señuelo sin uso legítimo: cualquier contacto con él es sospechoso. HNY01 es el honeypot de DMZ-HONEY; HNY02, el canary dentro de LAB. |
| SIEM | Sistema que reúne y correlaciona eventos de seguridad (Wazuh [6], en SIEM01). |
| Object Lock | Función de S3 que impide borrar o modificar una copia durante un período fijo, incluso con credenciales válidas [7]. |
| Modo L / Modo A / Modo H | Ejecuciones del diseño: L = laboratorio emulado local; A = AWS efímero; H = hardware del campus (S2). Los resultados del Modo L son de una **emulación** y no de equipos reales. |
| F-nn, T-nn, OD-nn, AM-nn, DET-nn, D-nn, S-nn | Identificadores de flujo, prueba, objetivo de diseño, amenaza, detección, decisión y supuesto del repositorio. Un ID retirado no se reutiliza. |
