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
- Disposición v0.4 (H1): FW01 detrás de FGT-EXT por la red de tránsito, 7 VLAN, WIFI-EST fuera de FW01, VPC con
  EC2-GW y app-a vacía, S3 fuera de la VPC. Las capas de defensa en profundidad salen de trazabilidad.yaml (CI-63).
- Lo que la figura pide y el inventario no trae se registra en docs/infra/e1/CAMBIOS-INVENTARIO.md (CI-70…CI-89).
- Todo componente, zona y flecha de flujo lleva el atributo `celeris_id` (validado por V-50+).
- Cada página cabe en 2^25 píxeles a escala 3: más allá, draw.io deja el final del PNG en blanco (ver `generar`).

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
    "aws_s3": "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.s3;fillColor=#7AA116;strokeColor=#FFFFFF;",
    "firewall_existente": "shape=mxgraph.networks.firewall;fillColor=#FFFFFF;strokeColor=#4D4D4D;dashed=1;",
    "grupo_pcs": "shape=mxgraph.networks.pc;fillColor=#FFFFFF;strokeColor=#4D4D4D;dashed=1;",
    "red_externa": "shape=mxgraph.networks.wireless_hub;fillColor=#FFFFFF;strokeColor=#4D4D4D;dashed=1;",
    "puesto_encargado": "shape=mxgraph.networks.monitor;fillColor=#CCCCCC;strokeColor=#4D4D4D;",
}
NOMBRE_ICONO = {
    "firewall": "Firewall", "switch": "Switch", "switch_existente": "Switch existente (fuera de alcance)",
    "puerto_emergencia": "Puerto break-glass (laptop)", "hipervisor": "Hipervisor", "gestion_fuera_banda": "Gestión fuera de banda",
    "ups": "UPS", "servidor": "Servidor / VM", "waf": "WAF", "web": "Servidor web", "honeypot": "Honeypot / canary",
    "ids": "Sensor IDS", "cliente_prueba": "Equipo de prueba", "nas": "NAS", "interfaz_tunel": "Interfaz de túnel (VTI)",
    "vpn_gateway": "VGW de AWS", "aws_instancia": "Instancia EC2", "aws_s3": "Bucket S3",
    "firewall_existente": "Firewall existente (DTI)", "grupo_pcs": "Grupo de PCs existentes",
    "red_externa": "Red Wi-Fi existente (DTI)", "puesto_encargado": "Puesto del encargado",
}
EXISTENTES = {"existente", "fuera_de_alcance"}
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

# Las capas de defensa en profundidad de D1.9 se leen de trazabilidad.yaml → defensa_profundidad (CI-63).

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


def estilo_flujo(f: dict) -> str:
    """Estilo de línea de CLAUDE.md: cifrado = continua; sin cifrar = discontinua; bloqueado = punteada con ✖."""
    if f["accion"] == "bloquear":
        return "dashed=1;dashPattern=1 4;strokeWidth=2;endArrow=cross;endFill=0;"
    if f["proteccion"]["tipo"] in CIFRADOS:
        return "strokeWidth=1.5;endArrow=block;endFill=1;"
    return "dashed=1;dashPattern=8 4;strokeWidth=1.5;endArrow=block;endFill=1;"


def ip_texto(x: Infra, comp: dict, detalle: bool = False) -> str:
    """IP (o rango) que se rotula en la segunda línea de la caja del componente."""
    if comp.get("cidr"):
        return comp["cidr"]
    ips = [i for i in comp["ips"] if i["ip"]]
    if comp["id"] == "FW01" and not detalle:
        wan = next(i["ip"] for i in ips if i["interfaz"] == "wan")
        return f"tránsito {wan} · .1 en {len(ips) - 1} VLAN"
    if comp["tipo"] == "grupo_pcs":
        labs = x.inv["rangos_lab"]["laboratorios"]
        return f"{labs[0]['id']}…{labs[-1]['id']}: {len(labs)} rangos /26 · DHCP con reservas"
    if comp["tipo"] == "red_externa":
        z = x.zonas[comp["zonas"][0]]
        return f"{z['cidr']} (provisional {z['supuesto'] and '[' + z['supuesto'] + ']'}) · red de la DTI"
    if comp["tipo"] == "aws_s3":
        s3 = x.inv["aws"]["s3"]
        return f"bucket {s3['bucket']} · Object Lock {s3['object_lock']['dias']} días"
    if comp["tipo"] == "firewall_existente":
        nombres = {"wan": "WAN", "transito": "tránsito"}
        return " · ".join(f"{nombres.get(i['interfaz'], i['interfaz'])} {i['ip']}" for i in ips)
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
        fuera = comp["estado"] in EXISTENTES
        if fuera:
            lineas[0] += " · <i>" + ("fuera de alcance" if comp["estado"] == "fuera_de_alcance" else "existente") + "</i>"
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
        elif z["tipo"] == "externa" and not z.get("color"):
            estilo = f"ellipse;shape=cloud;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#4D4D4D;fontSize=11;fontColor={TEXTO};"
            label = f"<b>{esc(z['nombre'])}</b>{extra}"
        elif z["tipo"] == "externa":
            # Red externa con color propio (WIFI-EST): rectángulo discontinuo, red de la DTI que FW01 no enruta.
            color = z["color"]
            estilo = (f"rounded=1;arcSize=4;whiteSpace=wrap;html=1;fillColor={aclarar(color, 0.75)};strokeColor={color};strokeWidth=2;"
                      f"dashed=1;dashPattern=8 4;verticalAlign=top;align=left;spacingLeft=6;spacingTop=2;fontSize=11;fontColor={TEXTO};")
            label = (f"<b>{esc(z['id'])}</b> · {esc(z['cidr'])} · confianza {esc(z['confianza'])} · "
                     f"<i>red de la DTI, fuera de FW01</i>{extra}")
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

    def flecha_flujo(self, fid: str, src: str, dst: str, label: str | None = None, extra="", puntos=None) -> str:
        """Una flecha del flujo F-nn entre dos celdas cualesquiera (p. ej. hacia la zona que contiene al destino)."""
        f = self.x.flujos[fid]
        estilo = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=9;labelBackgroundColor=#FFFFFF;"
                  f"strokeColor={FLECHA};fontColor={TEXTO};jumpStyle=gap;" + estilo_flujo(f) + extra)
        attrs = {"celeris_id": fid, "celeris_tipo": "flujo", "etiqueta": etiqueta_flujo(f), "proposito": f["proposito"],
                 "proteccion": f["proteccion"]["detalle"], "riesgo_residual": f.get("riesgo_residual", ""),
                 "regla_fw": f.get("regla_fw", ""), "tooltip": f"{etiqueta_flujo(f)}\n{f['proposito']}\n{f['proteccion']['detalle']}"}
        return self.flecha(src, dst, estilo, label or etiqueta_flujo(f), attrs, puntos=puntos)

    def nota_d25(self, x0, y0, w, h=58):
        """Nota visible de FIG-1.1 y FIG-5.1: la consola vive en el campus (D-25)."""
        d25 = self.x.decisiones["D-25"]["decision"]
        nube = [c for c in self.x.componentes.values() if "AWS" in c["zonas"] and c["tipo"] in ("aws_instancia", "aws_s3")
                and c["estado"] != "temporal"]
        return self.nota(x0, y0, w, h, f"<b>La consola no está en la nube: ver D-25</b> ({esc(d25)}). En AWS solo "
                         + " y ".join(esc(c["id"]) for c in nube) + ".", {"celeris_rol": "nota_d25", "celeris_ref": "D-25"},
                         color="#FFF8E1", borde="#1A1A1A", tam=11)

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
# Utilidades de disposición (v0.4)
# --------------------------------------------------------------------------------------------------
GRIS = "html=1;endArrow=none;strokeColor=#7F7F7F;strokeWidth=1.5;fontSize=10;labelBackgroundColor=#FFFFFF;"
VIOLETA = "html=1;endArrow=none;strokeColor=#8C4FFF;strokeWidth=3;fontSize=10;labelBackgroundColor=#FFFFFF;"
TRUNK = "rounded=0;whiteSpace=wrap;html=1;fillColor=#4D4D4D;strokeColor=#1A1A1A;fontColor=#FFFFFF;fontSize=10;"


