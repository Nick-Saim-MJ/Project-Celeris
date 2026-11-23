#!/usr/bin/env python3
"""Validador de la fuente única de datos de red (CE0311, Entregable 1).

Ejecuta los chequeos V-01…V-45 sobre infra/inventory.yaml, infra/pruebas.yaml e infra/trazabilidad.yaml,
ejecuta los ganchos de infra/checks/ (V-50+ diagramas, V-60+ XLSX componentes, V-70+ XLSX pruebas, V-80+ DOCX)
y escribe docs/infra/e1/validacion.md.

Cada hallazgo dice cómo corregirlo. Código de salida: 0 sin FALLA; 1 con alguna FALLA (con --estricto,
también si hay advertencias).

    python infra/validate.py [--md RUTA] [--estricto] [--sin-informe]
"""
from __future__ import annotations

import argparse
import importlib.util
import ipaddress
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import celeris_infra as ci  # noqa: E402
from celeris_infra import Infra, red  # noqa: E402

# --------------------------------------------------------------------------------------------------
# Modelo de resultados
# --------------------------------------------------------------------------------------------------


@dataclass
class Hallazgo:
    nivel: str          # error | advertencia | info
    mensaje: str
    corregir: str = ""


@dataclass
class Resultado:
    id: str
    titulo: str
    estado: str = "PASA"          # PASA | FALLA | ADVERTENCIA | PENDIENTE
    hallazgos: list[Hallazgo] = field(default_factory=list)
    detalle: str = ""


CHEQUEOS: list[tuple[str, str, callable]] = []


def chequeo(cid: str, titulo: str):
    def deco(fn):
        CHEQUEOS.append((cid, titulo, fn))
        return fn
    return deco


def E(msg, fix=""):
    return Hallazgo("error", msg, fix)


def W(msg, fix=""):
    return Hallazgo("advertencia", msg, fix)


def I(msg):  # noqa: E741
    return Hallazgo("info", msg)


def _lista(v):
    return [v] if isinstance(v, str) else list(v or [])


def _orig_dest(valor) -> list[str]:
    return _lista(valor)


# --------------------------------------------------------------------------------------------------
# V-01 … V-10: estructura, referencias y direccionamiento
# --------------------------------------------------------------------------------------------------


@chequeo("V-01", "Esquema JSON válido en los tres YAML")
def v01(x: Infra):
    return [E(f"{a}: {ruta}: {msg}", f"Corrija el campo en infra/{a} según infra/schema/{a.split('.')[0]}.schema.json")
            for a, ruta, msg in Infra.errores_de_esquema(x.raiz)]


@chequeo("V-02", "IDs únicos")
def v02(x: Infra):
    r = []

    def dup(nombre, ids):
        vistos, repetidos = set(), set()
        for i in ids:
            (repetidos if i in vistos else vistos).add(i)
        for i in sorted(repetidos):
            r.append(E(f"ID repetido en {nombre}: {i}", f"Deje un solo {i} en {nombre} o renómbrelo según el contrato de IDs"))

    dup("zonas", [z["id"] for z in x.inv["zonas"]])
    dup("componentes", [c["id"] for c in x.inv["componentes"]])
    dup("flujos", [f["id"] for f in x.inv["flujos"]])
    dup("pruebas", [t["id"] for t in x.pru["pruebas"]])
    dup("objetivos", [o["id"] for o in x.traz["objetivos"]])
    dup("amenazas", [a["id"] for a in x.traz["amenazas"]])
    dup("detecciones", [d["id"] for d in x.traz["detecciones"]])
    dup("figuras", [f["id"] for f in x.traz["figuras"]])
    dup("docx_secciones", [s["id"] for s in x.traz["docx_secciones"]])
    dup("reglas_fw", [f["regla_fw"] for f in x.inv["flujos"] if f.get("regla_fw")])
    dup("supernets/reservas", [s["id"] for s in x.inv["supernets"]] + [s["id"] for s in x.inv["reservas"]])
    dup("correspondencia", [str(c["n"]) for c in x.traz["correspondencia_contenidos"]])
    return r


def _existe(r, origen, valor, conjunto, que):
    if valor not in conjunto:
        r.append(E(f"{origen}: {que} «{valor}» no existe", f"Cree {valor} o corrija la referencia en {origen}"))


@chequeo("V-03", "Referencias existentes entre los tres archivos")
def v03(x: Infra):
    r = []
    zonas, comps, flujos, pruebas = set(x.zonas), set(x.componentes), set(x.flujos), set(x.pruebas)
    figs, ods, ads, reqs, sups = set(x.figuras), set(x.objetivos), set(x.decisiones), set(x.requisitos), set(x.supuestos)
    for c in x.componentes.values():
        o = f"componente {c['id']}"
        for z in c["zonas"]:
            _existe(r, o, z, zonas, "zona")
        for i in c["ips"]:
            _existe(r, f"{o} ({i['interfaz']})", i["zona"], zonas, "zona")
            if i["zona"] not in c["zonas"]:
                r.append(E(f"{o}: la interfaz {i['interfaz']} está en {i['zona']}, que no figura en sus zonas {c['zonas']}",
                           "Agregue la zona a `zonas` o corrija la zona de la interfaz"))
        if c.get("subred"):
            _existe(r, o, c["subred"], comps, "subred")
        for d in c["dependencias"]:
            _existe(r, o, d, comps, "dependencia")
        for a in c["adr"]:
            _existe(r, o, a, ads, "ADR")
        for q in c["req"]:
            _existe(r, o, q, reqs, "requisito")
        for od in c["objetivos"]:
            _existe(r, o, od, ods, "objetivo")
        for fg in c["figuras"]:
            _existe(r, o, fg, figs, "figura")
        for s in c["supuestos"]:
            _existe(r, o, s, sups, "supuesto")
    for f in x.flujos.values():
        o = f"flujo {f['id']}"
        for lado in ("origen", "destino"):
            for crudo in f[lado]:
                for e in x.resolver(crudo):
                    if e.error:
                        r.append(E(f"{o}: {lado}: {e.error}", "Use un ID de zona, de componente o «COMPONENTE:interfaz»"))
        if f.get("figura"):
            _existe(r, o, f["figura"], figs, "figura")
        for od in f["objetivos"]:
            _existe(r, o, od, ods, "objetivo")
        for a in f["adr"]:
            _existe(r, o, a, ads, "ADR")
        for q in f["req"]:
            _existe(r, o, q, reqs, "requisito")
    me = x.inv["matriz_esperada"]
    for z in me["orden"]:
        _existe(r, "matriz_esperada.orden", z, zonas, "zona")
    for zo, fila in me["celdas"].items():
        _existe(r, "matriz_esperada", zo, zonas, "zona origen")
        for zd, cel in fila.items():
            _existe(r, "matriz_esperada", zd, zonas, "zona destino")
            for fid in cel.get("flujos", []) + cel.get("bloqueados", []):
                _existe(r, f"matriz_esperada {zo}>{zd}", fid, flujos, "flujo")
    for t in x.pruebas.values():
        o = f"prueba {t['id']}"
        for fid in t["flujos"]:
            _existe(r, o, fid, flujos, "flujo")
        for cid in t["componentes"]:
            _existe(r, o, cid, comps, "componente")
        for lado in ("origen", "destino"):
            for crudo in _orig_dest(t[lado]):
                for e in x.resolver(crudo):
                    if e.error:
                        r.append(E(f"{o}: {lado}: {e.error}", "Use un ID de zona, de componente o «COMPONENTE:interfaz»"))
        for od in t["objetivos"]:
            _existe(r, o, od, ods, "objetivo")
        for a in t["amenazas"]:
            _existe(r, o, a, set(x.amenazas), "amenaza")
        for d in t.get("detecciones", []):
            _existe(r, o, d, set(x.detecciones), "detección")
        for rr in t["criterios_rubrica"]:
            _existe(r, o, rr, set(x.rubrica), "criterio de rúbrica")
        for cel in t.get("celdas_matriz", []):
            za, zb = cel.split(">")
            _existe(r, f"{o} celdas_matriz", za, zonas, "zona")
            _existe(r, f"{o} celdas_matriz", zb, zonas, "zona")
    for a in x.amenazas.values():
        for cid in a["componentes"]:
            _existe(r, f"amenaza {a['id']}", cid, comps, "componente")
        for t in a["pruebas"]:
            _existe(r, f"amenaza {a['id']}", t, pruebas, "prueba")
    for d in x.detecciones.values():
        _existe(r, f"detección {d['id']}", d["ubicacion"], comps, "componente")
        for t in d["validacion"]["pruebas"]:
            _existe(r, f"detección {d['id']}", t, pruebas, "prueba")
    for fg in x.figuras.values():
        _existe(r, f"figura {fg['id']}", fg["seccion_docx"], set(x.secciones), "sección del DOCX")
    for rid, rub in x.rubrica.items():
        for ev in rub["evidencias"]:
            o = f"rúbrica {rid}"
            if ev["tipo"] == "seccion_docx":
                _existe(r, o, ev["ref"], set(x.secciones), "sección del DOCX")
            elif ev["tipo"] == "figura":
                _existe(r, o, ev["ref"], figs, "figura")
            elif ev["tipo"] == "hoja_xlsx":
                _existe(r, o, ev["ref"], set(x.artefactos), "artefacto")
            elif ev["tipo"] == "prueba":
                _existe(r, o, ev["ref"], pruebas, "prueba")
    for c in x.traz["correspondencia_contenidos"]:
        for s in c["secciones_docx"]:
            _existe(r, f"correspondencia {c['d1']}", s, set(x.secciones), "sección del DOCX")
    return r


@chequeo("V-04", "Cada IP dentro del CIDR de su zona (y de su subred AWS)")
def v04(x: Infra):
    r = []
    for cid, iface, ip, zona in x.todas_las_ips():
        z = x.zonas.get(zona)
        if z is None:
            continue
        a = ipaddress.ip_address(ip)
        if z["cidr"]:
            n = red(z["cidr"])
            if a not in n:
                r.append(E(f"{cid}/{iface}: {ip} no está en {z['cidr']} ({zona})", f"Asigne una IP dentro de {z['cidr']} o cambie la zona"))
            elif a in (n.network_address, n.broadcast_address):
                r.append(E(f"{cid}/{iface}: {ip} es la dirección de red o de difusión de {z['cidr']}", "Use una IP de host"))
            elif z["gateway"] and ip == z["gateway"] and cid != "FW01" and z["tipo"] != "transito":
                r.append(E(f"{cid}/{iface}: {ip} es el gateway de {zona}, reservado a FW01", "Use otra IP"))
        sub = x.componentes[cid].get("subred")
        if sub and a not in red(x.componentes[sub]["cidr"]):
            r.append(E(f"{cid}: {ip} no está en la subred {sub} ({x.componentes[sub]['cidr']})", "Corrija la IP o la subred del componente"))
    for c in x.componentes.values():
        if c.get("cidr") and c["tipo"] == "aws_subred":
            if not red(c["cidr"]).subnet_of(red(x.zonas["AWS"]["cidr"])):
                r.append(E(f"{c['id']}: {c['cidr']} no está dentro de la VPC {x.zonas['AWS']['cidr']}", "Corrija el CIDR de la subred"))
    return r


