"""Configuración de la VPN híbrida EMULADA (strongSwan + FRR) para fw01-sim y vgw-sim, desde la sección `vpn`.

fw01-sim emula a FW01 (OPNsense/strongSwan) y vgw-sim al VGW de AWS (sin el servicio gestionado, F4.2).
Salidas por lado ('fw01' | 'vgw'): swanctl.conf, frr.conf y vti-up.sh (interfaces de túnel, MTU).

Lo que el inventario no fija y se decide aquí (CI-23):
  * la IP pública de los dos extremos AWS (D1.10: «asignadas por AWS») llega por parámetro;
  * en cada /30 de túnel, el primer host es el extremo AWS y el segundo el del campus (convención de AWS);
  * el AS-path prepending del túnel 2 es de una repetición del ASN (el mínimo que invierte la preferencia);
  * la interfaz es un VTI del kernel (D1.10: «route-based con interfaces VTI»); su clave y la marca de strongSwan son el número de túnel (VTI1 → 1).
    El kernel de WSL2 no trae interfaces XFRM (`ip link add type xfrm`), pero sí VTI.
La llave precompartida NO está en estos archivos: se genera al vuelo y se escribe aparte (ver `escribir_psk`).
"""
from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import Infra  # noqa: E402
from gen.comun import cabecera, escribir, nombre_kernel, psk_de_laboratorio  # noqa: E402

CIFRADOS = {"AES-256-GCM-16": "aes256gcm16"}
PRF = {"SHA2-384": "prfsha384"}
GRUPOS_DH = {20: "ecp384"}


def _dh(texto: str) -> str:
    n = int(re.search(r"grupo\s+(\d+)", texto).group(1))
    if n not in GRUPOS_DH:
        raise ValueError(f"grupo DH {n} sin equivalente strongSwan en gen/vpn.py")
    return GRUPOS_DH[n]


def _mapa(tabla: dict, valor: str, que: str) -> str:
    if valor not in tabla:
        raise ValueError(f"{que} «{valor}» del inventario no tiene equivalente en gen/vpn.py; agréguelo conscientemente")
    return tabla[valor]


def propuestas(x: Infra) -> tuple[str, str]:
    """(ike, esp) en notación strongSwan, derivadas de fase1/fase2."""
    f1, f2 = x.inv["vpn"]["fase1"], x.inv["vpn"]["fase2"]
    ike = f'{_mapa(CIFRADOS, f1["cifrado"], "cifrado fase 1")}-{_mapa(PRF, f1["prf"], "PRF")}-{_dh(f1["dh"])}'
    esp = f'{_mapa(CIFRADOS, f2["cifrado"], "cifrado fase 2")}-{_dh(f2["pfs"])}'
    return ike, esp


def _hosts(red: str) -> tuple[str, str]:
    h = list(ipaddress.ip_network(red).hosts())
    return str(h[0]), str(h[1])     # (extremo AWS, extremo del campus)


def tuneles(x: Infra) -> list[dict]:
    out = []
    for n, t in enumerate(x.inv["vpn"]["tuneles"], start=1):
        aws, campus = _hosts(t["red_interna"])
        out.append({"n": n, "id": t["id"], "nombre": f"tunel{n}", "rol": t["rol"], "red": t["red_interna"],
                    "ip_aws": aws, "ip_campus": campus, "iface": nombre_kernel(t["id"]),
                    "prepend": bool(t.get("bgp_as_path_prepending"))})
    return out


def _extremos(x: Infra, lado: str, aws_peers: list[str], wan_campus: str | None):
    v = x.inv["vpn"]
    wan = wan_campus or v["extremo_onpremise"]["ip_publica"]
    if len(aws_peers) != len(v["tuneles"]):
        raise ValueError(f"se esperaban {len(v['tuneles'])} IP públicas de AWS, llegaron {len(aws_peers)}")
    return wan


