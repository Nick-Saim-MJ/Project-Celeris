"""Ruleset nftables de fw01-sim (firewall EMULADO del Modo L) generado desde infra/inventory.yaml.

Reglas de generación (D1.13, F4.2):
  * política `drop` en input, forward y output; registro (log + contador) de cada denegación;
  * una regla `accept` por cada flujo F-nn permitido que cruza zonas, con el `regla_fw` del flujo como comentario;
  * los flujos bloqueados (F7) llevan reglas `drop` explícitas, colocadas antes de las de `accept`;
  * los flujos dentro de una misma VLAN (F15, F22) no pasan por el firewall: se anotan como comentario;
  * `piloto` incluye F6 (DIRECT fail-open); `gestionado` lo omite; F24 (señuelo) solo con `ventana=True`;
  * lo que NO es un flujo F-nn (NAT de salida, IKE/ESP/BGP de la VPN, anti-spoofing, MSS) va en secciones
    rotuladas y registradas en CAMBIOS-INVENTARIO.md (CI-23). Nada más.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import Extremo, Infra  # noqa: E402
from gen.comun import cabecera, conjunto, fw01_interfaces, ip_de, nombre_kernel  # noqa: E402

TABLA = "fw01sim"
BOGONS_WAN = ["0.0.0.0/8", "10.0.0.0/8", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12", "192.168.0.0/16"]


def _proto_expr(protocolos: list[dict], dnat: dict[int, int] | None = None) -> str:
    """Expresión de protocolo y puerto destino. Con DNAT, el puerto es el traducido (forward ve la IP/puerto final)."""
    pares = []
    for p in protocolos:
        if p["proto"] not in ("tcp", "udp"):
            continue
        for pt in p["puertos"]:
            pares.append((p["proto"], (p.get("dnat") or {}).get(str(pt), pt)))
    pares = sorted(set(pares))
    if not pares:
        return ""
    if len({pr for pr, _ in pares}) == 1:
        pr = pares[0][0]
        pts = sorted({pt for _, pt in pares})
        return f"{pr} dport " + (str(pts[0]) if len(pts) == 1 else "{ " + ", ".join(map(str, pts)) + " }")
    return "meta l4proto . th dport { " + ", ".join(f"{pr} . {pt}" for pr, pt in pares) + " }"


def _bogons_wan(x: Infra) -> list[str]:
    """Bogons de la WAN menos las excepciones de D1.13 v0.4: la red de tránsito (10.20.0.0/29) y la red del Wi-Fi (solo llega a F31/F32; el resto lo niega la política)."""
    import ipaddress
    excepciones = [ipaddress.ip_network(x.zonas["TRANSITO"]["cidr"]), ipaddress.ip_network(x.zonas["WIFI-EST"]["cidr"])]
    out = []
    for b in BOGONS_WAN:
        redes = [ipaddress.ip_network(b)]
        for e in excepciones:
            nuevas = []
            for r in redes:
                nuevas += list(r.address_exclude(e)) if (e.subnet_of(r) and e != r) else [r]
            redes = nuevas
        out += [str(r) for r in sorted(redes, key=lambda n: (int(n.network_address), n.prefixlen))]
    return out


def _comentario(f: dict) -> str:
    c = f["regla_fw"]
    if len(c) > 120:
        raise ValueError(f"{f['id']}: regla_fw excede 120 caracteres (límite práctico de nft)")
    if '"' in c:
        raise ValueError(f"{f['id']}: regla_fw no puede contener comillas")
    return f'comment "{c}"'


def _particion(x: Infra, f: dict):
    """Separa los pares origen→destino de un flujo en cruce de zonas, locales a FW01 y dentro de una VLAN."""
    cruce, a_fw, desde_fw, intra = [], [], [], []
    for o in x.extremos(f, "origen"):
        for d in x.extremos(f, "destino"):
            if o.es_firewall and d.es_firewall:
                continue
            if o.zona == "INTERNET" and d.zona == "AWS":
                continue          # F29: entra por la IP pública de EC2-GW en AWS; no pasa por FW01 (v0.4)
            if d.es_firewall:
                a_fw.append(o)
            elif o.es_firewall:
                desde_fw.append(d)
            elif o.zona == d.zona:
                intra.append((o, d))
            else:
                cruce.append((o, d))
    return cruce, a_fw, desde_fw, intra


def _unicos(extremos) -> list[Extremo]:
    vistos, out = set(), []
    for e in extremos:
        if e.crudo not in vistos:
            vistos.add(e.crudo)
            out.append(e)
    return out


def _lado(x: Infra, extremos: list[Extremo], campo: str, ifaces: dict) -> list[str]:
    """Tokens nft de un lado (origen/destino) de una regla de forward."""
    inet = [e for e in extremos if e.zona == "INTERNET"]
    resto = [e for e in extremos if e.zona != "INTERNET"]
    if inet and resto:
        raise ValueError(f"mezcla de INTERNET con zonas internas en {[e.crudo for e in extremos]}: divida el flujo")
    pref = "i" if campo == "s" else "o"
    if inet:
        return [f'{pref}ifname "{ifaces["PERIMETRO"]["interfaz"]}"']
    return [f"ip {campo}addr " + conjunto(ip_de(x, e) for e in resto)]


def _reglas_flujo(x: Infra, f: dict, ifaces: dict, wan_ip: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """(forward, input, output, nat) para un flujo permitido."""
    cruce, a_fw, desde_fw, intra = _particion(x, f)
    com = _comentario(f)
    proto = _proto_expr(f["protocolos"])
    fwd, inp, out, nat = [], [], [], []
    if cruce:
        o = _unicos(o for o, _ in cruce)
        d = _unicos(d for _, d in cruce)
        fwd.append(" ".join(_lado(x, o, "s", ifaces) + _lado(x, d, "d", ifaces) + [proto, "counter accept", com]).replace("  ", " "))
        # DNAT de entrada desde Internet: F21 (443 y 80 → WAF01) y F24 (22→2222, 23 → HNY01)
        if any(e.zona == "INTERNET" for e in o):
            for dd in d:
                ip = ip_de(x, dd)
                for p in f["protocolos"]:
                    for pt in p["puertos"]:
                        destino = (p.get("dnat") or {}).get(str(pt), pt)
                        nat.append(f'iifname "{ifaces["PERIMETRO"]["interfaz"]}" ip daddr {wan_ip} {p["proto"]} dport {pt} '
                                   f'dnat to {ip}:{destino} {com}')
    for zona in sorted({e.zona for e in a_fw}):
        miembros = [e for e in a_fw if e.zona == zona]
        if zona not in ifaces:
            raise ValueError(f"{f['id']}: FW01 no tiene interfaz en {zona}")
        inp.append(" ".join([f'iifname "{ifaces[zona]["interfaz"]}"', f"ip saddr {conjunto(ip_de(x, e) for e in miembros)}",
                             f"ip daddr {ifaces[zona]['ip']}", proto, "counter accept", com]))
    for d in _unicos(desde_fw):
        if d.zona == "INTERNET":
            out.append(" ".join([f'oifname "{ifaces["PERIMETRO"]["interfaz"]}"', proto, "counter accept", com]))
        else:
            out.append(" ".join([f'oifname "{ifaces[d.zona]["interfaz"]}"', f"ip daddr {ip_de(x, d)}", proto, "counter accept", com]))
    return fwd, inp, out, nat


def _reglas_bloqueo(x: Infra, f: dict, ifaces: dict) -> list[str]:
    com = _comentario(f)
    reglas = []
    cruce, *_ = _particion(x, f)
    o = _unicos(o for o, _ in cruce)
    d = _unicos(d for _, d in cruce)
    lado_o = _lado(x, o, "s", ifaces)
    lado_d = _lado(x, d, "d", ifaces)
    proto = _proto_expr(f["protocolos"])
    pref = f'log prefix "{f["id"]} BLOQUEADO " counter drop'
    if proto:
        reglas.append(" ".join(lado_o + lado_d + [proto, pref, com]))
    if any(p["proto"] == "ipv6" for p in f["protocolos"]):
        # IPv6 no se filtra por `ip saddr` (solo IPv4): se bloquea por la interfaz de cada zona de origen
        for zona in sorted({e.zona for e in o}):
            reglas.append(" ".join([f'iifname "{ifaces[zona]["interfaz"]}"', "meta nfproto ipv6", pref, com]))
    return reglas


def _vpn(x: Infra, ifaces: dict, aws_peers: list[str] | None) -> tuple[list[str], list[str]]:
    """Tráfico de control de la VPN (IKE, ESP, BGP): sin F-nn en D1.11 (CI-23)."""
    if not aws_peers:
        return ([f"# VPN D1.10: sin pares AWS (parámetro aws_peers): no se genera tráfico de control IKE/ESP/BGP"], [])
    wan = ifaces["PERIMETRO"]["interfaz"]
    pares = conjunto(f"{p}/32" for p in aws_peers).replace("/32", "")
    vtis = [t["id"] for t in x.inv["vpn"]["tuneles"]]
    ifs = "{ " + ", ".join(f'"{nombre_kernel(v)}"' for v in vtis) + " }"
    vecinos = conjunto(f"{_vecino(t['red_interna'])}/32" for t in x.inv["vpn"]["tuneles"]).replace("/32", "")
    nota = 'comment "VPN D1.10 (sin F-nn, CI-23)"'
    entra = [f'iifname "{wan}" ip saddr {pares} udp dport {{ 500, 4500 }} counter accept {nota}',
             f'iifname "{wan}" ip saddr {pares} ip protocol esp counter accept {nota}',
             f"iifname {ifs} ip saddr {vecinos} tcp dport 179 counter accept {nota}"]
    sale = [f'oifname "{wan}" ip daddr {pares} udp dport {{ 500, 4500 }} counter accept {nota}',
            f'oifname "{wan}" ip daddr {pares} ip protocol esp counter accept {nota}',
            f"oifname {ifs} ip daddr {vecinos} tcp dport 179 counter accept {nota}"]
    return entra, sale


def _vecino(red_interna: str) -> str:
    """Dirección del par AWS dentro del /30: el primer host (convención del laboratorio, CI-23)."""
    import ipaddress
    return str(next(ipaddress.ip_network(red_interna).hosts()))


def generar(x: Infra, modo: str = "piloto", ventana: bool = False, wan_ip: str | None = None,
            aws_peers: list[str] | None = None) -> str:
    """Devuelve el ruleset completo de fw01-sim.

    modo: 'piloto' (F6 permitido, fail-open) o 'gestionado' (F6 omitido).
    ventana: True activa F24 (señuelo), que exige autorización escrita de la DTI.
    wan_ip: IP WAN para los DNAT; por defecto la del inventario (FW01, interfaz wan).
    aws_peers: IP públicas de los dos extremos AWS (el inventario solo dice «asignadas por AWS»)."""
    if modo not in ("piloto", "gestionado"):
        raise ValueError("modo debe ser 'piloto' o 'gestionado'")
    ifaces = fw01_interfaces(x)
    wan = ifaces["PERIMETRO"]
    wan_ip = wan_ip or wan["ip"]
    activos = [f for f in x.inv["flujos"] if f["estado"] == "activo"]
    permitidos = [f for f in activos if f["accion"] == "permitir"]
    bloqueados = [f for f in activos if f["accion"] == "bloquear"]

    fwd, inp, out, nat, notas = [], [], [], [], []
    for f in sorted(permitidos, key=lambda f: int(f["id"][1:])):
        if f["modo"] == "piloto" and modo != "piloto":
            notas.append(f"# {f['id']}: omitido en modo {modo} (solo piloto, fail-open)")
            continue
        if f["id"] == "F24" and not ventana:
            notas.append("# F24: deshabilitado (señuelo): requiere ventana autorizada por escrito de la DTI (--ventana)")
            continue
        a, b, c, d = _reglas_flujo(x, f, ifaces, wan_ip)
        _, _, _, intra = _particion(x, f)
        if not (a or b or c) and intra:
            notas.append(f"# {f['id']}: dentro de una misma VLAN; no cruza FW01 (nftables de host): {f['regla_fw']}")
            continue
        if not (a or b or c or d) and not intra:
            notas.append(f"# {f['id']}: no pasa por FW01 (entra por la IP pública de EC2-GW en AWS, v0.4): {f['regla_fw']}")
            continue
        fwd += a
        inp += b
        out += c
        nat += d
    bloqueos = [r for f in sorted(bloqueados, key=lambda f: int(f["id"][1:])) for r in _reglas_bloqueo(x, f, ifaces)]
    vpn_in, vpn_out = _vpn(x, ifaces, aws_peers)
    mss = x.inv["vpn"]["mss_clamping"]
    vtis = "{ " + ", ".join(f'"{nombre_kernel(t["id"])}"' for t in x.inv["vpn"]["tuneles"]) + " }"
    antispoof = f'iifname "{wan["interfaz"]}" ip saddr {{ ' + ", ".join(_bogons_wan(x)) + ' } counter drop comment "Anti-spoofing WAN D1.13 (sin F-nn)"'

    L = [cabecera("#").rstrip(), f"# modo={modo} ventana={'sí' if ventana else 'no'} wan={wan_ip}", "flush ruleset", ""]
    L += [f"table inet {TABLA} {{"]
    L += ["  chain input {", "    type filter hook input priority 0; policy drop;",
          "    ct state established,related accept", "    ct state invalid counter drop", '    iifname "lo" accept',
          "    " + antispoof]
    L += [f"    {r}" for r in vpn_in + inp]
    L += ['    limit rate 20/second burst 50 packets log prefix "fw01sim DENEGADO input: " level info counter drop', "  }", ""]
    L += ["  chain forward {", "    type filter hook forward priority 0; policy drop;",
          "    ct state established,related accept", "    ct state invalid counter drop", "    " + antispoof]
    L += [f"    {r}" for r in bloqueos + fwd]
    L += ['    limit rate 20/second burst 50 packets log prefix "fw01sim DENEGADO forward: " level info counter drop', "  }", ""]
    L += ["  chain output {", "    type filter hook output priority 0; policy drop;",
          "    ct state established,related accept", "    ct state invalid counter drop", '    oifname "lo" accept']
    L += [f"    {r}" for r in vpn_out + out]
    L += ['    limit rate 20/second burst 50 packets log prefix "fw01sim DENEGADO output: " level info counter drop', "  }", ""]
    L += ["  chain mss_vpn {", "    type filter hook forward priority mangle; policy accept;",
          f'    oifname {vtis} tcp flags syn tcp option maxseg size set {mss} comment "MSS clamping D1.10 (sin F-nn)"', "  }", "}", ""]
    L += [f"table ip {TABLA}_nat {{", "  chain prerouting {", "    type nat hook prerouting priority dstnat; policy accept;"]
    L += [f"    {r}" for r in nat]
    L += ["  }", "  chain postrouting {", "    type nat hook postrouting priority srcnat; policy accept;",
          f'    oifname "{wan["interfaz"]}" masquerade comment "NAT de salida (sin F-nn)"', "  }", "}", ""]
    if notas:
        L += ["# --- Flujos sin regla en fw01-sim ---"] + notas + [""]
    return "\n".join(L)


def flujos_con_regla(ruleset: str) -> set[str]:
    """IDs F-nn con al menos una regla accept/dnat/drop en el ruleset (para el validador, V-40)."""
    ids = set()
    for linea in ruleset.splitlines():
        if linea.lstrip().startswith("#"):
            continue
        for m in re.finditer(r'comment "(F\d+)\b', linea):
            ids.add(m.group(1))
    return ids


def main(x: Infra, salida: Path, **kw) -> Path:
    from gen.comun import escribir
    ruta = salida / "fw01sim.nft"
    escribir(ruta, generar(x, **kw))
    return ruta