@chequeo("V-05", "Sin IP duplicadas")
def v05(x: Infra):
    r, vistos = [], {}
    for cid, iface, ip, zona in x.todas_las_ips():
        if ip in vistos:
            r.append(E(f"IP {ip} repetida: {vistos[ip]} y {cid}/{iface}", "Cada IP planeada debe ser única; cambie una de las dos"))
        vistos[ip] = f"{cid}/{iface}"
    return r


@chequeo("V-06", "Gateways .1 y coherentes con FW01; tránsito FW01 ↔ FortiGate (v0.4: 7 VLAN)")
def v06(x: Infra):
    r = []
    fw = x.componentes["FW01"]
    fw_if = {i["zona"]: i["ip"] for i in fw["ips"] if x.zonas.get(i["zona"], {}).get("tipo") == "interna"}
    for z in x.zonas.values():
        if z["tipo"] != "interna":
            continue
        esperado = str(red(z["cidr"]).network_address + 1)
        if z["gateway"] != esperado:
            r.append(E(f"{z['id']}: gateway {z['gateway']} ≠ {esperado} (.1 de {z['cidr']})", f"Use {esperado}"))
        if fw_if.get(z["id"]) != z["gateway"]:
            r.append(E(f"{z['id']}: FW01 tiene {fw_if.get(z['id'])} en la zona, el gateway es {z['gateway']}", "FW01 debe tener la IP del gateway en cada VLAN"))
    vlans_fw = sorted(x.zonas[z]["vlan"] for z in fw_if)
    if vlans_fw != [10, 20, 30, 40, 41, 50, 60]:
        r.append(E(f"Subinterfaces de FW01 {vlans_fw} ≠ D1.13 v0.4 [10, 20, 30, 40, 41, 50, 60]", "Ajuste las IP de FW01 al trunk de D1.13"))
    # D1.8 v0.4: tránsito 10.20.0.0/29, FortiGate .1 y FW01 .2 [S-29]
    tr = x.zonas.get("TRANSITO")
    if tr is None:
        return r + [E("Falta la zona TRANSITO (10.20.0.0/29)", "Agréguela (CI-37)")]
    wan = next((i for i in fw["ips"] if i["interfaz"] == "wan"), None)
    if wan is None or wan["zona"] != "TRANSITO" or wan["ip"] != "10.20.0.2":
        r.append(E(f"La WAN de FW01 debe ser 10.20.0.2 en TRANSITO y es {wan and wan['ip']} en {wan and wan['zona']}", "CI-37: la WAN de FW01 queda en la red de tránsito"))
    fgt = x.componentes.get("FGT-EXT")
    if fgt is None or next((i["ip"] for i in fgt["ips"] if i["zona"] == "TRANSITO"), None) != tr["gateway"]:
        r.append(E(f"FGT-EXT debe tener la IP del gateway de tránsito ({tr['gateway']})", "CI-37"))
    return r


@chequeo("V-07", "Sin solapamientos entre 10.20.0.0/16, 10.30.0.0/16, zonas, subredes y reservas")
def v07(x: Infra):
    r = []

    def pares(items, ambito):
        for i, (na, ra) in enumerate(items):
            for nb, rb in items[i + 1:]:
                if ra.overlaps(rb):
                    r.append(E(f"Solapamiento en {ambito}: {na} ({ra}) con {nb} ({rb})", "Ajuste uno de los dos CIDR"))

    sup = [(s["id"], red(s["cidr"])) for s in x.inv["supernets"] if not s.get("resumen")]
    pares(sup, "supernets")
    por_id = {s["id"]: red(s["cidr"]) for s in x.inv["supernets"]}
    resumen = [red(s["cidr"]) for s in x.inv["supernets"] if s.get("resumen")]
    for nom, rd in sup:
        if resumen and nom != "AWS-CELERIS" and not any(rd.subnet_of(rs) for rs in resumen):
            r.append(E(f"{nom} ({rd}) no está dentro del resumen del campus", "El resumen 10.20.0.0/14 debe agregar todas las sedes"))
    for nom, rd in sup:
        if nom == "AWS-CELERIS" and any(rd.overlaps(rs) for rs in resumen):
            r.append(E("La VPC de AWS se solapa con el resumen del campus", "Mantenga 10.30.0.0/16 fuera de 10.20.0.0/14"))
    sede = [(z["id"], red(z["cidr"])) for z in x.zonas.values() if z["tipo"] in ("interna", "transito") and z["cidr"]]
    for nom, rd in sede:
        if not rd.subnet_of(por_id["SEDE-JULIACA"]):
            r.append(E(f"Zona {nom} ({rd}) fuera de 10.20.0.0/16", "Las zonas internas viven en la supernet de la sede"))
    reservas = [(f"{rv['id']}", red(rv["cidr"]), rv["dentro_de"]) for rv in x.inv["reservas"]]
    for nom, rd, padre in reservas:
        if padre not in por_id or not rd.subnet_of(por_id[padre]):
            r.append(E(f"Reserva {nom} ({rd}) no está dentro de {padre}", "Corrija `dentro_de` o el CIDR"))
    pares(sede + [(n, rd) for n, rd, p in reservas if p == "SEDE-JULIACA"], "10.20.0.0/16 (zonas y reservas)")
    aws = [(c["id"], red(c["cidr"])) for c in x.inv["componentes"] if c["tipo"] == "aws_subred"]
    pares(aws + [(n, rd) for n, rd, p in reservas if p == "AWS-CELERIS"], "10.30.0.0/16 (subredes y reservas)")
    # Zonas externas con red propia (WIFI-EST, v0.4): quedan FUERA de 10.20.0.0/16 y del resumen, de AWS y de las demás
    externas = [(z["id"], red(z["cidr"])) for z in x.zonas.values() if z["tipo"] == "externa" and z["cidr"]]
    for nom, rd in externas:
        for sn, sr in [(s_["id"], red(s_["cidr"])) for s_ in x.inv["supernets"]]:
            if rd.overlaps(sr):
                r.append(E(f"La zona externa {nom} ({rd}) se solapa con {sn} ({sr})", "La red del Wi-Fi debe quedar fuera de 10.20.0.0/16, del resumen del campus y de AWS (S-28)"))
        for zn, zr in sede + aws:
            if rd.overlaps(zr):
                r.append(E(f"La zona externa {nom} ({rd}) se solapa con {zn} ({zr})", "Ajuste el CIDR"))
    # Rangos de laboratorio (D1.8, D-23): /26 dentro de la VLAN 30, sin solapamientos, con la infraestructura en 10.20.35.0/24
    rl = x.inv.get("rangos_lab")
    if rl:
        lab = red(x.zonas["LAB"]["cidr"])
        items = [(l["id"], red(l["cidr"])) for l in rl["laboratorios"]] + [(rl["reserva"]["id"], red(rl["reserva"]["cidr"])), (rl["infraestructura"]["id"], red(rl["infraestructura"]["cidr"]))]
        for nom, rd in items:
            if not rd.subnet_of(lab):
                r.append(E(f"{nom} ({rd}) no está dentro de LAB ({lab})", "Los rangos de laboratorio viven dentro de la VLAN 30"))
        for l in rl["laboratorios"]:
            if red(l["cidr"]).prefixlen != 26 or l["hosts_utiles"] != 62:
                r.append(E(f"{l['id']}: debe ser un /26 con 62 hosts útiles", "D1.8: un /26 por laboratorio"))
        pares(items, "rangos de laboratorio")
        infra_r = red(rl["infraestructura"]["cidr"])
        for cid in rl["infraestructura"]["componentes"]:
            for i in x.componentes[cid]["ips"]:
                if i["ip"] and ipaddress.ip_address(i["ip"]) not in infra_r:
                    r.append(E(f"{cid}: {i['ip']} no está en el rango de infraestructura {infra_r}", "ENC01, LABCLI01, KALI01 y HNY02 viven en 10.20.35.0/24"))
    vpn_nets = [(t["id"], red(t["red_interna"])) for t in x.inv["vpn"]["tuneles"]]
    pares(vpn_nets, "enlaces internos de la VPN")
    for nom, rd in vpn_nets:
        if not rd.subnet_of(ipaddress.ip_network("169.254.0.0/16")) or rd.prefixlen != 30:
            r.append(E(f"{nom}: {rd} debe ser un /30 de 169.254.0.0/16", "Use un /30 link-local para el túnel"))
    return r


@chequeo("V-08", "Convención VLAN = tercer octeto (excepción documentada: VLAN 30 → 10.20.32.0/22)")
def v08(x: Infra):
    r = []
    for z in x.inv["zonas"]:
        if z["tipo"] != "interna" or not z["cidr"]:
            continue
        n = red(z["cidr"])
        tercero = int(str(n.network_address).split(".")[2])
        if z.get("excepcion_convencion_vlan"):
            if z["vlan"] != 30 or str(n) != "10.20.32.0/22":
                r.append(E(f"{z['id']}: la única excepción documentada es VLAN 30 → 10.20.32.0/22", "Quite la excepción o ajuste el CIDR"))
        else:
            if tercero != z["vlan"]:
                r.append(E(f"{z['id']}: tercer octeto {tercero} ≠ VLAN {z['vlan']} ({z['cidr']})", "Ajuste el CIDR para que el tercer octeto sea la VLAN, o documente la excepción"))
            if n.prefixlen != 24:
                r.append(E(f"{z['id']}: {z['cidr']} no es /24", "Las zonas, salvo LAB, son /24"))
    return r


es_publica_ip = ci.es_publica


@chequeo("V-09", "IP públicas solo de documentación (RFC 5737)")
def v09(x: Infra):
    r = []
    patron = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])")
    for archivo in ("inventory.yaml", "pruebas.yaml", "trazabilidad.yaml"):
        texto = (x.raiz / "infra" / archivo).read_text(encoding="utf-8")
        for m in patron.finditer(texto):
            try:
                ip = m.group(1)
                if ci.es_publica(ip) and not ci.en_rfc5737(ip):
                    linea = texto.count("\n", 0, m.start()) + 1
                    r.append(E(f"{archivo}:{linea}: IP pública real {ip}", "Use una IP de documentación RFC 5737 (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24)"))
            except ValueError:
                continue
    for cid, iface, ip, zona in x.todas_las_ips():
        if x.zonas[zona]["tipo"] in ("perimetro", "externa") and es_publica_ip(ip) and not ci.en_rfc5737(ip):
            r.append(E(f"{cid}/{iface}: {ip} debe ser RFC 5737", "Use 203.0.113.0/24"))
    return r


@chequeo("V-10", "Hosts útiles coinciden con el CIDR")
def v10(x: Infra):
    r = []
    for z in x.inv["zonas"]:
        if z.get("hosts_utiles") and z["cidr"]:
            real = red(z["cidr"]).num_addresses - 2
            if real != z["hosts_utiles"]:
                r.append(E(f"{z['id']}: hosts_utiles {z['hosts_utiles']} ≠ {real} de {z['cidr']}", f"Use {real}"))
    return r


# --------------------------------------------------------------------------------------------------
# V-11 … V-16: matriz y flujos
# --------------------------------------------------------------------------------------------------