def swanctl(x: Infra, lado: str, aws_peers: list[str], wan_campus: str | None = None) -> str:
    """swanctl.conf del lado 'fw01' (inicia) o 'vgw' (responde). Sin secretos: `include` del archivo de llaves."""
    assert lado in ("fw01", "vgw")
    v = x.inv["vpn"]
    wan = _extremos(x, lado, aws_peers, wan_campus)
    ike, esp = propuestas(x)
    L = [cabecera("#").rstrip(), f"# lado={lado} (emula {'FW01 OPNsense' if lado == 'fw01' else 'el VGW de AWS'})", "connections {"]
    for t, peer in zip(tuneles(x), aws_peers):
        local, remote = (wan, peer) if lado == "fw01" else (peer, wan)
        # D1.10 v0.4: FW01 está detrás del FortiGate. Escucha en su IP interna (tránsito), se identifica con la IP pública (NAT 1:1) y usa NAT-T (UDP 4500).
        interna = v["extremo_onpremise"]["ip_interna"] if v["extremo_onpremise"].get("nat_t") else wan
        local_addr = interna if lado == "fw01" else local
        L += [f"  {t['nombre']} {{",
              "    version = 2",
              f"    local_addrs = {local_addr}",
              f"    remote_addrs = {remote}",
              f"    encap = {'yes' if v['extremo_onpremise'].get('nat_t') else 'no'}",
              f"    proposals = {ike}",
              f"    dpd_delay = {v['dpd']['intervalo_s']}s",
              f"    rekey_time = {v['fase1']['vida_s']}s",
              "    local {", "      auth = psk", f"      id = {local}", "    }",
              "    remote {", "      auth = psk", f"      id = {remote}", "    }",
              "    children {", f"      {t['nombre']} {{",
              "        local_ts = 0.0.0.0/0", "        remote_ts = 0.0.0.0/0",
              f"        esp_proposals = {esp}",
              f"        life_time = {v['fase2']['vida_s']}s",
              "        mode = tunnel",
              f"        mark_in = {t['n']}", f"        mark_out = {t['n']}",
              f"        dpd_action = {v['dpd']['accion']}",
              f"        start_action = {'start' if lado == 'fw01' else 'none'}",
              "      }", "    }", "  }"]
    L += ["}", "", f"include psk-{lado}.conf", ""]
    return "\n".join(L)


def frr(x: Infra, lado: str) -> str:
    assert lado in ("fw01", "vgw")
    v = x.inv["vpn"]
    mio = v["extremo_onpremise"] if lado == "fw01" else v["extremo_aws"]
    otro = v["extremo_aws"] if lado == "fw01" else v["extremo_onpremise"]
    redes = mio["redes_anunciadas"]
    ts = tuneles(x)
    vecino = lambda t: t["ip_aws"] if lado == "fw01" else t["ip_campus"]  # noqa: E731
    router_id = ts[0]["ip_campus"] if lado == "fw01" else ts[0]["ip_aws"]
    k, h = v["bgp"]["keepalive_s"], v["bgp"]["hold_s"]
    L = [cabecera("!").rstrip(), "frr defaults traditional", f"hostname {'fw01-sim' if lado == 'fw01' else 'vgw-sim'}",
         "log stdout", "!"] + [f"ip route {r} Null0" for r in redes] + ["!", f"router bgp {mio['asn']}", f" bgp router-id {router_id}", " no bgp ebgp-requires-policy"]
    for t in ts:
        L += [f" neighbor {vecino(t)} remote-as {otro['asn']}", f" neighbor {vecino(t)} timers {k} {h}",
              f" neighbor {vecino(t)} description {t['nombre']}-{t['rol']}"]
    # D1.10: el VGW usa un solo túnel a la vez y no reparte tráfico (sin ECMP): maximum-paths 1 en ambos extremos
    L += [" !", " address-family ipv4 unicast", "  maximum-paths 1"]
    L += [f"  network {r}" for r in redes]
    for t in ts:
        L.append(f"  neighbor {vecino(t)} activate")
        if lado == "fw01" and t["prepend"]:
            L.append(f"  neighbor {vecino(t)} route-map PREPEND-{t['nombre'].upper()} out")
    L += [" exit-address-family", "!"]
    if lado == "fw01":
        for t in ts:
            if t["prepend"]:
                L += [f"route-map PREPEND-{t['nombre'].upper()} permit 10", f" set as-path prepend {mio['asn']}", "!"]
    L += ["line vty", "!", ""]
    return "\n".join(L)


