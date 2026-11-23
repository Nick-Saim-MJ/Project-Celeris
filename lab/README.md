# Laboratorio emulado (Modo L, Parte F4)

Demostración previa del diseño de red de CE0311 con containerlab. **Todo es emulado**: `fw01-sim` no es OPNsense y `vgw-sim` no es el
VGW de AWS (equivalencias en F4.2 y en `docs/infra/e1/ensayo-laboratorio.md`). Las IP son las del inventario.

| Archivo | Qué es |
| --- | --- |
| `celeris.clab.yml` | Topología. **Generada** por `make lab-gen` desde `infra/inventory.yaml`; no se edita a mano |
| `generated/` | Configuración de cada nodo (nftables, swanctl, FRR, Unbound, nginx…). Generada, fuera de git |
| `.run/` | CA y certificados de laboratorio y llaves precompartidas aleatorias. Fuera de git, nunca se suben |
| `images/base` | Imagen con las herramientas de todos los nodos (strongSwan, FRR, Suricata, nginx + ModSecurity, nmap…) |
| `images/node` | Esa imagen + el binario de `celeris-node` (misma compilación que `deploy/image`) |
| `lab.sh` | `up`, `down` y `estado` |
| `entorno.sh` | Comprueba Docker, containerlab, cargo, tofu y nftables |

```bash
make lab-up      # genera, construye las imágenes que falten, crea los puentes y despliega
make lab-down    # destruye los contenedores y los puentes
bash lab/lab.sh estado
```

## Qué contiene (todo emulado, v0.4 según CE03 D5.3)

| Nodo | Qué es |
| --- | --- |
| `fw01-sim` | FW01: nftables generado del inventario, strongSwan + FRR (VPN con NAT-T), Suricata IDS en LAB y SERVERS, Unbound con DNSSEC, NTP y CrowdSec. Su WAN es la red de tránsito 10.20.0.0/29 |
| `fgt-sim` | FortiGate emulado: NAT 1:1 de la IP pública del laboratorio (198.51.100.10 en lugar de 203.0.113.10) hacia 10.20.0.2 solo para UDP 500/4500 y TCP 80/443, y ruta al Wi-Fi. Sin FortiGuard ni inspección SSL |
| `byod01` | Equipo personal en el Wi-Fi de estudiantes (`br-wifi`, 172.16.0.0/16); solo alcanza EDGE y el portal (F31, F32) |
| `vgw-sim`, `gw-sim` | El VGW de AWS (strongSwan + FRR, y NAT/IGW de la VPC) y EC2-GW (nginx + ModSecurity que reenvía a `ctrl01:443` con certificado de cliente, F29/F30) |
| `ctrl01` | Consola de prueba en 443: marca las sesiones `campus` o `remoto` y rechaza con 403 las acciones críticas remotas (REQ-F-37). No es la consola de CE02 |
| `edge01`, `edge02` | Nodos de caché: generan el PAC (REQ-F-26) y lo sirven, tienen una honey-URL (REQ-F-27) y aceptan solo los rangos /26 habilitados |
| `portal01` | PORTAL01: WAF (nginx + ModSecurity + CRS) y sitio estático en una sola VM |
| `siem01` + `siem01-wazuh` | Wazuh manager 4.9.2 (imagen fijada por digest) con su receptor de syslog por TLS en 6514 (F14); las reglas son las de `siem/wazuh/local_rules.xml` |
| `hny01`, `hny02`, `ctrl01`, `edge01`, `edge02`, `portal01`, `gw-sim` | Con agente de Wazuh, que se enrola solo al arrancar (F13) |
| `labcli01`, `labcli02`, `labcli03`, `enc01`, `kali01`, `jmp01` | Clientes de prueba: LABCLI01 con Chromium; `labcli02` en LAB-01 y `labcli03` en LAB-03 (T52); ENC01, KALI01 y administración |
| `ext01`, `origin-sim` | «Internet»: atacante externo y origen web, y origen con archivos de 100 MB a 1 GB |

Ya no existen `svc01`, `obs01`, `ids01`, `nas01`, `probe01`, `shield01`, `waf01` ni `web01`, ni las VLAN 31, 70 y 71 (CI-39). Los parámetros que el inventario no fija están en CI-48.
`make lab-up` necesita permisos de root para crear los puentes (en WSL: `wsl -u root`).

No se emulan ESX01, IPMI01, SW-CORE01, UPS01 ni BRK01 (CI-16), ni NTS, S3 ni PostgreSQL: esas pruebas son del Modo H.

## Docker Desktop

Si Docker Desktop tiene activada la integración con WSL, `/var/run/docker.sock` es el de Docker Desktop y containerlab falla con «Failed to lookup link br-…».
Ejecute una sola vez, como root, `sh lab/docker-nativo.sh`: agrega un socket al `dockerd` de la distribución y `lab/docker-env.sh` lo usa solo cuando detecta Docker Desktop.
`lab/entorno.sh` avisa si hace falta. No se toca Docker Desktop ni sus contenedores.

## Desde un clon limpio

`make lab-up` genera la topología y los certificados (en `lab/.run/`, fuera de git), construye las imágenes que falten, descarga la imagen del manager de Wazuh, crea los puentes,
despliega y espera a que el manager y todos los agentes estén activos (unos 6 minutos la primera vez). Las llaves y certificados son de laboratorio y se generan en cada
equipo; no hay secretos en el repositorio. Si cambia `lab/images/base/Dockerfile`, borre la imagen (`docker rmi celeris-lab/base:dev`) para que se reconstruya.

Requiere Linux con Docker y containerlab (en Windows, WSL2). Si falta alguno, `lab.sh` se detiene con un mensaje; no simula nada.
Los nodos se llaman `clab-celeris-<nodo>` (`docker exec clab-celeris-labcli01 …`).