@chequeo("V-11", "La matriz zona × zona derivada de los flujos coincide con D1.8")
def v11(x: Infra):
    r = []
    for d in x.diferencias_matriz():
        zo, zd = d["par"]
        partes = []
        if d["sobran_en_flujos"]:
            partes.append(f"los flujos {d['sobran_en_flujos']} permiten {zo}→{zd} pero la matriz no los lista")
        if d["faltan_en_flujos"]:
            partes.append(f"la matriz lista {d['faltan_en_flujos']} pero ningún flujo los deriva")
        if d["bloq_sobran"] or d["bloq_faltan"]:
            partes.append(f"bloqueados: sobran {d['bloq_sobran']}, faltan {d['bloq_faltan']}")
        if not partes:
            partes.append(f"la matriz indica «{d['esperado']['estado']}» sin flujos y los flujos derivan «{d['estado_derivado']}»")
        msg = f"{zo}→{zd}: " + "; ".join(partes)
        if d["pendiente"]:
            r.append(W(msg + f" — contradicción registrada ({', '.join(d['cambios']) or 'sin CI'})",
                       "Resuélvala en CAMBIOS-INVENTARIO.md y corrija el flujo o la celda; luego quite `pendiente`"))
        else:
            r.append(E(msg, f"Corrija el flujo (origen/destino/puertos) o la celda {zo}→{zd} de matriz_esperada; si es una contradicción del documento maestro, regístrela en CAMBIOS-INVENTARIO.md y marque `pendiente: true`"))
    return r


@chequeo("V-12", "Matriz esperada completa (celda por celda) y coherente con las acciones de los flujos")
def v12(x: Infra):
    r = []
    orden = x.orden_matriz
    cel = x.inv["matriz_esperada"]["celdas"]
    for zo in orden:
        for zd in orden:
            c = cel.get(zo, {}).get(zd)
            if c is None:
                r.append(E(f"Falta la celda {zo}→{zd} en matriz_esperada", "Transcriba la celda de D1.8"))
                continue
            if c["estado"] == "denegado" and (c.get("flujos") or c.get("bloqueados")):
                r.append(E(f"{zo}→{zd}: «denegado» no puede listar flujos", "Cambie el estado o quite los flujos"))
            if c["estado"] == "permitido" and not c.get("flujos") and not c.get("pendiente"):
                r.append(E(f"{zo}→{zd}: «permitido» sin flujos ni `pendiente`", "Cite el F-nn o registre la contradicción (CAMBIOS-INVENTARIO.md)"))
            for fid in c.get("flujos", []):
                if fid in x.flujos and x.flujos[fid]["accion"] != "permitir":
                    r.append(E(f"{zo}→{zd}: {fid} no es un flujo permitido", "Muévalo a `bloqueados`"))
            for fid in c.get("bloqueados", []):
                if fid in x.flujos and x.flujos[fid]["accion"] != "bloquear":
                    r.append(E(f"{zo}→{zd}: {fid} no es un flujo bloqueado", "Muévalo a `flujos`"))
    extra = set(cel) - set(orden)
    if extra:
        r.append(E(f"Filas fuera de `orden`: {sorted(extra)}", "Quite o agregue la zona a `orden`"))
    return r


@chequeo("V-13", "Todo flujo permitido tiene protección en tránsito y riesgo residual")
def v13(x: Infra):
    r = []
    for f in x.flujos.values():
        if f["estado"] == "reservado":
            if any(f.get(k) for k in ("origen", "destino", "protocolos", "accion", "proteccion", "regla_fw")):
                r.append(E(f"{f['id']} está reservado y tiene datos", "F4 debe quedar vacío; no se reutiliza"))
            continue
        if f["accion"] == "permitir":
            p = f.get("proteccion")
            if not p or p["tipo"] == "no_aplica" or not p.get("detalle"):
                r.append(E(f"{f['id']}: permitido sin protección en tránsito", "Indique `proteccion.tipo` y `detalle` (D1.11, columna «Protección»)"))
            if not f.get("riesgo_residual"):
                r.append(E(f"{f['id']}: permitido sin riesgo residual", "Describa el riesgo residual o el riesgo aceptado"))
            if p and p["tipo"] == "sin_cifrar_riesgo_aceptado" and not re.search(r"acept|bajo|compens|mitig|medio", f.get("riesgo_residual", ""), re.I):
                r.append(W(f"{f['id']}: flujo sin cifrar cuyo riesgo residual no declara su aceptación o compensación", "Indique por qué se acepta el riesgo"))
        elif f["accion"] == "bloquear":
            if not f.get("proteccion") or f["proteccion"]["tipo"] != "no_aplica":
                r.append(E(f"{f['id']}: un flujo bloqueado usa proteccion.tipo = no_aplica", "Corrija el tipo de protección"))
    return r


@chequeo("V-14", "F1–F26 de D1.11 completos (F4 reservado), ampliaciones F27+ registradas y regla de firewall con el ID del flujo")
def v14(x: Infra):
    r = []
    ids = [f["id"] for f in x.inv["flujos"]]
    faltan = sorted(set(ci.FLUJOS_ESPERADOS) - set(ids))
    if faltan:
        r.append(E(f"Faltan flujos de D1.11 (F1–F26): {faltan}", "Transcriba los 26 flujos de D1.11"))
    for f in x.flujos.values():
        if f["id"] not in ci.FLUJOS_ESPERADOS and not (f.get("ampliacion") and f.get("cambio")):
            r.append(E(f"{f['id']}: no es de D1.11; debe llevar `ampliacion: true` y `cambio` (CI-nn)", "Registre la ampliación en CAMBIOS-INVENTARIO.md"))
    if x.flujos.get("F4", {}).get("estado") != "reservado":
        r.append(E("F4 debe existir con estado «reservado»", "Restituya F4 como reservado"))
    for f in x.flujos.values():
        if f["estado"] != "activo":
            continue
        patron = rf"(?<![A-Za-z0-9]){f['id']}(?![0-9])"
        if not f.get("regla_fw") or not re.search(patron, f["regla_fw"]):
            r.append(E(f"{f['id']}: regla_fw «{f.get('regla_fw')}» no contiene el ID del flujo", f"Nombre la regla de modo que incluya «{f['id']}»"))
        if not f["protocolos"]:
            r.append(E(f"{f['id']}: sin protocolo ni puerto", "Indique protocolo y puertos de D1.11"))
        if not f.get("modo"):
            r.append(E(f"{f['id']}: sin modo (piloto | gestionado | ambos)", "Indique el modo"))
        if not f.get("figura"):
            r.append(E(f"{f['id']}: sin figura (FIG-5.5a o FIG-5.5b)", "Asigne la figura donde se dibuja"))
        if f["accion"] == "permitir" and not f["origen"]:
            r.append(E(f"{f['id']}: sin origen", "Indique al menos un origen"))
    return r


@chequeo("V-15", "Todo flujo bloqueado tiene una prueba")
def v15(x: Infra):
    return [E(f"{f['id']} está bloqueado y ninguna prueba lo cubre", f"Agregue {f['id']} a `flujos` de una prueba en pruebas.yaml")
            for f in x.flujos.values() if f["estado"] == "activo" and f["accion"] == "bloquear" and not x.pruebas_de_flujo(f["id"])]


@chequeo("V-16", "Todo flujo tiene ≥ 1 prueba o una justificación")
def v16(x: Infra):
    r = []
    for f in x.flujos.values():
        if f["estado"] != "activo":
            continue
        pr = x.pruebas_de_flujo(f["id"])
        if not pr and not f.get("sin_prueba_justificacion"):
            r.append(E(f"{f['id']}: sin prueba ni justificación", f"Agregue {f['id']} a una prueba o escriba `sin_prueba_justificacion`"))
        elif not pr:
            r.append(I(f"{f['id']}: sin prueba T-nn en D1.16 (justificado)"))
    sin = [f["id"] for f in x.flujos.values() if f["estado"] == "activo" and not x.pruebas_de_flujo(f["id"])]
    if sin:
        r.append(W(f"{len(sin)} flujos sin prueba T-nn propia ({', '.join(sin)}): se justifican en el inventario (CI-22)",
                   "Proponer pruebas T29+ en S2 o mantener la justificación"))
    return r


# --------------------------------------------------------------------------------------------------
# V-17 … V-19: componentes
# --------------------------------------------------------------------------------------------------


def _frases(t: str) -> int:
    limpio = re.sub(r"\b(p|etc|Sr|Dr)\.\s", r"\1 ", t)
    return len([s for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])", limpio.strip()) if s])


@chequeo("V-17", "Componentes: por_que (1–3 frases), aporta_corto (≤ 12 palabras), aporta, si_falla, criticidad")
def v17(x: Infra):
    r = []
    for c in x.componentes.values():
        for campo in ("por_que", "aporta", "si_falla", "aporta_corto", "criticidad", "funcion", "controles"):
            if not str(c.get(campo, "")).strip():
                r.append(E(f"{c['id']}: falta {campo}", f"Complete {campo} (sin texto genérico: IP, puerto, regla, figura o prueba)"))
        palabras = len(str(c["aporta_corto"]).split())
        if palabras > 12:
            r.append(E(f"{c['id']}: aporta_corto tiene {palabras} palabras (máximo 12)", "Acórtelo"))
        n = _frases(c["por_que"])
        if not 1 <= n <= 3:
            r.append(E(f"{c['id']}: por_que tiene {n} frases (1–3)", "Reescriba en 1–3 frases"))
        if c["estado"] == "fuera_de_alcance" and c["id"] != "SW-ACC":
            r.append(W(f"{c['id']}: marcado fuera de alcance; D1.5 solo excluye la capa de acceso", "Verifique la exclusión"))
    return r


@chequeo("V-18", "Componentes: ≥ 1 figura, FIG-5.1 y las figuras de sus flujos")
def v18(x: Infra):
    r = []
    for c in x.componentes.values():
        if c.get("estado") == "temporal":
            continue                    # EC2-DR y NAT-DR solo existen en el simulacro: no son faltantes en figuras permanentes
        if not c["figuras"]:
            r.append(E(f"{c['id']}: sin figuras", "Indique en qué FIG debe aparecer"))
            continue
        faltan = x.figuras_requeridas(c["id"]) - set(c["figuras"])
        if faltan:
            r.append(E(f"{c['id']}: debe aparecer también en {sorted(faltan)}", "Agregue las figuras a `figuras` (D1.7: todo ID de D1.12 en FIG-5.1; cada flecha de F-nn en su FIG-5.5)"))
    return r


@chequeo("V-19", "Componentes: ≥ 1 flujo o justificación de por qué no tienen")
def v19(x: Infra):
    r = []
    for c in x.componentes.values():
        if not x.flujos_de(c["id"]) and not c.get("flujos_justificacion"):
            r.append(E(f"{c['id']}: sin flujos ni `flujos_justificacion`", "Cite el F-nn que lo toca o justifique por qué no participa en ninguno"))
    return r


# --------------------------------------------------------------------------------------------------
# V-20 … V-27: pruebas, objetivos, amenazas, rúbrica, detecciones
# --------------------------------------------------------------------------------------------------


