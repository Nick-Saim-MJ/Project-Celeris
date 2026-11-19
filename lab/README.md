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

## Qué contiene (todo emulado)

| Nodo | Qué es |
| --- | --- |
| `fw01-sim`, `vgw-sim` | FW01 (nftables, Suricata, Unbound) y el VGW de AWS (strongSwan + FRR); `vgw-sim` también hace NAT de la VPC, como NAT01 |
| `shield01` | EC2-SHIELD: `celeris-cache` en modo shield, con mTLS en el puerto 8443 (F9) |
| `edge01`, `edge02` | Nodos de caché: envían los MISS al shield con mTLS (REQ-F-29), generan el PAC (REQ-F-26) y tienen una honey-URL (REQ-F-27) |
| `siem01` + `siem01-wazuh` | Wazuh manager 4.9.2 (imagen fijada por digest) con su receptor de syslog por TLS en 6514 (F14); las reglas son las de `siem/wazuh/local_rules.xml` |
| `nas01` | NAS01 con STORAGE (VLAN 70), BACKUP (VLAN 71) y MGMT: sshd + restic y un puerto 2049 que no es NFS |
| `obs01`, `svc01`, `waf01`, `web01`, `hny01`, `hny02`, `ids01` | Con agente de Wazuh, que se enrola solo al arrancar (F13) |
| `labcli01`, `kali01`, `jmp01`, `ext01` | Clientes de prueba (LABCLI01 con Chromium sin pantalla), administración y «Internet» |

No se emulan ESX01, IPMI01, SW-CORE01, UPS01 ni BRK01 (CI-16), ni CrowdSec, NTS, S3 ni PostgreSQL: esas pruebas son del Modo H (CI-28).

## Docker Desktop

Si Docker Desktop tiene activada la integración con WSL, `/var/run/docker.sock` es el de Docker Desktop y containerlab falla con «Failed to lookup link br-…».
Ejecute una sola vez, como root, `sh lab/docker-nativo.sh`: agrega un socket al `dockerd` de la distribución y `lab/docker-env.sh` lo usa solo cuando detecta Docker Desktop.
`lab/entorno.sh` avisa si hace falta. No se toca Docker Desktop ni sus contenedores.

## Desde un clon limpio

`make lab-up` genera la topología y los certificados (en `lab/.run/`, fuera de git), construye las imágenes que falten, descarga la imagen del manager de Wazuh, crea los puentes,
despliega y espera a que el manager y todos los agentes estén activos (unos 6 minutos la primera vez). Las llaves, certificados y la clave de restic son de laboratorio y se generan en cada
equipo; no hay secretos en el repositorio. Si cambia `lab/images/base/Dockerfile`, borre la imagen (`docker rmi celeris-lab/base:dev`) para que se reconstruya.

Requiere Linux con Docker y containerlab (en Windows, WSL2). Si falta alguno, `lab.sh` se detiene con un mensaje; no simula nada.
Los nodos se llaman `clab-celeris-<nodo>` (`docker exec clab-celeris-labcli01 …`).
