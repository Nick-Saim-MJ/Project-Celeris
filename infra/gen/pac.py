"""wpad.dat generado desde el inventario (REQ-F-26: PAC con varios nodos y DIRECT de respaldo).

PROXY EDGE01; PROXY EDGE02; DIRECT, con las redes internas (supernets del inventario) y el propio nombre del PAC
excluidos (DIRECT). El puerto es el de F1. Los nodos y sus IP salen de F1 (destino) y de los componentes.
"""
from __future__ import annotations

import ipaddress
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import Infra  # noqa: E402
from gen.comun import cabecera, escribir  # noqa: E402


def nodos_proxy(x: Infra) -> list[tuple[str, str, int]]:
    """(componente, ip, puerto) de los destinos de F1, en el orden en que F1 los lista."""
    f1 = x.flujos["F1"]
    puertos = [p for pr in f1["protocolos"] for p in pr["puertos"]]
    if len(puertos) != 1:
        raise ValueError("F1 debe tener un único puerto de proxy")
    out = []
    for crudo in f1["destino"]:
        comp = x.componentes[crudo]
        out.append((comp["id"], comp["ips"][0]["ip"], puertos[0]))
    return out


def redes_internas(x: Infra) -> list[ipaddress.IPv4Network]:
    """Supernets que no salen por el proxy: la sede, el resumen del campus y la VPC (DIRECT, sin caché)."""
    redes = {ipaddress.ip_network(s["cidr"]) for s in x.inv["supernets"]}
    # se conserva el resumen y se quitan las redes contenidas en otra, para que el PAC sea corto
    return sorted((r for r in redes if not any(r != o and r.subnet_of(o) for o in redes)), key=lambda n: (int(n.network_address), n.prefixlen))


def generar(x: Infra) -> str:
    nodos = nodos_proxy(x)
    cadena = "; ".join(f"PROXY {ip}:{pt}" for _, ip, pt in nodos) + "; DIRECT"
    pac_host = x.inv["servicios_base"]["pac"]["url"].split("/")[2]
    excl = "\n".join(
        f'  if (isInNet(host, "{n.network_address}", "{n.netmask}")) return "DIRECT";' for n in redes_internas(x))
    return f"""{cabecera("//").rstrip()}
// REQ-F-26 · F1 (proxy explícito) · D-05: PAC por URL fija; sin autodescubrimiento.
// Nodos: {", ".join(c for c, _, _ in nodos)}. Si ambos caen, el navegador usa DIRECT (F6, solo piloto).
function FindProxyForURL(url, host) {{
  if (isPlainHostName(host) || host === "localhost" || host === "{pac_host}") return "DIRECT";
  if (isInNet(host, "127.0.0.0", "255.0.0.0")) return "DIRECT";
{excl}
  return "{cadena}";
}}
"""


def main(x: Infra, salida: Path) -> Path:
    ruta = salida / "wpad.dat"
    escribir(ruta, generar(x))
    return ruta
