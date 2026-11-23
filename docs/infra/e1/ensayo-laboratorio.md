# Ensayo en el laboratorio emulado (Modo L)

> Generado por `make test-lab` (`tests/network/run.py`). No editar a mano.

> **El laboratorio es emulado** (Parte F4.2 del documento maestro). Lo que pasa aquí demuestra que el *diseño* se comporta como está descrito en una emulación funcional; no es la validación del producto real (OPNsense, VGW de AWS) ni del campus.

- Fecha: 2026-11-23 · commit: `desconocido`
- Resultado: **34 PASA**, **0 FALLA**, **1 PARCIAL**, **17 NO_APLICA** (de 52 pruebas vigentes, 24 de ellas ampliaciones T29+ que aún no tienen caso en el Modo L)
- `PARCIAL` = parte de los criterios no se pudo evaluar en el Modo L (navegador real, Wazuh…) o la medición no ejercitó lo que la prueba valida. **No cuenta como PASA.**
- `NO_APLICA` = la prueba no se puede ejecutar en L; se indica el modo en que sí se ejecutará. **Nunca cuenta como PASA.**

## Resultados

La columna «v0.2 → v0.4» compara con el ensayo anterior (2026-11-21, v0.2). «nueva» = prueba de la v0.4; «cambió de destino» = D1.16 v0.4 la apunta a otra pieza.