@chequeo("V-20", "Pruebas T01–T28 de D1.16 completas, ampliaciones T29+ registradas, con criterio verificable y modos válidos")
def v20(x: Infra):
    r = []
    ids = sorted(list(x.pruebas) + list(x.pruebas_retiradas))          # los retirados conservan su número: no hay huecos ni reutilización
    faltan = sorted(set(ci.PRUEBAS_ESPERADAS) - set(ids))
    if faltan:
        r.append(E(f"Faltan pruebas de D1.16 (T01–T28): {faltan}", "Transcriba las 28 pruebas de D1.16"))
    for t in x.pruebas.values():
        extra = t["id"] not in ci.PRUEBAS_ESPERADAS
        if extra and not (t.get("ampliacion") and t.get("cambio")):
            r.append(E(f"{t['id']}: no es de D1.16; debe llevar `ampliacion: true` y `cambio` (CI-nn)", "Registre la ampliación en CAMBIOS-INVENTARIO.md"))
        if not extra and t.get("ampliacion"):
            r.append(E(f"{t['id']}: es de D1.16 y no puede marcarse como ampliación", "Quite `ampliacion`"))
    if ids != sorted(ids, key=lambda s: int(s[1:])) or [int(i[1:]) for i in ids] != list(range(1, len(ids) + 1)):
        r.append(E(f"Los IDs de prueba deben ser consecutivos desde T01 (hay {ids[0]}…{ids[-1]}, {len(ids)} pruebas)", "Numere sin huecos"))
    for t in x.pruebas.values():
        manual = any(c["tipo"] == "manual" for c in t["criterio_aprobacion"])
        if manual == t["automatizable"]:
            r.append(E(f"{t['id']}: automatizable={t['automatizable']} pero {'tiene' if manual else 'no tiene'} criterios manuales", "Haga coincidir `automatizable` con los criterios"))
        if not t["flujos"] and not t.get("flujos_justificacion"):
            r.append(E(f"{t['id']}: sin flujos ni `flujos_justificacion`", "Cite el F-nn o justifique (p. ej. prueba de denegación)"))
        if "H" not in t["modos"]:
            r.append(E(f"{t['id']}: los modos no incluyen H; F3 ejecuta las pruebas en el campus", "Agregue H"))
        for c in t["criterio_aprobacion"]:
            if c["tipo"] == "regex":
                try:
                    re.compile(c["patron"])
                except re.error as e:
                    r.append(E(f"{t['id']}: regex inválida «{c['patron']}»: {e}", "Corrija el patrón"))
            if c["tipo"] in ("umbral", "contador") and "valor" not in c:
                r.append(E(f"{t['id']}: criterio {c['tipo']} sin valor", "Indique el umbral"))
    return r


@chequeo("V-21", "Coherencia bidireccional: pruebas ↔ amenazas, detecciones y rúbrica")
def v21(x: Infra):
    r = []
    for a in x.amenazas.values():
        declaradas = {t["id"] for t in x.pruebas.values() if a["id"] in t["amenazas"]}
        if declaradas != set(a["pruebas"]):
            r.append(E(f"{a['id']}: la amenaza lista {sorted(a['pruebas'])} pero las pruebas la citan en {sorted(declaradas)}", "Haga coincidir trazabilidad.yaml (amenazas) con pruebas.yaml (amenazas)"))
    for d in x.detecciones.values():
        declaradas = {t["id"] for t in x.pruebas.values() if d["id"] in t.get("detecciones", [])}
        if declaradas != set(d["validacion"]["pruebas"]):
            r.append(E(f"{d['id']}: la detección lista {sorted(d['validacion']['pruebas'])} pero las pruebas la citan en {sorted(declaradas)}", "Haga coincidir ambos archivos"))
    for rid, rub in x.rubrica.items():
        evid = {e["ref"] for e in rub["evidencias"] if e["tipo"] == "prueba"}
        declaradas = {t["id"] for t in x.pruebas.values() if rid in t["criterios_rubrica"]}
        if evid != declaradas:
            r.append(E(f"{rid}: evidencias {sorted(evid)} ≠ pruebas que lo citan {sorted(declaradas)}", "Haga coincidir `rubrica.evidencias` con `criterios_rubrica` de pruebas.yaml"))
    return r


@chequeo("V-22", "Todo objetivo OD tiene ≥ 1 prueba o indicador")
def v22(x: Infra):
    r = []
    for o in x.objetivos.values():
        if not o.get("indicador"):
            r.append(E(f"{o['id']}: sin indicador", "Complete el indicador de D1.6"))
        if not x.pruebas_de_objetivo(o["id"]):
            r.append(W(f"{o['id']}: sin pruebas que lo citen (solo indicador)", "Agregue el OD a una prueba que lo valide"))
    return r


@chequeo("V-23", "Toda amenaza AM tiene control y prueba")
def v23(x: Infra):
    r = []
    for a in x.amenazas.values():
        if not a.get("control"):
            r.append(E(f"{a['id']}: sin control", "Complete el control de D1.9"))
        if not a["pruebas"]:
            if a.get("prueba_justificacion"):
                r.append(W(f"{a['id']}: sin T-nn; se justifica «{a['prueba_justificacion'][:70]}…» (CI-18)", "Definir una prueba o aceptar la justificación"))
            else:
                r.append(E(f"{a['id']}: sin prueba ni justificación", "Asigne un T-nn o escriba `prueba_justificacion`"))
    return r


@chequeo("V-24", "Rúbrica R1–R8: pesos suman 100 y cada criterio tiene ≥ 1 evidencia")
def v24(x: Infra):
    r = []
    if sorted(x.rubrica) != [f"R{i}" for i in range(1, 9)]:
        r.append(E("La rúbrica debe tener R1–R8", "Transcriba los 8 criterios"))
    if sum(rr["peso"] for rr in x.rubrica.values()) != 100:
        r.append(E(f"Los pesos suman {sum(rr['peso'] for rr in x.rubrica.values())}, no 100", "Corrija los pesos según el XLSX oficial"))
    for rid, rr in x.rubrica.items():
        if not rr["evidencias"]:
            r.append(E(f"{rid}: sin evidencias declaradas", "Declare sección DOCX, figura, hoja XLSX o prueba"))
    return r


@chequeo("V-25", "Detecciones: ubicación existente y validación")
def v25(x: Infra):
    r = []
    for d in x.detecciones.values():
        v = d["validacion"]
        if not v["pruebas"]:
            if d.get("pendiente"):
                r.append(W(f"{d['id']} ({d['tecnologia']}): validación solo como escenario «{v['escenario']}», sin T-nn en D1.16 ({', '.join(ci._como_lista(d.get('cambio')))})",
                           "Definir una prueba T-nn en S2 o aceptar el escenario"))
            else:
                r.append(E(f"{d['id']}: sin prueba ni `pendiente`", "Asigne un T-nn de D1.16 o marque `pendiente` con su CI"))
    return r


@chequeo("V-26", "Correspondencia contenidos mínimos (1–15) → secciones del DOCX cubre las 11 secciones")
def v26(x: Infra):
    r = []
    cubiertas = {s for c in x.traz["correspondencia_contenidos"] for s in c["secciones_docx"]}
    cubiertas |= {s for c in x.traz.get("correspondencia_adicional", []) for s in c.get("secciones_docx", [])}
    for sid in x.secciones:
        # cubierta si ella, un ancestro (3 → 3.1) o un descendiente (5 → 5.1) está en la correspondencia
        if not any(c == sid or sid.startswith(c + ".") or c.startswith(sid + ".") for c in cubiertas):
            r.append(E(f"La sección {sid} del DOCX no corresponde a ningún contenido mínimo", "Asigne la sección en correspondencia_contenidos"))
    if sorted(c["n"] for c in x.traz["correspondencia_contenidos"]) != list(range(1, 16)):
        r.append(E("Los contenidos mínimos deben numerarse 1–15 sin huecos", "Corrija `n`"))
    if x.traz.get("correspondencia_pendiente"):
        r.append(W("La correspondencia 1–15 → DOCX es una propuesta: el documento maestro no incluye la tabla (CI-02)", "Confirmar o sustituir con la tabla oficial"))
    return r


@chequeo("V-27", "Cobertura de las denegaciones de la matriz por pruebas (informativo)")
def v27(x: Infra):
    den = [(a, b) for (a, b), c in x.matriz_esperada().items() if c["estado"] == "denegado"]
    sin = [f"{a}>{b}" for a, b in den if not x.pruebas_de_celda(f"{a}>{b}")]
    return [I(f"{len(den) - len(sin)} de {len(den)} celdas denegadas tienen una prueba dedicada; el resto se cubre por la política deny-all (OD-06) y las reglas de denegación con registro")]


# --------------------------------------------------------------------------------------------------
# V-28 … V-34: integridad del contrato, secretos, VPN, servicios base, modo L, rúbrica oficial
# --------------------------------------------------------------------------------------------------


@chequeo("V-28", "Inventario v0.4 completo: D1.12, VPC/subredes D2.5, D1.11 (F1–F33), D1.16 (T01–T60), 7 VLAN")
def v28(x: Infra):
    r = []
    faltan = [c for c in ci.COMPONENTES_D112 if c not in x.componentes]
    if faltan:
        r.append(E(f"Faltan componentes vigentes de D1.12 v0.4: {faltan}", "Agréguelos a inventory.yaml"))
    for c in ci.COMPONENTES_TEMPORALES:
        if x.componentes.get(c, {}).get("estado") != "temporal":
            r.append(E(f"{c} debe existir con estado «temporal» (simulacro T59)", "Agréguelo (CI-36)"))
    for c in ci.COMPONENTES_RETIRADOS:
        if c not in x.componentes_retirados:
            r.append(E(f"{c} debe quedar con estado «retirado» (no borrado, no vigente)", "Restituya el componente con `estado: retirado` y `retirado_por`"))
    for e in list(x.zonas_retiradas.values()) + list(x.componentes_retirados.values()) + list(x.flujos_retirados.values()) + list(x.pruebas_retiradas.values()):
        if not e.get("retirado_por"):
            r.append(E(f"{e['id']}: retirado sin `retirado_por` (CI-nn)", "Indique la entrada de CAMBIOS-INVENTARIO.md que lo retira"))
    aws = [c for c in x.componentes.values() if c["tipo"] in ("aws_vpc", "aws_subred")]
    if len(aws) != 3:
        r.append(E(f"Grupos AWS vigentes: {len(aws)} (esperados: 1 VPC + pub-a y app-a de D2.5 v0.4)", "Deje AWS-VPC, AWS-PUB-A y AWS-APP-A"))
    vlans = sorted(z["vlan"] for z in x.zonas.values() if z["tipo"] == "interna")
    if vlans != [10, 20, 30, 40, 41, 50, 60]:
        r.append(E(f"VLAN internas {vlans} ≠ las 7 de D1.8 v0.4", "Corrija las zonas"))
    for z in ("MGMT", "SERVERS", "LAB", "DMZ-SVC", "DMZ-HONEY", "SECURITY", "EDGE", "TRANSITO", "WIFI-EST", "AWS", "INTERNET"):
        if z not in x.zonas:
            r.append(E(f"Falta la zona {z}", "Agréguela"))
    for z in ("LAB-TEST", "STORAGE", "BACKUP"):
        if z not in x.zonas_retiradas:
            r.append(E(f"La zona {z} debe quedar «retirada»", "CI-39"))
    esperados_f = [f"F{n}" for n in range(1, 34)]
    ids_f = [f["id"] for f in x.inv["flujos"]]
    if ids_f != esperados_f:
        r.append(E(f"Los flujos deben ser F1…F33 sin huecos ni repeticiones y son {ids_f[0]}…{ids_f[-1]} ({len(ids_f)})", "Restituya los IDs (los retirados se conservan)"))
    retirados_f = sorted(x.flujos_retirados, key=lambda i: int(i[1:]))
    if retirados_f != sorted(["F9", "F11", "F12", "F15", "F16", "F17", "F19", "F22", "F23"], key=lambda i: int(i[1:])):
        r.append(E(f"Flujos retirados {retirados_f} ≠ F9, F11, F12, F15, F16, F17, F19, F22, F23 (D1.11 v0.4 y CI-52)", "CI-35, CI-36, CI-39, CI-52"))
    esperados_t = [f"T{n:02d}" for n in range(1, 61)]
    ids_t = [t["id"] for t in x.pru["pruebas"]]
    if ids_t != esperados_t:
        r.append(E(f"Las pruebas deben ser T01…T60 sin huecos y son {ids_t[0]}…{ids_t[-1]} ({len(ids_t)})", "Restituya los IDs (los retirados se conservan)"))
    if sorted(x.pruebas_retiradas) != ["T12", "T22", "T37", "T38", "T39", "T41", "T44", "T48"]:
        r.append(E(f"Pruebas retiradas {sorted(x.pruebas_retiradas)} ≠ T12, T22, T37, T38, T39, T41, T44, T48 (D1.16 v0.4)", "CI-41"))
    return r


