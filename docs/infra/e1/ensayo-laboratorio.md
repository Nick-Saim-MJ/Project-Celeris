# Ensayo en el laboratorio emulado (Modo L)

> Generado por `make test-lab` (`tests/network/run.py`). No editar a mano.

> **El laboratorio es emulado** (Parte F4.2 del documento maestro). Lo que pasa aquí demuestra que el *diseño* se comporta como está descrito en una emulación funcional; no es la validación del producto real (OPNsense, VGW de AWS) ni del campus.

- Fecha: 2026-11-21 · commit: `e480bdc60754`
- Resultado: **31 PASA**, **0 FALLA**, **1 PARCIAL**, **17 NO_APLICA** (de 49 pruebas, 21 de ellas ampliaciones T29+ que aún no tienen caso en el Modo L)
- `PARCIAL` = parte de los criterios no se pudo evaluar en el Modo L (navegador real, Wazuh…) o la medición no ejercitó lo que la prueba valida. **No cuenta como PASA.**
- `NO_APLICA` = la prueba no se puede ejecutar en L; se indica el modo en que sí se ejecutará. **Nunca cuenta como PASA.**

## Resultados

| Prueba | Resultado | Medido | Motivo o nota |
| --- | --- | --- | --- |
| T01 — ON-PREM → AWS | **NO_APLICA** | — | el Modo L no ejecuta T01 (modos de la prueba: A, H); se ejecuta en A y H |
| T02 — AWS → ON-PREM | **NO_APLICA** | — | el Modo L no ejecuta T02 (modos de la prueba: A, H); se ejecuta en A y H |
| T03 — DMZ → AWS | **NO_APLICA** | — | el Modo L no ejecuta T03 (modos de la prueba: A, H); se ejecuta en A y H |
| T04 — Internet → subred privada AWS | **NO_APLICA** | — | el Modo L no ejecuta T04 (modos de la prueba: A, H); se ejecuta en A y H |
| T05 — Falla de un túnel | **PASA** | convergencia_s = 22.6, interrupcion_s = 22.3 | tras la caída la ruta a 10.30.0.0/16 va por: vti2 |
| T06 — LAB → MGMT | **PASA** | puertos_open = 0, paquetes_denegados_por_fw01 = 665 |  |
| T07 — LAB → EDGE 3128 | **PASA** | x_celeris_cache_primera = 1, cache_status_primera_miss = 1, cache_status_segunda_hit = 1 |  |
| T08 — LAB → UDP 443 | **PASA** | paquetes_bloqueados_regla_F7 = 5, datagramas_recibidos_en_ext01 = 0, paquetes_quic_recibi… | curl del laboratorio no soporta HTTP/3: `curl --http3` se sustituyó por una sonda UDP 443 (5 datagramas) hacia ext01 |
| T09 — Caída de EDGE01 | **PASA** | tiempo_de_cambio_s = 8.9, tiempo_hasta_direct_s = 16.9, peticiones_nuevas_en_edge02_con_e… | el navegador es Chromium sin pantalla con --ignore-certificate-errors (la CA del nodo no está en su almacén); el cliente imitado con curl se conserva como control |
| T10 — DMZ → LAN | **PASA** | — |  |
| T11 — Internet → DMZ-HONEY | **PASA** | conexiones_en_cowrie = 6, latencia_alerta_wazuh_s = 0.7 | el puerto 23 de F24 no se prueba: OpenCanary no está en el laboratorio |
| T12 — STORAGE no enrutada | **PASA** | — | NAS01 es un equivalente funcional (F4.2): sshd, restic y un puerto 2049 que no es NFS; el origen CTRL01 no se emula (se usan LABCLI01 y OBS01) |
| T13 — Abuso del proxy | **PASA** | — |  |
| T14 — Puerto no permitido | **PASA** | — |  |
| T15 — Exposición del portal | **PASA** | puertos_abiertos = 2, alertas_suricata_fw01 = 69 |  |
| T16 — TLS del portal | **PASA** | — | calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H) |
| T17 — Escaneo web | **PASA** | alertas_altas = 0 |  |
| T18 — WAF | **PASA** | eventos_modsecurity = 5, latencia_alerta_wazuh_s = 2.0 |  |
| T19 — Salida del portal | **PASA** | — |  |
| T20 — Aislamiento del señuelo | **PASA** | — |  |
| T21 — MTU del túnel | **NO_APLICA** | — | el Modo L no ejecuta T21 (modos de la prueba: A, H); se ejecuta en A y H |
| T22 — Caída de SVC01 | **PASA** | tiempo_hasta_el_pac_s = 7.3, tiempo_navegador_con_svc01_caido_s = 6.4 | `nslookup` no está en la imagen: se usó kdig contra la IP de FW01 en la VLAN de LAB |
| T23 — Fuga IPv6 | **NO_APLICA** | — | RA guard es un control del switch de acceso (SW-ACC, S-14); los puentes Linux del laboratorio no lo emulan; se ejecuta en Modo H |
| T24 — DNS cifrado | **PASA** | paquetes_bloqueados_regla_F7 = 3 | el resolvedor de prueba es ext01 (IP del laboratorio), no 203.0.113.53 (CI-19): la regla F7 bloquea por puerto, no por destino |
| T25 — Break-glass | **NO_APLICA** | — | ESX01, IPMI01, BRK01 y SW-CORE01 no se emulan: el puerto break-glass no existe en F4.1 (CI-16); se ejecuta en Modo H |
| T26 — Privacidad del túnel | **PASA** | paquetes_en_la_vpn = 34 | F9 (EDGE → EC2-SHIELD) se ejercita con REQ-F-29: los MISS salen del nodo hacia el shield por la VPN con mTLS; en la VPN solo se ve TLS, y por eso se mira también lo que … |
| T27 — Métricas cifradas | **PASA** | esquema_https = 1, respuestas_http_en_claro_del_servidor = 0, paquetes_http_en_claro = 0,… | el puerto 9128 solo acepta TLS (REQ-NF-14); el certificado es autofirmado de laboratorio: en producción F12 usa los de step-ca (F11) |
| T28 — Syslog cifrado | **PASA** | paquetes_udp_514 = 0, handshakes_tls_6514 = 2, latencia_alerta_wazuh_s = 2.0 | fw01-sim no es OPNsense y no tiene syslog nativo: el evento lo envía `socat` desde fw01-sim; lo que se prueba es el receptor de SIEM01 (solo TLS) |
| T29 — Escaneo lateral detectado por IDS01 | **PASA** | puertos_open = 0, paquetes_denegados_por_fw01 = 1281, latencia_alerta_wazuh_s = 3.7 | las reglas del laboratorio son locales (sid 9000001, escaneo SYN por origen): ET Open no está disponible en el Modo L |
| T30 — Canary interno detecta un barrido en LAB | **PASA** | conexiones_registradas_en_hny02 = 4, paquetes_vistos_por_fw01 = 0, latencia_alerta_wazuh_… | el canario registró 0 eventos con un barrido SYN (-sS) y 4 con uno de conexión completa (-sT): un canario de aplicación no ve los SYN sin respuesta; IDS01 no captura la … |
| T31 — Honey-URL en el nodo de borde | **PASA** | latencia_alerta_wazuh_s = 2.1 | la ruta señuelo del laboratorio es /admin-backup.zip [S-17]; en S2 se define con el equipo |
| T32 — CrowdSec bloquea una IP abusiva en la WAN | **PASA** | paquetes_descartados_tras_la_decision = 8, latencia_alerta_wazuh_s = 21.5 | la decisión se agrega con `cscli decisions add` (la «simulación con su escenario de prueba» de D1.14): un escenario real exige logs de SSH o del WAF |
| T33 — Toda denegación deja rastro con hora fiable | **NO_APLICA** | — | el Modo L no ejecuta T33 (modos de la prueba: H); se ejecuta en H |
| T34 — Administración desde JMP01 | **NO_APLICA** | — | el Modo L no ejecuta T34 (modos de la prueba: H); se ejecuta en H |
| T35 — MGMT → Internet solo por 443 | **PASA** | — |  |
| T36 — Enrolamiento del nodo por mTLS | **NO_APLICA** | — | el Modo L no ejecuta T36 (modos de la prueba: H); se ejecuta en H |
| T37 — Telemetría OTLP por TLS | **NO_APLICA** | — | el Modo L no ejecuta T37 (modos de la prueba: H); se ejecuta en H |
| T38 — CTRL01 → base de datos por TLS | **NO_APLICA** | — | el Modo L no ejecuta T38 (modos de la prueba: H); se ejecuta en H |
| T39 — Respaldo y restauración en NAS01 | **PASA** | tiempo_restauracion_s = 1.2 | NAS01 es un equivalente funcional (F4.2): sshd + restic; la clave del repositorio se genera al vuelo y no se guarda |
| T40 — Respaldo en S3 con Object Lock | **NO_APLICA** | — | el Modo L no ejecuta T40 (modos de la prueba: H); se ejecuta en H |
| T41 — Montaje NFS de almacenamiento | **NO_APLICA** | — | el Modo L no ejecuta T41 (modos de la prueba: H); se ejecuta en H |
| T42 — Hora NTS y DNS cifrado desde SVC01 | **NO_APLICA** | — | el Modo L no ejecuta T42 (modos de la prueba: H); se ejecuta en H |
| T43 — Actualización de reglas de seguridad | **NO_APLICA** | — | el Modo L no ejecuta T43 (modos de la prueba: H); se ejecuta en H |
| T44 — Peering entre nodos de borde | **PARCIAL** | — | medición vacía: el protocolo y el puerto del peering no están definidos (CI-06): solo se probó el alcance IP |
| T45 — Internet → zonas internas | **PASA** | puertos_open = 0, paquetes_denegados_por_fw01 = 30 |  |
| T46 — DMZ-SVC → zonas internas | **PASA** | puertos_open = 0, paquetes_denegados_por_fw01 = 22 | WEB01 se probó como equipo comprometido, sin su nftables de host: con él, WEB01 ya no puede iniciar conexiones (D1.9, «Salida») y no sería FW01 quien deniega |
| T47 — DMZ-HONEY → cualquier zona | **PASA** | puertos_open = 0, paquetes_denegados_por_fw01 = 20 | «Internet» es ext01 (198.51.100.100): el laboratorio no tiene DNS ni salida a Internet real |
| T48 — Cualquier zona → STORAGE | **NO_APLICA** | — | el Modo L no ejecuta T48 (modos de la prueba: A, H); se ejecuta en A y H |
| T49 — Renovación ACME desde WAF01 | **PASA** | — | el directorio ACME es un servidor de laboratorio en ext01 (no Let's Encrypt, no emite certificados) |

## Mediciones

- **Convergencia de la VPN (T05, OD-05):** 22.6 s desde que cae el túnel 1 hasta que el tráfico vuelve a pasar por el túnel 2 (interrupción visible 22.3 s). Meta de D1.10: ≤ 60 s. El hold de BGP (30 s) es solo un componente; el valor real es el medido.
- **Cambio de nodo del PAC (T09/OD-03):** 8.9 s con EDGE01 caído; 16.9 s hasta DIRECT con ambos caídos (cliente que imita al PAC con `curl`, no un navegador).
- **TLS del portal (T16, OD-08):** calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H)
- **Exposición (T15):** 2 puertos abiertos desde Internet; alertas de Suricata en fw01-sim durante el escaneo: 69.
- **Métricas (T27, REQ-NF-14):** paquetes HTTP en claro = 0, handshakes TLS = 2, apariciones del token = 0.