| Prueba | Resultado | v0.2 → v0.4 | Medido | Motivo o nota |
| --- | --- | --- | --- | --- |
| T01 — ON-PREM → AWS | **NO_APLICA** | NO_APLICA → NO_APLICA (cambió de destino: destino EC2-GW 10.30.0.10 (antes EC2-SHIELD)) | — | el Modo L no ejecuta T01 (modos de la prueba: A, H); se ejecuta en A y H |
| T02 — AWS → ON-PREM | **NO_APLICA** | NO_APLICA → NO_APLICA (cambió de destino: EC2-GW → CTRL01:443 (antes EC2-CTRLR → DB01:5432)) | — | el Modo L no ejecuta T02 (modos de la prueba: A, H); se ejecuta en A y H |
| T03 — DMZ → AWS | **NO_APLICA** | NO_APLICA → NO_APLICA | — | el Modo L no ejecuta T03 (modos de la prueba: A, H); se ejecuta en A y H |
| T04 — Internet → subred privada AWS | **NO_APLICA** | NO_APLICA → NO_APLICA | — | el Modo L no ejecuta T04 (modos de la prueba: A, H); se ejecuta en A y H |
| T05 — Falla de un túnel | **PASA** | PASA → PASA | convergencia_s = 27.2, interrupcion_s = 26.8 | tras la caída la ruta a 10.30.0.0/16 va por: vti2 |
| T06 — LAB → MGMT | **PASA** | PASA → PASA | puertos_open = 0, paquetes_denegados_por_fw01 = 666 |  |
| T07 — LAB → EDGE 3128 | **PASA** | PASA → PASA | x_celeris_cache_primera = 2, cache_status_primera_miss = 0, cache_status_segunda_hit = 1 | Cache-Status presente pero distinto de lo esperado: primera = ['celeris; hit; ttl=1686'], segunda = ['celeris; hit; ttl=1686'] |
| T08 — LAB → UDP 443 | **PASA** | PASA → PASA | paquetes_bloqueados_regla_F7 = 5, datagramas_recibidos_en_ext01 = 0, paquetes_quic_recibi… | curl del laboratorio no soporta HTTP/3: `curl --http3` se sustituyó por una sonda UDP 443 (5 datagramas) hacia ext01 |
| T09 — Caída de EDGE01 | **PASA** | PASA → PASA | tiempo_de_cambio_s = 8.7, tiempo_hasta_direct_s = 30.6, peticiones_nuevas_en_edge02_con_e… | el navegador es Chromium sin pantalla con --ignore-certificate-errors (la CA del nodo no está en su almacén); el cliente imitado con curl se conserva como control |
| T10 — DMZ → LAN | **PASA** | PASA → PASA | — |  |
| T11 — Internet → DMZ-HONEY | **PASA** | PASA → PASA | conexiones_en_cowrie = 18, latencia_alerta_wazuh_s = 2.7 | F24 exige abrir TCP 22 y 23 en el FortiGate durante la ventana, pero D1.8 y S-29 limitan su NAT 1:1 a UDP 500/4500 y TCP 80/443 (CI-49) |
| T13 — Abuso del proxy | **PASA** | PASA → PASA | — |  |
| T14 — Puerto no permitido | **PASA** | PASA → PASA | — |  |
| T15 — Exposición del portal | **PASA** | PASA → PASA | puertos_abiertos = 2, puertos_abiertos_en_ctrl01 = 0, alertas_suricata_fw01 = 0 |  |
| T16 — TLS del portal | **PASA** | PASA → PASA | — | calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H) |
| T17 — Escaneo web | **PASA** | PASA → PASA | alertas_altas = 0 |  |
| T18 — WAF | **PASA** | PASA → PASA | eventos_modsecurity = 6, latencia_alerta_wazuh_s = 1.3 |  |
| T19 — PORTAL01 no establece conexiones hacia la WAN (TCP/UDP) | **PASA** | PASA → PASA | conexiones_establecidas_hacia_la_wan = 0, paquetes_denegados_por_fw01 = 12, salida_http_8… | el DNS hacia el resolvedor de FW01 (F2) no cuenta: es tráfico local a 10.20.0.0/16; ACME corre en FW01 y no se emula en el Modo L (no hay Internet) |
| T20 — Aislamiento del señuelo | **PASA** | PASA → PASA (cambió de destino: HNY01 → PORTAL01:443 (antes WEB01:8080)) | — |  |
| T21 — MTU del túnel | **NO_APLICA** | NO_APLICA → NO_APLICA (cambió de destino: destino 10.30.0.10) | — | el Modo L no ejecuta T21 (modos de la prueba: A, H); se ejecuta en A y H |
| T23 — Fuga IPv6 | **NO_APLICA** | NO_APLICA → NO_APLICA | — | RA guard es un control del switch de acceso (SW-ACC, S-14); los puentes Linux del laboratorio no lo emulan; se ejecuta en Modo H |
| T24 — DNS cifrado | **PASA** | PASA → PASA | paquetes_bloqueados_regla_F7 = 3 | el resolvedor de prueba es ext01 (IP del laboratorio), no 203.0.113.53 (CI-19): la regla F7 bloquea por puerto, no por destino |
| T25 — Break-glass | **NO_APLICA** | NO_APLICA → NO_APLICA | — | ESX01, IPMI01, BRK01 y SW-CORE01 no se emulan: el puerto break-glass no existe en F4.1 (CI-16); se ejecuta en Modo H |
| T26 — Privacidad hacia orígenes | **PASA** | PASA → PASA | paquetes_en_la_vpn = 0 | en la v0.4 el MISS sale a Internet (F8) y no por la VPN; se captura en la interfaz del nodo y se compara con el eco del origen (/echo de ext01) |
| T27 — Administración y consola cifradas | **PASA** | PASA → PASA | respuestas_http_en_claro_del_servidor = 0, paquetes_http_en_claro = 0, handshakes_tls = 7… | el 9128 de los nodos y el 443 de ctrl01 solo aceptan TLS; los certificados son de laboratorio (en producción, los de step-ca) |
| T28 — Syslog cifrado | **PASA** | PASA → PASA | paquetes_udp_514 = 0, handshakes_tls_6514 = 2, latencia_alerta_wazuh_s = 1.8 | fw01-sim no es OPNsense y no tiene syslog nativo: el evento lo envía `socat` desde fw01-sim; lo que se prueba es el receptor de SIEM01 (solo TLS) |
| T29 — Escaneo lateral detectado por Suricata de FW01 | **PASA** | PASA → PASA (cambió de destino: Suricata de FW01 en la interfaz LAB (antes IDS01)) | puertos_open = 0, paquetes_denegados_por_fw01 = 1282, latencia_alerta_wazuh_s = 2.6 | las reglas del laboratorio son locales (sid 9000001, escaneo SYN por origen): ET Open no está disponible en el Modo L |
| T30 — Canary interno detecta un barrido en LAB | **PASA** | PASA → PASA | conexiones_registradas_en_hny02 = 4, paquetes_vistos_por_fw01 = 0, latencia_alerta_wazuh_… | el canario registró 0 eventos con un barrido SYN (-sS) y 4 con uno de conexión completa (-sT): un canario de aplicación no ve los SYN sin respuesta; IDS01 no captura la … |
| T31 — Honey-URL en el nodo de borde | **PASA** | PASA → PASA | latencia_alerta_wazuh_s = 0.9 | la ruta señuelo del laboratorio es /admin-backup.zip [S-17]; en S2 se define con el equipo |
| T32 — CrowdSec bloquea una IP abusiva en la WAN | **PASA** | PASA → PASA | paquetes_descartados_tras_la_decision = 8, latencia_alerta_wazuh_s = 20.1 | la decisión se agrega con `cscli decisions add` (la «simulación con su escenario de prueba» de D1.14): un escenario real exige logs de SSH o del WAF |
| T33 — Toda denegación deja rastro con hora fiable | **NO_APLICA** | NO_APLICA → NO_APLICA | — | el Modo L no ejecuta T33 (modos de la prueba: H); se ejecuta en H |
| T34 — Administración desde JMP01 | **NO_APLICA** | NO_APLICA → NO_APLICA | — | el Modo L no ejecuta T34 (modos de la prueba: H); se ejecuta en H |
| T35 — MGMT → Internet solo por 443 | **PASA** | PASA → PASA | — |  |
| T36 — Enrolamiento del nodo por mTLS | **NO_APLICA** | NO_APLICA → NO_APLICA | — | el Modo L no ejecuta T36 (modos de la prueba: H); se ejecuta en H |
| T40 — Respaldo en S3 con Object Lock | **NO_APLICA** | NO_APLICA → NO_APLICA | — | el Modo L no ejecuta T40 (modos de la prueba: H); se ejecuta en H |
| T42 — Hora NTS y DNS cifrado desde FW01 | **NO_APLICA** | NO_APLICA → NO_APLICA (cambió de destino: origen FW01 (antes SVC01)) | — | el Modo L no ejecuta T42 (modos de la prueba: H); se ejecuta en H |
| T43 — Actualización de reglas de seguridad | **NO_APLICA** | NO_APLICA → NO_APLICA | — | el Modo L no ejecuta T43 (modos de la prueba: H); se ejecuta en H |
| T45 — Internet → zonas internas | **PASA** | PASA → PASA | puertos_open = 0, paquetes_denegados_por_fw01 = 20 | el FortiGate emulado reenvía todo y deja la política a FW01; el FortiGate real solo publica UDP 500/4500 y TCP 80/443 (D1.8) |
| T46 — DMZ-SVC → zonas internas | **PASA** | PASA → PASA (cambió de destino: DMZ-SVC → zonas internas, incluido CTRL01:5432) | puertos_open = 0, paquetes_denegados_por_fw01 = 24 | PORTAL01 se probó como equipo comprometido; el 5432 de CTRL01 es un puerto de prueba: PostgreSQL de la v0.4 no escucha en la red (socket local, D-25) |
| T47 — DMZ-HONEY → cualquier zona | **PASA** | PASA → PASA | puertos_open = 0, paquetes_denegados_por_fw01 = 16 | «Internet» es ext01 (198.51.100.100): el laboratorio no tiene DNS ni salida a Internet real |
| T49 — Entrega del certificado del portal por F33 (ACME en FW01) | **PASA** | PASA → PASA | — | Modo L: solo se comprueba que F33 abre; el SFTP (llave dedicada, usuario chroot) y la renovación ACME de FW01 se prueban en el Modo H (S-31) |
| T50 — Precarga en ventana horaria con límite de ancho de banda | **NO_APLICA** | nueva | — | requiere la consola (CE02, S2): la precarga programada con ventana horaria y límite de ancho de banda (REQ-F-34, REQ-RN-10) no existe en el nodo ni en ctrl01; se ejecuta… |
| T51 — Cambio del encargado y configuración sin firma | **PASA** | nueva | latencia_cambio_s = 2.5, bundles_sin_firma_aplicados = 0 | el nodo recarga cada 5 s (config_reload_secs en el laboratorio); en producción el intervalo lo fija la DTI. Solo cambian allowed_clients, intercept_domains, never_interc… |
| T52 — Laboratorio deshabilitado | **PASA** | nueva | — | el laboratorio es un /26 de allowed_clients; el tráfico de LAB-03 sigue llegando al nodo (F1 abre toda la VLAN 30 en FW01): el control está en el nodo (D1.8, nota 1) |
| T53 — Login remoto sin segundo factor y 10 intentos fallidos | **NO_APLICA** | nueva | — | requiere la consola (CE02, S2): el segundo factor, el límite de intentos y la auditoría de inicios de sesión (REQ-F-33, DET-10) no existen en ctrl01; se ejecuta en Modo … |
| T54 — Acción crítica desde una sesión remota | **NO_APLICA** | nueva | — | requiere la consola (CE02, S2): la aprobación de fuentes y el RBAC de la API (REQ-F-31, REQ-F-37); ctrl01 solo rechaza con 403 un POST /aprobar remoto de prueba; se ejec… |
| T55 — Coalescencia de descargas simultáneas | **PASA** | nueva | descargas_en_origen = 1, respuestas_collapsed_o_hit = 19, respuestas_200 = 20 | con el presupuesto de memoria por defecto (max_buffered_bytes = 512 MiB) los seguidores de un objeto de 100 MB se sirven desde memoria de a uno por cada 100 MB reservado… |
| T56 — BYOD no se descifra | **PASA** | nueva | certificados_emitidos_por_la_ca_del_proyecto = 0 | la red del Wi-Fi está en byod_networks del nodo; la regla no depende de la configuración que llegue (REQ-RN-11) |
| T57 — WIFI-EST hacia CTRL01, MGMT y LAB | **PASA** | nueva | puertos_open = 0, paquetes_denegados_por_fw01 = 12 |  |
| T58 — EC2-GW solo alcanza CTRL01:443 y SIEM01 | **PARCIAL** | nueva | paquetes_denegados_por_fw01 = 18 | medición vacía: el Security Group sg-gw no existe en el Modo L: aquí solo se midió la denegación de FW01; la del SG se prueba en el Modo A (D5.4, make test-aws) |
| T59 — Restaurar la consola desde S3 | **NO_APLICA** | nueva | — | el Modo L no ejecuta T59 (modos de la prueba: A, H); se ejecuta en A y H |
| T60 — Secuestro de WPAD | **PASA** | nueva | peticiones_a_la_url_falsa_wpad = 0 | el anuncio por DNS y DHCP se emula con una entrada `wpad` en el cliente y un servidor rogue en kali01: ni FW01 ni el laboratorio tienen un DHCP donde anunciar la opción … |