def strongswan_conf() -> str:
    """strongswan.conf mínimo: con VTI las rutas las pone BGP (FRR), no charon."""
    # kernel-libipsec (IPsec en espacio de usuario) crea la interfaz ipsec0 y desvía el tráfico IKE; forecast no aplica: se usa XFRM del kernel.
    # bypass-lan instala políticas de exclusión para las redes conectadas, incluidos los /30 de los túneles: el tráfico BGP no entraría al túnel.
    return (cabecera("#") + "charon {\n  install_routes = no\n  plugins {\n    kernel-libipsec { load = no }\n    forecast { load = no }\n"
            "    bypass-lan { load = no }\n  }\n}\n")


def vti_up(x: Infra, lado: str, aws_peers: list[str], wan_campus: str | None = None) -> str:
    """Script que crea las interfaces VTI (route-based), fija MTU, direcciones de los /30 y desactiva la política xfrm en ellas."""
    v = x.inv["vpn"]
    wan = _extremos(x, lado, aws_peers, wan_campus)
    L = ["#!/bin/sh", cabecera("#").rstrip(), "set -eu"]
    for t, peer in zip(tuneles(x), aws_peers):
        ip = t["ip_campus"] if lado == "fw01" else t["ip_aws"]
        local, remote = (wan, peer) if lado == "fw01" else (peer, wan)
        if lado == "fw01" and v["extremo_onpremise"].get("nat_t"):
            local = v["extremo_onpremise"]["ip_interna"]         # detrás del NAT 1:1: el VTI usa la IP de la WAN de FW01 (tránsito)
        mask = ipaddress.ip_network(t["red"]).prefixlen
        L += [f"ip tunnel add {t['iface']} mode vti local {local} remote {remote} key {t['n']}",
              f"ip addr add {ip}/{mask} dev {t['iface']}",
              f"ip link set {t['iface']} mtu {v['mtu']} up",
              f"sysctl -qw net.ipv4.conf.{t['iface']}.disable_policy=1 net.ipv4.conf.{t['iface']}.rp_filter=0"]
    return "\n".join(L) + "\n"


def escribir_psk(salida: Path, x: Infra, aws_peers: list[str], wan_campus: str | None = None) -> list[Path]:
    """Escribe psk-fw01.conf y psk-vgw.conf con la MISMA llave de laboratorio, aleatoria, fuera del control de versiones."""
    wan = _extremos(x, "fw01", aws_peers, wan_campus)
    llaves = {t["nombre"]: psk_de_laboratorio() for t in tuneles(x)}
    rutas = []
    for lado in ("fw01", "vgw"):
        L = ["secrets {"]
        for t, peer in zip(tuneles(x), aws_peers):
            local, remoto = (wan, peer) if lado == "fw01" else (peer, wan)
            # Dos identidades por secreto (local y remota): en el lado AWS el remoto es el mismo campus para los dos túneles
            # y con una sola identidad strongSwan no sabría cuál de las dos llaves usar.
            L += [f"  ike-{t['nombre']} {{", f"    id-1 = {local}", f"    id-2 = {remoto}", f'    secret = "{llaves[t["nombre"]]}"', "  }"]
        L += ["}", ""]
        ruta = salida / f"psk-{lado}.conf"
        escribir(ruta, "\n".join(L), modo=0o600)
        rutas.append(ruta)
    return rutas


def main(x: Infra, salida: Path, aws_peers: list[str], wan_campus: str | None = None, secretos: Path | None = None) -> list[Path]:
    rutas = []
    for lado in ("fw01", "vgw"):
        d = salida / lado
        escribir(d / "swanctl.conf", swanctl(x, lado, aws_peers, wan_campus))
        escribir(d / "frr.conf", frr(x, lado))
        escribir(d / "vti-up.sh", vti_up(x, lado, aws_peers, wan_campus), modo=0o755)
        escribir(d / "strongswan.conf", strongswan_conf())
        rutas += [d / "swanctl.conf", d / "frr.conf", d / "vti-up.sh", d / "strongswan.conf"]
    rutas += escribir_psk(secretos or (salida / ".secretos"), x, aws_peers, wan_campus)
    return rutas