def alto_texto(lineas: list[str], ancho: float, fuente: int = 10, extra: int = 26) -> int:
    return extra + sum(int(fuente * 1.4) * lineas_estimadas(l, ancho - 14, fuente) for l in lineas)


def vlans_fw(x: Infra) -> list[str]:
    fw = x.componentes["FW01"]
    return [str(x.zonas[i["zona"]]["vlan"]) for i in fw["ips"] if x.zonas[i["zona"]].get("vlan") is not None]


def destino_ruta(x: Infra, d: str) -> str:
    if d.startswith("supernet:"):
        sid = d.split(":", 1)[1]
        return next(s["cidr"] for s in x.inv["supernets"] if s["id"] == sid) + f" ({sid})"
    return {"prefijo_s3": "prefijo de S3"}.get(d, d)


SALTOS = {"internet_gateway": "Internet Gateway", "vgw": "VGW", "gateway_endpoint_s3": "Gateway Endpoint de S3"}


def tablas_rutas(x: Infra) -> list[str]:
    filas = []
    for rt in x.inv["aws"]["tablas_de_rutas"]:
        rutas = []
        for r in rt["rutas"]:
            salto = SALTOS.get(r["salto"], r["salto"].split(":", 1)[-1])
            extra = " (solo en el simulacro)" if r.get("solo_en_simulacro") else (f" ({r['nota']})" if r.get("nota") else "")
            rutas.append(f"{destino_ruta(x, r['destino'])} → {salto}{extra}")
        filas.append(f"<b>{esc(rt['id'])}</b> ({esc(', '.join(rt['subredes']))}): " + esc("; ".join(rutas)))
    return filas


def frase_con(texto: str, clave: str) -> str:
    return next((s.strip().rstrip(".") for s in re.split(r"(?<=[.;])\s", texto) if clave in s), "")


# --------------------------------------------------------------------------------------------------
# FIG-5.1 — topología general
# --------------------------------------------------------------------------------------------------
# filas de zonas: (y, [(zona, columnas, filas, ocupantes)]). La VLAN 30 agrupa los rangos y la infraestructura de LAB.
FILAS_51 = [
    (520, [("DMZ-SVC", 1, 1, ["PORTAL01"]), ("DMZ-HONEY", 1, 1, ["HNY01"]), ("EDGE", 2, 1, ["EDGE01", "EDGE02"]),
           ("SECURITY", 1, 1, ["SIEM01"]), ("SERVERS", 1, 1, ["CTRL01"])]),
    (690, [("LAB", 3, 2, ["PCS-LAB", "SW-ACC", "ENC01", "LABCLI01", "KALI01", "HNY02"]),
           ("MGMT", 3, 2, ["JMP01", "SW-CORE01", "BRK01", "ESX01", "IPMI01", "UPS01"])]),
]


def tam_zona(cols, filas):
    return PAD + cols * (W + GAP), CAB + PAD + filas * (H + GAP)