@chequeo("V-29", "Pendientes (`pendiente: true`) registrados en CAMBIOS-INVENTARIO.md")
def v29(x: Infra):
    r = []
    registrados = ci.ids_en_cambios()
    if not registrados:
        return [E("No se encontró docs/infra/e1/CAMBIOS-INVENTARIO.md o no tiene entradas CI-nn", "Cree el registro con encabezados «### CI-nn»")]
    usados = set()
    for origen, cid in x.referencias_cambio():
        usados.add(cid)
        if cid not in registrados:
            r.append(E(f"{origen}: referencia {cid}, que no está en CAMBIOS-INVENTARIO.md", f"Registre {cid} en docs/infra/e1/CAMBIOS-INVENTARIO.md"))

    def sin_cambio(nodo, ruta):
        if isinstance(nodo, dict):
            if nodo.get("pendiente") and not nodo.get("cambio"):
                r.append(E(f"{ruta}: `pendiente: true` sin `cambio`", "Indique la entrada CI-nn que lo registra"))
            for k, v in nodo.items():
                sin_cambio(v, f"{ruta}/{k}")
        elif isinstance(nodo, list):
            for i, v in enumerate(nodo):
                sin_cambio(v, f"{ruta}[{v.get('id', i) if isinstance(v, dict) else i}]")
    for n, d in (("inventory", x.inv), ("pruebas", x.pru), ("trazabilidad", x.traz)):
        sin_cambio(d, n)
    pend = len(x.referencias_cambio())
    r.append(I(f"{pend} elementos pendientes en los YAML; {len(registrados)} entradas CI en CAMBIOS-INVENTARIO.md; sin referencia desde los YAML: {sorted(registrados - usados) or 'ninguna'}"))
    return r


PATRONES_SECRETOS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "llave privada"),
    (re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"), "llave de acceso de AWS"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "token de GitHub"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"), "token de Slack"),
    (re.compile(r"(?i)\b(secret|passwd|password|api[_-]?key|access[_-]?key|token)\b\s*[:=]\s*[\"']?[A-Za-z0-9/+_\-]{16,}"), "credencial asignada"),
]


@chequeo("V-30", "Sin secretos, llaves ni credenciales en infra/, docs/infra/, Makefile y CI")
def v30(x: Infra):
    r = []
    objetivos = []
    for sub, patrones in (("infra", ("*.yaml", "*.py", "*.json", "*.txt")), ("docs/infra", ("*.md",)), (".github", ("*.yml", "*.yaml"))):
        for p in patrones:
            objetivos += list((x.raiz / sub).rglob(p))
    if (x.raiz / "Makefile").exists():
        objetivos.append(x.raiz / "Makefile")
    for f in objetivos:
        if f.name == "validate.py":
            continue                      # contiene los patrones de búsqueda
        for n, linea in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for pat, que in PATRONES_SECRETOS:
                if pat.search(linea):
                    r.append(E(f"{f.relative_to(x.raiz)}:{n}: posible {que}", "Quite el valor; los secretos van cifrados con SOPS o en variables de entorno, nunca en el repositorio"))
    return r


@chequeo("V-31", "VPN (D1.10 v0.4): ASN, /30 de túnel, NAT-T, MTU/MSS, temporizadores y flujos sobre la VPN")
def v31(x: Infra):
    r = []
    v = x.inv["vpn"]
    if not 64512 <= v["extremo_onpremise"]["asn"] <= 65534 or not 64512 <= v["extremo_aws"]["asn"] <= 65534:
        r.append(E("Los ASN deben ser privados (64512–65534)", "Corrija el ASN"))
    if v["extremo_onpremise"]["asn"] == v["extremo_aws"]["asn"]:
        r.append(E("Los dos extremos tienen el mismo ASN (eBGP exige ASN distintos)", "Use 65020 y 64512"))
    # v0.4: la IP pública es del FortiGate (NAT 1:1 hacia FW01) y FW01 usa NAT-T
    fgt_pub = next((i["ip"] for i in x.componentes["FGT-EXT"]["ips"] if i["interfaz"] == "wan"), None)
    wan = next(i["ip"] for i in x.componentes["FW01"]["ips"] if i["interfaz"] == "wan")
    on = v["extremo_onpremise"]
    if on["ip_publica"] != fgt_pub:
        r.append(E(f"IP pública de la VPN {on['ip_publica']} ≠ IP pública de FGT-EXT {fgt_pub}", "Use la misma IP"))
    if on.get("ip_publica_en") != "FGT-EXT":
        r.append(E("vpn.extremo_onpremise.ip_publica_en debe ser FGT-EXT (D-26)", "Agréguelo"))
    if on.get("ip_interna") != wan:
        r.append(E(f"vpn.extremo_onpremise.ip_interna {on.get('ip_interna')} ≠ WAN de FW01 {wan}", "Haga coincidir ambos"))
    if on.get("nat_t") is not True:
        r.append(E("FW01 está detrás de NAT: nat_t debe ser true (D1.10)", "Agregue `nat_t: true`"))
    if (on.get("identidad_ike") or {}).get("valor") != on["ip_publica"]:
        r.append(E("La identidad IKE de FW01 debe ser la IP pública (D1.10)", "Agregue `identidad_ike`"))
    for t in v["tuneles"]:
        comp = x.componentes.get(t["id"])
        if comp is None or comp.get("cidr") != t["red_interna"]:
            r.append(E(f"{t['id']}: la red interna {t['red_interna']} no coincide con el componente", "Haga coincidir el CIDR del componente con `vpn.tuneles`"))
    if v["mss_clamping"] > v["mtu"] - 40:
        r.append(E(f"MSS {v['mss_clamping']} > MTU {v['mtu']} − 40", "El MSS debe caber en la MTU (IPv4 + TCP = 40 bytes)"))
    if v["bgp"]["hold_s"] < 3 * v["bgp"]["keepalive_s"]:
        r.append(E("El hold de BGP debe ser ≥ 3 × keepalive", "Use keepalive 10 s y hold 30 s"))
    # flujos que cruzan la VPN: los que tienen un extremo en AWS y no nacen en Internet (F29 entra por la IP pública de EC2-GW)
    with_aws = {f["id"] for f in x.flujos.values() if f["estado"] == "activo"
                and any(e.zona == "AWS" for lado in ("origen", "destino") for e in x.extremos(f, lado))
                and not any(e.zona == "INTERNET" for e in x.extremos(f, "origen"))}
    if with_aws != set(v["flujos_sobre_vpn"]):
        r.append(E(f"Flujos con extremo en AWS por la VPN {sorted(with_aws)} ≠ vpn.flujos_sobre_vpn {sorted(v['flujos_sobre_vpn'])}", "Haga coincidir ambas listas"))
    for t in v["pruebas"]:
        if t not in x.pruebas:
            r.append(E(f"vpn.pruebas: {t} no existe o está retirada", "Corrija el ID"))
    if v["convergencia_meta_s"] != 60:
        r.append(E("La meta de convergencia de D1.10/OD-05 es 60 s", "Use 60"))
    return r


@chequeo("V-32", "Servicios base (DHCP, DNS, PAC, NTP, IPv6, DNS cifrado, Wi-Fi) consistentes con el inventario (D-28)")
def v32(x: Infra):
    r = []
    sb = x.inv["servicios_base"]
    ip = {c: {i["interfaz"]: i["ip"] for i in x.componentes[c]["ips"]} for c in x.componentes}
    if sb["dns"]["servidor"]["componente"] != "FW01" or sb["ntp"]["servidor"]["componente"] != "FW01":
        r.append(E("DNS y NTP deben estar en FW01 (D-28)", "servicios_base.dns.servidor y .ntp.servidor = FW01"))
    registros = [reg["componente"] for reg in sb["pac"]["registros_a"]]
    if registros != ["EDGE01", "EDGE02"]:
        r.append(E(f"El PAC lo sirven EDGE01 y EDGE02 con dos registros A y es {registros}", "Corrija registros_a"))
    for reg in sb["pac"]["registros_a"]:
        if reg["ip"] != ip[reg["componente"]]["eth0"]:
            r.append(E(f"PAC: {reg['componente']} {reg['ip']} ≠ IP del componente", "Haga coincidir la IP"))
    for nombre, bloque in sb.items():
        for fid in bloque.get("flujos", []):
            _existe(r, f"servicios_base.{nombre}", fid, set(x.flujos), "flujo")
        for tid in bloque.get("pruebas", []):
            _existe(r, f"servicios_base.{nombre}", tid, set(x.pruebas), "prueba")
        for od in bloque.get("objetivos", []):
            _existe(r, f"servicios_base.{nombre}", od, set(x.objetivos), "objetivo")
        for cid in bloque.get("componentes", []):
            _existe(r, f"servicios_base.{nombre}", cid, set(x.componentes), "componente")
        for sid in bloque.get("supuestos", []):
            _existe(r, f"servicios_base.{nombre}", sid, set(x.supuestos), "supuesto")
    return r


@chequeo("V-33", "Lo emulado se rotula como emulado: pruebas en Modo L solo con componentes emulados (F4.2)")
def v33(x: Infra):
    r = []
    for t in x.pruebas.values():
        if "L" not in t["modos"]:
            continue
        for lado in ("origen", "destino"):
            for crudo in _orig_dest(t[lado]):
                for e in x.resolver(crudo):
                    if e.tipo != "componente" or e.componente is None:
                        continue
                    eq = x.componentes[e.componente]["emulacion_lab"]["equivalencia"]
                    if eq == "no_emulado":
                        msg = f"{t['id']} (Modo L): {lado} {e.componente} no se emula en el laboratorio (F4.1/F4.2)"
                        if t.get("pendiente"):
                            r.append(W(msg + f" — registrado ({', '.join(ci._como_lista(t.get('cambio')))})", "Quitar L de `modos` o agregar el nodo a la topología F4.1"))
                        else:
                            r.append(E(msg, "Quite L de `modos` o emule el componente y regístrelo en F4.1"))
    for c in x.componentes.values():
        if c["estado"] == "emulado_en_lab" and c["emulacion_lab"]["equivalencia"] == "no_emulado":
            r.append(E(f"{c['id']}: estado emulado_en_lab sin equivalencia", "Documente la equivalencia (F4.2)"))
    return r


