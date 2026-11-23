"""Utilidades comunes de los generadores."""
from __future__ import annotations

import ipaddress
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import Infra  # noqa: E402

CABECERA = "GENERADO por infra/gen desde infra/inventory.yaml — no editar a mano. EMULADO (Modo L, Parte F4.2): no es el producto real."


def cabecera(comentario: str = "#") -> str:
    return f"{comentario} {CABECERA}\n"


def fw01_interfaces(x: Infra) -> dict[str, dict]:
    """zona → {interfaz, ip} de FW01 (el inventario nombra las interfaces: wan, vlan10, …)."""
    # v0.4: la WAN de FW01 está en la red de tránsito (TRANSITO, 10.20.0.2); los generadores la llaman «PERIMETRO» como antes
    return {("PERIMETRO" if i["interfaz"] == "wan" else i["zona"]): {"interfaz": i["interfaz"], "ip": i["ip"]} for i in x.componentes["FW01"]["ips"]}


def ip_de(x: Infra, extremo) -> str | None:
    """IP o CIDR de un extremo resuelto. Zona → su CIDR (None para INTERNET/PERIMETRO); componente → su IP."""
    if extremo.tipo == "zona":
        return x.zonas[extremo.zona]["cidr"]
    comp = x.componentes[extremo.componente]
    ips = [i for i in comp["ips"] if i["ip"] and (extremo.interfaz is None or i["interfaz"] == extremo.interfaz)]
    ips = [i for i in ips if i["zona"] == extremo.zona]
    if len(ips) != 1:
        raise ValueError(f"{extremo.crudo}: no se pudo fijar una IP única ({len(ips)} candidatas)")
    return ips[0]["ip"]


def clave_red(valor: str):
    n = ipaddress.ip_network(valor, strict=False)
    return (int(n.network_address), n.prefixlen)


def conjunto(valores) -> str:
    """Conjunto nft ordenado y sin repetidos; un solo valor va sin llaves."""
    vs = sorted(set(valores), key=clave_red)
    return vs[0] if len(vs) == 1 else "{ " + ", ".join(vs) + " }"


def nombre_kernel(componente_id: str) -> str:
    """Nombre de la interfaz de túnel en el kernel: el ID del componente en minúsculas (VTI1 → vti1)."""
    return componente_id.lower()


def escribir(ruta: Path, texto: str, modo: int | None = None) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")
    if modo is not None:
        try:
            os.chmod(ruta, modo)
        except OSError:
            pass


def psk_de_laboratorio() -> str:
    """Llave precompartida de laboratorio, generada al vuelo. Nunca se guarda en el repositorio."""
    return secrets.token_urlsafe(32)