def fig_5_1(x: Infra) -> Diagrama:
    ids = set(componentes_de(x, "FIG-5.1"))
    d = Diagrama(x, "FIG-5.1", 2290, 1300)
    d.titulo(w=1710)
    d.nota_d25(20, 62, 520, 52)
    d.zona("INTERNET", 600, 62, 260, 80, "<br>orígenes web, ACME, feeds, S3")
    d.zona("WIFI-EST", 20, 150, 430, 150, "")
    wifi = d.componente("WIFI-EST", 30, 200, w=410)
    fgt = d.componente("FGT-EXT", 600, 170, w=260)
    d.flecha(d.nodos["INTERNET"], fgt, GRIS + "strokeColor=#4D4D4D;strokeWidth=2;", "WAN")
    d.flecha(wifi, fgt, GRIS + "dashed=1;", "BYOD por el FortiGate")
    fgt_c, fw_c = x.componentes["FGT-EXT"], x.componentes["FW01"]
    ip_fgt = next(i["ip"] for i in fgt_c["ips"] if i["interfaz"] == "transito")
    ip_fw = next(i["ip"] for i in fw_c["ips"] if i["interfaz"] == "wan")
    tz = d.zona("TRANSITO", 480, 276, 500, 64, f"<br>FGT-EXT {ip_fgt} ↔ FW01 {ip_fw}")
    fw = d.componente("FW01", 600, 360, w=260)
    d.flecha(fgt, tz, GRIS + "strokeColor=#999999;strokeWidth=3;")
    d.flecha(tz, fw, GRIS + "strokeColor=#999999;strokeWidth=3;")
    on = x.inv["vpn"]["extremo_onpremise"]
    d.nota(900, 150, 360, 96, f"<b>NAT 1:1 en FGT-EXT</b>: {esc(on['ip_publica'])} → {esc(on['ip_interna'])}<br>"
           f"{esc(on['nat_t_nota'])}<br>{esc(frase_con(fgt_c['aporta'], 'ruta estática'))}",
           {"celeris_rol": "nat", "celeris_ref": "FGT-EXT"}, tam=10)
    trunk = d.caja(20, 476, 1440, 24, TRUNK,
                   f"<b>Trunk 802.1Q</b> FW01 ↔ SW-CORE01: una subinterfaz .1 de FW01 por VLAN ({', '.join(vlans_fw(x))}) · "
                   f"nativa {x.zonas['BLACKHOLE']['vlan']} (BLACKHOLE, sin uso)", {"celeris_rol": "trunk", "celeris_ref": "SW-CORE01"})
    d.flecha(fw, trunk, "html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=3;")
    for fy, zonas in FILAS_51:
        zx = 20
        for zid, cols, filas, occ in zonas:
            zw, zh = tam_zona(cols, filas)
            d.zona(zid, zx, fy, zw, zh, f" · GW {x.zonas[zid]['gateway']}")
            for i, o in enumerate(occ):
                if o not in ids:
                    continue
                d.componente(o, zx + PAD + (i % cols) * (W + GAP), fy + CAB + (i // cols) * (H + GAP))
            zx += zw + 20
    # VTI y AWS (columna derecha)
    d.componente("VTI1", 1000, 352, w=220, h=54, compacto=True)
    d.componente("VTI2", 1000, 412, w=220, h=54, compacto=True)
    for v in ("VTI1", "VTI2"):
        d.flecha(fw, d.nodos[v], "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#7F7F7F;exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    d.zona("AWS", 1480, 62, 250, 880, f"<br>{x.zonas['AWS']['cidr']}")
    d.componente("VGW", 1495, 110, w=220)
    d.grupo_aws("AWS-VPC", 1490, 214, 230, 410)
    d.grupo_aws("AWS-PUB-A", 1498, 254, 214, 150)
    d.componente("EC2-GW", 1505, 294, w=200)
    d.grupo_aws("AWS-APP-A", 1498, 414, 214, 120)
    d.nota(1505, 452, 200, 72, esc(x.componentes["AWS-APP-A"]["aporta_corto"]), {"celeris_rol": "nota", "celeris_ref": "AWS-APP-A"},
           color="#FFFFFF", borde="#BBBBBB")
    res = next(r for r in x.inv["reservas"] if r["dentro_de"] == "AWS-CELERIS")
    d.nota(1498, 544, 214, 70, f"Reservado {esc(res['cidr'])}: {esc(res['descripcion'])}", {"celeris_rol": "nota"},
           color="#FFFFFF", borde="#BBBBBB")
    d.componente("S3", 1495, 660, w=220)
    d.nota(1495, 754, 220, 90, f"Servicio regional, fuera de la VPC. Recibe el respaldo de CTRL01 por Internet "
           f"({esc(x.inv['aws']['s3']['flujo'])}), no por la VPN.", {"celeris_rol": "nota", "celeris_ref": "S3"},
           color="#FFFFFF", borde="#BBBBBB")
    tuneles(d)
    alto_l = d.leyenda(20, 960, w=1440, flujos=False)
    alto_p = d.panel(1750, 10, 530, orden_inventario(x, d.presentes), max_si_falla=72)
    d.alto = max(d.alto, 960 + alto_l + 20, 10 + alto_p + 20)
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
        label = f"{t['id']} {'ACTIVO' if activo else 'RESPALDO'} · IPsec + BGP{extra}"
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
    ("DMZ-HONEY", ["HNY01"]), ("DMZ-SVC", ["PORTAL01"]), ("WIFI-EST", ["WIFI-EST"]),
    ("LAB", ["PCS-LAB", "ENC01", "LABCLI01", "KALI01", "HNY02"]),
    ("EDGE", ["EDGE01", "EDGE02"]), ("SERVERS", ["CTRL01"]), ("SECURITY", ["SIEM01"]),
    ("MGMT", ["JMP01", "SW-CORE01", "ESX01", "IPMI01", "UPS01"]),
    ("AWS", ["EC2-GW", "S3"]),
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
    otra = "FIG-5.5b" if fig == "FIG-5.5a" else "FIG-5.5a"
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
        etiqueta = f"<b>{vlan}{esc(zid)}</b>{cidr} <i>(toda la zona)</i>"
        estilo = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={color};strokeWidth=2;"
                  f"align=left;verticalAlign=top;spacingLeft=6;spacingTop=6;fontSize=10;fontColor={TEXTO};")
        # Una zona con el mismo ID que un componente (WIFI-EST) solo lleva celeris_id donde el componente se dibuja.
        if zid in x.componentes and zid not in ids:
            nid = d.caja(20, y, x_fin - 20, alto, estilo, etiqueta)
        else:
            nid = d.caja(20, y, x_fin - 20, alto, estilo, etiqueta,
                         {"celeris_id": zid, "celeris_tipo": "zona", "cidr": z.get("cidr"), "confianza": z["confianza"],
                          "tooltip": f"{zid}: {z['proposito']}"})
            d.zonas_dibujadas.append(zid)
        d.nodos[zid] = nid
        fila_y[zid] = y + RP / 2 + 2
        for k, o in enumerate(occ):
            fy = y + RP * (k + 1) + 2
            fila_y[o] = fy + RP / 2
            if k % 2 == 0:
                d.caja(24, fy, x_fin - 28, RP, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=none;opacity=55;")
            if o in ids:
                d.componente(o, 36, fy + 2, w=X_COL0 - 50, h=RP - 4, compacto=True, una_linea=True)
            else:
                d.caja(36, fy + 2, X_COL0 - 50, RP - 4, "rounded=1;html=1;fillColor=none;strokeColor=#BBBBBB;dashed=1;dashPattern=2 2;"
                       "align=left;spacingLeft=6;fontSize=9;fontColor=#7F7F7F;", f"{esc(o)} · sin flujos aquí (ver {otra})")
        y += alto + 4
    y_fin = y
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
        return crudo if crudo in fila_y else crudo.split(":")[0]

    for i, fid in enumerate(flujos):
        f = x.flujos[fid]
        xc = X_COL0 + i * WC + WC // 2
        d.caja(X_COL0 + i * WC + 2, 64, WC - 4, Y_FILAS - 70,
               f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={FLECHA};strokeWidth=1;"
               f"verticalAlign=top;align=center;spacing=3;fontSize=9;fontColor={TEXTO};",
               f"<b>{esc(etiqueta_flujo(f)).replace(',', ',&#8203;')}</b><br><i>{esc(f['proposito'])}</i>",
               {"celeris_rol": "etiqueta_flujo", "celeris_ref": fid, "etiqueta": etiqueta_flujo(f)})
        d.linea_libre((xc, Y_FILAS - 6), (xc, y_fin), "html=1;endArrow=none;strokeColor=#BBBBBB;strokeWidth=1;dashed=1;dashPattern=1 3;")
        est = estilo_flujo(f).replace("strokeWidth=1.5", "strokeWidth=2")
        if f["accion"] == "bloquear":
            est += "endSize=10;"
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
    if "S3" in ids:
        s3 = x.inv["aws"]["s3"]
        d.nota(20, y_fin + 6, x_fin - 20, 24, f"S3 ({esc(s3['bucket'])}) recibe {esc(s3['flujo'])} por Internet, no por la VPN: "
               f"el inventario lo modela como {esc(s3['flujo'])} → INTERNET. {esc(s3['cifrado'])}.", {"celeris_rol": "nota", "celeris_ref": "S3"})
        y_fin += 34
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
    d = Diagrama(x, "FIG-5.2", 2290, 1500)
    d.titulo(w=1740)
    fgt_c, fw = x.componentes["FGT-EXT"], x.componentes["FW01"]
    wan_pub = next(i["ip"] for i in fgt_c["ips"] if i["interfaz"] == "wan")
    d.zona("INTERNET", 20, 62, 220, 96, f"<br>ISP · IP pública {wan_pub}")
    d.componente("FGT-EXT", 270, 68, w=250)
    t = x.zonas["TRANSITO"]
    d.zona("TRANSITO", 550, 62, 340, 96, f"<br>GW {t['gateway']} (FGT-EXT) · {t['hosts_utiles']} hosts útiles<br>"
           f"FW01 {next(i['ip'] for i in fw['ips'] if i['interfaz'] == 'wan')}")
    d.componente("FW01", 920, 68, w=250)
    d.flecha(d.nodos["INTERNET"], d.nodos["FGT-EXT"], GRIS + "strokeColor=#4D4D4D;strokeWidth=2;", "WAN")
    d.flecha(d.nodos["FGT-EXT"], d.nodos["TRANSITO"], GRIS + "strokeColor=#999999;strokeWidth=3;")
    d.flecha(d.nodos["TRANSITO"], d.nodos["FW01"], GRIS + "strokeColor=#999999;strokeWidth=3;")
    filas = [f"{esc(i['interfaz'])} · {esc(i['ip'])} · {esc(i['zona'])}" for i in fw["ips"]]
    d.nota(1196, 62, 290, 22 + 13 * len(filas), "<b>FW01: interfaces (gateway .1 de cada VLAN)</b><br>" + "<br>".join(filas),
           {"celeris_rol": "tabla", "celeris_ref": "FW01"})
    d.zona("WIFI-EST", 1510, 62, 250, 176, "<br>Entra por FGT-EXT; FW01 solo recibe F31 y F32")
    d.componente("WIFI-EST", 1520, 152, w=230, h=78, compacto=True)
    trunk = d.caja(20, 246, 1740, 24, TRUNK,
                   f"<b>Trunk 802.1Q</b> FW01 ↔ SW-CORE01 · VLAN permitidas {', '.join(vlans_fw(x))} · "
                   f"nativa {x.zonas['BLACKHOLE']['vlan']} (BLACKHOLE, sin uso)", {"celeris_rol": "trunk", "celeris_ref": "SW-CORE01"})
    d.flecha(d.nodos["FW01"], trunk, "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=3;")
    BW, BH = 158, 56
    disp = [("MGMT", 20, 2, ["JMP01", "SW-CORE01", "ESX01", "IPMI01", "UPS01"]), ("SERVERS", 384, 1, ["CTRL01"]),
            ("DMZ-SVC", 582, 1, ["PORTAL01"]), ("DMZ-HONEY", 780, 1, ["HNY01"]), ("SECURITY", 978, 1, ["SIEM01"]),
            ("EDGE", 1176, 2, ["EDGE01", "EDGE02"])]
    zy = 300
    for zid, zx, cols, occ in disp:
        z = x.zonas[zid]
        occ = [o for o in occ if o in ids]
        zw = PAD + cols * (BW + 8) + 2
        zh = 62 + ((len(occ) + cols - 1) // cols) * (BH + 8) + 4
        zc = d.zona(zid, zx, zy, zw, zh, f"<br>GW {z['gateway']} · {z['hosts_utiles']} hosts")
        for i, o in enumerate(occ):
            d.componente(o, zx + PAD + (i % cols) * (BW + 8), zy + 62 + (i // cols) * (BH + 8), w=BW, h=BH, compacto=True)
        d.flecha(zc, trunk, "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=1.5;fontSize=9;"
                 "labelBackgroundColor=#FFFFFF;exitX=0.5;exitY=0;", f"VLAN {z['vlan']} · .1")
    pac = x.inv["servicios_base"]["pac"]
    d.nota(1530, 300, 200, 150, f"<b>PAC</b> {esc(pac['url'])}<br>servido por {esc(pac['servido_por'])}: "
           + ", ".join(f"{esc(r['componente'])} {esc(r['ip'])}" for r in pac["registros_a"]) + f"<br>{esc(pac['distribucion'])}",
           {"celeris_rol": "pac", "celeris_ref": "EDGE01"}, borde="#4D4D4D", tam=9)
    # VLAN 30: los 10 rangos /26, la reserva y el rango de infraestructura
    rl, lab = x.inv["rangos_lab"], x.zonas["LAB"]
    ly = 580
    zc = d.zona("LAB", 20, ly, 1740, 250, f"<br>GW {lab['gateway']} · {lab['hosts_utiles']} hosts · "
                f"{esc(primera_frase(x.inv['servicios_base']['dhcp']['diseno'], 120))} · el nodo solo acepta los rangos habilitados "
                "(allowed_clients)")
    d.flecha(zc, trunk, "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#4D4D4D;strokeWidth=1.5;fontSize=9;"
             "labelBackgroundColor=#FFFFFF;exitX=0.993;exitY=0;entryX=0.993;entryY=1;", f"VLAN {lab['vlan']} · .1")
    rangos = rl["laboratorios"] + [rl["reserva"]]
    rw = (1720 - 6 * (len(rangos) - 1)) // len(rangos)
    for i, r in enumerate(rangos):
        nombre = r["id"] if r in rl["laboratorios"] else f"Reserva ({r['descripcion']})"
        d.nota(30 + i * (rw + 6), ly + 54, rw, 44, f"<b>{esc(nombre)}</b><br>{esc(r['cidr'])} · {r['hosts_utiles']} hosts",
               {"celeris_rol": "rango_lab", "celeris_ref": r["id"]}, color="#FFFFFF" if r in rl["laboratorios"] else "#EEEEEE",
               borde=lab["color"], tam=9)
    inf = rl["infraestructura"]
    iw = PAD + len(inf["componentes"]) * (BW + 8) + 2
    d.nota(30, ly + 108, iw, 132, f"<b>{esc(inf['id'])}</b> · {esc(inf['cidr'])} · infraestructura de laboratorio",
           {"celeris_rol": "rango_lab", "celeris_ref": inf["id"]}, color="#FFFFFF", borde=lab["color"], tam=10)
    for i, o in enumerate(c for c in inf["componentes"] if c in ids):
        d.componente(o, 30 + PAD + i * (BW + 8), ly + 140, w=BW, h=BH + 20, compacto=True)
    d.componente("PCS-LAB", 30 + iw + 20, ly + 140, w=330, h=BH + 20, compacto=True)
    d.componente("SW-ACC", 30 + iw + 370, ly + 140, w=260, h=BH + 20, compacto=True)
    # AWS: VPC, subredes y tablas de rutas
    ya = 860
    rt = tablas_rutas(x)
    res = next(r for r in x.inv["reservas"] if r["dentro_de"] == "AWS-CELERIS")
    rt.append(f"Reservado: {esc(res['cidr'])} ({esc(res['descripcion'])})")
    h_rt = alto_texto(rt, 536)
    d.zona("AWS", 20, ya, 580, 254 + h_rt, "")
    d.grupo_aws("AWS-VPC", 32, ya + 34, 556, 210 + h_rt)
    d.grupo_aws("AWS-PUB-A", 42, ya + 70, 260, 120)
    d.componente("EC2-GW", 52, ya + 112, w=240, h=BH + 10, compacto=True)
    d.grupo_aws("AWS-APP-A", 314, ya + 70, 264, 120)
    d.nota(324, ya + 112, 244, 66, esc(x.componentes["AWS-APP-A"]["aporta_corto"]), {"celeris_rol": "nota", "celeris_ref": "AWS-APP-A"},
           color="#FFFFFF", borde="#BBBBBB")
    d.nota(42, ya + 200, 536, h_rt, "<b>Tablas de rutas de la VPC</b><br>" + "<br>".join(rt), {"celeris_rol": "tablas_rutas", "celeris_ref": "AWS-VPC"}, tam=10)
    # Resumen zona × zona (matriz_esperada)
    orden_m = x.orden_matriz
    celdas = x.matriz_esperada()
    cw, ch, mx, my = 52, 24, 620, ya + 26
    d.nota(mx, ya, len(orden_m) * cw + 92, 24, "<b>Resumen zona × zona</b> (fila = origen, columna = destino; ✔ permitido, ✖ denegado; detalle en el Anexo A)",
           {"celeris_rol": "matriz"}, color="#FFFFFF", borde="#FFFFFF", tam=10)
    abrev = {"SERVERS": "SRV", "WIFI-EST": "WIFI", "DMZ-SVC": "D-SVC", "DMZ-HONEY": "D-HNY", "SECURITY": "SEC", "INTERNET": "INET"}
    celda_txt = f"rounded=0;html=1;whiteSpace=wrap;fontSize=9;fontColor={TEXTO};strokeColor=#BBBBBB;align=center;verticalAlign=middle;"
    d.caja(mx, my, 92, ch, celda_txt + "fillColor=#EEEEEE;", "<b>origen \\ destino</b>")
    for j, zd in enumerate(orden_m):
        d.caja(mx + 92 + j * cw, my, cw, ch, celda_txt + "fillColor=#EEEEEE;", f"<b>{abrev.get(zd, zd)}</b>")
    hay_pendiente = False
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
                hay_pendiente = True
            d.caja(mx + 92 + j * cw, my + (i + 1) * ch, cw, ch, celda_txt + f"fillColor={fill};", txt,
                   {"celeris_rol": "celda", "par": f"{zo}>{zd}", "estado": c["estado"], "flujos": fl})
    nota_m = "«F…»: varios flujos (ver Anexo A) · —: intra-zona o no aplica · F2 (DNS y NTP hacia FW01) no se repite"
    if hay_pendiente:
        nota_m = "* observación abierta en CAMBIOS-INVENTARIO.md · " + nota_m
    yme = my + (len(orden_m) + 1) * ch + 4
    d.nota(mx, yme, len(orden_m) * cw + 92, 34, nota_m, {"celeris_rol": "nota"}, color="#FFFFFF", borde="#FFFFFF", tam=9)
    # Ruteo y servicios base
    vpn = x.inv["vpn"]
    on, aws = vpn["extremo_onpremise"], vpn["extremo_aws"]
    ruteo = [
        f"FW01: 0.0.0.0/0 → FGT-EXT {t['gateway']} (red de tránsito {t['cidr']})",
        f"FW01: {', '.join(aws['redes_anunciadas'])} → AWS por BGP (VTI1 activo, VTI2 respaldo) · ASN {on['asn']} ↔ {aws['asn']}",
        f"FW01 anuncia {', '.join(on['redes_anunciadas'])} (futuro {on['redes_anunciadas_futuro']})",
        "Entre VLAN: FW01 con una subinterfaz .1 por VLAN; deny-all con registro",
        f"FGT-EXT: {frase_con(fgt_c['aporta'], 'ruta estática')}",
    ]
    xr, wr = 1250, 510
    hr = alto_texto(ruteo, wr)
    d.nota(xr, ya, wr, hr, "<b>Ruteo</b><br>" + "<br>".join(esc(r) for r in ruteo),
           {"celeris_rol": "ruteo", "celeris_ref": "FW01"}, borde="#1A1A1A", tam=10)
    sb = x.inv["servicios_base"]
    dns, ntp = sb["dns"], sb["ntp"]
    serv = [
        f"DHCP: {primera_frase(sb['dhcp']['diseno'], 110)}; {', '.join(sb['dhcp']['controles'])}",
        f"DNS: {dns['servidor']['componente']} ({dns['servidor']['software']}, DNSSEC) en la {dns['servidor']['ip']}; "
        f"hacia arriba {dns['hacia_arriba']}",
        f"NTP: {ntp['servidor']['componente']} ({ntp['servidor']['software']}); clientes {ntp['clientes']}; hacia arriba {ntp['hacia_arriba']}",
        f"PAC: {pac['url']} → " + ", ".join(f"{r['componente']} {r['ip']}" for r in pac["registros_a"]),
        f"IPv6: {sb['ipv6']['postura']} ({', '.join(sb['ipv6']['controles'])})",
        f"DNS cifrado: {sb['dns_cifrado']['dot']}; {sb['dns_cifrado']['doh']}",
        f"Wi-Fi: {primera_frase(sb['wifi']['diseno'], 150)}",
    ]
    hs = alto_texto(serv, wr)
    d.nota(xr, ya + hr + 10, wr, hs, "<b>Servicios base</b> (D-28)<br>" + "<br>".join(esc(s) for s in serv),
           {"celeris_rol": "servicios_base"}, borde="#1A1A1A", tam=10)
    yl = max(ya + 264 + h_rt, yme + 44, ya + hr + 10 + hs + 10)
    alto_l = d.leyenda(20, yl, w=1740, flujos=False)
    alto_p = d.panel(1780, 10, 500, orden_inventario(x, d.presentes), max_si_falla=68)
    d.alto = max(yl + alto_l + 20, 10 + alto_p + 20)
    return d


# --------------------------------------------------------------------------------------------------
# FIG-5.3 — seguridad y zonas
# --------------------------------------------------------------------------------------------------
# Filas de arriba abajo: lo expuesto, el perímetro y las zonas internas de menor a mayor confianza.
BANDAS_53 = [
    [("INTERNET", []), ("AWS", ["EC2-GW"])],
    [("PERIMETRO", ["FGT-EXT", "FW01", "VTI1", "VTI2"])],
    [("DMZ-HONEY", ["HNY01"]), ("WIFI-EST", ["WIFI-EST"]), ("DMZ-SVC", ["PORTAL01"])],
    [("LAB", ["PCS-LAB", "SW-ACC", "ENC01", "LABCLI01", "KALI01", "HNY02"])],
    [("EDGE", ["EDGE01", "EDGE02"]), ("SERVERS", ["CTRL01"]), ("SECURITY", ["SIEM01"])],
    [("MGMT", ["JMP01", "SW-CORE01", "BRK01", "ESX01", "IPMI01", "UPS01"])],
]
H53 = H + 98


def fig_5_3(x: Infra) -> Diagrama:
    ids = set(componentes_de(x, "FIG-5.3"))
    d = Diagrama(x, "FIG-5.3", 2290, 1700)
    d.titulo(w=1740)
    am_por_comp: dict[str, list[str]] = {}
    for am in x.amenazas.values():
        punto = next((c for c in am["componentes"] if c in ids), None)
        if punto:
            am_por_comp.setdefault(punto, []).append(am["id"])
    d.caja(20, 62, 1400, 22, f"text;html=1;align=left;fontSize=11;fontColor={TEXTO};",
           "<b>Recorrido del tráfico de arriba abajo</b>: lo expuesto (Internet, AWS) → perímetro (FGT-EXT, FW01) → zonas internas "
           "de menor a mayor confianza (MGMT, Máxima, al final). Etiquetas negras AM-xx = amenaza STRIDE mitigada en ese componente.")
    y = 90
    pos_portal = (0, 0)
    for segmentos in BANDAS_53:
        xs = 20
        for zz, oo in segmentos:
            z = x.zonas[zz]
            ancho = max(PAD + len(oo) * (W + GAP), 380)
            conf = f"confianza <b>{esc(z['confianza'])}</b>" + (f" ({esc(z['confianza_nota'])})" if z.get("confianza_nota") else "")
            regla = f"<br><i>{esc(z['regla_diseno'])}</i>"
            if zz == "PERIMETRO":
                d.caja(xs, y, ancho, H53, "rounded=0;whiteSpace=wrap;html=1;fillColor=#F2F2F2;strokeColor=#1A1A1A;strokeWidth=2;"
                       f"verticalAlign=top;align=left;spacingLeft=6;fontSize=10;fontColor={TEXTO};",
                       f"<b>PERIMETRO</b> · {conf} · {esc(z['regla_diseno'])}<br><i>{esc(x.zonas['TRANSITO']['proposito'])}</i>",
                       {"celeris_id": "PERIMETRO", "celeris_tipo": "zona", "confianza": z["confianza"]})
                d.nodos["PERIMETRO"] = d.celdas[-1].get("id")
            elif z["tipo"] in ("externa", "nube"):
                d.zona(zz, xs, y, ancho, H53, f" · {conf}" if z["tipo"] == "externa" and not z.get("color") else regla)
            else:
                vlan = f"VLAN {z['vlan']} · " if z.get("vlan") is not None else ""
                d.caja(xs, y, ancho, H53, f"rounded=0;whiteSpace=wrap;html=1;fillColor={aclarar(z['color'], 0.86)};strokeColor={z['color']};strokeWidth=2;"
                       f"verticalAlign=top;align=left;spacingLeft=6;spacingTop=1;fontSize=10;fontColor={TEXTO};",
                       f"<b>{vlan}{esc(zz)}</b> · {esc(z['cidr'])} · {conf}{regla}",
                       {"celeris_id": zz, "celeris_tipo": "zona", "cidr": z["cidr"], "confianza": z["confianza"],
                        "tooltip": f"{zz}: {z['proposito']}. Regla: {z['regla_diseno']}"})
                d.nodos[zz] = d.celdas[-1].get("id")
                d.zonas_dibujadas.append(zz)
            for i, o in enumerate(oo):
                cx, cy = xs + PAD + i * (W + GAP), y + 74
                d.componente(o, cx, cy, compacto=True, h=H - 20)
                if o == "PORTAL01":
                    pos_portal = (cx, cy)
                for j, am in enumerate(am_por_comp.get(o, [])):
                    a = x.amenazas[am]
                    d.caja(cx + (j % 4) * 45, cy + H - 16 + (j // 4) * 19, 43, 16,
                           "rounded=1;html=1;fillColor=#000000;strokeColor=#000000;fontColor=#FFFFFF;fontSize=9;fontStyle=1;",
                           esc(am), {"celeris_id": am, "celeris_tipo": "amenaza", "stride": "".join(a["stride"]),
                                     "amenaza": a["amenaza"], "control": a["control"],
                                     "tooltip": f"{am} ({''.join(a['stride'])}): {a['amenaza']} → {a['control']}"})
            xs += ancho + 12
        if segmentos[0][0] == "PERIMETRO":
            ctl = (f"<b>Controles de FGT-EXT</b>: {esc(x.componentes['FGT-EXT']['controles'])}<br>"
                   f"<b>Controles de FW01</b>: {esc(x.componentes['FW01']['controles'])}")
            d.nota(xs, y, 1420 - xs, H53, ctl, {"celeris_rol": "controles", "celeris_ref": "FW01"}, color="#FFFFFF", borde="#1A1A1A", tam=9)
        y += H53 + 8
    y_bandas = y
    # El portal no sale a la WAN (D-29): el certificado llega desde FW01 por F33.
    if "PORTAL01" in d.nodos:
        stub = d.nota(pos_portal[0] + W + 14, pos_portal[1], 166, H + 6,
                      "<b>WAN / Internet</b><br>✖ BLOQUEADO: PORTAL01 no inicia conexiones hacia la WAN (D-29); solo envía a Wazuh (F13). El certificado llega desde FW01 por F33 (SFTP)",
                      {"celeris_rol": "sin_salida", "celeris_ref": "PORTAL01"}, color="#FFFFFF", borde="#1A1A1A", tam=9)
        d.flecha(d.nodos["PORTAL01"], stub, "html=1;strokeColor=#1A1A1A;dashed=1;dashPattern=1 4;strokeWidth=2;endArrow=cross;endFill=0;"
                 "endSize=10;exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
        d.flecha_flujo("F33", d.nodos["FW01"], d.nodos["PORTAL01"], "F33",
                       "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    # Detecciones DET-xx (columna derecha), recolectadas en SIEM01
    x_det, w_det = 1440, 320
    d.nota(x_det, 62, w_det, 22, "<b>Detecciones (D1.14) → recolectadas en SIEM01</b>", {"celeris_rol": "titulo_det"}, color="#FFFFFF", tam=10)
    yd = 88
    for det in x.detecciones.values():
        pruebas = ", ".join(det["validacion"]["pruebas"]) or "—"
        texto = (f"<b>{esc(det['id'])}</b> · {esc(det['tecnologia'])} · {esc(det['ubicacion_detalle'])}<br>"
                 f"{esc(det['que_detecta'])} · ATT&amp;CK {esc(', '.join(det['attack']) or '—')} · valida {esc(pruebas)}")
        hd = max(62, alto_texto([texto], w_det, 9, 10))
        nid = d.nota(x_det, yd, w_det, hd, texto, {"celeris_id": det["id"], "celeris_tipo": "deteccion", "ubicacion": det["ubicacion"]},
                     color="#E8F4FB", borde="#56B4E9", tam=9)
        d.nodos[det["id"]] = nid
        yd += hd + 6
    # Defensa en profundidad (D1.9; trazabilidad.yaml → defensa_profundidad, CI-63)
    capas = x.traz["defensa_profundidad"]
    yb = max(y_bandas, yd) + 6
    d.caja(20, yb, 1740, 20, f"text;html=1;align=left;fontSize=11;fontColor={TEXTO};",
           "<b>Defensa en profundidad</b> (D1.9, de afuera hacia adentro)", {"celeris_rol": "defensa"})
    por_fila = (len(capas) + 1) // 2
    cw = 1740 // por_fila
    hc = max(alto_texto([f"<b>{c['capa']}</b> {c['controles']} ({c['detalle']})"], cw - 6, 9, 22) for c in capas)
    for i, c in enumerate(capas):
        d.nota(20 + (i % por_fila) * cw, yb + 22 + (i // por_fila) * (hc + 6), cw - 6, hc,
               f"<b>{i + 1}. {esc(c['capa'])}</b><br>{esc(c['controles'])} <i>({esc(c['detalle'])})</i>", {"celeris_rol": "capa"},
               color="#F7F7F7", borde="#4D4D4D", tam=9)
    y_fin = yb + 22 + 2 * (hc + 6)
    alto_p = d.panel(1780, 10, 500, orden_inventario(x, d.presentes), max_si_falla=62)
    filas_am = [f"<b>{esc(a['id'])}</b> ({esc(''.join(a['stride']))}) {esc(a['amenaza'])} → {esc(a['control'])}" for a in x.amenazas.values()]
    alto_am = alto_texto(filas_am, 500, 9, 30)
    d.nota(1780, 20 + alto_p, 500, alto_am, "<b>Amenazas STRIDE (AM-xx), marcadas en su punto de mitigación</b><br>" + "<br>".join(filas_am),
           {"celeris_rol": "amenazas"}, tam=9)
    alto_l = d.leyenda(1780, 30 + alto_p + alto_am, w=500)
    d.alto = max(y_fin + 20, 50 + alto_p + alto_am + alto_l)
    return d


# --------------------------------------------------------------------------------------------------
# FIG-5.4 — VPN híbrida
# --------------------------------------------------------------------------------------------------
def fig_5_4(x: Infra) -> Diagrama:
    vpn = x.inv["vpn"]
    d = Diagrama(x, "FIG-5.4", 2200, 1300)
    d.titulo(w=1660)
    on, aws = vpn["extremo_onpremise"], vpn["extremo_aws"]
    d.caja(20, 70, 580, 520, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#1A1A1A;strokeWidth=1;verticalAlign=top;"
           f"align=left;spacingLeft=8;spacingTop=4;fontSize=11;fontColor={TEXTO};",
           f"<b>On-premise · Campus Juliaca</b> · anuncia por BGP {esc(', '.join(on['redes_anunciadas']))} "
           f"(futuro {esc(on['redes_anunciadas_futuro'])}) · ASN {on['asn']}", {"celeris_rol": "campus"})
    p = x.zonas["PERIMETRO"]
    d.caja(30, 100, 560, 240, "rounded=0;whiteSpace=wrap;html=1;fillColor=#F2F2F2;strokeColor=#1A1A1A;strokeWidth=2;verticalAlign=top;"
           f"align=left;spacingLeft=6;fontSize=10;fontColor={TEXTO};", f"<b>PERIMETRO</b> · confianza {esc(p['confianza'])}",
           {"celeris_id": "PERIMETRO", "celeris_tipo": "zona", "confianza": p["confianza"]})
    d.nodos["PERIMETRO"] = d.celdas[-1].get("id")
    d.componente("FW01", 40, 140, w=250)
    d.componente("VTI1", 340, 130, w=230)
    d.componente("VTI2", 340, 240, w=230)
    for v in ("VTI1", "VTI2"):
        d.flecha(d.nodos["FW01"], d.nodos[v], "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#7F7F7F;exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    d.nota(40, 276, 250, 56, f"<b>Identidad IKE</b>: {esc(on['identidad_ike']['tipo'])} {esc(on['identidad_ike']['valor'])}<br>"
           f"IP interna de FW01: {esc(on['ip_interna'])} (tránsito)", {"celeris_rol": "extremo", "celeris_ref": "FW01"}, tam=10)
    d.nota(30, 350, 560, 110, f"<b>Extremo on-premise</b>: {esc(on['dispositivo'])}<br>IP pública {esc(on['ip_publica'])} en "
           f"{esc(on['ip_publica_en'])}: {esc(on['ip_publica_nota'])}<br>NAT-T: {esc(on['nat_t_nota'])}",
           {"celeris_rol": "extremo", "celeris_ref": "FW01"}, tam=10)
    ctrl, siem = x.componentes["CTRL01"], x.componentes["SIEM01"]
    srv = d.zona("SERVERS", 30, 476, 270, 100, f"<br>CTRL01 {ctrl['ips'][0]['ip']}: destino de F30")
    sec = d.zona("SECURITY", 320, 476, 270, 100, f"<br>SIEM01 {siem['ips'][0]['ip']}: destino de F13")
    fgt = d.componente("FGT-EXT", 640, 330, w=230)
    d.nota(640, 424, 230, 56, f"<b>NAT 1:1</b>: {esc(primera_frase(x.componentes['FGT-EXT']['controles'], 90))}",
           {"celeris_rol": "nat", "celeris_ref": "FGT-EXT"}, tam=10)
    d.flecha(d.nodos["PERIMETRO"], fgt, GRIS + "strokeColor=#999999;strokeWidth=3;exitX=1;exitY=0.9;", f"tránsito {x.zonas['TRANSITO']['cidr']}")
    inet = d.zona("INTERNET", 900, 330, 190, 110, "<br>transporte de los túneles")
    d.flecha(fgt, inet, GRIS + "strokeColor=#4D4D4D;strokeWidth=2;", "WAN")
    d.zona("AWS", 1120, 70, 560, 760, f" · {x.zonas['AWS']['cidr']}")
    d.componente("VGW", 1140, 110, w=220)
    d.nota(1380, 110, 280, 120, f"<b>Extremo AWS</b><br>{esc(aws['dispositivo'])}<br>{esc(aws['ip_publica'])}<br>Anuncia "
           f"{esc(', '.join(aws['redes_anunciadas']))} · ASN {aws['asn']} ({esc(aws['asn_nota'])})", {"celeris_rol": "extremo", "celeris_ref": "VGW"}, tam=10)
    d.grupo_aws("AWS-VPC", 1140, 250, 520, 560)
    d.grupo_aws("AWS-PUB-A", 1150, 290, 500, 230)
    gw = d.componente("EC2-GW", 1165, 330, w=200)
    sg = next(s for s in x.inv["aws"]["security_groups"] if s["componente"] == "EC2-GW")

    def regla(r, lado):
        pts = r.get("puertos") or [r.get("puerto")]
        extremo = (r.get("origen") or r.get("destino")).split(":", 1)[-1]
        cola = f" ({r['flujo']})" if r.get("flujo") else (f" ({r['nota']})" if r.get("nota") else "")
        return f"{lado} {r['proto'].upper()}/{','.join(str(p) for p in pts)} {'desde' if lado == 'entrada' else 'hacia'} {extremo}{cola}"
    sg_txt = [regla(r, "entrada") for r in sg["ingress"]] + [regla(r, "salida") for r in sg["egress"]]
    d.nota(1375, 330, 265, 180, f"<b>Security Group {esc(sg['id'])}</b><br>" + "<br>".join(esc(s) for s in sg_txt),
           {"celeris_rol": "sg", "celeris_ref": "EC2-GW"}, tam=10)
    d.grupo_aws("AWS-APP-A", 1375, 535, 275, 90)
    d.nota(1385, 572, 255, 44, esc(x.componentes["AWS-APP-A"]["aporta_corto"]), {"celeris_rol": "nota", "celeris_ref": "AWS-APP-A"},
           color="#FFFFFF", borde="#BBBBBB")
    rt = tablas_rutas(x)
    d.nota(1375, 640, 275, alto_texto(rt, 275) + 40, "<b>Rutas previstas (BGP → tablas de la VPC)</b><br>" + "<br>".join(rt),
           {"celeris_rol": "rutas", "celeris_ref": "AWS-VPC"}, tam=10)
    tuneles(d)
    # Qué viaja por la VPN: F29 llega a EC2-GW por Internet; F30 y F13 van de EC2-GW al campus dentro de IPsec.
    d.flecha_flujo("F29", inet, gw, None, "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    d.flecha_flujo("F30", gw, srv, None, "exitX=0.3;exitY=1;entryX=0.5;entryY=1;", puntos=[(1225, 860), (165, 860)])
    d.flecha_flujo("F13", gw, sec, None, "exitX=0.7;exitY=1;entryX=0.5;entryY=1;", puntos=[(1305, 890), (455, 890)])
    f1, f2, bgp, dpd = vpn["fase1"], vpn["fase2"], vpn["bgp"], vpn["dpd"]
    params = [
        f"Tipo: {vpn['tipo']}",
        f"Fase 1 (IKEv2): {f1['cifrado']} · PRF {f1['prf']} · DH {f1['dh']} · vida {f1['vida_s']} s",
        f"Fase 2 (ESP): {f2['cifrado']} · PFS {f2['pfs']} · vida {f2['vida_s']} s",
        f"DPD: cada {dpd['intervalo_s']} s, acción {dpd['accion']}",
        f"BGP: keepalive {bgp['keepalive_s']} s · hold {bgp['hold_s']} s ({bgp['hold_nota']}) · {bgp['respaldo']}",
        "Direcciones internas: " + "; ".join(f"{t['id']} {t['red_interna']} ({t['rol']})" for t in vpn["tuneles"]),
        f"MTU {vpn['mtu']} · MSS clamping {vpn['mss_clamping']} ({vpn['mss_nota']}) · {vpn['capacidad_gbps_por_tunel']} Gbps por túnel",
        f"IPv6: {vpn['ipv6']} · Convergencia meta ≤ {vpn['convergencia_meta_s']} s (prueba {vpn['convergencia_prueba']})",
        f"Secretos: {vpn['secretos']}",
        "Por la VPN viaja: " + "; ".join(etiqueta_flujo(x.flujos[f]) for f in vpn["flujos_sobre_vpn"]),
        f"Pruebas: {', '.join(vpn['pruebas'])} · Escalamiento: {vpn['escalamiento']}",
    ]
    hp = alto_texto(params, 1100)
    d.nota(20, 920, 1100, hp, "<b>Parámetros de la VPN (D1.10, sin secretos)</b><br>" + "<br>".join(esc(p) for p in params),
           {"celeris_rol": "parametros_vpn", "celeris_ref": vpn["id"]}, color="#F3EDFF", borde="#8C4FFF", tam=10)
    alto_l = d.leyenda(1140, 920, w=540)
    alto_p = d.panel(1700, 10, 490, orden_inventario(x, d.presentes), max_si_falla=62)
    d.alto = max(920 + max(hp, alto_l) + 20, alto_p + 30)
    return d


# --------------------------------------------------------------------------------------------------
# FIG-1.1 — topología ejecutiva (≤ 12 bloques)
# --------------------------------------------------------------------------------------------------
def fig_1_1(x: Infra) -> Diagrama:
    """12 bloques: 40 PCs por laboratorio → nodos de caché → una sola descarga por el FortiGate; consola en el campus;
    en AWS solo EC2-GW y S3; Wi-Fi de estudiantes como cliente sin descifrado."""
    d = Diagrama(x, "FIG-1.1", 1680, 900)
    d.titulo(w=1640)
    plantilla = (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={{fill}};strokeColor={{stroke}};strokeWidth={{sw}};"
                 f"align=center;verticalAlign={{va}};fontSize=13;fontColor={TEXTO};spacing=6;spacingLeft={{sl}};")

    def bloque(cid, x0, y0, w, h, titulo, frase, incluye=None, arriba=False):
        if cid in x.componentes:
            c = x.componentes[cid]
            sw, tag = CRITICIDAD[c["criticidad"]]
            color = color_de(x, c)
            attrs = d.datos_componente(c)
            label = f"<b>{esc(titulo)}</b> · <b>{tag}</b><br>{esc(ip_texto(x, c))}<br><i>{esc(frase)}</i>"
            d.presentes.append(cid)
            discont = "dashed=1;dashPattern=6 3;" if c["estado"] in EXISTENTES else ""
        else:
            z = x.zonas[cid]
            color = z.get("color") or "#4D4D4D"
            sw = 2
            attrs = {"celeris_id": cid, "celeris_tipo": "zona"}
            cidr = f" · {esc(z['cidr'])}" if z.get("cidr") else ""
            label = f"<b>{esc(titulo)}</b><br>zona {esc(cid)}{cidr}<br><i>{esc(frase)}</i>"
            if z.get("color"):
                d.zonas_dibujadas.append(cid)
            discont = ""
        if incluye:
            attrs["celeris_incluye"] = ",".join(incluye)
        fill = aclarar(color, 0.86) if color not in ("#4D4D4D", AWS_TINTA) else "#F2F2F2"
        icono = cid in x.componentes and x.componentes[cid]["tipo"] in ICONO
        nid = d.caja(x0, y0, w, h, plantilla.format(fill=fill, stroke=color, sw=sw, sl=34 if icono else 6,
                                                    va="top" if arriba else "middle") + discont, label, attrs)
        d.nodos[cid] = nid
        if icono:
            d.caja(x0 + 6, y0 + 6, 26, 26, ICONO[x.componentes[cid]["tipo"]] + "html=1;aspect=fixed;outlineConnect=0;dashed=0;")
            d.tipos.add(x.componentes[cid]["tipo"])
        return nid

    z, c = x.zonas, x.componentes
    ctrl_ip = c["CTRL01"]["ips"][0]["ip"]
    e1, e2 = (c[e]["ips"][0]["ip"] for e in ("EDGE01", "EDGE02"))
    bloque("WIFI-EST", 20, 70, 280, 110, "WIFI-EST · Wi-Fi de estudiantes", c["WIFI-EST"]["aporta_corto"])
    bloque("INTERNET", 700, 70, 280, 100, "Internet", z["INTERNET"]["proposito"].split(":")[0])
    bloque("PCS-LAB", 20, 240, 280, 120, "PCS-LAB · PCs de laboratorio", c["PCS-LAB"]["aporta_corto"])
    bloque("EDGE", 400, 240, 250, 120, f"Caché EDGE01 {e1} y EDGE02 {e2}", c["EDGE01"]["aporta_corto"], ["EDGE01", "EDGE02"])
    bloque("FGT-EXT", 700, 240, 280, 120, "FGT-EXT · FortiGate de la DTI", c["FGT-EXT"]["aporta_corto"])
    bloque("S3", 1340, 240, 300, 110, "S3 · respaldos", c["S3"]["aporta_corto"])
    bloque("ESX01", 20, 430, 280, 110, "ESX01 · Servidor ESXi", c["ESX01"]["aporta_corto"])
    bloque("SERVERS", 400, 430, 250, 110, f"Consola en el campus: CTRL01 {ctrl_ip}", c["CTRL01"]["aporta_corto"], ["CTRL01"])
    bloque("FW01", 700, 430, 280, 110, "FW01 · Firewall OPNsense", c["FW01"]["aporta_corto"])
    bloque("VGW", 1110, 430, 200, 110, "VGW · extremo AWS", c["VGW"]["aporta_corto"])
    bloque("AWS-VPC", 1330, 390, 330, 180, "AWS · VPC " + c["AWS-VPC"]["cidr"], c["AWS-VPC"]["aporta_corto"], arriba=True)
    bloque("EC2-GW", 1340, 470, 310, 90, "EC2-GW · panel remoto", c["EC2-GW"]["aporta_corto"])
    d.nota_d25(1010, 70, 300, 96)
    n = d.nodos
    e = "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=11;labelBackgroundColor=#FFFFFF;strokeColor=#1A1A1A;"

    def conex(fid, a, b, label, extra="", puntos=None):
        d.flecha_flujo(fid, n[a], n[b], label, "fontSize=11;" + extra, puntos=puntos)

    conex("F1", "PCS-LAB", "EDGE", "F1 · TCP/3128")
    conex("F31", "WIFI-EST", "EDGE", "F31 · sin descifrado", "exitX=1;exitY=0.5;entryX=0.5;entryY=0;")
    conex("F8", "EDGE", "FGT-EXT", "F8 · una sola descarga (solo MISS)", "exitX=0.8;exitY=0;entryX=0;entryY=0.3;",
          puntos=[(600, 210), (680, 210), (680, 276)])
    conex("F10", "EDGE", "SERVERS", "F10 · config. firmada (mTLS)")
    conex("F18", "SERVERS", "S3", "F18 · respaldo cifrado, por Internet", "exitX=0.5;exitY=1;entryX=1;entryY=0.5;",
          puntos=[(525, 610), (1665, 610), (1665, 295)])
    conex("F29", "INTERNET", "EC2-GW", "F29 · encargado fuera del campus", "exitX=1;exitY=0.9;entryX=0;entryY=0.5;",
          puntos=[(995, 160), (995, 205), (1320, 205), (1320, 515)])
    d.flecha(n["INTERNET"], n["FGT-EXT"], e + "endArrow=none;strokeColor=#4D4D4D;strokeWidth=2;", "WAN · FortiGuard")
    d.flecha(n["FGT-EXT"], n["FW01"], e + "endArrow=none;strokeColor=#999999;strokeWidth=3;", f"tránsito {z['TRANSITO']['cidr']}")
    d.flecha(n["FW01"], n["SERVERS"], e + "endArrow=none;strokeColor=#7F7F7F;strokeWidth=1.5;")
    d.flecha(n["ESX01"], n["SERVERS"], e + "endArrow=none;strokeColor=#7F7F7F;strokeWidth=1.5;dashed=1;dashPattern=2 2;")
    vpn = x.inv["vpn"]
    d.flecha(n["FW01"], n["VGW"], VIOLETA + "fontSize=10;", "VPN IPsec<br>2 túneles<br>lleva " + " y ".join(vpn["flujos_sobre_vpn"]),
             {"celeris_id": vpn["id"], "celeris_tipo": "tunel", "flujos": ", ".join(vpn["flujos_sobre_vpn"])})
    d.flecha(n["VGW"], n["AWS-VPC"], VIOLETA + "strokeWidth=2;")
    d.nota(20, 560, 960, 44, "La VPN sale por FGT-EXT (NAT-T, UDP 4500). FW01 → consola: ruteo entre zonas. ESX01 hospeda las VM (línea punteada). "
           "Vista simplificada: F8 también cruza FW01 (EDGE → FW01 → FGT-EXT); la regla «F8 EDGE > INTERNET miss tcp/80,443» está en FW01.",
           {"celeris_rol": "nota"}, color="#FFFFFF", borde="#FFFFFF", tam=10)
    alto_p = d.panel(20, 640, 940, list(d.presentes), max_si_falla=90)
    alto_l = d.leyenda(980, 640, w=680)
    d.alto = max(640 + alto_l + 20, 640 + alto_p + 20)
    return d


GENERADORES = {
    "FIG-1.1": fig_1_1, "FIG-5.1": fig_5_1, "FIG-5.2": fig_5_2, "FIG-5.3": fig_5_3, "FIG-5.4": fig_5_4,
    "FIG-5.5a": lambda x: fig_5_5(x, "FIG-5.5a"), "FIG-5.5b": lambda x: fig_5_5(x, "FIG-5.5b"),
}


# draw.io Desktop deja de dibujar las celdas que caen fuera de ~2^25 píxeles al exportar el PNG (se vio en FIG-5.3:
# a escala 3 y 6847 × 4963 px quedó en blanco el último cuarto). Cada página debe caber a la escala de exportación.
ESCALA_PNG = 3
PIXELES_MAX = 2 ** 25


def generar(x: Infra, salida: Path = SALIDA, figuras=None) -> list[Path]:
    salida.mkdir(parents=True, exist_ok=True)
    hechos = []
    for fig in figuras or FIGURAS:
        d = GENERADORES[fig](x)
        px = (d.ancho + 20) * (d.alto + 20) * ESCALA_PNG ** 2
        if px > PIXELES_MAX:
            raise SystemExit(f"{fig}: {d.ancho} × {d.alto} a escala {ESCALA_PNG} son {px / 1e6:.1f} Mpx (> {PIXELES_MAX / 1e6:.1f}); "
                             "draw.io no dibujaría el final del PNG. Compacte la disposición.")
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