## Hallazgos (contradicen o precisan el diseño)

- T05 — tras la caída la ruta a 10.30.0.0/16 va por: vti2
- T08 — curl del laboratorio no soporta HTTP/3: `curl --http3` se sustituyó por una sonda UDP 443 (5 datagramas) hacia ext01
- T09 — el navegador es Chromium sin pantalla con --ignore-certificate-errors (la CA del nodo no está en su almacén); el cliente imitado con curl se conserva como control
- T11 — el puerto 23 de F24 no se prueba: OpenCanary no está en el laboratorio
- T12 — NAS01 es un equivalente funcional (F4.2): sshd, restic y un puerto 2049 que no es NFS; el origen CTRL01 no se emula (se usan LABCLI01 y OBS01)
- T16 — calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H)
- T22 — `nslookup` no está en la imagen: se usó kdig contra la IP de FW01 en la VLAN de LAB
- T24 — el resolvedor de prueba es ext01 (IP del laboratorio), no 203.0.113.53 (CI-19): la regla F7 bloquea por puerto, no por destino
- T26 — F9 (EDGE → EC2-SHIELD) se ejercita con REQ-F-29: los MISS salen del nodo hacia el shield por la VPN con mTLS; en la VPN solo se ve TLS, y por eso se mira también lo que llega al motor del shield ya descifrado
- T27 — el puerto 9128 solo acepta TLS (REQ-NF-14); el certificado es autofirmado de laboratorio: en producción F12 usa los de step-ca (F11)
- T28 — fw01-sim no es OPNsense y no tiene syslog nativo: el evento lo envía `socat` desde fw01-sim; lo que se prueba es el receptor de SIEM01 (solo TLS)
- T28 — escuchas UDP en el puerto 514 de SIEM01: 0
- T29 — las reglas del laboratorio son locales (sid 9000001, escaneo SYN por origen): ET Open no está disponible en el Modo L
- T29 — el destino es OBS01, el nodo de SERVERS que existe en el laboratorio y que ningún flujo alcanza desde LAB-TEST (SVC01 no sirve: F3 le abre el puerto 80)
- T30 — el canario registró 0 eventos con un barrido SYN (-sS) y 4 con uno de conexión completa (-sT): un canario de aplicación no ve los SYN sin respuesta; IDS01 no captura la VLAN 30 (D1.14)
- T30 — el canario es un equivalente funcional de OpenCanary (F4.2): registra la conexión en un archivo, sin enviarla a un agente de Wazuh
- T31 — la ruta señuelo del laboratorio es /admin-backup.zip [S-17]; en S2 se define con el equipo
- T32 — la decisión se agrega con `cscli decisions add` (la «simulación con su escenario de prueba» de D1.14): un escenario real exige logs de SSH o del WAF
- T32 — fw01-sim no es OPNsense: el aviso a Wazuh lo envía `socat` por el syslog TLS (F14); CrowdSec y su bouncer sí son los reales, en modo local sin nube
- T39 — NAS01 es un equivalente funcional (F4.2): sshd + restic; la clave del repositorio se genera al vuelo y no se guarda
- T46 — WEB01 se probó como equipo comprometido, sin su nftables de host: con él, WEB01 ya no puede iniciar conexiones (D1.9, «Salida») y no sería FW01 quien deniega
- T47 — «Internet» es ext01 (198.51.100.100): el laboratorio no tiene DNS ni salida a Internet real
- T49 — el directorio ACME es un servidor de laboratorio en ext01 (no Let's Encrypt, no emite certificados)

## Qué se emula y qué no (equivalencias de F4.2)

| En el diseño | En el laboratorio | Equivalencia |
| --- | --- | --- |
| FW01 OPNsense | `fw01-sim`: Debian + nftables (reglas generadas del inventario) + strongSwan + FRR + Suricata + Unbound | Funcional: mismas zonas, flujos, política por defecto, VPN y BGP. No es OPNsense (FreeBSD); no se prueban sus GUI, MFA ni CrowdSec |
| Port groups de ESXi, SW-CORE01 | Puentes Linux por VLAN (`br-vlanNN`), sin br-vlan70 ni br-vlan71 | Funcional. No hay trunk 802.1Q ni controles de capa 2 (RA guard, DHCP snooping, port-security) |
| VGW de AWS | `vgw-sim`: strongSwan + FRR con los mismos parámetros de fase 1/2 y BGP | Funcional, sin el servicio gestionado ni sus tablas de rutas, Security Groups o NACL |
| EC2-SHIELD | `shield01`: binario de `celeris-node` sobre la imagen base de laboratorio | Solo recibe tráfico de prueba directo (REQ-F-29 pendiente) |
| EDGE01/02 | `edge01`/`edge02`: el mismo binario que la imagen OCI de producción, sobre la imagen base de laboratorio (la imagen mínima no trae shell para configurar la red) | Mismo código; el contenedor final no es el de producción |
| WAF01 | `waf01`: nginx + ModSecurity v3 + OWASP CRS | Equivalente funcional; F4.2 dice Caddy + Coraza |
| WEB01 | `web01`: nginx con el aviso de `docs/AVISO.md` como sitio estático | Mismo producto de la familia; sitio generado, no firmado (REQ-F-30 pendiente) |
| HNY01 | `hny01` + Cowrie oficial (SSH, puerto 2222) | Cowrie sí; OpenCanary y el puerto 23 de F24 no |
| HNY02 | `hny02`: canario propio en Python (puertos 22, 80, 445, 3389) | Equivalente funcional; no es OpenCanary |
| IDS01 | `ids01`: Suricata 7 con 4 interfaces de captura (VLAN 10, 20, 31, 50) y espejo de puertos con `tc mirred` | Funcional, con reglas locales mínimas (sin ET Open: el laboratorio no tiene Internet) |
| SIEM01 Wazuh | No desplegado | Sin SIEM: las comprobaciones de alertas de Wazuh no se evalúan |
| Certificado público del portal | Certificado de una CA de laboratorio (se genera en `lab/.run/pki`, fuera de git) | El ACME real y la calificación con CA pública se prueban en Modo A o H |
| ESX01, IPMI01, UPS01, BRK01, NAS01, CTRL01, DB01, PROBE01, EC2-CTRLR, NAT01 | No existen en el laboratorio (F4.1) | Sus pruebas se ejecutan en Modo H (CI-16, CI-24) |

## Limitaciones

- Las IP son las del inventario, salvo la WAN (198.51.100.0/24, F4.1), el nombre del portal y los dominios de prueba (CI-24).
- `curl` de la imagen no soporta HTTP/3: T08 usa datagramas UDP 443 en lugar de `curl --http3`.
- T09 y T22 imitan la lógica del PAC con `curl`; el cambio real de un navegador se mide en Modo H.
- Los comandos de `infra/pruebas.yaml` son la referencia; el runner ejecuta su equivalente en los nodos del laboratorio (ver `evidencias/<fecha>-L/<T-xx>/salida.txt`).
- Las evidencias (pcap, registros, salidas) están en `evidencias/<fecha>-L/`, fuera de git: pueden contener el token de laboratorio. `resultados.json` y `junit.xml` sí se versionan.

## Reproducir

```bash
make lab-up      # genera, construye y despliega (Docker + containerlab en Linux/WSL)
make test-lab    # ejecuta T05–T28 en Modo L y reescribe este archivo
make lab-down
```
