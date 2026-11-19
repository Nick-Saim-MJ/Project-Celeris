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

Requiere Linux con Docker y containerlab (en Windows, WSL2). Si falta alguno, `lab.sh` se detiene con un mensaje; no simula nada.
Los nodos se llaman `clab-celeris-<nodo>` (`docker exec clab-celeris-labcli01 …`).