@chequeo("V-34", "La rúbrica coincide con el XLSX oficial (nombre, peso y descriptor de nivel 4)")
def v34(x: Infra):
    if not ci.RUBRICA_XLSX.exists():
        return [W(f"No se encontró {ci.RUBRICA_XLSX.relative_to(x.raiz)}", "Restaure el XLSX oficial de docs/fuentes/CE03/")]
    import openpyxl

    def limpia(t):
        return re.sub(r"\s+", " ", str(t).replace("**", "")).strip()

    ws = openpyxl.load_workbook(ci.RUBRICA_XLSX, read_only=True, data_only=False)["Rúbrica"]
    r = []
    for fila in ws.iter_rows(min_row=5, max_row=12, values_only=True):
        rid = f"R{int(fila[0])}"
        mio = x.rubrica.get(rid)
        if mio is None:
            r.append(E(f"{rid} no está en trazabilidad.yaml", "Agréguelo"))
            continue
        if limpia(fila[1]) != limpia(mio["nombre"]):
            r.append(E(f"{rid}: el nombre difiere del XLSX oficial", "Copie el nombre del XLSX"))
        if int(fila[2]) != mio["peso"]:
            r.append(E(f"{rid}: peso {mio['peso']} ≠ {int(fila[2])} del XLSX", "Copie el peso del XLSX"))
        if limpia(fila[3]) != limpia(mio["descriptor_nivel_4"]):
            r.append(E(f"{rid}: el descriptor de nivel 4 difiere del XLSX oficial", "Copie el descriptor del XLSX sin modificarlo"))
    return r


# --------------------------------------------------------------------------------------------------
# V-40 … V-43: artefactos generados del laboratorio y resultados de las pruebas (Etapa 7)
# --------------------------------------------------------------------------------------------------

PARES_AWS_DOC = ["198.51.100.21", "198.51.100.22"]      # RFC 5737: solo para poder generar (CI-23)


def _cruza_fw01(x: Infra, f: dict) -> bool:
    """¿Algún par origen→destino del flujo pasa por FW01? (si todo es una misma VLAN, FW01 no ve el tráfico)."""
    for o in x.extremos(f, "origen"):
        for d in x.extremos(f, "destino"):
            if o.zona == "INTERNET" and d.zona == "AWS":
                continue          # F29 no pasa por FW01 (entra por la IP pública de EC2-GW)
            if o.es_firewall or d.es_firewall or o.zona != d.zona:
                return True
    return False


def _puertos_de_regla(linea: str) -> set[tuple[str, int]]:
    out = set()
    m = re.search(r"meta l4proto \. th dport \{([^}]*)\}", linea)
    if m:
        for par in m.group(1).split(","):
            pr, _, pt = par.partition(" . ")
            out.add((pr.strip(), int(pt)))
    for m in re.finditer(r"\b(tcp|udp) dport (\{[^}]*\}|\d+)", linea):
        for pt in re.findall(r"\d+", m.group(2)):
            out.add((m.group(1), int(pt)))
    return out


def _puertos_permitidos(f: dict) -> set[tuple[str, int]]:
    """Puertos del flujo, con el original y el traducido por DNAT (la regla NAT usa el original; forward, el traducido)."""
    out = set()
    for p in f["protocolos"]:
        if p["proto"] in ("tcp", "udp"):
            for pt in p["puertos"]:
                out.add((p["proto"], pt))
                out.add((p["proto"], (p.get("dnat") or {}).get(str(pt), pt)))
    return out


def _verbo(linea: str) -> str:
    return "drop" if " drop" in linea else "dnat" if " dnat to" in linea else "accept" if " accept" in linea else "?"


def ruleset_contra_inventario(x: Infra, texto: str, modo: str, ventana: bool) -> list[Hallazgo]:
    """Compara un ruleset de nftables con los flujos del inventario: ni una regla de más, ni una de menos."""
    r = []
    etiqueta = f"modo={modo}{' +ventana' if ventana else ''}"
    por_flujo: dict[str, list[str]] = {}
    for linea in texto.splitlines():
        s = linea.strip()
        if not s or s.startswith(("#", "type ")):       # «type … policy accept» declara una cadena, no una regla
            continue
        m = re.search(r'comment "(F\d+)\b', s)
        if m:
            por_flujo.setdefault(m.group(1), []).append(s)
        if re.match(r"(counter\s+)?accept\b", s):
            r.append(E(f"[{etiqueta}] regla que acepta todo sin condición: «{s}»", "Toda regla accept debe llevar interfaz, dirección o puerto"))
        elif " accept" in f" {s}" and not m:
            ok = s.startswith("ct state established,related accept") or re.match(r'[io]ifname "lo" accept', s) or "(sin F-nn" in s
            if not ok:
                r.append(E(f"[{etiqueta}] regla accept sin flujo F-nn ni rótulo «sin F-nn»: «{s[:110]}»",
                           "Agregue el flujo a D1.11 o rotule la regla como «sin F-nn» (CI-23)"))
    for cadena in ("input", "forward", "output"):
        if not re.search(rf"hook {cadena} priority 0; policy drop;", texto):
            r.append(E(f"[{etiqueta}] la cadena {cadena} no tiene política drop", "La política por defecto de FW01 es denegar (D1.13)"))
    flujos = {f["id"]: f for f in x.inv["flujos"]}
    for fid in sorted(set(por_flujo) - set(flujos)):
        r.append(E(f"[{etiqueta}] el ruleset tiene reglas de {fid}, que no existe en el inventario", "Regenere el ruleset (make gen)"))
    for fid, f in flujos.items():
        lineas = por_flujo.get(fid, [])
        verbos = {_verbo(linea) for linea in lineas}
        if f["estado"] != "activo":
            if lineas:
                r.append(E(f"[{etiqueta}] {fid} está {f['estado']} y tiene regla en el ruleset", "Un flujo no activo no se abre"))
            continue
        if f["accion"] == "bloquear":
            if "accept" in verbos or "dnat" in verbos:
                r.append(E(f"[{etiqueta}] {fid} es un bloqueo y el ruleset lo acepta", "Un flujo con accion=bloquear solo genera drop"))
            elif not lineas:
                r.append(E(f"[{etiqueta}] {fid} es un bloqueo y no tiene regla drop", "Regenere el ruleset"))
        else:
            sin_regla = (f["modo"] == "piloto" and modo != "piloto") or (fid == "F24" and not ventana) or not _cruza_fw01(x, f)
            if sin_regla:
                if lineas:
                    r.append(E(f"[{etiqueta}] {fid} no debe estar abierto en este modo y tiene {len(lineas)} regla(s)",
                               "F6 solo en piloto; F24 solo con ventana autorizada; lo local a una VLAN no pasa por FW01"))
                continue
            if not lineas:
                r.append(E(f"[{etiqueta}] {fid} está permitido y no tiene regla", "Regenere el ruleset"))
                continue
            if "drop" in verbos or "?" in verbos:
                r.append(E(f"[{etiqueta}] {fid} está permitido y una de sus reglas no es accept/dnat", "Regenere el ruleset"))
            if any(p["proto"] in ("tcp", "udp") and p["puertos"] for p in f["protocolos"]):
                for linea in lineas:
                    if " dnat to" not in linea and not _puertos_de_regla(linea):
                        r.append(E(f"[{etiqueta}] {fid}: regla sin protocolo ni puerto (acepta cualquier tráfico entre los extremos): «{linea[:100]}»",
                                   "La regla debe limitar protocolo y puerto"))
        esperado = _puertos_permitidos(f)
        vistos = set().union(*[_puertos_de_regla(linea) for linea in lineas]) if lineas else set()
        if vistos - esperado:
            r.append(E(f"[{etiqueta}] {fid}: puertos abiertos fuera del inventario: {sorted(vistos - esperado)}", "Los puertos salen solo de `protocolos` del flujo"))
        if lineas and esperado - vistos:
            r.append(E(f"[{etiqueta}] {fid}: puertos del inventario sin regla: {sorted(esperado - vistos)}", "Regenere el ruleset"))
    for fid, lineas in por_flujo.items():
        f = flujos.get(fid)
        if f and any(" dnat to" in linea for linea in lineas) and not any(e.zona == "INTERNET" for e in x.extremos(f, "origen")):
            r.append(E(f"[{etiqueta}] {fid} tiene DNAT y su origen no es INTERNET", "El DNAT es solo de entrada desde Internet (F21, F24)"))
    return r


@chequeo("V-40", "El ruleset generado de fw01-sim contiene exactamente los flujos permitidos (y los bloqueos) del inventario")
def v40(x: Infra):
    from gen import nftables
    r = []
    for modo, ventana in (("piloto", False), ("gestionado", False), ("piloto", True)):
        r += ruleset_contra_inventario(x, nftables.generar(x, modo=modo, ventana=ventana, aws_peers=PARES_AWS_DOC), modo, ventana)
    return r


_CIFRADO = {"AES-256-GCM-16": "aes256gcm16"}
_PRF = {"SHA2-384": "prfsha384"}
_DH = {20: "ecp384"}


