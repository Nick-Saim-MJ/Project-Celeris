"""Generador de los diagramas draw.io del Entregable CE0311 (P3) desde la fuente única infra/*.yaml.

Produce un .drawio editable por figura en entregables/CE0311/diagramas/:
    FIG-1.1  Topología ejecutiva simplificada (≤ 12 bloques)
    FIG-5.1  Topología general
    FIG-5.2  Topología lógica (VLAN, gateways, trunk 802.1Q, ruteo, servicios base, AWS, resumen zona × zona)
    FIG-5.3  Seguridad y zonas (confianza, controles, DET-xx, AM-xx, defensa en profundidad)
    FIG-5.4  VPN híbrida
    FIG-5.5a Flujos (a) y FIG-5.5b Flujos (b): la división y la asignación de cada F-nn salen del campo
             `figura` de cada flujo (CI-20). Son diagramas de carriles: una fila por componente (agrupadas por
             zona, mismas filas en las dos figuras) y una columna por flujo con su etiqueta completa.

Reglas:
- Ningún dato de red se escribe aquí: IP, CIDR, VLAN, puertos, nombres, criticidad, textos «aporta»/«si falla»
  y la lista de componentes de cada figura salen de infra/*.yaml (campo `figuras` de cada componente).
- Lo único que este módulo fija es la DISPOSICIÓN (coordenadas) y el estilo visual de CLAUDE.md.
- Lo que la figura pide y el inventario no trae (capas de defensa en profundidad de D1.9, ruta por defecto hacia
  el ISP) se rotula con la entrada de docs/infra/e1/CAMBIOS-INVENTARIO.md que lo registra (CI-24).
- Todo componente, zona y flecha de flujo lleva el atributo `celeris_id` (validado por V-50+).

    python infra/gen/drawio.py [--salida entregables/CE0311/diagramas]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import RAIZ, Infra  # noqa: E402

SALIDA = RAIZ / "entregables" / "CE0311" / "diagramas"
FIGURAS = ["FIG-1.1", "FIG-5.1", "FIG-5.2", "FIG-5.3", "FIG-5.4", "FIG-5.5a", "FIG-5.5b"]

# --------------------------------------------------------------------------------------------------
# Identidad visual (CLAUDE.md)
# --------------------------------------------------------------------------------------------------
CRITICIDAD = {"Alta": (3, "ALTA"), "Media": (2, "MEDIA"), "Baja": (1, "BAJA")}
TEXTO = "#1A1A1A"
FLECHA = "#1A1A1A"
AWS_TINTA = "#232F3E"

# Un ícono estándar por tipo de componente: el mismo en todas las figuras (criterio 7).
ICONO = {
    "firewall": "shape=mxgraph.networks.firewall;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "switch": "shape=mxgraph.networks.switch;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "switch_existente": "shape=mxgraph.networks.switch;fillColor=#FFFFFF;strokeColor=#4D4D4D;dashed=1;",
    "puerto_emergencia": "shape=mxgraph.networks.laptop;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "hipervisor": "shape=mxgraph.networks.virtual_server;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "gestion_fuera_banda": "shape=mxgraph.networks.terminal;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "ups": "shape=mxgraph.networks.ups_enterprise;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "servidor": "shape=mxgraph.networks.server;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "waf": "shape=mxgraph.networks.proxy_server;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "web": "shape=mxgraph.networks.web_server;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "honeypot": "shape=mxgraph.networks.secured;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "ids": "shape=mxgraph.networks.monitor;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "cliente_prueba": "shape=mxgraph.networks.pc;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "nas": "shape=mxgraph.networks.nas_filer;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
    "interfaz_tunel": "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpn_connection;fillColor=#8C4FFF;strokeColor=#FFFFFF;",
    "vpn_gateway": "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpn_gateway;fillColor=#8C4FFF;strokeColor=#FFFFFF;",
    "aws_instancia": "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;fillColor=#ED7100;strokeColor=#FFFFFF;",
}
NOMBRE_ICONO = {
    "firewall": "Firewall", "switch": "Switch", "switch_existente": "Switch existente (fuera de alcance)",
    "puerto_emergencia": "Puerto break-glass (laptop)", "hipervisor": "Hipervisor", "gestion_fuera_banda": "Gestión fuera de banda",
    "ups": "UPS", "servidor": "Servidor / VM", "waf": "WAF", "web": "Servidor web", "honeypot": "Honeypot / canary",
    "ids": "Sensor IDS", "cliente_prueba": "Equipo de prueba", "nas": "NAS", "interfaz_tunel": "Interfaz de túnel (VTI)",
    "vpn_gateway": "VGW de AWS", "aws_instancia": "Instancia EC2",
}
AWS_GRUPO = {
    "nube": "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;",
    "aws_vpc": "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;",
    "publica": "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;",
    "privada": "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;",
}
PROTECCION = {
    "tls": "TLS", "mtls": "mTLS", "mtls_en_ipsec": "mTLS en IPsec", "tls_en_ipsec": "TLS en IPsec", "ssh": "SSH",
    "cifrado_aplicacion": "cifrado Wazuh (AES)", "sin_cifrar_riesgo_aceptado": "sin cifrar (riesgo aceptado)",
    "no_aplica": "✖ BLOQUEADO",
}
CIFRADOS = {"tls", "mtls", "mtls_en_ipsec", "tls_en_ipsec", "ssh", "cifrado_aplicacion"}

# Capas de defensa en profundidad de D1.9 (tabla «Defensa en profundidad»). No están en infra/*.yaml: CI-24.
CAPAS_D19 = [
    ("Perímetro", "FW01 deny-all, Suricata IPS inline WAN y DMZ, CrowdSec, filtrado de salida"),
    ("Zona", "10 VLAN, matriz zona × zona, DMZ dividida (D-16), STORAGE sin ruteo"),
    ("Capa 2", "DHCP snooping, DAI, IP source guard, RA guard, port-security, BPDU/root guard, nativa 999"),
    ("Host", "nftables por servidor, CIS, sin ip_forward en NAS01 e IDS01"),
    ("Aplicación", "WAF con OWASP CRS; nodo Celeris con ACL y SSRF; CA con Name Constraints"),
    ("Datos en tránsito", "Una protección por flujo (D1.11)"),
    ("Detección", "Suricata, honeypots, canary, detecciones Celeris, honey-URLs, WAF → Wazuh"),
    ("Respuesta", "Bloquear IP en OPNsense, aislar VLAN, revocar CA de un nodo"),
    ("Recuperación", "Break-glass, configuraciones en Git, respaldos 3-2-1-1-0"),
]

W, H = 180, 84          # caja de componente
WP, HP = 180, 40        # caja de interfaz (componente con varias zonas)
GAP, PAD, CAB = 10, 10, 46


def aclarar(hex_color: str, f: float = 0.85) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#{:02X}{:02X}{:02X}".format(*(round(c + (255 - c) * f) for c in (r, g, b)))


def nombre_corto(comp: dict) -> str:
    n = comp["nombre"]
    return n.split("—", 1)[1].strip() if "—" in n else n


def primera_frase(texto: str, maximo: int) -> str:
    frase = re.split(r"(?<=[.;])\s", texto.strip(), maxsplit=1)[0].rstrip(".;")
    if len(frase) <= maximo:
        return frase
    corte = frase[:maximo].rsplit(" ", 1)[0]
    return corte.rstrip(",;:") + "…"


def lineas_estimadas(texto_html: str, ancho_px: float, fuente: float) -> int:
    """Líneas que ocupa un texto HTML de draw.io (estimación: ancho medio de carácter 0,55 × tamaño de letra)."""
    plano = re.sub(r"<[^>]+>", "", texto_html).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    por_linea = max(1, int(ancho_px / (0.55 * fuente)))
    return max(1, -(-len(plano) // por_linea))


def tam_fuente(lineas: list[str], ancho_px: float, alto_px: float) -> int:
    """10 pt si cabe en la caja; si no, 9 (nunca menos: legibilidad)."""
    necesarias = sum(lineas_estimadas(l, ancho_px, 10) for l in lineas)
    return 10 if necesarias * 13 <= alto_px else 9


def esc(t) -> str:
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------------------------------------------------------------------------------------
# Texto derivado del inventario (compartido con infra/gen/drawio_check.py)
# --------------------------------------------------------------------------------------------------
def protocolos_texto(f: dict) -> str:
    partes = []
    for p in f.get("protocolos") or []:
        proto = p["proto"].upper() if p["proto"] != "ipv6" else "IPv6"
        partes.append(proto if not p["puertos"] else f"{proto}/{','.join(str(n) for n in p['puertos'])}")
    return " + ".join(partes)


def etiqueta_flujo(f: dict) -> str:
    """«F-nn · protocolo/puerto · protección» (P3). F7 y todo flujo bloqueado: «✖ BLOQUEADO»."""
    prot = "✖ BLOQUEADO" if f["accion"] == "bloquear" else PROTECCION.get(f["proteccion"]["tipo"], f["proteccion"]["tipo"])
    return f"{f['id']} · {protocolos_texto(f)} · {prot}"


def ip_texto(x: Infra, comp: dict, detalle: bool = False) -> str:
    """IP (o rango) que se rotula en la segunda línea de la caja del componente."""
    if comp.get("cidr"):
        return comp["cidr"]
    ips = [i for i in comp["ips"] if i["ip"]]
    if comp["id"] == "FW01" and not detalle:
        wan = next(i["ip"] for i in ips if i["interfaz"] == "wan")
        return f"WAN {wan} · .1 en {len(ips) - 1} VLAN"
    if comp["id"] == "IDS01":
        cap = [i["interfaz"].split("-")[1] for i in comp["ips"] if i["interfaz"].startswith("captura")]
        return f"{ips[0]['ip']} · captura VLAN {'/'.join(cap)}"
    if not ips:
        if comp["tipo"] == "vpn_gateway":
            return "IP públicas asignadas por AWS (1 por túnel)"
        nota = next((i.get("nota") for i in comp["ips"] if i.get("nota")), "sin IP")
        return nota
    if len(ips) == 1:
        return ips[0]["ip"]
    return " · ".join(f"{i['interfaz']} {i['ip']}" for i in ips)


def color_de(x: Infra, comp: dict) -> str:
    for z in comp["zonas"]:
        c = x.zonas[z].get("color")
        if c:
            return c
    return AWS_TINTA if "AWS" in comp["zonas"] else "#4D4D4D"


def commit_fuente() -> str:
    try:
        return subprocess.run(["git", "log", "-1", "--format=%h", "--", "infra/inventory.yaml", "infra/trazabilidad.yaml",
                               "infra/pruebas.yaml"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip() or "sin-commit"
    except (OSError, subprocess.CalledProcessError):
        return "sin-commit"


# --------------------------------------------------------------------------------------------------
# Modelo mínimo de un diagrama draw.io
# --------------------------------------------------------------------------------------------------
class Diagrama:
    def __init__(self, x: Infra, fig: str, ancho: int, alto: int):
        self.x, self.fig, self.ancho, self.alto = x, fig, ancho, alto
        self.celdas: list[ET.Element] = []
        self.n = 0
        self.nodos: dict[str, str] = {}        # celeris_id (o ID:interfaz) → id de celda
        self.presentes: list[str] = []         # componentes dibujados, en orden
        self.tipos: set[str] = set()
        self.zonas_dibujadas: list[str] = []

    def _id(self) -> str:
        self.n += 1
        return f"{self.fig}-{self.n}"

    def _celda(self, attrs: dict | None, label: str, style: str, geo: dict, vertex=True, parent="1",
               source=None, target=None, puntos=None, extremos=None) -> str:
        cid = self._id()
        cell = ET.Element("mxCell", {"style": style, "parent": parent})
        if vertex:
            cell.set("vertex", "1")
        else:
            cell.set("edge", "1")
            if source:
                cell.set("source", source)
            if target:
                cell.set("target", target)
        g = ET.SubElement(cell, "mxGeometry", {**{k: str(v) for k, v in geo.items()}, "as": "geometry"})
        if extremos:
            ET.SubElement(g, "mxPoint", {"x": str(extremos[0][0]), "y": str(extremos[0][1]), "as": "sourcePoint"})
            ET.SubElement(g, "mxPoint", {"x": str(extremos[1][0]), "y": str(extremos[1][1]), "as": "targetPoint"})
        if puntos:
            arr = ET.SubElement(g, "Array", {"as": "points"})
            for px, py in puntos:
                ET.SubElement(arr, "mxPoint", {"x": str(px), "y": str(py)})
        if attrs:
            obj = ET.Element("object", {"id": cid, "label": label, **{k: str(v) for k, v in attrs.items() if v is not None}})
            obj.append(cell)
            self.celdas.append(obj)
        else:
            cell.set("id", cid)
            cell.set("value", label)
            self.celdas.append(cell)
        return cid

    def caja(self, x, y, w, h, style, label="", attrs=None) -> str:
        return self._celda(attrs, label, style, {"x": x, "y": y, "width": w, "height": h})

    def flecha(self, src, tgt, style, label="", attrs=None, puntos=None) -> str:
        return self._celda(attrs, label, style, {"relative": 1}, vertex=False, source=src, target=tgt, puntos=puntos)

    def linea_libre(self, p1, p2, style, label="") -> str:
        return self._celda(None, label, style, {"relative": 1}, vertex=False, extremos=(p1, p2))

    def xml(self) -> str:
        mxfile = ET.Element("mxfile", {"host": "celeris-infra-gen", "type": "device", "version": "24.7.17"})
        diag = ET.SubElement(mxfile, "diagram", {"id": self.fig, "name": self.fig})
        model = ET.SubElement(diag, "mxGraphModel", {
            "dx": "0", "dy": "0", "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1", "connect": "1",
            "arrows": "1", "fold": "1", "page": "1", "pageScale": "1", "pageWidth": str(self.ancho),
            "pageHeight": str(self.alto), "background": "#FFFFFF", "math": "0", "shadow": "0"})
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
        for c in self.celdas:
            root.append(c)
        ET.indent(mxfile, space="  ")
        return ET.tostring(mxfile, encoding="unicode") + "\n"

    # ------------------------------------------------------------ elementos del inventario
    def datos_componente(self, comp: dict) -> dict:
        x = self.x
        flujos = sorted(x.flujos_de(comp["id"], incluir_zona=False), key=lambda f: int(f[1:]))
        pruebas = sorted({t["id"] for t in x.pruebas.values() if comp["id"] in t.get("componentes", [])
                          or set(t["flujos"]) & set(flujos)})
        return {
            "celeris_id": comp["id"], "celeris_tipo": "componente", "ip": ip_texto(x, comp, detalle=True),
            "zona": ", ".join(comp["zonas"]), "criticidad": comp["criticidad"], "estado": comp["estado"],
            "por_que": comp["por_que"], "aporta": comp["aporta"], "si_falla": comp["si_falla"],
            "flujos": ", ".join(flujos), "pruebas": ", ".join(pruebas), "placeholders": "1",
            "tooltip": f"{comp['id']} · {comp['criticidad']}\nPor qué: {comp['por_que']}\nAporta: {comp['aporta']}\nSi falla: {comp['si_falla']}",
        }

    def componente(self, cid: str, x0, y0, w=W, h=H, compacto=False, detalle_ip=False, solo_iface=None,
                   una_linea=False) -> str:
        """Caja de componente en 3 líneas: «ID · nombre · CRITICIDAD», IP y aporta_corto (P3).
        compacto: sin la 3.ª línea. una_linea: todo en una línea (filas de FIG-5.5). solo_iface: se rotula solo la IP
        de esa interfaz (las demás interfaces se dibujan como «ID:interfaz» en su propia zona)."""
        comp = self.x.componentes[cid]
        grosor, tag = CRITICIDAD[comp["criticidad"]]
        color = color_de(self.x, comp)
        if solo_iface:
            i = next(i for i in comp["ips"] if i["interfaz"] == solo_iface)
            ip = f"{i['ip']} ({solo_iface})"
        else:
            ip = ip_texto(self.x, comp, detalle_ip)
        lineas = [f"<b>{esc(cid)}</b> · {esc(nombre_corto(comp))} · <b>{tag}</b>", esc(ip)]
        if not compacto:
            lineas.append(f"<i>{esc(comp['aporta_corto'])}</i>")
        fuera = comp["estado"] == "fuera_de_alcance"
        if fuera:
            lineas[0] += " · <i>fuera de alcance</i>"
        icono = h - 8 if una_linea else 22
        fuente = tam_fuente(lineas if not una_linea else [" · ".join(lineas)], w - icono - 14, h - 4)
        estilo = (f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={color};strokeWidth={grosor};"
                  f"align=left;verticalAlign={'middle' if una_linea else 'top'};spacingLeft={icono + 10};spacingTop=1;spacingRight=2;"
                  f"fontSize={fuente};fontColor={TEXTO};")
        if fuera:
            estilo += "dashed=1;dashPattern=6 3;"
        label = " · ".join(lineas) if una_linea else "<br>".join(lineas)
        c = self.caja(x0, y0, w, h, estilo, label, self.datos_componente(comp))
        if comp["tipo"] in ICONO:
            self.caja(x0 + 5, y0 + (4 if una_linea else 6), icono, icono, ICONO[comp["tipo"]] + "html=1;aspect=fixed;outlineConnect=0;dashed=0;")
            self.tipos.add(comp["tipo"])
        self.nodos[cid] = c
        if cid not in self.presentes:
            self.presentes.append(cid)
        return c

    def interfaz(self, ref: str, x0, y0, w=WP, h=HP) -> str:
        """Interfaz de un componente con varias zonas, dibujada dentro de la otra zona («ID:interfaz»)."""
        cid, iface = ref.split(":")
        comp = self.x.componentes[cid]
        ip = next(i for i in comp["ips"] if i["interfaz"] == iface)
        crit = ip.get("criticidad", comp["criticidad"])
        grosor, tag = CRITICIDAD[crit]
        color = self.x.zonas[ip["zona"]]["color"] or "#4D4D4D"
        label = f"<b>{esc(cid)}:{esc(iface)}</b> · <b>{tag}</b><br>{esc(ip['ip'])}"
        estilo = (f"rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={color};strokeWidth={grosor};"
                  f"dashed=1;dashPattern=2 2;align=left;verticalAlign=top;spacingLeft=6;fontSize=10;fontColor={TEXTO};")
        attrs = {"celeris_id": ref, "celeris_tipo": "interfaz", "ip": ip["ip"], "zona": ip["zona"], "criticidad": crit,
                 "tooltip": f"{cid}, interfaz {iface} en {ip['zona']} ({ip.get('nota', '')})"}
        c = self.caja(x0, y0, w, h, estilo, label, attrs)
        self.nodos[ref] = c
        return c

    def zona(self, zid: str, x0, y0, w, h, extra="") -> str:
        z = self.x.zonas[zid]
        if z["tipo"] == "nube":
            estilo = (AWS_GRUPO["nube"] + "html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=30;fontSize=11;"
                      f"fontColor={AWS_TINTA};container=0;dashed=0;")
            label = f"<b>AWS</b> · zona {esc(z['nombre'])} · confianza {esc(z['confianza'])}{extra}"
        elif z["tipo"] == "externa":
            estilo = f"ellipse;shape=cloud;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#4D4D4D;fontSize=11;fontColor={TEXTO};"
            label = f"<b>{esc(z['nombre'])}</b>{extra}"
        else:
            color = z["color"]
            vlan = f"VLAN {z['vlan']} · " if z.get("vlan") is not None else ""
            cidr = f" · {z['cidr']}" if z.get("cidr") else ""
            estilo = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={aclarar(color, 0.86)};strokeColor={color};strokeWidth=2;"
                      f"verticalAlign=top;align=left;spacingLeft=6;spacingTop=2;fontSize=11;fontColor={TEXTO};")
            label = f"<b>{vlan}{esc(z['id'])}</b>{cidr} · confianza {esc(z['confianza'])}{extra}"
        attrs = {"celeris_id": zid, "celeris_tipo": "zona", "cidr": z.get("cidr"), "vlan": z.get("vlan"),
                 "gateway": z.get("gateway"), "confianza": z["confianza"], "proposito": z["proposito"],
                 "tooltip": f"{zid}: {z['proposito']}. Regla: {z['regla_diseno']}"}
        c = self.caja(x0, y0, w, h, estilo, label, attrs)
        self.nodos[zid] = c
        self.zonas_dibujadas.append(zid)
        return c

    def grupo_aws(self, cid: str, x0, y0, w, h) -> str:
        comp = self.x.componentes[cid]
        grosor, tag = CRITICIDAD[comp["criticidad"]]
        clave = "aws_vpc" if comp["tipo"] == "aws_vpc" else comp.get("subred_tipo", "privada")
        az = f" · AZ {comp['az']}" if comp.get("az") else ""
        estilo = (AWS_GRUPO[clave] + f"strokeWidth={grosor};html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=30;"
                  f"fontSize=10;fontColor={AWS_TINTA};container=0;dashed=0;")
        label = f"<b>{esc(cid)}</b> · {esc(comp['cidr'])}{az} · <b>{tag}</b>"
        c = self.caja(x0, y0, w, h, estilo, label, self.datos_componente(comp))
        self.nodos[cid] = c
        if cid not in self.presentes:
            self.presentes.append(cid)
        return c

    def flujo(self, fid: str, extremos_dib: dict | None = None, estilo_extra="") -> list[str]:
        """Dibuja el flujo F-nn como una flecha por cada par origen → destino presente en la figura.
        La primera lleva la etiqueta completa; las demás, solo el ID."""
        f = self.x.flujos[fid]
        if f["accion"] == "bloquear":
            estilo = "dashed=1;dashPattern=1 4;strokeWidth=2;endArrow=cross;endFill=0;"
        elif f["proteccion"]["tipo"] in CIFRADOS:
            estilo = "strokeWidth=1.5;endArrow=block;endFill=1;"
        else:
            estilo = "dashed=1;dashPattern=8 4;strokeWidth=1.5;endArrow=block;endFill=1;"
        estilo = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=9;labelBackgroundColor=#FFFFFF;"
                  f"strokeColor={FLECHA};fontColor={TEXTO};jumpStyle=gap;" + estilo + estilo_extra)
        hechos = []
        origenes = [self._resolver_nodo(o) for o in f["origen"]]
        destinos = [self._resolver_nodo(d) for d in f["destino"]]
        pares = [(o, d) for o in origenes for d in destinos if o and d and o != d]
        vistos = set()
        for i, (o, d) in enumerate(pares):
            if (o, d) in vistos:
                continue
            vistos.add((o, d))
            label = etiqueta_flujo(f) if not hechos else f["id"]
            attrs = {"celeris_id": fid, "celeris_tipo": "flujo", "etiqueta": etiqueta_flujo(f), "proposito": f["proposito"],
                     "proteccion": f["proteccion"]["detalle"], "riesgo_residual": f.get("riesgo_residual", ""),
                     "regla_fw": f.get("regla_fw", ""), "tooltip": f"{etiqueta_flujo(f)}\n{f['proposito']}\n{f['proteccion']['detalle']}"}
            hechos.append(self.flecha(o, d, estilo, label, attrs))
        return hechos

    def _resolver_nodo(self, crudo: str) -> str | None:
        if crudo in self.nodos:
            return self.nodos[crudo]
        cid = crudo.split(":")[0]
        return self.nodos.get(cid)

    # ------------------------------------------------------------ marco común
    def titulo(self, x0=20, y0=10, w=None):
        fig = self.x.figuras[self.fig]
        meta = self.x.inv["meta"]
        w = w or (self.ancho - 40)
        label = (f"<b>{esc(fig['leyenda'])}</b><br>{self.fig} · Inventario v{meta['inventario_version']} · {meta['fecha']} · "
                 f"commit de la fuente {commit_fuente()} · CE0311 Celeris Edge · generado desde infra/*.yaml")
        self.caja(x0, y0, w, 44, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1A1A1A;strokeWidth=1;"
                  f"align=left;spacingLeft=10;fontSize=13;fontColor={TEXTO};",
                  label, {"celeris_rol": "titulo", "figura": self.fig, "titulo": fig["leyenda"]})

    def panel(self, x0, y0, w, ids: list[str] | None = None, max_si_falla=80) -> int:
        ids = ids or self.presentes
        filas = []
        for cid in ids:
            c = self.x.componentes[cid]
            filas.append(f"<b>{esc(cid)}</b> — {esc(c['aporta_corto'])}. <i>Si falla:</i> {esc(primera_frase(c['si_falla'], max_si_falla))}")
        alto = 30 + sum(12 * lineas_estimadas(f, w - 16, 9) for f in filas)
        label = "<b>Qué aporta y qué pasa si falla</b><br>" + "<br>".join(filas)
        self.caja(x0, y0, w, alto, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#4D4D4D;align=left;"
                  f"verticalAlign=top;spacingLeft=8;spacingRight=6;spacingTop=4;fontSize=9;fontColor={TEXTO};",
                  label, {"celeris_rol": "panel", "componentes": ", ".join(ids)})
        return alto

    def leyenda(self, x0, y0, w=700, flujos=True, carriles=False):
        """Leyenda: zonas (color + nombre), criticidad, estilos de flujo e íconos. Con w ≥ 1100 usa dos columnas."""
        zonas = [z for z in self.zonas_dibujadas if self.x.zonas[z].get("color")]
        tipos = sorted(self.tipos)
        dos = w >= 1100
        wc = (w - 24) // 2 if dos else w - 16
        txt = f"text;html=1;align=left;verticalAlign=middle;fontSize=10;fontColor={TEXTO};whiteSpace=wrap;"
        nz = 5 if wc >= 800 else 4 if wc >= 560 else 3
        ni = 4 if wc >= 600 else 3
        # columna A: zonas + criticidad
        alto_a = 26 + 18 + ((len(zonas) + nz - 1) // nz) * 22 + 6 + 20 + 34 + 34 if zonas else 26 + 20 + 34 + 34
        alto_b = (22 + 30 if flujos else 0) + (36 if carriles else 0) + ((22 + ((len(tipos) + ni - 1) // ni) * 26) if tipos else 0)
        alto = (max(alto_a, 26 + alto_b) if dos else alto_a + alto_b) + 8
        self.caja(x0, y0, w, alto, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4D4D4D;align=left;"
                  f"verticalAlign=top;spacingLeft=8;spacingTop=4;fontSize=11;fontColor={TEXTO};",
                  "<b>Leyenda</b>", {"celeris_rol": "leyenda"})
        xa, y = x0 + 8, y0 + 26
        if zonas:
            self.caja(xa, y, 300, 16, txt, "<b>Zonas</b> (color + nombre):")
            y += 18
            for i, z in enumerate(zonas):
                zz = self.x.zonas[z]
                cx, cy = xa + (i % nz) * (wc // nz), y + (i // nz) * 22
                self.caja(cx, cy, 16, 16, f"rounded=0;html=1;fillColor={aclarar(zz['color'], 0.86)};strokeColor={zz['color']};strokeWidth=2;")
                vl = f" (VLAN {zz['vlan']})" if zz.get("vlan") is not None else ""
                self.caja(cx + 20, cy - 2, wc // nz - 22, 20, txt, f"{esc(z)}{vl}")
            y += ((len(zonas) + nz - 1) // nz) * 22 + 6
        self.caja(xa, y, 360, 16, txt, "<b>Criticidad</b> (grosor del borde + etiqueta):")
        y += 20
        cw = (wc - 8) // 3
        for i, (nombre, (grosor, tag)) in enumerate(CRITICIDAD.items()):
            self.caja(xa + i * cw, y, cw - 8, 28, f"rounded=1;html=1;fillColor=#FFFFFF;strokeColor={TEXTO};strokeWidth={grosor};fontSize=10;fontColor={TEXTO};",
                      f"<b>{tag}</b> · borde {grosor} px")
        y += 34
        self.caja(xa, y, cw * 3 // 2 - 8, 26, f"rounded=1;html=1;fillColor=#FFFFFF;strokeColor={TEXTO};strokeWidth=1;dashed=1;dashPattern=2 2;fontSize=10;fontColor={TEXTO};",
                  "interfaz de un equipo en otra zona")
        self.caja(xa + cw * 3 // 2, y, cw * 3 // 2 - 8, 26, f"rounded=1;html=1;fillColor=#FFFFFF;strokeColor={TEXTO};strokeWidth=2;dashed=1;dashPattern=6 3;fontSize=10;fontColor={TEXTO};",
                  "existente, fuera de alcance")
        y += 34
        xb, y = (x0 + 16 + wc, y0 + 26) if dos else (xa, y)
        if flujos:
            self.caja(xb, y, wc, 16, txt, "<b>Flujos</b> «F-nn · protocolo/puerto · protección»:")
            y += 22
            muestras = [("strokeWidth=1.5;endArrow=block;endFill=1;", "cifrado (TLS, mTLS, SSH, IPsec)"),
                        ("dashed=1;dashPattern=8 4;strokeWidth=1.5;endArrow=block;endFill=1;", "sin cifrar, riesgo aceptado"),
                        ("dashed=1;dashPattern=1 4;strokeWidth=2;endArrow=cross;endFill=0;", "✖ BLOQUEADO")]
            for i, (est, nombre) in enumerate(muestras):
                cx = xb + i * (wc // 3)
                self.linea_libre((cx, y + 8), (cx + 46, y + 8), f"html=1;strokeColor={FLECHA};" + est)
                self.caja(cx + 52, y, wc // 3 - 54, 18, txt, nombre)
            y += 30
        if carriles:
            self.caja(xb, y, 14, 14, f"ellipse;html=1;fillColor={FLECHA};strokeColor={FLECHA};")
            self.caja(xb + 20, y - 4, wc - 20, 30, txt, "● origen del flujo · punta de flecha = destino · cada columna es un flujo "
                      "y su encabezado es la etiqueta de la flecha · fila gris = componente sin flujos en esta figura")
            y += 36
        if tipos:
            self.caja(xb, y, 300, 16, txt, "<b>Íconos</b> (draw.io redes / AWS4):")
            y += 20
            for i, t in enumerate(tipos):
                cx, cy = xb + (i % ni) * (wc // ni), y + (i // ni) * 26
                self.caja(cx, cy, 20, 20, ICONO[t] + "html=1;aspect=fixed;outlineConnect=0;dashed=0;")
                self.caja(cx + 24, cy, wc // ni - 26, 20, txt, NOMBRE_ICONO[t])
        return alto

    def nota(self, x0, y0, w, h, label, attrs=None, color="#FFFFFF", borde="#4D4D4D", tam=9):
        return self.caja(x0, y0, w, h, f"rounded=1;arcSize=4;whiteSpace=wrap;html=1;fillColor={color};strokeColor={borde};"
                         f"align=left;verticalAlign=top;spacingLeft=6;spacingRight=4;spacingTop=2;fontSize={tam};fontColor={TEXTO};",
                         label, attrs)


def componentes_de(x: Infra, fig: str) -> list[str]:
    return [c["id"] for c in x.componentes.values() if fig in c["figuras"]]


def orden_inventario(x: Infra, ids) -> list[str]:
    pos = {c: i for i, c in enumerate(x.componentes)}
    return sorted(ids, key=lambda c: pos[c])


# --------------------------------------------------------------------------------------------------
# FIG-5.1 — disposición por zonas
# --------------------------------------------------------------------------------------------------
# filas de zonas: (zona, columnas, filas, ocupantes). Un ocupante «ID:interfaz» es una interfaz de otra zona.
FILAS_51 = [
    (300, [("DMZ-HONEY", 1, 1, ["HNY01"]), ("DMZ-SVC", 2, 1, ["WAF01", "WEB01"]),
           ("EDGE", 2, 1, ["EDGE01", "EDGE02"]), ("SECURITY", 2, 1, ["SIEM01", "IDS01"])]),
    (470, [("LAB", 2, 2, ["LABCLI01", "PROBE01", "HNY02", "SW-ACC"]), ("LAB-TEST", 1, 1, ["KALI01"]),
           ("SERVERS", 2, 2, ["CTRL01", "DB01", "OBS01", "SVC01"]), ("BACKUP", 1, 1, ["NAS01:respaldo"])]),
    (734, [("MGMT", 4, 2, ["JMP01", "SW-CORE01", "BRK01", "ESX01", "IPMI01", "UPS01", "NAS01:gestion"]),
           ("STORAGE", 2, 1, ["NAS01", "ESX01:vmk1"])]),
]
# Interfaz principal que se rotula en la caja de un componente con varias zonas (las demás van en su zona).
IFACE_PRINCIPAL = {"NAS01": "almacenamiento", "ESX01": "vmk0"}


def tam_zona(cols, filas):
    return PAD + cols * (W + GAP), CAB + PAD + filas * (H + GAP)


def fig_5_1(x: Infra) -> Diagrama:
    ids = set(componentes_de(x, "FIG-5.1"))
    d = Diagrama(x, "FIG-5.1", 2290, 1260)
    d.titulo(w=1720)
    d.zona("INTERNET", 520, 62, 300, 84, "<br>ISP, orígenes web, ACME, feeds, S3")
    fw = d.componente("FW01", 590, 172, w=220)
    d.flecha(d.nodos["INTERNET"], fw, "html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=2;fontSize=10;labelBackgroundColor=#FFFFFF;", "WAN")
    trunk = d.caja(20, 268, 1440, 22, "rounded=0;whiteSpace=wrap;html=1;fillColor=#4D4D4D;strokeColor=#1A1A1A;fontColor=#FFFFFF;fontSize=10;",
                   "<b>Trunk 802.1Q</b> FW01 ↔ SW-CORE01 (PG-FW-TRUNK): una subinterfaz .1 de FW01 por VLAN · la VLAN 70 no llega al firewall",
                   {"celeris_rol": "trunk", "celeris_ref": "SW-CORE01"})
    d.flecha(fw, trunk, "html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=3;")
    for fy, zonas in FILAS_51:
        zx = 20
        for zid, cols, filas, occ in zonas:
            zw, zh = tam_zona(cols, filas)
            extra = " · <b>sin gateway, no enrutada</b>" if x.zonas[zid]["gateway"] is None else ""
            d.zona(zid, zx, fy, zw, zh, extra)
            for i, o in enumerate(occ):
                if o.split(":")[0] not in ids:
                    continue
                cx, cy = zx + PAD + (i % cols) * (W + GAP), fy + CAB + (i // cols) * (H + GAP)
                if ":" in o:
                    d.interfaz(o, cx, cy + (H - HP) // 2)
                else:
                    d.componente(o, cx, cy, solo_iface=IFACE_PRINCIPAL.get(o))
            zx += zw + 20
    # VTI y AWS (columna derecha)
    d.componente("VTI1", 1060, 150, w=200, h=54, compacto=True)
    d.componente("VTI2", 1060, 210, w=200, h=54, compacto=True)
    for v in ("VTI1", "VTI2"):
        d.flecha(fw, d.nodos[v], "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#7F7F7F;")
    d.zona("AWS", 1480, 62, 250, 900, f"<br>{x.zonas['AWS']['cidr']}")
    d.componente("VGW", 1495, 120, w=220)
    d.grupo_aws("AWS-VPC", 1490, 222, 230, 728)
    y = 262
    for sid, occ in [("AWS-PUB-A", "NAT01"), ("AWS-PUB-B", None), ("AWS-APP-A", "EC2-SHIELD"), ("AWS-APP-B", "EC2-CTRLR"),
                     ("AWS-DATA-A", None), ("AWS-DATA-B", None)]:
        h = 130 if occ else 48
        d.grupo_aws(sid, 1498, y, 214, h)
        if occ:
            d.componente(occ, 1505, y + 38, w=200)
        y += h + 10
    tuneles(d)
    alto_l = d.leyenda(20, 990, w=1440)
    d.panel(1750, 10, 530, orden_inventario(x, d.presentes), max_si_falla=72)
    d.alto = max(d.alto, 990 + alto_l + 20)
    return d


def tuneles(d: Diagrama, grosor_activo=3):
    """Los dos túneles IPsec VTI1 (activo) y VTI2 (respaldo) hacia el VGW. Ambos cifrados: línea continua."""
    x = d.x
    vpn = x.inv["vpn"]
    for t in vpn["tuneles"]:
        src, dst = d.nodos.get(t["id"]), d.nodos.get("VGW")
        if not (src and dst):
            continue
        activo = t["rol"] == "activo"
        extra = " · prepending" if t.get("bgp_as_path_prepending") else ""
        label = f"{t['id']} {'ACTIVO' if activo else 'RESPALDO'} · IPsec{extra}"
        estilo = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=9;labelBackgroundColor=#FFFFFF;fontColor={TEXTO};"
                  f"strokeColor={'#8C4FFF' if activo else '#7F7F7F'};strokeWidth={grosor_activo if activo else 1.5};"
                  f"endArrow=none;startArrow=none;exitX=1;exitY=0.5;entryX=0;entryY={0.35 if activo else 0.8};")
        d.flecha(src, dst, estilo, label, {"celeris_id": vpn["id"], "celeris_tipo": "tunel", "tunel": t["id"], "rol": t["rol"],
                                           "red_interna": t["red_interna"]})


# --------------------------------------------------------------------------------------------------
# FIG-5.5a / FIG-5.5b — diagrama de carriles: filas = componentes (por zona), columnas = flujos
# --------------------------------------------------------------------------------------------------
# Mismas filas, en la misma posición, en las dos figuras. Fila «zona» = la zona completa como extremo.
FILAS_FLUJO = [
    ("INTERNET", []), ("PERIMETRO", ["FW01"]),
    ("DMZ-HONEY", ["HNY01"]), ("DMZ-SVC", ["WAF01", "WEB01"]),
    ("LAB", ["LABCLI01", "PROBE01", "HNY02"]), ("LAB-TEST", ["KALI01"]),
    ("EDGE", ["EDGE01", "EDGE02"]), ("SERVERS", ["CTRL01", "DB01", "OBS01", "SVC01"]),
    ("SECURITY", ["SIEM01", "IDS01"]), ("BACKUP", ["NAS01:respaldo"]), ("STORAGE", ["NAS01", "ESX01:vmk1"]),
    ("MGMT", ["JMP01", "SW-CORE01", "ESX01", "IPMI01", "UPS01", "NAS01:gestion"]),
    ("AWS", ["EC2-SHIELD", "EC2-CTRLR"]),
]
RP = 30            # alto de fila
X_COL0 = 390       # primera columna de flujo
WC = 104           # ancho de columna
Y_FILAS = 196      # primera fila


def fig_5_5(x: Infra, fig: str) -> Diagrama:
    ids = set(componentes_de(x, fig))
    flujos = x.flujos_de_figura(fig)
    n_max = max(len(x.flujos_de_figura(f)) for f in ("FIG-5.5a", "FIG-5.5b"))
    x_fin = X_COL0 + n_max * WC + 10          # mismo ancho en ambas figuras
    d = Diagrama(x, fig, x_fin + 520, 1500)
    d.titulo(w=x_fin - 20)
    # filas
    fila_y: dict[str, float] = {}
    y = Y_FILAS
    for zid, occ in FILAS_FLUJO:
        z = x.zonas[zid]
        alto = RP * (1 + len(occ)) + 4
        if zid in ("INTERNET", "PERIMETRO"):
            color, fill = "#4D4D4D", "#F2F2F2"
        elif zid == "AWS":
            color, fill = AWS_TINTA, "#FFF5E6"
        else:
            color, fill = z["color"], aclarar(z["color"], 0.86)
        vlan = f"VLAN {z['vlan']} · " if z.get("vlan") is not None else ""
        cidr = f" · {z['cidr']}" if z.get("cidr") else ""
        gw = " · sin gateway" if zid == "STORAGE" else ""
        etiqueta = f"<b>{vlan}{esc(zid)}</b>{cidr}{gw} <i>(toda la zona)</i>"
        nid = d.caja(20, y, x_fin - 20, alto, f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={color};strokeWidth=2;"
                     f"align=left;verticalAlign=top;spacingLeft=6;spacingTop=6;fontSize=10;fontColor={TEXTO};", etiqueta,
                     {"celeris_id": zid, "celeris_tipo": "zona", "cidr": z.get("cidr"), "confianza": z["confianza"],
                      "tooltip": f"{zid}: {z['proposito']}"})
        d.nodos[zid] = nid
        d.zonas_dibujadas.append(zid)
        fila_y[zid] = y + RP / 2 + 2
        for k, o in enumerate(occ):
            fy = y + RP * (k + 1) + 2
            fila_y[o] = fy + RP / 2
            # franja alterna para leer la fila de lado a lado
            if k % 2 == 0:
                d.caja(24, fy, x_fin - 28, RP, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=none;opacity=55;")
            cid = o.split(":")[0]
            if cid in ids:
                if ":" in o:
                    d.interfaz(o, 36, fy + 2, w=X_COL0 - 50, h=RP - 4)
                else:
                    d.componente(cid, 36, fy + 2, w=X_COL0 - 50, h=RP - 4, compacto=True, una_linea=True,
                                 solo_iface=IFACE_PRINCIPAL.get(cid))
            else:
                otra = "FIG-5.5b" if fig == "FIG-5.5a" else "FIG-5.5a"
                d.caja(36, fy + 2, X_COL0 - 50, RP - 4, "rounded=1;html=1;fillColor=none;strokeColor=#BBBBBB;dashed=1;dashPattern=2 2;"
                       "align=left;spacingLeft=6;fontSize=9;fontColor=#7F7F7F;", f"{esc(o)} · sin flujos aquí (ver {otra})")
        y += alto + 4
    y_fin = y
    # columnas de flujo
    puertos: dict[tuple[str, str], str] = {}

    def puerto(fid, fila, xc, origen):
        clave = (fid, fila)
        if clave in puertos:
            return puertos[clave]
        if origen:
            pid = d.caja(xc - 5, fila_y[fila] - 5, 10, 10, f"ellipse;html=1;fillColor={FLECHA};strokeColor={FLECHA};",
                         "", {"celeris_rol": "extremo", "celeris_ref": fila, "flujo": fid, "lado": "origen"})
        else:
            pid = d.caja(xc - 1, fila_y[fila] - 1, 2, 2, "rounded=0;html=1;fillColor=none;strokeColor=none;",
                         "", {"celeris_rol": "extremo", "celeris_ref": fila, "flujo": fid, "lado": "destino"})
        puertos[clave] = pid
        return pid

    def fila_de(crudo: str) -> str:
        if crudo in fila_y:
            return crudo
        return crudo.split(":")[0]

    for i, fid in enumerate(flujos):
        f = x.flujos[fid]
        xc = X_COL0 + i * WC + WC // 2
        d.caja(X_COL0 + i * WC + 2, 64, WC - 4, Y_FILAS - 70,
               f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={FLECHA};strokeWidth=1;"
               f"verticalAlign=top;align=center;spacing=3;fontSize=9;fontColor={TEXTO};",
               f"<b>{esc(etiqueta_flujo(f)).replace(',', ',&#8203;')}</b><br><i>{esc(f['proposito'])}</i>",
               {"celeris_rol": "etiqueta_flujo", "celeris_ref": fid, "etiqueta": etiqueta_flujo(f)})
        d.linea_libre((xc, Y_FILAS - 6), (xc, y_fin), "html=1;endArrow=none;strokeColor=#BBBBBB;strokeWidth=1;dashed=1;dashPattern=1 3;")
        if f["accion"] == "bloquear":
            est = "dashed=1;dashPattern=1 4;strokeWidth=2;endArrow=cross;endFill=0;endSize=10;"
        elif f["proteccion"]["tipo"] in CIFRADOS:
            est = "strokeWidth=2;endArrow=block;endFill=1;"
        else:
            est = "dashed=1;dashPattern=8 4;strokeWidth=2;endArrow=block;endFill=1;"
        estilo = f"html=1;noLabel=1;strokeColor={FLECHA};" + est
        origenes = sorted({fila_de(o) for o in f["origen"]}, key=lambda r: fila_y[r])
        destinos = sorted({fila_de(t) for t in f["destino"]}, key=lambda r: fila_y[r])
        for o in origenes:
            puerto(fid, o, xc, True)
        attrs = {"celeris_id": fid, "celeris_tipo": "flujo", "etiqueta": etiqueta_flujo(f), "proposito": f["proposito"],
                 "origen": ", ".join(f["origen"]), "destino": ", ".join(f["destino"]),
                 "proteccion": f["proteccion"]["detalle"], "riesgo_residual": f.get("riesgo_residual", ""),
                 "regla_fw": f.get("regla_fw", ""), "tooltip": f"{etiqueta_flujo(f)}\n{f['proposito']}\n{f['proteccion']['detalle']}"}
        for t in destinos:
            arriba = [o for o in origenes if fila_y[o] < fila_y[t]]
            abajo = [o for o in origenes if fila_y[o] > fila_y[t]]
            dst = puerto(fid, t, xc, False) if t not in origenes else puertos[(fid, t)]
            if arriba:
                d.flecha(puertos[(fid, arriba[0])], dst, estilo, etiqueta_flujo(f), attrs)
            if abajo:
                d.flecha(puertos[(fid, abajo[-1])], dst, estilo, etiqueta_flujo(f), attrs)
    # leyenda y panel a la derecha
    xp = x_fin + 10
    alto_p = d.panel(xp, 10, 500, orden_inventario(x, d.presentes), max_si_falla=62)
    alto_l = d.leyenda(xp, 10 + alto_p + 10, w=500, carriles=True)
    d.alto = max(y_fin + 20, 10 + alto_p + 10 + alto_l + 20)
    return d


# --------------------------------------------------------------------------------------------------
# FIG-5.2 — topología lógica
# --------------------------------------------------------------------------------------------------
def fig_5_2(x: Infra) -> Diagrama:
    ids = set(componentes_de(x, "FIG-5.2"))
    d = Diagrama(x, "FIG-5.2", 2290, 1400)
    d.titulo(w=1740)
    fw = x.componentes["FW01"]
    wan = next(i for i in fw["ips"] if i["interfaz"] == "wan")
    d.zona("INTERNET", 20, 62, 240, 96, f"<br>ISP · WAN {wan['ip']}")
    d.componente("FW01", 320, 68, w=240)
    filas = [f"{esc(i['interfaz'])} · {esc(i['ip'])} · {esc(i['zona'])}" for i in fw["ips"]]
    d.nota(1180, 62, 290, 20 + 13 * len(filas), "<b>FW01: subinterfaces (gateway .1 de cada VLAN)</b><br>" + "<br>".join(filas),
           {"celeris_rol": "tabla", "celeris_ref": "FW01"})
    d.flecha(d.nodos["INTERNET"], d.nodos["FW01"], "html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=2;fontSize=10;labelBackgroundColor=#FFFFFF;", "WAN")
    vlans = [str(x.zonas[i["zona"]]["vlan"]) for i in fw["ips"] if x.zonas[i["zona"]].get("vlan") is not None]
    nativa = x.zonas["BLACKHOLE"]["vlan"]
    est_trunk = "rounded=0;whiteSpace=wrap;html=1;fillColor=#4D4D4D;strokeColor=#1A1A1A;fontColor=#FFFFFF;fontSize=10;"
    trunk = d.caja(20, 200, 1740, 24, est_trunk,
                   f"<b>Trunk 802.1Q</b> FW01 ↔ SW-CORE01 (PG-FW-TRUNK) · VLAN permitidas {', '.join(vlans)} · nativa {nativa} (BLACKHOLE, sin uso) · "
                   "la VLAN 70 no viaja al firewall", {"celeris_rol": "trunk", "celeris_ref": "SW-CORE01"})
    trunk2 = d.caja(366, 480, 1394, 20, est_trunk, "<b>Trunk 802.1Q</b> (continuación, mismo enlace) · VLAN 50, 60, 71",
                    {"celeris_rol": "trunk", "celeris_ref": "SW-CORE01"})
    d.flecha(trunk, trunk2, "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=3;exitX=1;exitY=0.5;entryX=1;entryY=0.5;",
             puntos=[(1775, 212), (1775, 490)])
    d.flecha(d.nodos["FW01"], trunk, "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=3;")
    BW, BH = 158, 56
    disp = [
        ("MGMT", 20, 248, 2, ["JMP01", "SW-CORE01", "BRK01", "ESX01", "IPMI01", "UPS01", "NAS01:gestion"], trunk),
        ("SERVERS", 366, 248, 2, ["CTRL01", "DB01", "OBS01", "SVC01"], trunk),
        ("LAB", 712, 248, 2, ["LABCLI01", "PROBE01", "HNY02", "SW-ACC"], trunk),
        ("LAB-TEST", 1058, 248, 1, ["KALI01"], trunk),
        ("DMZ-SVC", 1240, 248, 2, ["WAF01", "WEB01"], trunk),
        ("DMZ-HONEY", 1586, 248, 1, ["HNY01"], trunk),
        ("SECURITY", 366, 520, 2, ["SIEM01", "IDS01"], trunk2),
        ("EDGE", 712, 520, 2, ["EDGE01", "EDGE02"], trunk2),
        ("STORAGE", 1058, 520, 2, ["ESX01:vmk1", "NAS01"], None),
        ("BACKUP", 1404, 520, 1, ["NAS01:respaldo"], trunk2),
    ]
    for zid, zx, zy, cols, occ, bus in disp:
        z = x.zonas[zid]
        occ = [o for o in occ if o.split(":")[0] in ids]
        filas_z = (len(occ) + cols - 1) // cols
        zw = PAD + cols * (BW + 8) + 2
        zh = 48 + filas_z * (BH + 8) + 4
        gw = f"GW {z['gateway']}" if z["gateway"] else "<b>sin gateway, no enrutada</b>"
        zc = d.zona(zid, zx, zy, zw, zh, f"<br>{gw} · {z['hosts_utiles']} hosts útiles")
        for i, o in enumerate(occ):
            cx, cy = zx + PAD + (i % cols) * (BW + 8), zy + 48 + (i // cols) * (BH + 8)
            if ":" in o:
                d.interfaz(o, cx, cy + 6, w=BW, h=HP)
            else:
                d.componente(o, cx, cy, w=BW, h=BH, compacto=True, solo_iface=IFACE_PRINCIPAL.get(o))
        if bus and z["gateway"]:
            d.flecha(zc, bus, "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=1.5;fontSize=9;"
                     "labelBackgroundColor=#FFFFFF;exitX=0.5;exitY=0;", f"VLAN {z['vlan']} · .1")
    # AWS: VPC, subredes y tablas de rutas
    ya = 700
    d.zona("AWS", 20, ya, 580, 450, "")
    d.grupo_aws("AWS-VPC", 32, ya + 34, 556, 406)
    ocupa = {"AWS-PUB-A": "NAT01", "AWS-APP-A": "EC2-SHIELD", "AWS-APP-B": "EC2-CTRLR"}
    rejilla = [("AWS-PUB-A", 0, 0), ("AWS-APP-A", 1, 0), ("AWS-DATA-A", 2, 0), ("AWS-PUB-B", 0, 1), ("AWS-APP-B", 1, 1), ("AWS-DATA-B", 2, 1)]
    for sid, col, fila in rejilla:
        sx, sy = 42 + col * 180, ya + 70 + fila * 116
        d.grupo_aws(sid, sx, sy, 172, 108)
        if sid in ocupa and ocupa[sid] in ids:
            d.componente(ocupa[sid], sx + 6, sy + 44, w=160, h=BH, compacto=True)
    rt = [esc(x.componentes["AWS-PUB-A"]["aporta"]), esc(x.componentes["AWS-APP-A"]["aporta"]),
          "AWS-APP-B: " + esc(x.componentes["AWS-APP-B"]["aporta"]),
          f"Reservado: {esc(next(r['cidr'] for r in x.inv['reservas'] if r['id'] == 'RES-AWS-CRECIMIENTO'))} (crecimiento)"]
    d.nota(42, ya + 306, 532, 124, "<b>Tablas de rutas de la VPC</b> (texto del inventario; IGW y tablas sin ID: CI-13)<br>" + "<br>".join(rt),
           {"celeris_rol": "tablas_rutas", "celeris_ref": "AWS-VPC"}, tam=10)
    # Resumen zona × zona (matriz_esperada)
    orden_m = x.orden_matriz
    celdas = x.matriz_esperada()
    cw, ch, mx, my = 50, 24, 620, 726
    d.nota(mx, ya, 12 * cw + 92, 24, "<b>Resumen zona × zona</b> (fila = origen, columna = destino; ✔ permitido, ✖ denegado; detalle en el Anexo A)",
           {"celeris_rol": "matriz"}, color="#FFFFFF", borde="#FFFFFF", tam=10)
    abrev = {"SERVERS": "SRV", "LAB-TEST": "L-TST", "DMZ-SVC": "D-SVC", "DMZ-HONEY": "D-HNY", "SECURITY": "SEC", "STORAGE": "STOR",
             "BACKUP": "BKP", "INTERNET": "INET"}
    celda_txt = f"rounded=0;html=1;whiteSpace=wrap;fontSize=9;fontColor={TEXTO};strokeColor=#BBBBBB;align=center;verticalAlign=middle;"
    d.caja(mx, my, 92, ch, celda_txt + "fillColor=#EEEEEE;", "<b>origen \\ destino</b>")
    for j, zd in enumerate(orden_m):
        d.caja(mx + 92 + j * cw, my, cw, ch, celda_txt + "fillColor=#EEEEEE;", f"<b>{abrev.get(zd, zd)}</b>")
    for i, zo in enumerate(orden_m):
        col = x.zonas[zo].get("color")
        d.caja(mx, my + (i + 1) * ch, 92, ch, celda_txt + f"fillColor={aclarar(col, 0.8) if col else '#EEEEEE'};", f"<b>{zo}</b>")
        for j, zd in enumerate(orden_m):
            c = celdas.get((zo, zd), {"estado": "no_aplica"})
            fl = ",".join(c.get("flujos", []))
            if c["estado"] == "permitido":
                txt, fill = "✔ " + (fl if len(fl) <= 7 else "F…"), "#FFFFFF"
            elif c["estado"] == "denegado":
                txt, fill = "✖", "#F2F2F2"
            else:
                txt, fill = "—", "#DDDDDD"
            if c.get("pendiente"):
                txt += "*"
            d.caja(mx + 92 + j * cw, my + (i + 1) * ch, cw, ch, celda_txt + f"fillColor={fill};", txt,
                   {"celeris_rol": "celda", "par": f"{zo}>{zd}", "estado": c["estado"], "flujos": fl})
    d.nota(mx, my + 13 * ch + 4, 12 * cw + 92, 34, "* observación abierta en CAMBIOS-INVENTARIO.md (CI-03…CI-07) · «F…»: varios flujos (ver Anexo A) · "
           "— : intra-zona (capa 2) o no aplica", {"celeris_rol": "nota"}, color="#FFFFFF", borde="#FFFFFF", tam=9)
    # Ruteo y servicios base
    vpn = x.inv["vpn"]
    on, aws = vpn["extremo_onpremise"], vpn["extremo_aws"]
    ruteo = [
        f"0.0.0.0/0 → ISP por la WAN {wan['ip']} (salto del ISP no definido: CI-24)",
        f"{', '.join(aws['redes_anunciadas'])} → AWS por BGP (VTI1 activo, VTI2 respaldo) · ASN {on['asn']} ↔ {aws['asn']}",
        f"FW01 anuncia {', '.join(on['redes_anunciadas'])} (futuro {on['redes_anunciadas_futuro']}; CI-25)",
        "Entre VLAN: FW01 router-on-a-stick, deny-all con registro",
        f"VLAN {x.zonas['STORAGE']['vlan']} {x.zonas['STORAGE']['cidr']}: sin gateway, no enrutada",
    ]
    d.nota(1312, ya, 448, 22 + 15 * len(ruteo) + 8, "<b>Ruteo</b><br>" + "<br>".join(esc(r) for r in ruteo),
           {"celeris_rol": "ruteo", "celeris_ref": "FW01"}, borde="#1A1A1A", tam=10)
    sb = x.inv["servicios_base"]
    serv = [
        f"DHCP: pools por VLAN en FW01 o DHCP existente de la DTI [S-14]; {', '.join(sb['dhcp']['controles'])}",
        f"DNS primario: {sb['dns']['primario']['componente']} {sb['dns']['primario']['ip']} ({sb['dns']['primario']['software']}, DNSSEC)",
        f"DNS secundario: {sb['dns']['secundario']['componente']} ({sb['dns']['secundario']['ip']})",
        f"PAC: {sb['pac']['url']} → " + ", ".join(f"{r['componente']} {r['ip']}" for r in sb['pac']['registros_a']),
        f"NTP: {sb['ntp']['servidor']['componente']} ({sb['ntp']['servidor']['software']}); hacia arriba {sb['ntp']['hacia_arriba']}",
        f"IPv6: {sb['ipv6']['postura']} ({', '.join(sb['ipv6']['controles'])})",
        f"DNS cifrado: {sb['dns_cifrado']['dot']}",
    ]
    d.nota(1312, ya + 130, 448, 22 + 15 * len(serv) + 44, "<b>Servicios base</b><br>" + "<br>".join(esc(s) for s in serv),
           {"celeris_rol": "servicios_base"}, borde="#1A1A1A", tam=10)
    alto_l = d.leyenda(20, 1170, w=1740, flujos=False)
    d.panel(1780, 10, 500, orden_inventario(x, d.presentes), max_si_falla=68)
    d.alto = max(d.alto, 1170 + alto_l + 20)
    return d


# --------------------------------------------------------------------------------------------------
# FIG-5.3 — seguridad y zonas
# --------------------------------------------------------------------------------------------------
def fig_5_3(x: Infra) -> Diagrama:
    ids = set(componentes_de(x, "FIG-5.3"))
    d = Diagrama(x, "FIG-5.3", 2290, 1300)
    d.titulo(w=1740)
    bandas = [
        ("INTERNET", [], []),
        ("PERIMETRO", ["FW01", "VTI1", "VTI2"], []),
        ("DMZ-HONEY", ["HNY01"], [("DMZ-SVC", ["WAF01", "WEB01"])]),
        ("LAB", ["LABCLI01", "PROBE01", "HNY02", "SW-ACC"], [("LAB-TEST", ["KALI01"])]),
        ("EDGE", ["EDGE01", "EDGE02"], []),
        ("SERVERS", ["CTRL01", "DB01", "OBS01", "SVC01"], [("SECURITY", ["SIEM01", "IDS01"])]),
        ("BACKUP", ["NAS01:respaldo"], [("STORAGE", ["NAS01", "ESX01:vmk1"])]),
        ("MGMT", ["JMP01", "SW-CORE01", "BRK01", "ESX01", "IPMI01", "UPS01", "NAS01:gestion"], []),
    ]
    am_por_comp: dict[str, list[str]] = {}
    for am in x.amenazas.values():
        punto = next((c for c in am["componentes"] if c in ids), None)
        if punto:
            am_por_comp.setdefault(punto, []).append(am["id"])
    d.caja(20, 62, 1400, 22, f"text;html=1;align=left;fontSize=11;fontColor={TEXTO};",
           "<b>De menor a mayor confianza</b> (arriba: Internet, confianza Nula → abajo: MGMT, confianza Máxima). "
           "Etiquetas negras AM-xx = amenaza STRIDE mitigada en ese punto.")
    y = 90
    for zid, occ, adicionales in bandas:
        h = 64 if zid == "INTERNET" else (H + 62)
        segmentos = [(zid, occ)] + adicionales
        xs = 20
        for zz, oo in segmentos:
            z = x.zonas[zz]
            ancho = max(PAD + len(oo) * (W + GAP), 380) if oo else 560
            conf = f"confianza <b>{esc(z['confianza'])}</b>" + (f" ({esc(z['confianza_nota'])})" if z.get("confianza_nota") else "")
            regla = f"<br><i>{esc(z['regla_diseno'])}</i>"
            if zz == "PERIMETRO":
                d.caja(xs, y, ancho, h, "rounded=0;whiteSpace=wrap;html=1;fillColor=#F2F2F2;strokeColor=#1A1A1A;strokeWidth=2;"
                       f"verticalAlign=top;align=left;spacingLeft=6;fontSize=10;fontColor={TEXTO};",
                       f"<b>PERIMETRO</b> · {conf} · <i>{esc(z['regla_diseno'])}</i>",
                       {"celeris_id": "PERIMETRO", "celeris_tipo": "zona", "confianza": z["confianza"]})
                d.nodos["PERIMETRO"] = d.celdas[-1].get("id")
                d.zonas_dibujadas.append("PERIMETRO")
            elif zz == "INTERNET":
                d.zona("INTERNET", xs, y, ancho, h, f" · {conf}<br><i>{esc(z['regla_diseno'])}</i>")
            else:
                gw = " · <b>sin gateway, no enrutada</b>" if z["gateway"] is None else ""
                vlan = f"VLAN {z['vlan']} · " if z.get("vlan") is not None else ""
                d.caja(xs, y, ancho, h, f"rounded=0;whiteSpace=wrap;html=1;fillColor={aclarar(z['color'], 0.86)};strokeColor={z['color']};strokeWidth=2;"
                       f"verticalAlign=top;align=left;spacingLeft=6;spacingTop=1;fontSize=10;fontColor={TEXTO};",
                       f"<b>{vlan}{esc(zz)}</b> · {esc(z['cidr'])} · {conf}{gw}{regla}",
                       {"celeris_id": zz, "celeris_tipo": "zona", "cidr": z["cidr"], "confianza": z["confianza"],
                        "tooltip": f"{zz}: {z['proposito']}. Regla: {z['regla_diseno']}"})
                d.nodos[zz] = d.celdas[-1].get("id")
                d.zonas_dibujadas.append(zz)
            for i, o in enumerate(oo):
                cx, cy = xs + PAD + i * (W + GAP), y + 58
                if ":" in o:
                    d.interfaz(o, cx, cy + 20)
                    continue
                d.componente(o, cx, cy, compacto=True, h=H - 20, solo_iface=IFACE_PRINCIPAL.get(o))
                for j, am in enumerate(am_por_comp.get(o, [])):
                    a = x.amenazas[am]
                    d.caja(cx + W - 46 - j * 47, cy + H - 18, 44, 16,
                           "rounded=1;html=1;fillColor=#000000;strokeColor=#000000;fontColor=#FFFFFF;fontSize=9;fontStyle=1;",
                           esc(am), {"celeris_id": am, "celeris_tipo": "amenaza", "stride": "".join(a["stride"]),
                                     "amenaza": a["amenaza"], "control": a["control"],
                                     "tooltip": f"{am} ({''.join(a['stride'])}): {a['amenaza']} → {a['control']}"})
            xs += ancho + 12
        if zid == "PERIMETRO":
            d.nota(xs, y, 1420 - xs, h, f"<b>Controles de FW01</b>: {esc(x.componentes['FW01']['controles'])}",
                   {"celeris_rol": "controles", "celeris_ref": "FW01"}, color="#FFFFFF", borde="#1A1A1A", tam=10)
        y += h + 8
    y_bandas = y
    # Detecciones DET-xx (columna derecha), recolectadas en SIEM01
    x_det, w_det = 1440, 320
    d.nota(x_det, 62, w_det, 22, "<b>Detecciones (D1.14) → recolectadas en SIEM01</b>", {"celeris_rol": "titulo_det"}, color="#FFFFFF", tam=10)
    yd = 88
    for det in x.detecciones.values():
        pruebas = ", ".join(det["validacion"]["pruebas"]) or "sin T-nn (CI-17)"
        texto = (f"<b>{esc(det['id'])}</b> · {esc(det['tecnologia'])} · {esc(det['ubicacion_detalle'])}<br>"
                 f"{esc(det['que_detecta'])} · ATT&amp;CK {esc(', '.join(det['attack']) or '—')} · valida {esc(pruebas)}")
        nid = d.nota(x_det, yd, w_det, 66, texto, {"celeris_id": det["id"], "celeris_tipo": "deteccion", "ubicacion": det["ubicacion"]},
                     color="#E8F4FB", borde="#56B4E9", tam=9)
        d.nodos[det["id"]] = nid
        yd += 72
    # Capturas de IDS01 (interfaces captura-NN)
    ids01 = d.nodos.get("IDS01")
    vlan_zona = {str(z["vlan"]): zid for zid, z in x.zonas.items() if z.get("vlan") is not None}
    for i in x.componentes["IDS01"]["ips"]:
        if i["interfaz"].startswith("captura") and ids01:
            vl = i["interfaz"].split("-")[1]
            zona = vlan_zona[vl]
            if zona in d.nodos and zona != "SECURITY":
                lados = ("exitX=0.5;exitY=1;entryX=0.95;entryY=1;" if zona == "SERVERS"
                         else "exitX=1;exitY=0.5;entryX=1;entryY=0.5;")
                d.flecha(ids01, d.nodos[zona], "edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#56B4E9;strokeWidth=2;dashed=1;dashPattern=1 2;"
                         "endArrow=oval;endFill=1;fontSize=9;labelBackgroundColor=#FFFFFF;" + lados,
                         f"captura VLAN {vl} (DET-02)")
    # La recolección hacia SIEM01 (F13 agentes, F14 syslog de FW01) se dibuja en FIG-5.5b; aquí va en el título de DET-xx.
    # Defensa en profundidad (D1.9; CI-24)
    yb = max(y_bandas, yd) + 6
    d.caja(20, yb, 1740, 20, f"text;html=1;align=left;fontSize=11;fontColor={TEXTO};",
           "<b>Defensa en profundidad</b> (capas de D1.9; la tabla no está en infra/*.yaml: CI-24)", {"celeris_rol": "defensa"})
    cw = 1740 // len(CAPAS_D19)
    for i, (capa, control) in enumerate(CAPAS_D19):
        d.nota(20 + i * cw, yb + 22, cw - 6, 76, f"<b>{i + 1}. {esc(capa)}</b><br>{esc(control)}", {"celeris_rol": "capa"},
               color="#F7F7F7", borde="#4D4D4D", tam=9)
    ya = yb + 108
    alto_l = d.leyenda(20, ya, w=1100)
    filas_am = [f"<b>{esc(a['id'])}</b> ({esc(''.join(a['stride']))}) {esc(a['amenaza'])} → {esc(a['control'])}" for a in x.amenazas.values()]
    alto_am = 24 + 13 * len(filas_am) + 6
    d.nota(1130, ya, 630, alto_am, "<b>Amenazas STRIDE (AM-xx), marcadas en su punto de mitigación</b><br>" + "<br>".join(filas_am),
           {"celeris_rol": "amenazas"}, tam=9)
    alto_p = d.panel(1780, 10, 500, orden_inventario(x, d.presentes), max_si_falla=62)
    d.alto = max(ya + max(alto_l, alto_am) + 20, 10 + alto_p + 20)
    return d


# --------------------------------------------------------------------------------------------------
# FIG-5.4 — VPN híbrida
# --------------------------------------------------------------------------------------------------
def fig_5_4(x: Infra) -> Diagrama:
    vpn = x.inv["vpn"]
    d = Diagrama(x, "FIG-5.4", 2200, 1100)
    d.titulo(w=1660)
    on, aws = vpn["extremo_onpremise"], vpn["extremo_aws"]
    d.caja(20, 70, 500, 430, "rounded=0;whiteSpace=wrap;html=1;fillColor=#F2F2F2;strokeColor=#1A1A1A;strokeWidth=2;verticalAlign=top;"
           f"align=left;spacingLeft=8;spacingTop=4;fontSize=11;fontColor={TEXTO};",
           f"<b>On-premise · Campus Juliaca (PERIMETRO)</b><br>Redes anunciadas por BGP: {esc(', '.join(on['redes_anunciadas']))} "
           f"(futuro {esc(on['redes_anunciadas_futuro'])}) · ASN {on['asn']}",
           {"celeris_id": "PERIMETRO", "celeris_tipo": "zona"})
    d.nodos["PERIMETRO"] = d.celdas[-1].get("id")
    d.componente("FW01", 40, 140, w=240)
    d.componente("VTI1", 320, 250, w=180)
    d.componente("VTI2", 320, 360, w=180)
    for v in ("VTI1", "VTI2"):
        d.flecha(d.nodos["FW01"], d.nodos[v], "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#7F7F7F;exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    d.nota(40, 250, 260, 120, f"<b>Extremo on-premise</b><br>{esc(on['dispositivo'])}<br>IP pública {esc(on['ip_publica'])} ({esc(on['ip_publica_nota'])})",
           {"celeris_rol": "extremo", "celeris_ref": "FW01"}, tam=10)
    d.zona("INTERNET", 570, 260, 270, 150, "<br>transporte de los túneles")
    d.zona("AWS", 890, 70, 790, 760, f" · {x.zonas['AWS']['cidr']}")
    d.componente("VGW", 910, 270, w=220)
    d.nota(910, 110, 220, 140, f"<b>Extremo AWS</b><br>{esc(aws['dispositivo'])}<br>{esc(aws['ip_publica'])}<br>Anuncia {esc(', '.join(aws['redes_anunciadas']))} · "
           f"ASN {aws['asn']} ({esc(aws['asn_nota'])})", {"celeris_rol": "extremo", "celeris_ref": "VGW"}, tam=10)
    rt = d.nota(910, 420, 230, 390, "<b>Propagación de rutas (BGP → tablas de la VPC)</b><br>" + esc(x.componentes["VGW"]["aporta"]) + "<br><br>"
                + esc(x.componentes["AWS-PUB-A"]["aporta"]) + "<br><br>" + esc(x.componentes["AWS-APP-A"]["aporta"])
                + "<br><br><b>Observación CI-25</b>: FW01 anuncia " + esc(", ".join(on["redes_anunciadas"])) + "; las tablas citan "
                + esc(on["redes_anunciadas_futuro"]) + ".", {"celeris_rol": "rutas", "celeris_ref": "AWS-VPC"}, tam=10)
    d.flecha(d.nodos["VGW"], rt, "edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#8C4FFF;strokeWidth=1.5;dashed=1;dashPattern=4 3;endArrow=block;"
             "fontSize=9;labelBackgroundColor=#FFFFFF;", "propaga")
    d.grupo_aws("AWS-VPC", 1160, 110, 500, 700)
    for k, (sid, occ) in enumerate([("AWS-PUB-A", "NAT01"), ("AWS-APP-A", "EC2-SHIELD"), ("AWS-APP-B", "EC2-CTRLR")]):
        sy = 150 + k * 215
        d.grupo_aws(sid, 1175, sy, 470, 200)
        d.componente(occ, 1190, sy + 40, w=200)
        titulo = "Controles" if occ == "NAT01" else "Security Group"
        d.nota(1400, sy + 40, 230, 145, f"<b>{titulo} de {occ}</b><br>" + esc(x.componentes[occ]["controles"]),
               {"celeris_rol": "sg", "celeris_ref": occ}, tam=10)
    tuneles(d)
    f1, f2, bgp, dpd = vpn["fase1"], vpn["fase2"], vpn["bgp"], vpn["dpd"]
    params = [
        f"Tipo: {vpn['tipo']}",
        f"Fase 1 (IKEv2): {f1['cifrado']} · PRF {f1['prf']} · DH {f1['dh']} · vida {f1['vida_s']} s",
        f"Fase 2 (ESP): {f2['cifrado']} · PFS {f2['pfs']} · vida {f2['vida_s']} s",
        f"DPD: cada {dpd['intervalo_s']} s, acción {dpd['accion']}",
        f"BGP: keepalive {bgp['keepalive_s']} s · hold {bgp['hold_s']} s ({bgp['hold_nota']}) · {bgp['respaldo']}",
        f"MTU {vpn['mtu']} · MSS clamping {vpn['mss_clamping']} · {vpn['capacidad_gbps_por_tunel']} Gbps por túnel",
        f"IPv6: {vpn['ipv6']} · Convergencia meta ≤ {vpn['convergencia_meta_s']} s (prueba {vpn['convergencia_prueba']})",
        f"Secretos: {vpn['secretos']}",
        "Flujos sobre la VPN: " + "; ".join(etiqueta_flujo(x.flujos[f]) for f in vpn["flujos_sobre_vpn"]),
        f"Pruebas: {', '.join(vpn['pruebas'])} · Escalamiento: {vpn['escalamiento']}",
    ]
    d.nota(20, 520, 850, 24 + 15 * len(params) + 30, "<b>Parámetros de la VPN (D1.10, sin secretos)</b><br>" + "<br>".join(esc(p) for p in params),
           {"celeris_rol": "parametros_vpn", "celeris_ref": vpn["id"]}, color="#F3EDFF", borde="#8C4FFF", tam=10)
    alto_l = d.leyenda(20, 850, w=1660, flujos=False)
    alto_p = d.panel(1700, 10, 490, orden_inventario(x, d.presentes), max_si_falla=62)
    d.alto = max(850 + alto_l + 20, alto_p + 30)
    return d


# --------------------------------------------------------------------------------------------------
# FIG-1.1 — topología ejecutiva (≤ 12 bloques)
# --------------------------------------------------------------------------------------------------
def fig_1_1(x: Infra) -> Diagrama:
    """≤ 12 bloques; cada uno con la frase de lo que aporta (aporta_corto del componente o propósito de la zona)."""
    d = Diagrama(x, "FIG-1.1", 1640, 860)
    d.titulo(w=1600)
    plantilla = (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={{fill}};strokeColor={{stroke}};strokeWidth={{sw}};"
                 f"align=center;verticalAlign=middle;fontSize=13;fontColor={TEXTO};spacing=6;spacingLeft={{sl}};")

    def bloque(cid, x0, y0, w, h, titulo, frase, incluye=None):
        if cid in x.componentes:
            c = x.componentes[cid]
            sw, tag = CRITICIDAD[c["criticidad"]]
            color = color_de(x, c)
            attrs = d.datos_componente(c)
            label = f"<b>{esc(titulo)}</b> · <b>{tag}</b><br>{esc(ip_texto(x, c))}<br><i>{esc(frase)}</i>"
            d.presentes.append(cid)
        else:
            z = x.zonas.get(cid)
            color = (z or {}).get("color") or ("#4D4D4D" if z else "#8C4FFF")
            sw = 2
            attrs = {"celeris_id": cid, "celeris_tipo": "zona" if z else "vpn"}
            cidr = f"<br>{esc(z['cidr'])}" if z and z.get("cidr") else ""
            nombre = f" · zona {esc(cid)}" if z and cid not in titulo else ""
            label = f"<b>{esc(titulo)}</b>{nombre}{cidr}<br><i>{esc(frase)}</i>"
            if z and z.get("color"):
                d.zonas_dibujadas.append(cid)
        if incluye:
            attrs["celeris_incluye"] = ",".join(incluye)
        fill = aclarar(color, 0.86) if color not in ("#4D4D4D", AWS_TINTA) else "#F2F2F2"
        icono = cid in x.componentes and x.componentes[cid]["tipo"] in ICONO
        nid = d.caja(x0, y0, w, h, plantilla.format(fill=fill, stroke=color, sw=sw, sl=34 if icono else 6), label, attrs)
        d.nodos[cid] = nid
        if icono:
            d.caja(x0 + 6, y0 + 6, 26, 26, ICONO[x.componentes[cid]["tipo"]] + "html=1;aspect=fixed;outlineConnect=0;dashed=0;")
            d.tipos.add(x.componentes[cid]["tipo"])
        return nid

    z, c = x.zonas, x.componentes
    vpn_id = x.inv["vpn"]["id"]
    BW, BH = 300, 100
    bloque("DMZ-SVC", 20, 70, BW, BH, "Portal de transparencia (WAF01 + WEB01)", c["WAF01"]["aporta_corto"], ["WAF01", "WEB01"])
    bloque("INTERNET", 660, 70, BW, BH, "Internet", z["INTERNET"]["proposito"].split(":")[0])
    bloque("LAB", 20, 240, 240, BH, "Usuarios de laboratorio (LAB + LAB-TEST)", z["LAB"]["proposito"].split(".")[0], ["LAB", "LAB-TEST"])
    bloque("FW01", 660, 240, BW, BH, "FW01 · Firewall OPNsense", c["FW01"]["aporta_corto"])
    bloque(vpn_id, 1000, 240, 280, BH, "VPN IPsec (VTI1 activo, VTI2 respaldo)", f"IKEv2 · {x.inv['vpn']['fase1']['cifrado']} · BGP", ["VTI1", "VTI2"])
    bloque("VGW", 1320, 240, 300, BH, "VGW · extremo AWS", c["VGW"]["aporta_corto"])
    bloque("EDGE", 350, 240, 270, BH, "Nodos de caché (EDGE01, EDGE02)", c["EDGE01"]["aporta_corto"], ["EDGE01", "EDGE02"])
    bloque("SERVERS", 660, 410, BW, BH, "Zonas internas: SERVERS, MGMT, STORAGE, BACKUP", "Control, DNS/PAC/NTP, gestión con MFA y respaldos",
           ["SERVERS", "MGMT", "STORAGE", "BACKUP"])
    bloque("SECURITY", 1000, 410, 280, BH, "SIEM y detección (SIEM01, IDS01)", c["SIEM01"]["aporta_corto"], ["SIEM01", "IDS01"])
    bloque("AWS-VPC", 1320, 410, 300, 130, "AWS · VPC " + c["AWS-VPC"]["cidr"],
           c["EC2-SHIELD"]["aporta_corto"] + "; " + c["EC2-CTRLR"]["aporta_corto"].lower(), ["AWS-VPC", "EC2-SHIELD", "EC2-CTRLR", "NAT01"])
    bloque("DMZ-HONEY", 20, 410, BW, BH, "Señuelos (HNY01)", z["DMZ-HONEY"]["regla_diseno"], ["HNY01"])
    bloque("ESX01", 660, 580, BW, BH, "ESX01 · Servidor ESXi", c["ESX01"]["aporta_corto"])
    e = "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=11;labelBackgroundColor=#FFFFFF;strokeColor=#1A1A1A;endArrow=block;endFill=1;strokeWidth=1.5;"
    n = d.nodos

    def conex(fid, a, b, label=None, extra=""):
        f = x.flujos[fid]
        est = e + ("" if f["proteccion"]["tipo"] in CIFRADOS else "dashed=1;dashPattern=8 4;") + extra
        d.flecha(n[a], n[b], est, label or f"{fid} · {protocolos_texto(f)}", {"celeris_id": fid, "celeris_tipo": "flujo", "etiqueta": etiqueta_flujo(f)})

    conex("F21", "INTERNET", "DMZ-SVC", "F21 · " + protocolos_texto(x.flujos["F21"]).split(" + ")[0])
    conex("F1", "LAB", "EDGE", "F1 · " + protocolos_texto(x.flujos["F1"]))
    conex("F8", "EDGE", "FW01", "F8 · MISS")
    conex("F13", "SERVERS", "SECURITY", "F13 · agentes Wazuh")
    gris = "html=1;endArrow=none;strokeColor=#7F7F7F;strokeWidth=1.5;fontSize=11;labelBackgroundColor=#FFFFFF;"
    d.flecha(n["INTERNET"], n["FW01"], gris + "strokeColor=#4D4D4D;strokeWidth=2;", "WAN")
    d.flecha(n["FW01"], n[vpn_id], "html=1;endArrow=none;strokeColor=#8C4FFF;strokeWidth=3;")
    d.flecha(n[vpn_id], n["VGW"], "html=1;endArrow=none;strokeColor=#8C4FFF;strokeWidth=3;fontSize=11;labelBackgroundColor=#FFFFFF;", "2 túneles")
    d.flecha(n["VGW"], n["AWS-VPC"], "html=1;endArrow=none;strokeColor=#8C4FFF;strokeWidth=2;")
    d.flecha(n["FW01"], n["SERVERS"], gris, "ruteo entre zonas")
    d.flecha(n["ESX01"], n["SERVERS"], gris, "hospeda las VM")
    alto_l = d.leyenda(1000, 580, w=620)
    alto_p = d.panel(20, 580, 620, list(d.presentes), max_si_falla=80)
    d.alto = max(580 + alto_l + 20, 580 + alto_p + 20)
    return d


GENERADORES = {
    "FIG-1.1": fig_1_1, "FIG-5.1": fig_5_1, "FIG-5.2": fig_5_2, "FIG-5.3": fig_5_3, "FIG-5.4": fig_5_4,
    "FIG-5.5a": lambda x: fig_5_5(x, "FIG-5.5a"), "FIG-5.5b": lambda x: fig_5_5(x, "FIG-5.5b"),
}


def generar(x: Infra, salida: Path = SALIDA, figuras=None) -> list[Path]:
    salida.mkdir(parents=True, exist_ok=True)
    hechos = []
    for fig in figuras or FIGURAS:
        d = GENERADORES[fig](x)
        ruta = salida / f"{fig}.drawio"
        ruta.write_text(d.xml(), encoding="utf-8", newline="\n")
        hechos.append(ruta)
    return hechos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--figura", action="append", choices=FIGURAS)
    a = ap.parse_args(argv)
    for r in generar(Infra.cargar(), Path(a.salida), a.figura):
        print(r.relative_to(RAIZ) if r.is_relative_to(RAIZ) else r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
