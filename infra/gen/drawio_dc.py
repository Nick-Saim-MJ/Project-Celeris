"""Generador de los diagramas draw.io del Entregable CE0331 (centro de datos híbrido) desde infra/centro_datos.yaml + infra/inventory.yaml.

Produce un .drawio editable por figura en entregables/CE0331/diagramas/:
    DC-0  Topología ejecutiva (Figura 1.1)
    DC-1  Topología física: rack de 12U, ESX01 con sus 4 NIC y datastores, SW-CORE01, UPS01, enlace al FortiGate, BRK01 e IPMI01
    DC-2  Hipervisor: vSwitch0 y vSwitch1, port groups con su VLAN, cada VM con vCPU y RAM, datastores
    DC-3  AWS: región, VPC y CIDR, pub-a y app-a, IGW, VGW, tablas de rutas, endpoint de S3, S3 con Object Lock, SG y NACL
La integración híbrida NO se redibuja: el informe reutiliza FIG-5.4 de CE0311 tal cual.

Mismo método que CE0311 (infra/gen/drawio.py, de donde se reutiliza la clase Diagrama): cada caja lleva `celeris_id`, tres líneas
(«ID · nombre · CRITICIDAD», recursos o IP, qué aporta), criticidad por grosor de borde + texto, leyenda, bloque de título y panel
«Qué aporta / si falla». Ningún dato se escribe aquí: IP, CIDR, VLAN, vCPU, RAM, recursos y textos salen de los YAML; este módulo
fija solo la disposición (coordenadas).

    python infra/gen/drawio_dc.py [--salida entregables/CE0331/diagramas]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from celeris_infra import RAIZ, Infra  # noqa: E402
from centro_datos import CentroDatos, coma  # noqa: E402
from drawio import (AWS_TINTA, CRITICIDAD, FLECHA, ICONO, NOMBRE_ICONO, TEXTO, Diagrama, aclarar, color_de,  # noqa: E402
                    esc, etiqueta_flujo, lineas_estimadas, nombre_corto, primera_frase, tam_fuente)

SALIDA = RAIZ / "entregables" / "CE0331" / "diagramas"
FIGURAS_DC = ["DC-0", "DC-1", "DC-2", "DC-3"]
ESCALA_PNG = 3

CABLE = "html=1;endArrow=none;strokeColor=#7F7F7F;fontSize=10;labelBackgroundColor=#FFFFFF;fontColor=#1A1A1A;"
ENLACE_10G = CABLE + "strokeWidth=4;"
ENLACE_1G = CABLE + "strokeWidth=2.5;"
ENLACE_GEST = CABLE + "strokeWidth=1.5;"
ENERGIA = "html=1;endArrow=none;strokeColor=#1A1A1A;strokeWidth=2;dashed=1;dashPattern=10 3 2 3;fontSize=10;labelBackgroundColor=#FFFFFF;fontColor=#1A1A1A;"
VPN_LINEA = "html=1;endArrow=none;strokeColor=#8C4FFF;strokeWidth=3;fontSize=10;labelBackgroundColor=#FFFFFF;fontColor=#1A1A1A;"
TEMPORAL = "dashed=1;dashPattern=3 3;"


def vm_txt(cd: CentroDatos, cid: str) -> str:
    v = cd.vm_por_id[cid]
    return f"{v['vcpu']} vCPU · {v['ram_gb']} GB"


def huella_dc() -> str:
    h = hashlib.sha256()
    for f in ("infra/centro_datos.yaml", "infra/inventory.yaml"):
        h.update((RAIZ / f).read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:8]


class DiagramaDC(Diagrama):
    def __init__(self, x: Infra, cd: CentroDatos, fig: str, ancho: int, alto: int):
        super().__init__(x, fig, ancho, alto)
        self.cd = cd
        self.extras_dibujados: list[str] = []

    # ------------------------------------------------------------------ marco común
    def titulo(self, x0=20, y0=10, w=None):
        f = self.cd.raw["figuras"][self.fig]
        m = self.cd.meta
        w = w or (self.ancho - 40)
        label = (f"<b>{esc(f['leyenda'])}</b><br>{self.fig} · Centro de datos v{m['version']} · {m['fecha']} · inventario "
                 f"v{self.x.inv['meta']['inventario_version']} · huella de la fuente {huella_dc()} · CE0331 Celeris Edge · generado desde infra/*.yaml")
        self.caja(x0, y0, w, 44, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1A1A1A;strokeWidth=1;"
                  f"align=left;spacingLeft=10;fontSize=13;fontColor={TEXTO};", label,
                  {"celeris_rol": "titulo", "figura": self.fig, "titulo": f["leyenda"]})

    # ------------------------------------------------------------------ cajas
    def comp(self, cid: str, x0, y0, w, h, l2: str, l3: str | None = None, dashed=False, extra_nombre="", sin_icono=False,
             nombre: str | None = None, borde: str | None = None) -> str:
        """Caja de un componente del inventario en tres líneas: «ID · nombre · CRITICIDAD», recursos/IP y qué aporta."""
        comp = self.x.componentes[cid]
        grosor, tag = CRITICIDAD[comp["criticidad"]]
        color = borde or color_de(self.x, comp)
        temporal = comp["estado"] == "temporal"
        lineas = [f"<b>{esc(cid)}</b> · {esc(nombre or nombre_corto(comp))} · <b>{tag}</b>" + (" · <i>temporal</i>" if temporal else "")
                  + (f" · <i>{esc(extra_nombre)}</i>" if extra_nombre else ""), esc(l2)]
        if l3:
            lineas.append(f"<i>{esc(l3)}</i>")
        icono = 0 if sin_icono or comp["tipo"] not in ICONO else 22
        fuente = tam_fuente(lineas, w - icono - 20, h - 4)
        estilo = (f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={color};strokeWidth={grosor};"
                  f"align=left;verticalAlign=top;spacingLeft={icono + 10 if icono else 8};spacingTop=2;spacingRight=2;"
                  f"fontSize={fuente};fontColor={TEXTO};" + (TEMPORAL if (dashed or temporal) else ""))
        c = self.caja(x0, y0, w, h, estilo, "<br>".join(lineas), self.datos_componente(comp))
        if icono:
            self.caja(x0 + 5, y0 + 6, icono, icono, ICONO[comp["tipo"]] + "html=1;aspect=fixed;outlineConnect=0;dashed=0;")
            self.tipos.add(comp["tipo"])
        self.nodos[cid] = c
        if cid not in self.presentes:
            self.presentes.append(cid)
        return c

    def elem(self, eid: str, x0, y0, w, h, l2: str | None = None, l3: str | None = None, nombre: str | None = None,
             color: str | None = None, dashed=False, container=False) -> str:
        """Caja de un elemento propio del centro de datos (port group, NIC, datastore, vSwitch, rack, IGW, SG…)."""
        e = self.cd.extras()[eid]
        grosor, tag = CRITICIDAD[e["criticidad"]]
        nom = nombre if nombre is not None else e["nombre"].split("—", 1)[1].strip()
        l1 = f"<b>{esc(eid)}</b>" + (f" · {esc(nom)}" if nom else "") + f" · <b>{tag}</b>"
        lineas = [l1] + ([esc(l2)] if l2 else []) + ([f"<i>{esc(l3)}</i>"] if l3 else [])
        fuente = tam_fuente(lineas, w - 16, h - 4)
        estilo = (f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={color or '#4D4D4D'};strokeWidth={grosor};"
                  f"align=left;verticalAlign=top;spacingLeft=8;spacingTop=2;spacingRight=2;fontSize={fuente};fontColor={TEXTO};"
                  + (TEMPORAL if (dashed or e.get('estado') == 'temporal') else ""))
        attrs = {"celeris_id": eid, "celeris_tipo": "elemento", "tipo": e["tipo"], "entorno": e["entorno"], "criticidad": e["criticidad"],
                 "funcion": e["funcion"], "recursos": e["recursos"], "por_que": e["por_que"], "si_falla": e["si_falla"],
                 "tooltip": f"{eid} · {e['criticidad']}\nFunción: {e['funcion']}\nPor qué: {e['por_que']}\nSi falla: {e['si_falla']}"}
        c = self.caja(x0, y0, w, h, estilo, "<br>".join(lineas), attrs)
        self.nodos[eid] = c
        if eid not in self.presentes:
            self.presentes.append(eid)
        return c

    def recurso(self, eid: str) -> str:
        return self.cd.extras()[eid]["recursos"]

    def cable(self, a, b, pts, estilo, label="", ida="", idb=""):
        """Enlace físico o lógico entre dos puntos, con vértices intermedios: celeris_tipo=enlace."""
        attrs = {"celeris_id": f"{ida}>{idb}", "celeris_tipo": "enlace", "enlace_a": ida, "enlace_b": idb, "etiqueta": label}
        return self._celda(attrs, label, estilo, {"relative": 1}, vertex=False, extremos=(a, b), puntos=pts)

    def nota_dc(self, x0, y0, w, h, texto, rol="nota", ref=None, **kw):
        return self.nota(x0, y0, w, h, texto, {"celeris_rol": rol, **({"celeris_ref": ref} if ref else {})}, **kw)

    def zona_color(self, zid: str | None) -> str:
        if zid and self.x.zonas.get(zid, {}).get("color"):
            if zid not in self.zonas_dibujadas:
                self.zonas_dibujadas.append(zid)
            return self.x.zonas[zid]["color"]
        return "#4D4D4D"

    # ------------------------------------------------------------------ panel y leyenda
    def panel_dc(self, x0, y0, w, columnas=2) -> int:
        ids = list(self.presentes)
        filas = []
        for i in ids:
            if i in self.x.componentes:
                c = self.x.componentes[i]
                filas.append(f"<b>{esc(i)}</b> — {esc(c['aporta_corto'])}. <i>Si falla:</i> {esc(primera_frase(c['si_falla'], 78))}")
            else:
                e = self.cd.extras()[i]
                filas.append(f"<b>{esc(i)}</b> — {esc(primera_frase(e['funcion'], 70))}. <i>Si falla:</i> {esc(primera_frase(e['si_falla'], 78))}")
        wc = (w - 10 * (columnas - 1)) / columnas
        por_col = -(-len(filas) // columnas)
        alto = 0
        for k in range(columnas):
            parte = filas[k * por_col:(k + 1) * por_col]
            if not parte:
                continue
            h = 30 + sum(12 * lineas_estimadas(f, wc - 16, 9) for f in parte)
            label = ("<b>Qué aporta y qué pasa si falla</b><br>" if k == 0 else "<b>…continúa</b><br>") + "<br>".join(parte)
            self.caja(x0 + k * (wc + 10), y0, wc, h, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#4D4D4D;align=left;"
                      f"verticalAlign=top;spacingLeft=8;spacingRight=6;spacingTop=4;fontSize=9;fontColor={TEXTO};", label,
                      {"celeris_rol": "panel", "componentes": ", ".join(ids)})
            alto = max(alto, h)
        return alto

    def leyenda_dc(self, x0, y0, w, enlaces: list[tuple[str, str]]) -> int:
        alto_base = self.leyenda(x0, y0, w=min(w, 1000), flujos=False)
        yb = y0 + alto_base + 8
        txt = f"text;html=1;align=left;verticalAlign=middle;fontSize=10;fontColor={TEXTO};whiteSpace=wrap;"
        n = len(enlaces)
        alto = 30 + ((n + 2) // 3) * 24
        self.caja(x0, yb, min(w, 1000), alto, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4D4D4D;align=left;"
                  f"verticalAlign=top;spacingLeft=8;spacingTop=4;fontSize=11;fontColor={TEXTO};",
                  "<b>Enlaces</b> (el estilo y el texto de la etiqueta dicen qué es):", {"celeris_rol": "leyenda_enlaces"})
        cw = (min(w, 1000) - 16) // 3
        for i, (est, nombre) in enumerate(enlaces):
            cx, cy = x0 + 8 + (i % 3) * cw, yb + 28 + (i // 3) * 24
            self.linea_libre((cx, cy + 9), (cx + 44, cy + 9), est)
            self.caja(cx + 50, cy, cw - 54, 20, txt, esc(nombre))
        return alto_base + 8 + alto


def _fin(d: DiagramaDC, y_contenido: int, x_derecha: int, enlaces, w_der: int = 1000):
    """Leyenda y panel a la derecha del dibujo; ajusta el alto del lienzo."""
    alto_l = d.leyenda_dc(x_derecha, 70, w_der, enlaces)
    alto_p = d.panel_dc(x_derecha, 70 + alto_l + 16, w_der, columnas=2)
    d.alto = max(y_contenido, 70 + alto_l + 16 + alto_p) + 30
    return d


# --------------------------------------------------------------------------------------------------
# DC-1 — Topología física
# --------------------------------------------------------------------------------------------------
def dc_1(x: Infra, cd: CentroDatos) -> DiagramaDC:
    d = DiagramaDC(x, cd, "DC-1", 2300, 1200)
    d.titulo(w=1180)
    h, r = cd.host, cd.raw["rack"]
    SU, Y0 = 80, 112                      # alto de una U y borde superior de la U12

    def top(u):                           # borde superior de la unidad u (U12 arriba)
        return Y0 + (12 - u) * SU
    # marco del rack
    e = cd.extras()["RACK01"]
    d.caja(20, 80, 770, 12 * SU + 44, "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#1A1A1A;strokeWidth=3;"
           f"verticalAlign=top;align=left;spacingLeft=8;spacingTop=3;fontSize=11;fontColor={TEXTO};",
           f"<b>RACK01</b> · Rack de {r['unidades']}U · <b>ALTA</b> · {esc(e['recursos'])} · U12 arriba",
           {"celeris_id": "RACK01", "celeris_tipo": "elemento", "tipo": e["tipo"], "entorno": "On-premise", "criticidad": e["criticidad"],
            "funcion": e["funcion"], "recursos": e["recursos"], "por_que": e["por_que"], "si_falla": e["si_falla"]})
    d.nodos["RACK01"] = d.celdas[-1].get("id")
    d.presentes.append("RACK01")
    for u in range(1, 13):                # numeración de las U
        d.caja(2, top(u) + 26, 18, 18, "text;html=1;align=center;verticalAlign=middle;fontSize=9;fontColor=#595959;", f"U{u}")
    X, W = 70, 640
    d.elem("CD-PP01", X, top(12) + 4, W, 72, d.recurso("CD-PP01"), "Ordena los enlaces hacia la capa de acceso", nombre="Patch panel 24 puertos", color="#4D4D4D")
    sw = d.comp("SW-CORE01", X, top(11) + 4, W, 72, "10.20.10.2 · 24× 1 GbE + 2–4× SFP+ 10 GbE · U11", x.componentes["SW-CORE01"]["aporta_corto"])
    d.elem("CD-ORG01", X, top(10) + 4, W, 72, d.recurso("CD-ORG01"), "Guía los cables entre el switch y el servidor", nombre="Organizador de cables")
    # ESX01 (U6–9) con sus NIC, datastores, IPMI01 y JMP01 dentro
    ex_y = top(9) + 4
    esx = d.comp("ESX01", X, ex_y, W, 4 * SU - 8, f"10.20.10.10 (vmk0) · {cd.recursos_de('ESX01')} · rango U6–9 (CI-79)",
                 x.componentes["ESX01"]["aporta_corto"])
    nic_ids = list(cd.nics)
    for i, nid in enumerate(nic_ids):
        n = cd.nics[nid]
        vel = f"{n['velocidad_gbps']} GbE" if n["velocidad_gbps"] else "libre"
        d.elem(nid, 515, ex_y + 72 + i * 58, 190, 50, f"{vel} · {n['vswitch'] or 'sin vSwitch'}", None, nombre="NIC física")
    for i, did in enumerate(cd.datastores):
        ds = cd.datastores[did]
        tam = f"{coma(ds['capacidad_gb'] / 1000, 2)} TB"
        d.elem(did, X + 6 + i * 147, ex_y + 72, 138, 56, f"{ds['raid'] if ds['raid'] != 'ninguno' else 'sin RAID'} · {tam}",
               "SSD" if did == "DS-VM" else "NVMe", nombre="")
    d.comp("IPMI01", X + 6, ex_y + 140, 222, 76, "10.20.10.11 · MGMT", x.componentes["IPMI01"]["aporta_corto"])
    d.comp("JMP01", X + 238, ex_y + 140, 194, 76, "10.20.10.20 · VM 2 vCPU, 4 GB", "Servidor NUT: apaga VM y ESXi")
    fases = {f: ", ".join(v["componente"] for v in cd.vms if v["fase"] == f) for f in ("F1", "F2")}
    d.nota_dc(X + 6, ex_y + 224, 426, 44, f"<b>VM de ESX01:</b> {esc(fases['F1'])} (F1) y {esc(fases['F2'])} (F2); detalle en DC-2.",
              "vm_lista", "ESX01", tam=9)
    d.nota_dc(X, top(5) + 4, W, 2 * SU - 8, "<b>U4–U5 libres.</b> D2.4 asigna el rango U6–9 a ESX01, un equipo de 2U; no se define el uso de las U sobrantes (CI-79).",
              "libre", "RACK01", color="#FFFFFF", tam=10)
    ups = d.comp("UPS01", X, top(3) + 8, 340, 120, "10.20.10.40 (tarjeta de red) · " + cd.recursos_de("UPS01"), x.componentes["UPS01"]["aporta_corto"])
    d.elem("CD-PDU01", X + 370, top(3) + 8, 270, 120, d.recurso("CD-PDU01"), "Reparte la UPS a ESX01 y SW-CORE01", nombre="PDU")
    en = cd.raw["energia"]
    d.nota_dc(X, top(3) + 136, W, 90, f"<b>Energía:</b> consumo ≈ {en['consumo_w']} W; autonomía {en['autonomia_min'][0]}–{en['autonomia_min'][1]} min "
              f"({esc(en['autonomia_nota'].lower())}). <b>NUT:</b> {esc(en['nut']['accion'])}.<br><b>Arranque:</b> FW01 → CTRL01 → EDGE01/02 → SIEM01 → resto (D2.4).",
              "energia", "UPS01", tam=10)
    # columna externa
    XE = 930
    acc = d.comp("SW-ACC", XE, 98, 300, 100, "Según levantamiento AS-IS [S-14]", x.componentes["SW-ACC"]["aporta_corto"], dashed=True)
    brk = d.comp("BRK01", XE, 232, 300, 86, "laptop 10.20.10.250 · VLAN 10", x.componentes["BRK01"]["aporta_corto"])
    fgt = d.comp("FGT-EXT", XE, 560, 300, 112, "WAN 203.0.113.10 · tránsito 10.20.0.1", x.componentes["FGT-EXT"]["aporta_corto"], dashed=True)
    inet = d.zona("INTERNET", XE + 40, 740, 220, 96, "<br>salida del campus")
    # cables
    d.cable((X + W, top(12) + 40), (XE, 148), [], ENLACE_1G, "trunk 802.1Q a la capa de acceso · velocidad sin definir (CI-80)", "CD-PP01", "SW-ACC")
    d.cable((X + 560, top(11) + 4), (X + 560, top(12) + 76), [], ENLACE_1G, "", "SW-CORE01", "CD-PP01")
    d.cable((XE, 275), (X + W, 205), [(880, 275), (880, 205)], ENLACE_1G, "puerto break-glass · VLAN 10 · apagado por defecto", "BRK01", "SW-CORE01")
    ex = ex_y
    d.cable((700, ex + 72 + 25), (X + W, 232), [(725, ex + 72 + 25), (725, 232)], ENLACE_10G, "10 GbE · trunk 802.1Q (vSwitch0)", "vmnic0", "SW-CORE01")
    d.cable((700, ex + 72 + 58 + 25), (X + W, 220), [(742, ex + 72 + 58 + 25), (742, 220)], ENLACE_10G, "", "vmnic1", "SW-CORE01")
    d.cable((700, ex + 72 + 116 + 25), (XE, 616), [(850, ex + 72 + 116 + 25), (850, 616)], ENLACE_1G, "1 GbE · NIC dedicada · tránsito 10.20.0.0/29 (vSwitch1)", "vmnic2", "FGT-EXT")
    d.cable((X, ex + 140 + 38), (X, 244), [(54, ex + 140 + 38), (54, 244)], ENLACE_GEST, "", "IPMI01", "SW-CORE01")
    d.cable((X, top(3) + 8 + 100), (X, 222), [(42, top(3) + 8 + 100), (42, 222)], ENLACE_GEST, "", "UPS01", "SW-CORE01")
    d.cable((X, top(3) + 8 + 112), (X, 205), [(30, top(3) + 8 + 112), (30, 205)], ENERGIA, "", "UPS01", "SW-CORE01")
    d.cable((X + 340, top(3) + 68), (X + 370, top(3) + 68), [], ENERGIA, "", "UPS01", "CD-PDU01")
    d.cable((X + 505, top(3) + 8), (X + 505, ex_y + 4 * SU - 8), [], ENERGIA, "alimentación", "CD-PDU01", "ESX01")
    d.cable((XE + 150, 672), (XE + 150, 740), [], ENLACE_1G, "", "FGT-EXT", "INTERNET")
    d.nota_dc(XE, 380, 300, 150, "<b>Cables</b> (las etiquetas llevan la velocidad):<br>vmnic0 y vmnic1 (10 GbE) → SW-CORE01, teaming por puerto virtual de origen.<br>"
              "vmnic2 (1 GbE) → FortiGate, dedicada. vmnic3 libre.<br>IPMI01 y la tarjeta de la UPS en MGMT (VLAN 10).", "cables", "ESX01", tam=9)
    d.nota_dc(XE, 860, 300, 70, "Lados del trunk: las 7 VLAN del proyecto con lista explícita y nativa 999 (D1.9).", "trunk", "SW-CORE01", tam=9)
    d.nota_dc(20, 12 * SU + 100, 770, 44, "Líneas de las tres columnas izquierdas del rack: negro punteado = alimentación; gris fino = gestión (IPMI01 y red de UPS01 hacia SW-CORE01).",
              "carriles", "RACK01", tam=9, color="#FFFFFF")
    return _fin(d, 12 * SU + 180, 1260, [(ENLACE_10G, "10 GbE trunk"), (ENLACE_1G, "1 GbE / trunk de acceso"), (ENLACE_GEST, "gestión (MGMT)"), (ENERGIA, "alimentación eléctrica")])


# --------------------------------------------------------------------------------------------------
# DC-2 — Hipervisor
# --------------------------------------------------------------------------------------------------
def dc_2(x: Infra, cd: CentroDatos) -> DiagramaDC:
    d = DiagramaDC(x, cd, "DC-2", 2400, 1500)
    d.titulo(w=1560)
    vs0, vs1 = cd.vswitches["vSwitch0"], cd.vswitches["vSwitch1"]
    seg = cd.raw["hipervisor_red"]["seguridad_por_defecto"]
    # uplinks físicos (columna izquierda)
    XN, XS = 30, 270
    yv0 = 80
    filas = vs0["port_groups"]
    FH, FG = 78, 8
    alto0 = 66 + len(filas) * (FH + FG)
    d.caja(XS, yv0, 1260, alto0, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#1A1A1A;strokeWidth=3;verticalAlign=top;align=left;"
           f"spacingLeft=8;spacingTop=3;fontSize=11;fontColor={TEXTO};",
           f"<b>vSwitch0</b> · <b>ALTA</b> · vSwitch estándar · {esc(vs0['teaming']['politica'])} (activo/activo, sin LACP) · uplinks {', '.join(vs0['uplinks'])}",
           {"celeris_id": "vSwitch0", "celeris_tipo": "elemento", "tipo": cd.extras()["vSwitch0"]["tipo"], "entorno": "On-premise",
            "criticidad": cd.extras()["vSwitch0"]["criticidad"], "funcion": cd.extras()["vSwitch0"]["funcion"], "recursos": cd.extras()["vSwitch0"]["recursos"],
            "por_que": cd.extras()["vSwitch0"]["por_que"], "si_falla": cd.extras()["vSwitch0"]["si_falla"]})
    d.nodos["vSwitch0"] = d.celdas[-1].get("id")
    d.presentes.append("vSwitch0")
    d.nota_dc(XS + 8, yv0 + 28, 1244, 30, f"Seguridad de todos los port groups: modo promiscuo <b>{seg['modo_promiscuo']}</b> · cambios de MAC <b>{seg['cambios_mac']}</b> · "
              f"transmisiones falsificadas <b>{seg['transmisiones_falsificadas']}</b> (v0.4: sin excepciones).", "seguridad_pg", "vSwitch0", tam=10, color="#FFFFFF")
    ypos = {}
    for i, pg in enumerate(filas):
        yy = yv0 + 66 + i * (FH + FG)
        ypos[pg["id"]] = yy
        zona = pg["zona"]
        col = d.zona_color(zona)
        vlan = f"VLAN {pg['vlan']}"
        vms = [v for v in cd.vms if pg["id"] in v["port_groups"]]
        d.elem(pg["id"], XS + 10, yy, 300, FH, vlan + (f" · zona {zona}" if zona else " · todas las VLAN (VGT)") + f" · {vs0['id']}",
               f"VM: {', '.join(v['componente'] for v in vms)}", nombre="Port group", color=col)
        for k, v in enumerate(vms):
            c = x.componentes[v["componente"]]
            l2 = f"{v['vcpu']} vCPU · {v['ram_gb']} GB · {cd.vm_texto_disco(v)} GB · {v['so']} · {v['fase']}"
            d.comp(v["componente"], XS + 330 + k * 300, yy, 292, FH, l2, c["aporta_corto"], dashed=(v["fase"] == "F2"),
                   extra_nombre="F2" if v["fase"] == "F2" else "")
    # vSwitch1 con PG-TRANSITO
    yv1 = yv0 + alto0 + 30
    pgt = vs1["port_groups"][0]
    d.caja(XS, yv1, 1260, 150, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#1A1A1A;strokeWidth=3;verticalAlign=top;align=left;"
           f"spacingLeft=8;spacingTop=3;fontSize=11;fontColor={TEXTO};",
           f"<b>vSwitch1</b> · <b>ALTA</b> · vSwitch estándar · uplink {vs1['uplinks'][0]} (sin teaming) · {esc(vs1['uso'])}",
           {"celeris_id": "vSwitch1", "celeris_tipo": "elemento", "tipo": cd.extras()["vSwitch1"]["tipo"], "entorno": "On-premise",
            "criticidad": cd.extras()["vSwitch1"]["criticidad"], "funcion": cd.extras()["vSwitch1"]["funcion"], "recursos": cd.extras()["vSwitch1"]["recursos"],
            "por_que": cd.extras()["vSwitch1"]["por_que"], "si_falla": cd.extras()["vSwitch1"]["si_falla"]})
    d.nodos["vSwitch1"] = d.celdas[-1].get("id")
    d.presentes.append("vSwitch1")
    col_t = "#999999"
    d.zonas_dibujadas.append("TRANSITO") if "TRANSITO" not in d.zonas_dibujadas and x.zonas["TRANSITO"].get("color") else None
    d.elem(pgt["id"], XS + 10, yv1 + 40, 300, FH, "sin etiqueta · zona TRANSITO 10.20.0.0/29 · vSwitch1", "Solo FW01 (D-26)", nombre="Port group", color=col_t)
    d.interfaz("FW01:wan", XS + 330, yv1 + 40, w=292, h=FH)
    # uplinks
    for i, nid in enumerate(cd.nics):
        n = cd.nics[nid]
        yy = yv0 + 66 + i * 90 if i < 2 else yv1 + 40 + (i - 2) * 56
        d.elem(nid, XN, yy, 220, 76 if i < 2 else 50, (f"{n['velocidad_gbps']} GbE" if n["velocidad_gbps"] else "libre") + f" · {n['vswitch'] or '—'}",
               n["uso"].split(" hacia ")[0][:44] if i < 2 else None, nombre="NIC física")
    d.cable((XN + 220, yv0 + 66 + 38), (XS, yv0 + 90), [(250, yv0 + 66 + 38), (250, yv0 + 90)], ENLACE_10G, "", "vmnic0", "vSwitch0")
    d.cable((XN + 220, yv0 + 66 + 90 + 38), (XS, yv0 + 90 + 20), [(256, yv0 + 66 + 90 + 38), (256, yv0 + 110)], ENLACE_10G, "", "vmnic1", "vSwitch0")
    d.cable((XN + 220, yv1 + 40 + 25), (XS, yv1 + 65), [], ENLACE_1G, "", "vmnic2", "vSwitch1")
    d.nota_dc(XN, yv0 + 66 + 190, 220, 120, "<b>Teaming:</b> vmnic0 y vmnic1 hacia SW-CORE01 (trunk). Reparte las VM por puerto virtual de origen; si un enlace cae, sus VM pasan al otro. El vSwitch estándar no soporta LACP.",
              "teaming", "vSwitch0", tam=9)
    d.nota_dc(XN, yv0 + 66 + 330, 220, 130, "<b>vmk0</b> 10.20.10.10 en PG-MGMT (gestión de ESX01). PG-FW-TRUNK (VLAN 4095) entrega todas las VLAN a FW01, que enruta con una subinterfaz por VLAN (D-17).",
              "vmk", "ESX01", tam=9)
    # FW01 ↔ PG-TRANSITO
    d.cable((XS + 330 + 146, ypos["PG-FW-TRUNK"] + FH), (XS + 330 + 146, yv1 + 40), [], ENLACE_1G, "segunda vNIC de FW01 (WAN)", "FW01", "FW01:wan")
    # datastores
    XD = XS + 1260 + 40
    ds_vm, c1, c2 = (cd.datastores[k] for k in ("DS-VM", "DS-CACHE1", "DS-CACHE2"))
    d.elem("DS-VM", XD, yv0 + 66 + 3 * (FH + FG), 330, 120, f"{ds_vm['medio']} · {coma(ds_vm['capacidad_gb'] / 1000, 2)} TB",
           "Discos de las VM (sin caché) y la copia local de restic", nombre="Datastore VM (RAID 1)")
    d.elem("DS-CACHE1", XD, ypos["PG-EDGE"] - 10, 330, 70, f"{c1['medio']} · {coma(c1['capacidad_gb'] / 1000, 2)} TB", "Caché de EDGE01: 500 GB",
           nombre="Datastore caché 1")
    d.elem("DS-CACHE2", XD, ypos["PG-EDGE"] + 70, 330, 70, f"{c2['medio']} · {coma(c2['capacidad_gb'] / 1000, 2)} TB", "Caché de EDGE02 (F2): 500 GB",
           nombre="Datastore caché 2", dashed=True)
    d.cable((XS + 1260, ypos["PG-EDGE"] + 30), (XD, ypos["PG-EDGE"] + 25), [], ENLACE_GEST, "EDGE01 → caché 1", "EDGE01", "DS-CACHE1")
    d.cable((XS + 1260, ypos["PG-EDGE"] + 60), (XD, ypos["PG-EDGE"] + 105), [(XS + 1290, ypos["PG-EDGE"] + 60), (XS + 1290, ypos["PG-EDGE"] + 105)], ENLACE_GEST, "EDGE02 → caché 2", "EDGE02", "DS-CACHE2")
    d.cable((XS + 1260, yv0 + 66 + 3 * (FH + FG) + 60), (XD, yv0 + 66 + 3 * (FH + FG) + 60), [], ENLACE_GEST, "discos de las 11 VM", "vSwitch0", "DS-VM")
    # resumen de capacidad (cifras de D2.4/D2.8, calculadas)
    t1, t2, dm = cd.totales("F1"), cd.totales("F2"), cd.dimensionar()
    h = cd.host
    d.nota_dc(XD, yv1 - 10, 330, 180,
              f"<b>Capacidad de ESX01:</b> {h['cpu']['nucleos']} núcleos, {h['ram_gb']} GB RAM, DS-VM {coma(ds_vm['capacidad_gb'] / 1000, 2)} TB.<br>"
              f"<b>F1:</b> {t1['vms']} VM · {t1['vcpu']} vCPU · {t1['ram_gb']} GB · {coma(t1['disco_gb'], 0)} GB.<br>"
              f"<b>F2:</b> {t2['vms']} VM · {t2['vcpu']} vCPU · {t2['ram_gb']} GB · {coma(t2['disco_gb'], 0)} GB.<br>"
              f"Ninguna VM supera {cd.host['hipervisor']['vcpu_max_por_vm']} vCPU (ESXi gratuito); mayor: {dm['vcpu_max_vm']}.", "capacidad", "ESX01", tam=10)
    d.nota_dc(XS, yv1 + 160, 1260, 56, "<b>Orden de arranque (NUT apaga en orden inverso):</b> FW01 → CTRL01 → EDGE01/EDGE02 → SIEM01 → el resto. "
              "ENC01 es una PC física del laboratorio, no una VM.", "arranque", "ESX01", tam=10, color="#FFFFFF")
    return _fin(d, yv1 + 240, XD + 360 + 20, [(ENLACE_10G, "10 GbE trunk"), (ENLACE_1G, "1 GbE"), (ENLACE_GEST, "vínculo VM → datastore")], w_der=860)


# --------------------------------------------------------------------------------------------------
# DC-3 — AWS
# --------------------------------------------------------------------------------------------------
def dc_3(x: Infra, cd: CentroDatos) -> DiagramaDC:
    d = DiagramaDC(x, cd, "DC-3", 2400, 1450)
    d.titulo(w=1560)
    aws = x.inv["aws"]
    reg = cd.aws["region"]
    camp = x.inv["supernets"][0]["cidr"]
    # Internet y campus
    d.zona("INTERNET", 60, 100, 240, 90, "<br>usuarios del panel y ACME")
    d.nota_dc(20, 760, 250, 150, f"<b>Campus Juliaca {camp}</b><br>FW01 (VTI1, VTI2), detrás de FGT-EXT: extremo VPN on-premise. La integración se dibuja en FIG-5.4 de CE0311 y no se repite aquí.",
              "campus", "VGW", color="#F3EDFF", borde="#8C4FFF", tam=10)
    # nube y VPC
    nube = d.zona("AWS", 310, 80, 1500, 1080, f" · región {esc(reg['laboratorio'])} (laboratorio) · producción candidata {esc(reg['produccion_candidata'])} [S-11]")
    vpc = d.grupo_aws("AWS-VPC", 400, 130, 1060, 1000)
    d.nota_dc(1010, 135, 440, 56, f"<b>Reserva</b> {esc(x.inv['reservas'][1]['cidr'])}: crecimiento (sin subredes). Etiquetas: Proyecto=celeris-edge; Ttl en lo efímero.", "reserva", "AWS-VPC", tam=9, color="#FFFFFF")
    d.elem("IGW01", 700, 138, 280, 56, "Entrada y salida de Internet de pub-a", None, nombre="Internet Gateway", color=AWS_TINTA)
    vgw = d.comp("VGW", 330, 330, 240, 100, "2 túneles IPsec · ASN 64512 · propaga rutas por BGP", x.componentes["VGW"]["aporta_corto"], borde="#8C4FFF")
    # pub-a
    d.grupo_aws("AWS-PUB-A", 600, 230, 820, 320)
    gw = d.comp("EC2-GW", 620, 270, 330, 110, cd.recursos_de("EC2-GW") + " · 10.30.0.10", x.componentes["EC2-GW"]["aporta_corto"])
    nat = d.comp("NAT-DR", 620, 400, 330, 90, "t3.micro · solo en el simulacro T59", x.componentes["NAT-DR"]["aporta_corto"])
    sg = next(s for s in aws["security_groups"] if s["id"] == "sg-gw")
    d.elem("sg-gw", 980, 270, 420, 110, f"entrada TCP 443 desde 0.0.0.0/0 (F29)", "salida: 443 → 10.20.20.10 · 1514/1515 → 10.20.50.10 · 443 Internet",
           nombre="Security Group de EC2-GW", color="#7AA116")
    d.elem("nacl-public", 980, 400, 420, 90, "deniega TCP 22 y 3389 desde Internet; permite 443 y retorno efímero", None, nombre="NACL de pub-a", color="#7AA116")
    d.elem("rt-public", 620, 500, 780, 40, "0.0.0.0/0 → IGW01 · 10.20.0.0/16 → VGW (BGP)", None, nombre="Tabla de rutas de pub-a", color="#7AA116")
    # app-a
    d.grupo_aws("AWS-APP-A", 600, 600, 820, 320)
    dr = d.comp("EC2-DR", 620, 640, 330, 100, "t3.small · 2 vCPU · 2 GiB · sin entrada desde Internet", x.componentes["EC2-DR"]["aporta_corto"])
    d.elem("sg-dr", 980, 640, 420, 70, "sin entrada; salida a S3 (endpoint) y a NAT-DR", None, nombre="Security Group de EC2-DR", color="#00A4A6", dashed=True)
    d.elem("nacl-private", 980, 720, 420, 70, "permite TCP 443 desde pub-a y retorno efímero; sin SSH", None, nombre="NACL de app-a", color="#00A4A6")
    d.elem("VPCE-S3", 620, 760, 330, 56, "Gateway Endpoint de S3 · sin costo por hora", None, nombre="Endpoint", color=AWS_TINTA)
    d.elem("rt-private", 620, 830, 780, 70, "10.20.0.0/16 → VGW · prefijo S3 → VPCE-S3 · 0.0.0.0/0 → NAT-DR (solo en el simulacro)", None, nombre="Tabla de rutas de app-a", color="#00A4A6")
    d.nota_dc(420, 950, 1020, 76, f"<b>Sin NAT permanente.</b> {esc(cd.aws['nat']['razon'])} {esc(cd.aws['nat']['temporal'])}", "nat", "NAT-DR", tam=10, color="#FFFFFF")
    d.nota_dc(420, 1034, 1020, 90, "<b>Administración:</b> " + esc(cd.aws["gobierno"]) + "<br><b>Región:</b> " + esc(reg["por_que"]), "gobierno", "AWS-VPC", tam=10, color="#FFFFFF")
    # S3
    s3 = d.comp("S3", 1500, 330, 290, 120, cd.recursos_de("S3") + " · regional", x.componentes["S3"]["aporta_corto"])
    d.nota_dc(1500, 460, 290, 100, "Recibe TCP 443 de CTRL01 por Internet (F18); solo acepta la IP pública del campus; credencial solo s3:PutObject [S-30]; la llave de restic no está en AWS.", "s3_nota", "S3", tam=9)
    # enlaces
    d.cable((180, 190), (700, 166), [(180, 166)], ENLACE_1G, "TCP 443 (F29)", "INTERNET", "IGW01")
    d.cable((840, 194), (700, 270), [(840, 230), (700, 230)], ENLACE_1G, "", "IGW01", "EC2-GW")
    d.cable((620, 325), (570, 380), [(595, 325), (595, 380)], VPN_LINEA, "F30 · F13 por IPsec", "EC2-GW", "VGW")
    d.cable((330, 380), (270, 800), [(300, 380), (300, 800)], VPN_LINEA, "VPN IPsec IKEv2 · 2 túneles · BGP", "VGW", "campus")
    d.cable((785, 640), (785, 490), [], TEMPORAL + ENLACE_GEST, "instala paquetes (solo T59)", "EC2-DR", "NAT-DR")
    d.cable((785, 760), (785, 740), [], ENLACE_GEST, "", "VPCE-S3", "EC2-DR")
    d.cable((620, 788), (1500, 420), [(560, 788), (560, 928), (1480, 928), (1480, 420)], ENLACE_GEST, "restauración desde S3 (T59)", "VPCE-S3", "S3")
    d.cable((300, 122), (1640, 330), [(1640, 122)], TEMPORAL + ENLACE_GEST, "respaldos F18: TCP 443 cifrado en origen", "INTERNET", "S3")
    return _fin(d, 1200, 1840, [(ENLACE_1G, "tráfico de aplicación"), (VPN_LINEA, "VPN IPsec"), (TEMPORAL + ENLACE_GEST, "temporal / punteado")], w_der=540)


# --------------------------------------------------------------------------------------------------
# DC-0 — Topología ejecutiva
# --------------------------------------------------------------------------------------------------
def dc_0(x: Infra, cd: CentroDatos) -> DiagramaDC:
    d = DiagramaDC(x, cd, "DC-0", 2000, 900)
    d.titulo(w=1200)
    t = cd.totales("F2")
    d.zona("INTERNET", 40, 120, 200, 90, "<br>usuarios y respaldos")
    d.caja(280, 90, 640, 520, "rounded=0;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#1A1A1A;strokeWidth=2;verticalAlign=top;align=left;"
           f"spacingLeft=8;spacingTop=4;fontSize=11;fontColor={TEXTO};", "<b>On-premise · Campus Juliaca</b> · un rack de 12U · ESXi gratuito, un host", {"celeris_rol": "campus"})
    d.comp("FGT-EXT", 300, 130, 300, 90, "WAN 203.0.113.10 · tránsito 10.20.0.1", x.componentes["FGT-EXT"]["aporta_corto"], dashed=True)
    d.comp("ESX01", 300, 260, 600, 330, f"{cd.recursos_de('ESX01')} · {t['vms']} VM · {t['vcpu']} vCPU · {t['ram_gb']} GB (F2)", x.componentes["ESX01"]["aporta_corto"])
    d.comp("FW01", 320, 330, 270, 100, f"{vm_txt(cd, 'FW01')} · tránsito 10.20.0.2", x.componentes["FW01"]["aporta_corto"])
    d.comp("EDGE01", 610, 330, 270, 100, f"{vm_txt(cd, 'EDGE01')} · 10.20.60.10", x.componentes["EDGE01"]["aporta_corto"])
    d.comp("CTRL01", 320, 450, 270, 100, f"{vm_txt(cd, 'CTRL01')} · 10.20.20.10", x.componentes["CTRL01"]["aporta_corto"])
    d.comp("SIEM01", 610, 450, 270, 100, f"{vm_txt(cd, 'SIEM01')} · 10.20.50.10", x.componentes["SIEM01"]["aporta_corto"])
    d.zona("AWS", 1040, 90, 520, 520, f" · {esc(cd.aws['region']['laboratorio'])} · {esc(next(s['cidr'] for s in x.inv['supernets'] if s['id'] == 'AWS-CELERIS'))}")
    d.comp("VGW", 1060, 130, 480, 80, "2 túneles IPsec · ASN 64512", x.componentes["VGW"]["aporta_corto"], borde="#8C4FFF")
    d.comp("EC2-GW", 1060, 250, 480, 100, cd.recursos_de("EC2-GW") + " · 10.30.0.10", x.componentes["EC2-GW"]["aporta_corto"])
    d.comp("S3", 1060, 400, 480, 120, cd.recursos_de("S3"), x.componentes["S3"]["aporta_corto"])
    d.cable((240, 165), (300, 175), [], ENLACE_1G, "", "INTERNET", "FGT-EXT")
    d.cable((312, 220), (320, 360), [(312, 360)], ENLACE_1G, "tránsito", "FGT-EXT", "FW01")
    d.cable((590, 380), (610, 380), [], ENLACE_1G, "", "FW01", "EDGE01")
    d.cable((900, 380), (1060, 170), [(960, 380), (960, 170)], VPN_LINEA, "VPN IPsec (FIG-5.4 de CE0311)", "FW01", "VGW")
    d.cable((1300, 210), (1300, 250), [], VPN_LINEA, "", "VGW", "EC2-GW")
    d.cable((590, 500), (1060, 470), [(590, 640), (1000, 640), (1000, 470)], TEMPORAL + ENLACE_GEST, "respaldo cifrado, TCP 443 (F18)", "CTRL01", "S3")
    d.nota_dc(280, 680, 1280, 90, "<b>Reparto campus / nube (D-25).</b> En el campus: nodos de caché, consola y base, SIEM y firewall; en AWS: solo EC2-GW (sin datos ni llaves) y S3 (respaldos cifrados en origen). "
              "La caché no va en AWS (D-19).", "reparto", "ESX01", tam=11, color="#FFF8E1", borde="#1A1A1A")
    return _fin(d, 800, 1600, [(ENLACE_1G, "enlace"), (VPN_LINEA, "VPN IPsec"), (TEMPORAL + ENLACE_GEST, "respaldo (cifrado en origen)")], w_der=360)


GENERADORES = {"DC-0": dc_0, "DC-1": dc_1, "DC-2": dc_2, "DC-3": dc_3}


def generar(x: Infra, cd: CentroDatos, salida: Path = SALIDA, figuras=None) -> list[Path]:
    salida.mkdir(parents=True, exist_ok=True)
    hechos = []
    for fig in figuras or FIGURAS_DC:
        d = GENERADORES[fig](x, cd)
        px = (d.ancho + 20) * (d.alto + 20) * ESCALA_PNG ** 2
        if px > 2 ** 25:
            raise SystemExit(f"{fig}: {d.ancho} × {d.alto} a escala {ESCALA_PNG} son {px / 1e6:.1f} Mpx (> 33,5): compacte la disposición")
        ruta = salida / f"{fig}.drawio"
        ruta.write_text(d.xml(), encoding="utf-8", newline="\n")
        hechos.append(ruta)
    return hechos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--figura", action="append", choices=FIGURAS_DC)
    a = ap.parse_args(argv)
    x = Infra.cargar()
    for r in generar(x, CentroDatos.cargar(x), Path(a.salida), a.figura):
        print(r.relative_to(RAIZ) if r.is_relative_to(RAIZ) else r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