### Pruebas retiradas en la v0.4 (no se ejecutan ni se reutilizan sus IDs)

| Prueba | Motivo | Resultado en la v0.2 |
| --- | --- | --- |
| T12 | STORAGE y NFS | PASA |
| T22 | SVC01 | PASA |
| T37 | OTLP | NO_APLICA |
| T38 | base de datos en red | NO_APLICA |
| T39 | NAS | PASA |
| T41 | NFS | NO_APLICA |
| T44 | peering | PARCIAL |
| T48 | STORAGE | NO_APLICA |

## Mediciones

- **Convergencia de la VPN (T05, OD-05):** 27.2 s desde que cae el túnel 1 hasta que el tráfico vuelve a pasar por el túnel 2 (interrupción visible 26.8 s). Meta de D1.10: ≤ 60 s. El hold de BGP (30 s) es solo un componente; el valor real es el medido.
- **Cambio de nodo del PAC (T09/OD-03):** 8.7 s con EDGE01 caído; 30.6 s hasta DIRECT con ambos caídos (cliente que imita al PAC con `curl`, no un navegador).
- **Coalescencia (T55):** 1 descarga(s) en origin-sim para 20 clientes simultáneos de 100 MB; 19 respuestas HIT de las 19 que esperaron.
- **Cambio firmado (T51, REQ-NF-16):** el nodo aplicó la configuración firmada en 2.5 s (meta ≤ 60 s; intervalo de recarga del laboratorio: 5 s).
- **TLS del portal (T16, OD-08):** calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H)
- **Exposición (T15):** 2 puertos abiertos desde Internet; alertas de Suricata en fw01-sim durante el escaneo: 0.
- **Métricas (T27, REQ-NF-14):** paquetes HTTP en claro = 0, handshakes TLS = 7, apariciones del token = 0.