def vpn_contra_inventario(x: Infra, lado: str, swanctl_txt: str, frr_txt: str, vti_txt: str) -> list[Hallazgo]:
    """Compara swanctl.conf, frr.conf y vti-up.sh de un lado con la sección `vpn` del inventario."""
    import ipaddress
    v = x.inv["vpn"]
    r = []
    mio, otro = (v["extremo_onpremise"], v["extremo_aws"]) if lado == "fw01" else (v["extremo_aws"], v["extremo_onpremise"])
    pref = f"[{lado}]"
    # ---- swanctl
    conns = re.findall(r"^  (tunel\d+) \{\n(.*?)^  \}$", swanctl_txt, re.S | re.M)
    if len(conns) != len(v["tuneles"]):
        r.append(E(f"{pref} swanctl.conf tiene {len(conns)} conexiones y el inventario {len(v['tuneles'])} túneles", "Regenere (make gen)"))
    f1, f2 = v["fase1"], v["fase2"]
    dh1 = int(re.search(r"\d+", f1["dh"]).group())
    dh2 = int(re.search(r"\d+", f2["pfs"]).group())
    esperado_ike = [_CIFRADO.get(f1["cifrado"]), _PRF.get(f1["prf"]), _DH.get(dh1)]
    esperado_esp = [_CIFRADO.get(f2["cifrado"]), _DH.get(dh2)]
    if None in esperado_ike + esperado_esp:
        r.append(W(f"{pref} algoritmo de fase 1/2 sin equivalente conocido por el validador: {f1['cifrado']}, {f1['prf']}, {f1['dh']}",
                   "Agregue el equivalente a _CIFRADO/_PRF/_DH de validate.py"))
    for i, (nombre, cuerpo) in enumerate(conns):
        n = i + 1

        def campo(k, _c=cuerpo):
            m = re.search(rf"^\s+{k} = (.+)$", _c, re.M)
            return m.group(1).strip() if m else None

        comprobar = [
            ("proposals", "-".join(esperado_ike) if None not in esperado_ike else None),
            ("esp_proposals", "-".join(esperado_esp) if None not in esperado_esp else None),
            ("rekey_time", f"{f1['vida_s']}s"), ("life_time", f"{f2['vida_s']}s"),
            ("dpd_delay", f"{v['dpd']['intervalo_s']}s"), ("dpd_action", v["dpd"]["accion"]),
            ("mark_in", str(n)), ("mark_out", str(n)), ("version", "2"),
            ("start_action", "start" if lado == "fw01" else "none"),
        ]
        for k, esp in comprobar:
            if esp is not None and campo(k) != esp:
                r.append(E(f"{pref} {nombre}: {k} = {campo(k)} y el inventario pide {esp}", "Regenere desde la sección vpn del inventario"))
        on = v["extremo_onpremise"]
        propio = "local_addrs" if lado == "fw01" else "remote_addrs"
        esperado_prop = on["ip_interna"] if (lado == "fw01" and on.get("nat_t")) else on["ip_publica"]     # NAT-T: FW01 escucha en su IP de tránsito
        if campo(propio) != esperado_prop:
            r.append(E(f"{pref} {nombre}: {propio} = {campo(propio)} y el inventario pide {esperado_prop}", "Regenere"))
        if on.get("nat_t") and campo("encap") != "yes":
            r.append(E(f"{pref} {nombre}: encap = {campo('encap')}; con NAT-T (D1.10) debe ser yes", "Regenere"))
        if lado == "fw01" and re.search(r"local \{[^}]*id = ([^\n]+)", cuerpo, re.S) and re.search(r"local \{[^}]*id = ([^\n]+)", cuerpo, re.S).group(1).strip() != on["ip_publica"]:
            r.append(E(f"{pref} {nombre}: la identidad IKE de FW01 debe ser la IP pública {on['ip_publica']}", "Regenere"))
    # ---- FRR
    asn = re.search(r"^router bgp (\d+)", frr_txt, re.M)
    if not asn or int(asn.group(1)) != mio["asn"]:
        r.append(E(f"{pref} frr.conf: router bgp {asn.group(1) if asn else '—'} y el inventario pide {mio['asn']}", "Regenere"))
    esperados = {}
    for t in v["tuneles"]:
        h = list(ipaddress.ip_network(t["red_interna"]).hosts())
        esperados[str(h[0] if lado == "fw01" else h[1])] = t
    vecinos = dict(re.findall(r"^ neighbor (\S+) remote-as (\d+)", frr_txt, re.M))
    if set(vecinos) != set(esperados):
        r.append(E(f"{pref} frr.conf: vecinos {sorted(vecinos)} ≠ {sorted(esperados)} (host de cada /30 del inventario)", "Regenere"))
    for ip, rem in vecinos.items():
        if int(rem) != otro["asn"]:
            r.append(E(f"{pref} frr.conf: el vecino {ip} usa remote-as {rem} y el inventario pide {otro['asn']}", "Regenere"))
    for ip, k, h in re.findall(r"^ neighbor (\S+) timers (\d+) (\d+)", frr_txt, re.M):
        if (int(k), int(h)) != (v["bgp"]["keepalive_s"], v["bgp"]["hold_s"]):
            r.append(E(f"{pref} frr.conf: timers {k}/{h} del vecino {ip} ≠ {v['bgp']['keepalive_s']}/{v['bgp']['hold_s']} del inventario", "Regenere"))
    if not re.search(r"^\s+maximum-paths 1$", frr_txt, re.M):
        r.append(E(f"{pref} frr.conf: falta `maximum-paths 1` (D1.10: un solo túnel a la vez, sin ECMP)", "Regenere"))
    redes = sorted(re.findall(r"^  network (\S+)", frr_txt, re.M))
    if redes != sorted(mio["redes_anunciadas"]):
        r.append(E(f"{pref} frr.conf: redes anunciadas {redes} ≠ {sorted(mio['redes_anunciadas'])}", "Regenere"))
    con_prepend = set(re.findall(r"^  neighbor (\S+) route-map PREPEND-\S+ out", frr_txt, re.M))
    esperados_prepend = {ip for ip, t in esperados.items() if t.get("bgp_as_path_prepending")} if lado == "fw01" else set()
    if con_prepend != esperados_prepend:
        r.append(E(f"{pref} frr.conf: prepending en {sorted(con_prepend)} y el inventario lo pide en {sorted(esperados_prepend)}",
                   "Solo el túnel de respaldo de FW01 lleva AS-path prepending"))
    # ---- VTI
    mtus = set(re.findall(r"mtu (\d+) up", vti_txt))
    if mtus != {str(v["mtu"])}:
        r.append(E(f"{pref} vti-up.sh: MTU {sorted(mtus)} ≠ {v['mtu']} del inventario", "Regenere"))
    claves = re.findall(r"key (\d+)", vti_txt)
    if claves != [str(i + 1) for i in range(len(v["tuneles"]))]:
        r.append(E(f"{pref} vti-up.sh: claves VTI {claves} no coinciden con las marcas de swanctl.conf", "Regenere"))
    return r


@chequeo("V-41", "swanctl, FRR y VTI generados coinciden con la sección vpn del inventario (cifrado, DPD, vidas, ASN, BGP, MTU, MSS)")
def v41(x: Infra):
    from gen import nftables, vpn
    r = []
    for lado in ("fw01", "vgw"):
        r += vpn_contra_inventario(x, lado, vpn.swanctl(x, lado, PARES_AWS_DOC), vpn.frr(x, lado), vpn.vti_up(x, lado, PARES_AWS_DOC))
    mss = re.findall(r"maxseg size set (\d+)", nftables.generar(x, aws_peers=PARES_AWS_DOC))
    if mss != [str(x.inv["vpn"]["mss_clamping"])]:
        r.append(E(f"El ruleset fija MSS {mss} y el inventario pide {x.inv['vpn']['mss_clamping']}", "Regenere el ruleset"))
    return r


def evaluar_resultados(x: Infra, datos: dict, origen: str) -> list[Hallazgo]:
    """FALLA en una prueba crítica = error. Crítica que aplica al modo y no está en PASA, o FALLA no crítico = advertencia."""
    r = []
    modo = str(datos.get("meta", {}).get("modo", ""))[:1]
    por_id = {t["id"]: t for t in datos["resultados"]}
    for tid in sorted(por_id):
        if tid in x.pruebas_retiradas:
            r.append(I(f"{origen}: {tid} está retirada en la v0.4 y se ignora en los resultados del ensayo (v0.2)"))
        elif tid not in x.pruebas:
            r.append(E(f"{origen}: {tid} no existe en pruebas.yaml", "Vuelva a ejecutar make test-lab con el inventario actual"))
    for t in x.pruebas.values():
        res = por_id.get(t["id"])
        aplica = modo in t["modos"]
        if res is None:
            if aplica:
                r.append(W(f"{origen}: {t['id']} aplica al modo {modo} y no está en los resultados", "Vuelva a ejecutar make test-lab"))
            continue
        estado = res["resultado"]
        if t["critica"]:
            if estado == "FALLA":
                r.append(E(f"{origen}: la prueba crítica {t['id']} ({t['nombre']}) FALLA",
                           "Corrija el diseño o la implementación; una prueba crítica en FALLA invalida un límite de seguridad"))
            elif aplica and estado != "PASA":
                r.append(W(f"{origen}: la prueba crítica {t['id']} ({t['nombre']}) está en {estado}, no en PASA", "Complete la prueba o registre por qué no aplica (CI-16)"))
            elif res.get("error_de_ejecucion"):
                r.append(W(f"{origen}: la prueba crítica {t['id']} terminó con error de ejecución", "Repita la prueba"))
        elif estado == "FALLA":
            r.append(W(f"{origen}: {t['id']} ({t['nombre']}) FALLA (no es crítica)", "Revise el hallazgo en docs/infra/e1/ensayo-laboratorio.md"))
    return r


@chequeo("V-42", "Los últimos resultados de make test-lab no tienen FALLA en pruebas críticas")
def v42(x: Infra):
    carpeta, datos = ci.resultados_mas_recientes(x.raiz)
    if datos is None:
        return [W("No hay evidencias/*/resultados.json: no se ha ejecutado make test-lab", "Ejecute make lab-up && make test-lab y versione resultados.json")]
    meta = datos.get("meta", {})
    return [I(f"Resultados de {carpeta.name} (commit {str(meta.get('commit', '—'))[:7]}): {meta.get('resumen', {})}")] + evaluar_resultados(x, datos, carpeta.name)


@chequeo("V-43", "Los artefactos generados versionados (tfvars de OpenTofu, topología de containerlab) están al día con el inventario")
def v43(x: Infra):
    from gen import lab, tofu
    r = []
    for etiqueta, ruta, generar, prompt in (("OpenTofu", x.raiz / "deploy/opentofu/envs/demo/diseno.auto.tfvars.json", lambda: tofu.texto(x), "I3"),
                                            ("containerlab", x.raiz / "lab/celeris.clab.yml", lambda: lab.topologia_yaml(x), "I2")):
        try:
            texto = generar()
        except Exception as exc:   # el generador aún lee la v0.2 (SVC01, WAF01, EC2-SHIELD…): lo actualiza el prompt I2/I3
            r.append(W(f"El generador de {etiqueta} no puede leer el inventario v0.4 ({exc!r}); queda pendiente de {prompt}",
                       f"Adaptar infra/gen/{'tofu' if prompt == 'I3' else 'lab'}.py a la v0.4 ({prompt}) y regenerar {ruta.relative_to(x.raiz)}"))
            continue
        if not ruta.exists():
            r.append(W(f"Falta {ruta.relative_to(x.raiz)}", "Genérelo (make tofu-gen / make lab-gen) y versiónelo"))
        elif ruta.read_text(encoding="utf-8").replace("\r\n", "\n") != texto:
            r.append(E(f"{ruta.relative_to(x.raiz)} no coincide con el inventario", "Regénerelo (make tofu-gen / make lab-gen) y commitee el resultado"))
    return r


# --------------------------------------------------------------------------------------------------
# V-44 … V-45: v0.4 (retirados y BYOD)
# --------------------------------------------------------------------------------------------------

CAMPOS_SIN_ESCANEO = {"nota", "nota_modos", "observacion_ensayo", "retirado_por", "cambio", "pendiente", "confianza_nota", "ip_publica_nota", "hold_nota", "asn_nota", "redes_internas_nota"}


def _textos(nodo, ruta=""):
    """(ruta, texto) de cada cadena de un nodo, saltando los campos de nota."""
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if k in CAMPOS_SIN_ESCANEO:
                continue
            yield from _textos(v, f"{ruta}/{k}")
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo):
            yield from _textos(v, f"{ruta}[{i}]")
    elif isinstance(nodo, str):
        yield ruta, nodo


@chequeo("V-44", "Un ID retirado no se reutiliza ni aparece en flujos, pruebas, componentes, zonas, rúbrica o textos vigentes")
def v44(x: Infra):
    r = []
    ret = {"componente": set(x.componentes_retirados), "zona": set(x.zonas_retiradas), "flujo": set(x.flujos_retirados), "prueba": set(x.pruebas_retiradas)}
    todos = set().union(*ret.values())
    vigentes = set(x.componentes) | set(x.zonas) | set(x.flujos) | set(x.pruebas)
    for i in sorted(todos & vigentes):
        r.append(E(f"El ID retirado {i} también existe como vigente (reutilizado)", "Un ID retirado nunca se reutiliza: use el siguiente libre"))
    patron = re.compile(r"(?<![A-Za-z0-9-])(" + "|".join(re.escape(i) for i in sorted(todos, key=len, reverse=True)) + r")(?![A-Za-z0-9-])")
    fuentes = []
    for z in x.zonas.values():
        fuentes.append((f"zona {z['id']}", z))
    for c in x.componentes.values():
        fuentes.append((f"componente {c['id']}", c))
    for f in x.flujos.values():
        fuentes.append((f"flujo {f['id']}", f))
    for t in x.pruebas.values():
        fuentes.append((f"prueba {t['id']}", t))
    for a in x.amenazas.values():
        fuentes.append((f"amenaza {a['id']}", a))
    for d in x.detecciones.values():
        fuentes.append((f"detección {d['id']}", d))
    for rid, rub in x.rubrica.items():
        fuentes.append((f"rúbrica {rid}", {"elementos": rub.get("elementos_evaluados", []), "evidencias": rub["evidencias"]}))
    for k in ("servicios_base", "rangos_lab", "vpn", "matriz_esperada", "aws"):
        fuentes.append((k, x.inv[k]))
    for origen, nodo in fuentes:
        for ruta, texto in _textos(nodo):
            for m in patron.finditer(texto):
                r.append(E(f"{origen}{ruta}: menciona el ID retirado {m.group(1)}", "Quite la referencia o use el componente que lo reemplaza (CAMBIOS-INVENTARIO.md)"))
    # una figura no puede dibujar un ID retirado: lo comprueba V-52 sobre los .drawio (pendiente de I4 mientras sean v0.2)
    for e in list(x.componentes_retirados.values()):
        if e.get("figuras"):
            r.append(E(f"{e['id']} está retirado y todavía declara figuras {e['figuras']}", "Deje `figuras: []` en un componente retirado"))
    return r


