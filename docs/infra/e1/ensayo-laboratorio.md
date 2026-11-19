# Ensayo en el laboratorio emulado (Modo L)

> Generado por `make test-lab` (`tests/network/run.py`). No editar a mano.

> **El laboratorio es emulado** (Parte F4.2 del documento maestro). Lo que pasa aquí demuestra que el *diseño* se comporta como está descrito en una emulación funcional; no es la validación del producto real (OPNsense, VGW de AWS) ni del campus.

- Fecha: 2026-11-19 · commit: `19124d4646d1`
- Resultado: **12 PASA**, **1 FALLA**, **6 PARCIAL**, **9 NO_APLICA** (de 28 pruebas T01–T28)
- `PARCIAL` = parte de los criterios no se pudo evaluar en el Modo L (navegador real, Wazuh…) o la medición no ejercitó lo que la prueba valida. **No cuenta como PASA.**
- `NO_APLICA` = la prueba no se puede ejecutar en L; se indica el modo en que sí se ejecutará. **Nunca cuenta como PASA.**

## Resultados

| Prueba | Resultado | Medido | Motivo o nota |
| --- | --- | --- | --- |
| T01 — ON-PREM → AWS | **NO_APLICA** | — | el Modo L no ejecuta T01 (modos de la prueba: A, H); se ejecuta en A y H |
| T02 — AWS → ON-PREM | **NO_APLICA** | — | el Modo L no ejecuta T02 (modos de la prueba: A, H); se ejecuta en A y H |
| T03 — DMZ → AWS | **NO_APLICA** | — | el Modo L no ejecuta T03 (modos de la prueba: A, H); se ejecuta en A y H |
| T04 — Internet → subred privada AWS | **NO_APLICA** | — | el Modo L no ejecuta T04 (modos de la prueba: A, H); se ejecuta en A y H |
| T05 — Falla de un túnel | **PASA** | convergencia_s = 23.1, interrupcion_s = 22.8 | tras la caída la ruta a 10.30.0.0/16 va por: vti2 |
| T06 — LAB → MGMT | **PASA** | puertos_open = 0, paquetes_denegados_por_fw01 = 666 |  |
| T07 — LAB → EDGE 3128 | **FALLA** | x_celeris_cache_primera = 1 | /(?im)^cache-status:/ sobre stdout: no coincide |
| T08 — LAB → UDP 443 | **PARCIAL** | paquetes_bloqueados_regla_F7 = 5, datagramas_recibidos_en_ext01 = 0 | sin evaluar: El navegador carga la página por HTTP/2 sobre TCP (requiere un navegador real con QUIC activado (Modo H)) |
| T09 — Caída de EDGE01 | **PARCIAL** | tiempo_de_cambio_s = 2.2, tiempo_hasta_direct_s = 4.2 | sin evaluar: Con EDGE01 apagado la navegación continúa por EDGE02 (registro de acceso de EDGE02) (requiere navegar con un navegador real (Modo H); aquí se imita la lógic… |
| T10 — DMZ → LAN | **PASA** | — |  |
| T11 — Internet → DMZ-HONEY | **PARCIAL** | conexiones_en_cowrie = 6 | sin evaluar: /"level":\s*(1[0-9]\|[2-9][0-9])/ sobre alerta_wazuh (Wazuh (siem01) no está desplegado en el laboratorio: la alerta del SIEM no se puede evaluar en el Modo… |
| T12 — STORAGE no enrutada | **NO_APLICA** | — | NAS01 y la VLAN 70 no se emulan (F4.1 no tiene br-vlan70, CI-16): que 10.20.70.20 no responda no demuestra que la VLAN no tenga ruta; se ejecuta en Modo H |
| T13 — Abuso del proxy | **PASA** | — |  |
| T14 — Puerto no permitido | **PASA** | — |  |
| T15 — Exposición del portal | **PASA** | puertos_abiertos = 2, alertas_suricata_fw01 = 69 |  |
| T16 — TLS del portal | **PASA** | — | calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H) |
| T17 — Escaneo web | **PASA** | alertas_altas = 0 |  |
| T18 — WAF | **PARCIAL** | eventos_modsecurity = 5 | sin evaluar: /"level":\s*(1[0-9]\|[2-9][0-9])/ sobre alerta_wazuh (Wazuh (siem01) no está desplegado en el laboratorio: la alerta del SIEM no se puede evaluar en el Modo… |
| T19 — Salida del portal | **PASA** | — |  |
| T20 — Aislamiento del señuelo | **PASA** | — |  |
| T21 — MTU del túnel | **NO_APLICA** | — | el Modo L no ejecuta T21 (modos de la prueba: A, H); se ejecuta en A y H |
| T22 — Caída de SVC01 | **PARCIAL** | — | sin evaluar: La navegación del usuario continúa sin intervención (requiere comprobar la navegación del usuario con un navegador real (Modo H)) |
| T23 — Fuga IPv6 | **NO_APLICA** | — | RA guard es un control del switch de acceso (SW-ACC, S-14); los puentes Linux del laboratorio no lo emulan; se ejecuta en Modo H |
| T24 — DNS cifrado | **PASA** | paquetes_bloqueados_regla_F7 = 3 | el resolvedor de prueba es ext01 (IP del laboratorio), no 203.0.113.53 (CI-19): la regla F7 bloquea por puerto, no por destino |
| T25 — Break-glass | **NO_APLICA** | — | ESX01, IPMI01, BRK01 y SW-CORE01 no se emulan: el puerto break-glass no existe en F4.1 (CI-16); se ejecuta en Modo H |
| T26 — Privacidad del túnel | **PARCIAL** | paquetes_en_la_vpn = 10 | medición vacía: durante el MISS no cruzó nada por la VPN: el nodo no tiene ruta al shield (REQ-F-29 pendiente), así que la ausencia de cabeceras no demuestra nada |
| T27 — Métricas cifradas | **PASA** | esquema_https = 1, respuestas_http_en_claro_del_servidor = 0, paquetes_http_en_claro = 0,… | el puerto 9128 solo acepta TLS (REQ-NF-14); el certificado es autofirmado de laboratorio: en producción F12 usa los de step-ca (F11) |
| T28 — Syslog cifrado | **NO_APLICA** | — | siem01 (Wazuh) no está desplegado y fw01-sim no tiene syslog sobre TLS configurado: no hay flujo F14 que capturar; se ejecuta en Modo H |

## Mediciones

- **Convergencia de la VPN (T05, OD-05):** 23.1 s desde que cae el túnel 1 hasta que el tráfico vuelve a pasar por el túnel 2 (interrupción visible 22.8 s). Meta de D1.10: ≤ 60 s. El hold de BGP (30 s) es solo un componente; el valor real es el medido.
- **Cambio de nodo del PAC (T09/OD-03):** 2.2 s con EDGE01 caído; 4.2 s hasta DIRECT con ambos caídos (cliente que imita al PAC con `curl`, no un navegador).
- **TLS del portal (T16, OD-08):** calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H)
- **Exposición (T15):** 2 puertos abiertos desde Internet; alertas de Suricata en fw01-sim durante el escaneo: 69.
- **Métricas (T27, REQ-NF-14):** paquetes HTTP en claro = 0, handshakes TLS = 2, apariciones del token = 0.

## Hallazgos (contradicen o precisan el diseño)

- **T07 FALLA** — /(?im)^cache-status:/ sobre stdout: no coincide (el nodo responde X-Celeris-Cache (MISS, HIT) pero no la cabecera estándar Cache-Status (RFC 9211) que pide D1.16 (REQ-NF-11))
- T05 — tras la caída la ruta a 10.30.0.0/16 va por: vti2
- T08 — curl del laboratorio no soporta HTTP/3: `curl --http3` se sustituyó por una sonda UDP 443 (5 datagramas) hacia ext01
- T11 — el puerto 23 de F24 no se prueba: OpenCanary no está en el laboratorio
- T16 — calificación de testssl.sh: A+ (certificado de la CA de laboratorio; el ACME público se prueba en Modo H)
- T22 — `nslookup` no está en la imagen: se usó kdig contra la IP de FW01 en la VLAN de LAB
- T24 — el resolvedor de prueba es ext01 (IP del laboratorio), no 203.0.113.53 (CI-19): la regla F7 bloquea por puerto, no por destino
- T26 — F9 (EDGE → EC2-SHIELD) no se ejercita en un MISS real hasta que exista REQ-F-29; REQ-F-28 se prueba en e2e (Etapa 5)
- T27 — el puerto 9128 solo acepta TLS (REQ-NF-14); el certificado es autofirmado de laboratorio: en producción F12 usa los de step-ca (F11)

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