## Hallazgos (contradicen o precisan el diseño)

- T05 — tras la caída la ruta a 10.30.0.0/16 va por: vti2
- T05 — la sonda va de EC2-GW (gw-sim) a CTRL01:443 (F30): es el flujo que la VPN transporta en la v0.4
- T07 — Cache-Status presente pero distinto de lo esperado: primera = ['celeris; hit; ttl=1686'], segunda = ['celeris; hit; ttl=1686']
- T08 — curl del laboratorio no soporta HTTP/3: `curl --http3` se sustituyó por una sonda UDP 443 (5 datagramas) hacia ext01
- T09 — el navegador es Chromium sin pantalla con --ignore-certificate-errors (la CA del nodo no está en su almacén); el cliente imitado con curl se conserva como control
- T11 — F24 exige abrir TCP 22 y 23 en el FortiGate durante la ventana, pero D1.8 y S-29 limitan su NAT 1:1 a UDP 500/4500 y TCP 80/443 (CI-49)
- T11 — el puerto 23 de F24 no se prueba: OpenCanary no está en el laboratorio
- T16 — calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H)
- T19 — el DNS hacia el resolvedor de FW01 (F2) no cuenta: es tráfico local a 10.20.0.0/16; ACME corre en FW01 y no se emula en el Modo L (no hay Internet)
- T24 — el resolvedor de prueba es ext01 (IP del laboratorio), no 203.0.113.53 (CI-19): la regla F7 bloquea por puerto, no por destino
- T26 — en la v0.4 el MISS sale a Internet (F8) y no por la VPN; se captura en la interfaz del nodo y se compara con el eco del origen (/echo de ext01)
- T27 — el 9128 de los nodos y el 443 de ctrl01 solo aceptan TLS; los certificados son de laboratorio (en producción, los de step-ca)
- T28 — fw01-sim no es OPNsense y no tiene syslog nativo: el evento lo envía `socat` desde fw01-sim; lo que se prueba es el receptor de SIEM01 (solo TLS)
- T28 — escuchas UDP en el puerto 514 de SIEM01: 0
- T29 — las reglas del laboratorio son locales (sid 9000001, escaneo SYN por origen): ET Open no está disponible en el Modo L
- T29 — el escaneo cruza FW01 desde la interfaz LAB (vlan30): Suricata de fw01-sim lo ve aunque el firewall lo deniegue; el evento llega a Wazuh por syslog TLS (F14)
- T30 — el canario registró 0 eventos con un barrido SYN (-sS) y 4 con uno de conexión completa (-sT): un canario de aplicación no ve los SYN sin respuesta; IDS01 no captura la VLAN 30 (D1.14)
- T30 — el canario es un equivalente funcional de OpenCanary (F4.2): registra la conexión en un archivo, sin enviarla a un agente de Wazuh
- T31 — la ruta señuelo del laboratorio es /admin-backup.zip [S-17]; en S2 se define con el equipo
- T32 — la decisión se agrega con `cscli decisions add` (la «simulación con su escenario de prueba» de D1.14): un escenario real exige logs de SSH o del WAF
- T32 — fw01-sim no es OPNsense: el aviso a Wazuh lo envía `socat` por el syslog TLS (F14); CrowdSec y su bouncer sí son los reales, en modo local sin nube
- T45 — el FortiGate emulado reenvía todo y deja la política a FW01; el FortiGate real solo publica UDP 500/4500 y TCP 80/443 (D1.8)
- T46 — PORTAL01 se probó como equipo comprometido; el 5432 de CTRL01 es un puerto de prueba: PostgreSQL de la v0.4 no escucha en la red (socket local, D-25)
- T47 — «Internet» es ext01 (198.51.100.100): el laboratorio no tiene DNS ni salida a Internet real
- T49 — Modo L: solo se comprueba que F33 abre; el SFTP (llave dedicada, usuario chroot) y la renovación ACME de FW01 se prueban en el Modo H (S-31)
- T51 — el nodo recarga cada 5 s (config_reload_secs en el laboratorio); en producción el intervalo lo fija la DTI. Solo cambian allowed_clients, intercept_domains, never_intercept y byod_networks
- T52 — el laboratorio es un /26 de allowed_clients; el tráfico de LAB-03 sigue llegando al nodo (F1 abre toda la VLAN 30 en FW01): el control está en el nodo (D1.8, nota 1)
- T55 — con el presupuesto de memoria por defecto (max_buffered_bytes = 512 MiB) los seguidores de un objeto de 100 MB se sirven desde memoria de a uno por cada 100 MB reservados; en una primera corrida solo 5 de 19 obtuvieron HIT y 15 pasaron por el origen (sobre presupuesto). El laboratorio fija 3 GiB; el dimensionamiento de RAM del nodo (8 GB, D2.4) debe reservar max_buffered_bytes para 20 clientes × el instalador más grande
- T55 — los 19 que esperan reciben la copia ya guardada (Cache-Status: hit): el nodo no marca «collapsed»; el líder es el único MISS
- T55 — el laboratorio sube max_object_bytes a 200 MiB y coalesce_wait_secs a 30 en los nodos EDGE: con los valores por defecto (64 MiB) un objeto de 100 MB no se guarda ni se coalesce
- T56 — la red del Wi-Fi está en byod_networks del nodo; la regla no depende de la configuración que llegue (REQ-RN-11)
- T58 — sg-gw (D2.5) no se emula; la mitad «SG» de T58 queda para el Modo A
- T60 — el anuncio por DNS y DHCP se emula con una entrada `wpad` en el cliente y un servidor rogue en kali01: ni FW01 ni el laboratorio tienen un DHCP donde anunciar la opción 252
- T60 — `nslookup` no está en la imagen: se usó kdig contra la IP de FW01 en la VLAN de LAB