@chequeo("V-45", "Ningún flujo permite descifrado con origen WIFI-EST (REQ-F-36, REQ-RN-11)")
def v45(x: Infra):
    r = []
    for f in x.flujos.values():
        if f["estado"] != "activo" or f["accion"] != "permitir":
            continue
        if not any(e.zona == "WIFI-EST" or e.componente == "WIFI-EST" for e in x.extremos(f, "origen")):
            continue
        detalle = f["proteccion"]["detalle"] if f.get("proteccion") else ""
        destinos = {e.componente or e.zona for e in x.extremos(f, "destino")}
        if destinos & {"EDGE01", "EDGE02", "EDGE"}:
            if "passthrough" not in detalle.lower() or "nunca descifra" not in detalle.lower() and "sin descifr" not in detalle.lower():
                r.append(E(f"{f['id']}: viene de WIFI-EST hacia el nodo y su protección no declara passthrough ni «nunca descifra»", "REQ-F-36: el nodo nunca descifra esta red"))
            if "REQ-F-36" not in f["req"]:
                r.append(E(f"{f['id']}: debe citar REQ-F-36", "Agregue REQ-F-36 a `req`"))
        elif re.search(r"(?i)(CA limitada|certificado de la CA|descifra(r|do)?\b(?! esta)|intercept|mitm)", detalle):
            r.append(E(f"{f['id']}: un flujo de WIFI-EST describe descifrado en su protección", "REQ-F-36: el Wi-Fi de estudiantes nunca se descifra"))
    for cid in ("EDGE01", "EDGE02"):
        if "REQ-F-36" not in x.componentes[cid]["req"]:
            r.append(E(f"{cid}: debe citar REQ-F-36 (passthrough para WIFI-EST)", "Agregue REQ-F-36 a `req`"))
    return r


# --------------------------------------------------------------------------------------------------
# Ganchos P2–P5 (infra/checks/*.py)
# --------------------------------------------------------------------------------------------------


def ejecutar_ganchos(x: Infra) -> list[Resultado]:
    """Carga infra/checks/v*.py. Cada módulo define GRUPO, PRIMER_ID, DESCRIPCION y run(infra) → list[Resultado] | None.
    Si run devuelve None, el gancho aún no está implementado y se informa «PENDIENTE de P#»."""
    salida = []
    d = x.raiz / "infra" / "checks"
    for ruta in sorted(d.glob("v[5-9]0_*.py")):
        spec = importlib.util.spec_from_file_location(f"checks_{ruta.stem}", ruta)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        try:
            spec.loader.exec_module(mod)
            res = mod.run(x)
        except Exception as exc:  # un gancho roto no debe tumbar el validador, pero sí fallar
            salida.append(Resultado(mod.PRIMER_ID if hasattr(mod, "PRIMER_ID") else ruta.stem, f"{ruta.name}: excepción", "FALLA",
                                    [E(f"El gancho falló: {exc!r}", "Corrija infra/checks/" + ruta.name)]))
            continue
        if res is None:
            salida.append(Resultado(mod.PRIMER_ID, mod.DESCRIPCION, "PENDIENTE", [], f"pendiente de {mod.GRUPO}"))
        else:
            salida.extend(res)
    return salida


# --------------------------------------------------------------------------------------------------
# Ejecución e informe
# --------------------------------------------------------------------------------------------------


def estado_de(hs: list[Hallazgo]) -> str:
    if any(h.nivel == "error" for h in hs):
        return "FALLA"
    if any(h.nivel == "advertencia" for h in hs):
        return "ADVERTENCIA"
    return "PASA"


def correr(x: Infra) -> list[Resultado]:
    res = []
    for cid, titulo, fn in CHEQUEOS:
        try:
            hs = fn(x)
        except Exception as exc:
            hs = [E(f"El chequeo no pudo ejecutarse: {exc!r}", "Corrija primero los errores de V-01/V-03; si persiste, revise infra/validate.py")]
        res.append(Resultado(cid, titulo, estado_de(hs), hs))
    res.extend(ejecutar_ganchos(x))
    return res


ICONO = {"PASA": "PASA", "FALLA": "FALLA", "ADVERTENCIA": "PASA con advertencias", "PENDIENTE": "PENDIENTE"}


def informe_md(x: Infra, res: list[Resultado]) -> str:
    inv = x.inv
    L = []
    L.append("# Validación de la fuente única — CE0311 (Entregable 1)\n")
    L.append("> Generado por `infra/validate.py` (`make validate`). No editar a mano.\n")
    L.append(f"- Inventario: versión {inv['meta']['inventario_version']} · fecha {inv['meta']['fecha']}")
    act = sum(f["estado"] == "activo" for f in x.flujos.values())
    L.append(f"- Contenido cargado (v0.4): **{len(x.zonas)} zonas vigentes** ({len(x.zonas_retiradas)} retiradas), **{len(x.componentes)} componentes vigentes** "
             f"({len(x.componentes_retirados)} retirados; {sum(c['estado'] == 'temporal' for c in x.componentes.values())} temporales), "
             f"**{len(x.flujos)} flujos vigentes** ({act} activos, F4 reservado) y {len(x.flujos_retirados)} retirados, **{len(x.pruebas)} pruebas vigentes** y {len(x.pruebas_retiradas)} retiradas, "
             f"{len(x.objetivos)} objetivos OD, {len(x.amenazas)} amenazas AM, {len(x.detecciones)} detecciones DET, "
             f"{len(x.figuras)} figuras, {len(x.rubrica)} criterios de rúbrica.")
    n = {k: sum(r.estado == k for r in res) for k in ("PASA", "ADVERTENCIA", "FALLA", "PENDIENTE")}
    L.append(f"- Resultado: **{n['FALLA']} FALLA**, {n['ADVERTENCIA']} con advertencias, {n['PASA']} PASA, {n['PENDIENTE']} pendientes de P2–P5.\n")
    L.append("## Chequeos\n")
    L.append("| ID | Chequeo | Resultado | Hallazgos |")
    L.append("| --- | --- | --- | --- |")
    for r in res:
        cuentas = f"{sum(h.nivel == 'error' for h in r.hallazgos)} errores, {sum(h.nivel == 'advertencia' for h in r.hallazgos)} advertencias"
        det = r.detalle or (cuentas if r.hallazgos else "—")
        L.append(f"| {r.id} | {r.titulo} | {ICONO[r.estado]} | {det} |")
    L.append("\n## Errores\n")
    errs = [(r, h) for r in res for h in r.hallazgos if h.nivel == "error"]
    if not errs:
        L.append("Ninguno.\n")
    for r, h in errs:
        L.append(f"- **{r.id}** — {h.mensaje}. *Cómo corregir:* {h.corregir}")
    L.append("\n## Advertencias (contradicciones y vacíos registrados)\n")
    warn = [(r, h) for r in res for h in r.hallazgos if h.nivel == "advertencia"]
    if not warn:
        L.append("Ninguna.\n")
    for r, h in warn:
        L.append(f"- **{r.id}** — {h.mensaje}")
    L.append("\n## Información\n")
    for r in res:
        for h in r.hallazgos:
            if h.nivel == "info":
                L.append(f"- **{r.id}** — {h.mensaje}")
    L.append("\n## Cobertura\n")
    L.append("| Relación | Cubiertos | Total |")
    L.append("| --- | ---: | ---: |")
    for k, (a, b) in x.coberturas().items():
        L.append(f"| {k} | {a} | {b} |")
    L.append("\n## Pendientes de P2–P5 (ganchos)\n")
    pend = [r for r in res if r.estado == "PENDIENTE"]
    if pend:
        L.append("| Gancho | Qué validará | Estado |")
        L.append("| --- | --- | --- |")
        for r in pend:
            L.append(f"| {r.id}+ | {r.titulo} | {r.detalle} |")
    else:
        L.append("Todos los ganchos están implementados.")
    L.append("")
    return "\n".join(L)


def consola(x: Infra, res: list[Resultado]) -> None:
    print(f"Celeris E1 — inventario {x.inv['meta']['inventario_version']}: {len(x.zonas)} zonas, {len(x.componentes)} componentes, "
          f"{len(x.flujos)} flujos, {len(x.pruebas)} pruebas (vigentes; {len(x.zonas_retiradas)} zonas, {len(x.componentes_retirados)} componentes, "
          f"{len(x.flujos_retirados)} flujos y {len(x.pruebas_retiradas)} pruebas retirados)\n")
    for r in res:
        tag = {"PASA": "[ OK ]", "ADVERTENCIA": "[ AVISO ]", "FALLA": "[FALLA]", "PENDIENTE": "[PENDIENTE]"}[r.estado]
        print(f"{tag:11} {r.id}  {r.titulo}" + (f"  → {r.detalle}" if r.detalle else ""))
        for h in r.hallazgos:
            if h.nivel == "error":
                print(f"             ✖ {h.mensaje}\n               → {h.corregir}")
            elif h.nivel == "advertencia":
                print(f"             ! {h.mensaje}")
    n = {k: sum(r.estado == k for r in res) for k in ("PASA", "ADVERTENCIA", "FALLA", "PENDIENTE")}
    print(f"\nResumen: {n['FALLA']} FALLA · {n['ADVERTENCIA']} con advertencias · {n['PASA']} PASA · {n['PENDIENTE']} pendientes de P2–P5")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--md", default=str(ci.RAIZ / "docs" / "infra" / "e1" / "validacion.md"))
    ap.add_argument("--estricto", action="store_true", help="las advertencias también hacen fallar")
    ap.add_argument("--sin-informe", action="store_true")
    a = ap.parse_args(argv)
    try:
        x = Infra.cargar()
    except Exception as exc:                       # YAML ilegible o clave duplicada
        print(f"[FALLA] V-01  No se pudieron cargar los YAML: {exc}\n         → Corrija la sintaxis YAML (¿clave duplicada, sangría?)")
        return 1
    res = correr(x)
    consola(x, res)
    if not a.sin_informe:
        ruta = Path(a.md)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(informe_md(x, res), encoding="utf-8", newline="\n")
        print(f"\nInforme: {ruta}")
    if any(r.estado == "FALLA" for r in res) or (a.estricto and any(r.estado == "ADVERTENCIA" for r in res)):
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