## Qué se emula y qué no (equivalencias de F4.2)

| En el diseño | En el laboratorio | Equivalencia |
| --- | --- | --- |
| FW01 OPNsense | `fw01-sim`: Debian + nftables (reglas generadas del inventario) + strongSwan + FRR + Suricata + Unbound + NTP + CrowdSec | Funcional (D5.3): mismas zonas, flujos, política por defecto, VPN con NAT-T y BGP. No es OPNsense; el IPS inline se emula como IDS |
| FortiGate (FGT-EXT) | `fgt-sim`: nftables con NAT 1:1 de la IP pública del laboratorio (198.51.100.10) hacia 10.20.0.2 solo para UDP 500/4500 y TCP 80/443, y ruta al Wi-Fi | Funcional (D5.3), sin FortiGuard ni inspección SSL: la exclusión de EDGE01/02 de esa inspección [S-29] no se puede probar en el Modo L |
| Wi-Fi de estudiantes (WIFI-EST) | Puente `br-wifi` (172.16.0.0/16) + `byod01` | Funcional (D5.3), sin puntos de acceso ni el DNS y el DHCP de la DTI [S-28] |
| Port groups de ESXi, SW-CORE01 | Puentes Linux por VLAN (`br-vlanNN`, 7 VLAN) | Funcional. No hay trunk 802.1Q ni controles de capa 2 (RA guard, DHCP snooping, port-security) |
| VGW de AWS | `vgw-sim`: strongSwan + FRR con los mismos parámetros de fase 1/2 y BGP; también hace de Internet Gateway y NAT de la VPC | Funcional, sin el servicio gestionado ni sus tablas de rutas, Security Groups o NACL |
| EC2-GW | `gw-sim`: nginx + ModSecurity + OWASP CRS detrás de `vgw-sim`, con certificado de cliente hacia `ctrl01:443` | Funcional; D5.3 dice Caddy + Coraza («mismo producto»), que la imagen base no trae (CI-48). El Security Group `sg-gw` no se emula |
| CTRL01 (consola) | `ctrl01`: consola de prueba HTTPS en 443 (sesiones `campus` y `remoto`, 403 a las acciones críticas remotas) y firma ed25519 de la configuración de los nodos | Funcional y mínima (D5.3). No es la consola de CE02: T50, T53 y T54 la necesitan y quedan NO_APLICA |
| EDGE01/02 | `edge01`/`edge02`: el mismo binario que la imagen OCI de producción, sobre la imagen base de laboratorio (la imagen mínima no trae shell para configurar la red) | Mismo código; el contenedor es el de laboratorio, no la imagen OCI |
| PORTAL01 | `portal01`: nginx + ModSecurity + OWASP CRS con el aviso de `docs/AVISO.md` como sitio estático | Funcional; D5.3 dice Caddy + Coraza. El sitio es generado, no firmado (REQ-F-30 pendiente) |
| HNY01 | `hny01` + Cowrie oficial (SSH, puerto 2222) | Cowrie sí; OpenCanary y el puerto 23 de F24 no |
| HNY02 | `hny02`: canario propio en Python (puertos 22, 80, 445, 3389) | Equivalente funcional; no es OpenCanary |
| SIEM01 Wazuh | `siem01` + `siem01-wazuh`: Wazuh manager 4.9.2 real y agentes en CTRL01, EDGE01/02, PORTAL01, HNY01, HNY02 y EC2-GW | Mismo producto; las reglas locales 100300–100305 son de laboratorio. El IDS de FW01 llega por syslog TLS (F14), no por un agente |
| ENC01, PCs de LAB-01…LAB-10 | `enc01`, `labcli01` (con Chromium), `labcli02` (LAB-01) y `labcli03` (LAB-03) | Funcional (D5.3): no se emulan los 400 equipos |
| Orígenes de Internet | `ext01` (atacante externo y origen web) y `origin-sim` (archivos de 100 MB a 1 GB) | Funcional; no hay Internet real ni DNS público |
| Certificado público del portal y de EC2-GW | Certificados de una CA de laboratorio (se generan en `lab/.run/pki`, fuera de git) | El ACME real y la calificación con CA pública se prueban en Modo A o H |
| ESX01, IPMI01, UPS01, BRK01, SW-CORE01, SW-ACC, S3, EC2-DR, NAT-DR | No existen en el laboratorio | Sus pruebas se ejecutan en Modo A o H (CI-16, D5.4) |

## Limitaciones

- Las IP son las del inventario, salvo la WAN (198.51.100.0/24, F4.1), el nombre del portal, los dominios de prueba y los parámetros de CI-24 y CI-48.
- T50, T53 y T54 requieren la consola (CE02, S2): son NO_APLICA aquí y se ejecutan en Modo H (T50) o A y H (T53, T54).
- `curl` de la imagen no soporta HTTP/3: T08 usa datagramas UDP 443 en lugar de `curl --http3`.
- T09 imita la lógica del PAC con `curl` además de usar Chromium; el cambio real de un navegador de producción se mide en Modo H.
- Los comandos de `infra/pruebas.yaml` son la referencia; el runner ejecuta su equivalente en los nodos del laboratorio (ver `evidencias/<fecha>-L/<T-xx>/salida.txt`).
- Las evidencias (pcap, registros, salidas) están en `evidencias/<fecha>-L/`, fuera de git: pueden contener el token de laboratorio. `resultados.json` y `junit.xml` sí se versionan.

## Reproducir

```bash
make lab-up      # genera, construye y despliega (Docker + containerlab en Linux/WSL)
make test-lab    # ejecuta las pruebas del Modo L (T05–T60) y reescribe este archivo
make lab-down
```
