"""BPMN 2.0 de los procesos de CE01 E4 desde gestion/e4/simulacion.yaml (CI-104).

    python gestion/e4/bpmn.py

Escribe gestion/e4/bpmn/<diagrama>.bpmn (P1-AS-IS, P1-TO-BE, P2-AS-IS, P2-TO-BE) en BPMN 2.0 XML con diagrama gráfico
(BPMNDI): colaboración con el pool «UPeU Campus Juliaca» y sus carriles, el pool colapsado «Internet / ISP» con los
flujos de mensaje de las descargas, tareas (de usuario y de servicio en el TO-BE), compuertas exclusivas, eventos de
inicio, fin y temporizador, y una anotación «PD-xx» sobre cada ineficiencia del AS-IS. Cada tarea documenta su
duración y su recurso (los parámetros que se cargan en la simulación de Bizagi). Los colores son los de la paleta de
CE01 (extensión BPMN in Color, que bpmn-js respeta y Bizagi ignora sin error).

Cada archivo se valida contra el XSD de OMG (gestion/e4/herramientas/xsd/BPMN20.xsd) y contra reglas propias: todo
flujo une nodos del mismo proceso, todo nodo tiene forma en el diagrama y todo PD-xx tiene su anotación.
"""
from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

import yaml
from lxml import etree

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import estilo_ce01 as est  # noqa: E402
from ce01_datos import num  # noqa: E402

SALIDA = AQUI / "bpmn"
XSD = AQUI / "herramientas" / "xsd" / "BPMN20.xsd"
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "bioc": "http://bpmn.io/schema/bpmn/biocolor/1.0",
    "color": "http://www.omg.org/spec/BPMN/non-normative/color/1.0",
}

# Geometría (px)
X0, POOL_BANDA, CARRIL_BANDA = 20, 30, 30
COL_W, FILA_H, MARGEN_SUP, MARGEN_INF = 158, 150, 22, 30
TAREA = (120, 72)
EVENTO = (36, 36)
COMPUERTA = (50, 50)
EXT_H, EXT_SEP = 60, 40
ETIQUETA = {"tarea": "Tarea", "tarea_usuario": "Tarea de usuario", "tarea_servicio": "Tarea de servicio"}
ELEMENTO = {"tarea": "task", "tarea_usuario": "userTask", "tarea_servicio": "serviceTask", "xor": "exclusiveGateway",
            "inicio": "startEvent", "inicio_temporizador": "startEvent", "temporizador": "intermediateCatchEvent",
            "fin": "endEvent"}


class BpmnError(Exception):
    pass


def _tam(tipo: str) -> tuple[int, int]:
    if tipo.startswith("tarea"):
        return TAREA
    return COMPUERTA if tipo == "xor" else EVENTO


def _iso_h(h: float) -> str:
    return f"PT{int(round(h * 60))}M" if h < 1 else f"PT{round(h, 2):g}H"


def _doc(n: dict, carriles: dict) -> str:
    partes = []
    if "tri" in n:
        a, m, b = n["tri"]
        partes.append(f"Duración triangular {num(a, 3)} / {num(m, 3)} / {num(b, 3)} h [S-43]" + (" por PC" if n.get("por_pc") else ""))
    if "calculo" in n:
        partes.append(f"Duración calculada en gestion/e4/procesos.py ({n['calculo']}" + (f" × {n['factor']}" if n.get("factor") else "") + ")")
    if n.get("recurso"):
        partes.append(f"Recurso: {carriles[n['recurso']]}")
    if n.get("req"):
        partes.append("Requisitos: " + ", ".join(n["req"]))
    return ". ".join(partes)


class Diagrama:
    def __init__(self, pid: str, p: dict, meta: dict, problemas: dict):
        self.pid, self.p, self.meta, self.problemas = pid, p, meta, problemas
        self.nodos = {n["id"]: n for n in p["nodos"]}
        self.flujos = [{"de": f[0], "a": f[1]} if isinstance(f, list) else dict(f) for f in p["flujos"]]
        for k, f in enumerate(self.flujos):
            f["id"] = f"Flujo_{k + 1}"
        self.colores = est.bpmn_colores()
        self._geometria()

    # ------------------------------------------------------------------ geometría
    def _geometria(self):
        filas = {c: 1 + max((n.get("fila", 0) for n in self.p["nodos"] if n["carril"] == c), default=0) for c in self.p["carriles"]}
        # El pool «Internet / ISP» va del lado más cercano a las tareas que descargan (menos carriles cruzados).
        idx = [self.p["carriles"].index(self.nodos[m]["carril"]) for m in self.p.get("mensajes", [])]
        self.ext_arriba = bool(idx) and sum(idx) / len(idx) < (len(self.p["carriles"]) - 1) / 2
        self.y0 = EXT_H + EXT_SEP if self.ext_arriba else 0
        self.carril_y, y = {}, self.y0
        for c in self.p["carriles"]:
            alto = MARGEN_SUP + filas[c] * FILA_H + MARGEN_INF
            self.carril_y[c] = (y, alto)
            y += alto
        self.alto_pool = y - self.y0
        ncol = 1 + max(n["col"] for n in self.p["nodos"])
        self.ancho_pool = POOL_BANDA + CARRIL_BANDA + 40 + ncol * COL_W
        self.caja = {}
        for n in self.p["nodos"]:
            w, h = _tam(n["tipo"])
            y0, _ = self.carril_y[n["carril"]]
            cy = y0 + MARGEN_SUP + 58 + TAREA[1] / 2 + n.get("fila", 0) * FILA_H
            cx = X0 + POOL_BANDA + CARRIL_BANDA + 40 + n["col"] * COL_W + TAREA[0] / 2
            self.caja[n["id"]] = (cx - w / 2, cy - h / 2, w, h)
        self.ext_y = 0 if self.ext_arriba else self.alto_pool + EXT_SEP

    def _c(self, nid):
        x, y, w, h = self.caja[nid]
        return x + w / 2, y + h / 2

    def ruta(self, f: dict, k: int) -> list[tuple[float, float]]:
        sx, sy, sw, sh = self.caja[f["de"]]
        tx, ty, tw, th = self.caja[f["a"]]
        scx, scy = sx + sw / 2, sy + sh / 2
        tcx, tcy = tx + tw / 2, ty + th / 2
        modo = f.get("ruta") or ("abajo" if tx + tw / 2 < scx else None)
        if modo == "abajo":
            yc = max(sy + sh, ty + th) + 26 + 10 * (k % 3)
            return [(scx, sy + sh), (scx, yc), (tcx - 18, yc), (tcx - 18, ty + th)]
        if modo == "arriba":
            yc = min(sy, ty) - 30 - 12 * (k % 3)
            return [(scx, sy), (scx, yc), (tcx - 18, yc), (tcx - 18, ty)]
        if abs(scy - tcy) < 1:
            return [(sx + sw, scy), (tx, tcy)]
        if abs(scx - tcx) < 1:
            return [(scx, sy + sh), (tcx, ty)] if tcy > scy else [(scx, sy), (tcx, ty + th)]
        xm = sx + sw + (tx - (sx + sw)) / 2
        return [(sx + sw, scy), (xm, scy), (xm, tcy), (tx, tcy)]

    # ------------------------------------------------------------------ XML
    def xml(self) -> str:
        pid, p, cars = self.pid, self.p, self.meta["carriles"]
        proc, colab, ext = f"Proceso_{pid.replace('-', '_')}", f"Colaboracion_{pid.replace('-', '_')}", "Participante_Internet"
        L = [f'<?xml version="1.0" encoding="UTF-8"?>',
             '<bpmn:definitions ' + " ".join(f'xmlns:{k}="{v}"' for k, v in NS.items()) +
             f' id="Def_{pid.replace("-", "_")}" targetNamespace="https://celeris.test/ce01/e4/{pid}" '
             'exporter="Celeris gestion/e4/bpmn.py" exporterVersion="0.1">',
             f'  <bpmn:collaboration id="{colab}">',
             f'    <bpmn:participant id="Participante_Campus" name="{escape(self.meta["pool"])}" processRef="{proc}"/>',
             f'    <bpmn:participant id="{ext}" name="{escape(self.meta["pool_externo"])}"/>']
        for k, nid in enumerate(p.get("mensajes", [])):
            L.append(f'    <bpmn:messageFlow id="Mensaje_{k + 1}" name="Descarga" sourceRef="{nid}" targetRef="{ext}"/>')
        L += ['  </bpmn:collaboration>', f'  <bpmn:process id="{proc}" name="{escape(p["nombre"])}" isExecutable="false">',
              '    <bpmn:laneSet id="Carriles">']
        for c in p["carriles"]:
            L.append(f'      <bpmn:lane id="Carril_{c}" name="{escape(cars[c])}">')
            L += [f'        <bpmn:flowNodeRef>{n["id"]}</bpmn:flowNodeRef>' for n in p["nodos"] if n["carril"] == c]
            L.append('      </bpmn:lane>')
        L.append('    </bpmn:laneSet>')
        for n in p["nodos"]:
            el = ELEMENTO[n["tipo"]]
            L.append(f'    <bpmn:{el} id="{n["id"]}" name="{escape(n["nombre"])}">')
            doc = _doc(n, cars)
            if doc:
                L.append(f'      <bpmn:documentation>{escape(doc)}</bpmn:documentation>')
            L += [f'      <bpmn:incoming>{f["id"]}</bpmn:incoming>' for f in self.flujos if f["a"] == n["id"]]
            L += [f'      <bpmn:outgoing>{f["id"]}</bpmn:outgoing>' for f in self.flujos if f["de"] == n["id"]]
            if n["tipo"] in ("inicio_temporizador", "temporizador"):
                L.append(f'      <bpmn:timerEventDefinition id="Temp_{n["id"]}">')
                if "tri" in n:
                    L.append(f'        <bpmn:timeDuration xsi:type="bpmn:tFormalExpression">{_iso_h(n["tri"][1])}</bpmn:timeDuration>')
                L.append('      </bpmn:timerEventDefinition>')
            L.append(f'    </bpmn:{el}>')
        for f in self.flujos:
            nombre = f' name="{escape(f["nombre"])}"' if f.get("nombre") else ""
            L.append(f'    <bpmn:sequenceFlow id="{f["id"]}"{nombre} sourceRef="{f["de"]}" targetRef="{f["a"]}"/>')
        anot = [n for n in p["nodos"] if n.get("pd")]
        for n in anot:
            pr = self.problemas[n["pd"]]
            L.append(f'    <bpmn:textAnnotation id="Anot_{n["pd"].replace("-", "_")}">'
                     f'<bpmn:text>{escape(n["pd"] + ": " + pr["problema"])}</bpmn:text></bpmn:textAnnotation>')
            L.append(f'    <bpmn:association id="Asoc_{n["pd"].replace("-", "_")}" sourceRef="Anot_{n["pd"].replace("-", "_")}" '
                     f'targetRef="{n["id"]}" associationDirection="None"/>')
        L.append('  </bpmn:process>')
        L += self._di(colab, ext, anot)
        L.append('</bpmn:definitions>')
        return "\n".join(L) + "\n"

    def _col(self, clave: str) -> str:
        c = self.colores[clave]
        return (f'bioc:fill="{c["fill"]}" bioc:stroke="{c["stroke"]}" '
                f'color:background-color="{c["fill"]}" color:border-color="{c["stroke"]}"')

    def _di(self, colab: str, ext: str, anot: list) -> list[str]:
        p = self.p
        L = ['  <bpmndi:BPMNDiagram id="Diagrama_1">', f'    <bpmndi:BPMNPlane id="Plano_1" bpmnElement="{colab}">',
             f'      <bpmndi:BPMNShape id="Participante_Campus_di" bpmnElement="Participante_Campus" isHorizontal="true" {self._col("pool")}>',
             f'        <dc:Bounds x="{X0}" y="{self.y0}" width="{self.ancho_pool}" height="{self.alto_pool}"/>',
             '      </bpmndi:BPMNShape>']
        for c in p["carriles"]:
            y, h = self.carril_y[c]
            clave = "celeris" if c == "celeris" else "carril"
            L += [f'      <bpmndi:BPMNShape id="Carril_{c}_di" bpmnElement="Carril_{c}" isHorizontal="true" {self._col(clave)}>',
                  f'        <dc:Bounds x="{X0 + POOL_BANDA}" y="{y}" width="{self.ancho_pool - POOL_BANDA}" height="{h}"/>',
                  '      </bpmndi:BPMNShape>']
        for n in p["nodos"]:
            x, y, w, h = self.caja[n["id"]]
            clave = "servicio" if n["tipo"] == "tarea_servicio" else "tarea" if n["tipo"].startswith("tarea") else \
                "evento" if n["tipo"] != "xor" else "tarea"
            marcador = ' isMarkerVisible="true"' if n["tipo"] == "xor" else ""
            L += [f'      <bpmndi:BPMNShape id="{n["id"]}_di" bpmnElement="{n["id"]}"{marcador} {self._col(clave)}>',
                  f'        <dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w}" height="{h}"/>']
            if not n["tipo"].startswith("tarea"):
                # Compuertas: etiqueta arriba a la izquierda, fuera de la entrada (izquierda) y de las salidas (arriba/abajo/derecha).
                lx, ly = (x - 112, y - 42) if n["tipo"] == "xor" else (x + w / 2 - 60, y + h + 4)
                L += ['        <bpmndi:BPMNLabel>',
                      f'          <dc:Bounds x="{lx:.0f}" y="{ly:.0f}" width="120" height="40"/>',
                      '        </bpmndi:BPMNLabel>']
            L.append('      </bpmndi:BPMNShape>')
        for k, f in enumerate(self.flujos):
            pts = self.ruta(f, k)
            L.append(f'      <bpmndi:BPMNEdge id="{f["id"]}_di" bpmnElement="{f["id"]}">')
            L += [f'        <di:waypoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in pts]
            if f.get("nombre"):
                # Etiqueta junto al primer tramo vertical (si lo hay) para no confundir las salidas de una compuerta.
                i = 1 if len(pts) == 4 and f.get("ruta") is None else 0
                (x1, y1), (x2, y2) = pts[i], pts[i + 1]
                vertical = abs(x1 - x2) < 1
                lx, ly = ((x1 + 6, (y1 + y2) / 2 - 7) if vertical else (x1 + 4, y1 - 18))
                L += ['        <bpmndi:BPMNLabel>',
                      f'          <dc:Bounds x="{lx:.0f}" y="{ly:.0f}" width="80" height="14"/>',
                      '        </bpmndi:BPMNLabel>']
            L.append('      </bpmndi:BPMNEdge>')
        # Pool externo colapsado y flujos de mensaje
        L += [f'      <bpmndi:BPMNShape id="{ext}_di" bpmnElement="{ext}" isHorizontal="true" {self._col("pool")}>',
              f'        <dc:Bounds x="{X0}" y="{self.ext_y}" width="{self.ancho_pool}" height="{EXT_H}"/>',
              '      </bpmndi:BPMNShape>']
        for k, nid in enumerate(p.get("mensajes", [])):
            x, y, w, h = self.caja[nid]
            xm = x + w / 2 + 22
            L += [f'      <bpmndi:BPMNEdge id="Mensaje_{k + 1}_di" bpmnElement="Mensaje_{k + 1}">',
                  *((f'        <di:waypoint x="{xm:.0f}" y="{y:.0f}"/>', f'        <di:waypoint x="{xm:.0f}" y="{EXT_H}"/>')
                    if self.ext_arriba else
                    (f'        <di:waypoint x="{xm:.0f}" y="{y + h:.0f}"/>', f'        <di:waypoint x="{xm:.0f}" y="{self.ext_y}"/>')),
                  '      </bpmndi:BPMNEdge>']
        # Anotaciones PD-xx: encima del nodo, en la franja libre de su fila
        for n in anot:
            x, y, w, h = self.caja[n["id"]]
            a = n["pd"].replace("-", "_")
            ax, ay, aw, ah = x + w / 2 - 70, y - 62 if n["tipo"].startswith("tarea") else y - 76, 150, 48
            L += [f'      <bpmndi:BPMNShape id="Anot_{a}_di" bpmnElement="Anot_{a}" {self._col("dolor")}>',
                  f'        <dc:Bounds x="{ax:.0f}" y="{ay:.0f}" width="{aw}" height="{ah}"/>', '      </bpmndi:BPMNShape>',
                  f'      <bpmndi:BPMNEdge id="Asoc_{a}_di" bpmnElement="Asoc_{a}" bioc:stroke="{self.colores["dolor"]["stroke"]}" '
                  f'color:border-color="{self.colores["dolor"]["stroke"]}">',
                  f'        <di:waypoint x="{x + w / 2:.0f}" y="{ay + ah:.0f}"/>', f'        <di:waypoint x="{x + w / 2:.0f}" y="{y:.0f}"/>',
                  '      </bpmndi:BPMNEdge>']
        L += ['    </bpmndi:BPMNPlane>', '  </bpmndi:BPMNDiagram>']
        return L


# ==================================================================================================
# Validación
# ==================================================================================================
_ESQUEMA = None


def esquema() -> etree.XMLSchema:
    global _ESQUEMA
    if _ESQUEMA is None:
        if not XSD.exists():
            raise BpmnError(f"Falta el XSD de OMG en {XSD} (README de gestion/e4, paso 0)")
        _ESQUEMA = etree.XMLSchema(etree.parse(str(XSD)))
    return _ESQUEMA


def validar(texto: str, pd_esperados: set[str]) -> list[str]:
    err = []
    doc = etree.fromstring(texto.encode("utf-8"))
    xs = esquema()
    if not xs.validate(etree.ElementTree(doc)):
        err += [f"XSD: {e.message} (línea {e.line})" for e in xs.error_log]
    b = "{%s}" % NS["bpmn"]
    ids_nodos = {e.get("id") for e in doc.iter() if e.tag.startswith(b) and e.getparent() is not None
                 and e.getparent().tag == f"{b}process" and e.tag not in (f"{b}sequenceFlow", f"{b}laneSet",
                                                                           f"{b}textAnnotation", f"{b}association")}
    for f in doc.iter(f"{b}sequenceFlow"):
        if f.get("sourceRef") not in ids_nodos or f.get("targetRef") not in ids_nodos:
            err.append(f"flujo {f.get('id')} une nodos que no son del proceso")
    con_forma = {e.get("bpmnElement") for e in doc.iter("{%s}BPMNShape" % NS["bpmndi"])}
    con_borde = {e.get("bpmnElement") for e in doc.iter("{%s}BPMNEdge" % NS["bpmndi"])}
    for i in ids_nodos - con_forma:
        err.append(f"el nodo {i} no tiene forma en el diagrama")
    for f in doc.iter(f"{b}sequenceFlow"):
        if f.get("id") not in con_borde:
            err.append(f"el flujo {f.get('id')} no tiene trazo en el diagrama")
    textos = " ".join(t.text or "" for t in doc.iter(f"{b}text"))
    for pd in pd_esperados:
        if f"{pd}:" not in textos:
            err.append(f"falta la anotación {pd}")
    return err


def escribir_todo(sim: dict, car: dict) -> list[Path]:
    SALIDA.mkdir(parents=True, exist_ok=True)
    problemas = {p["id"]: p for p in car["problemas"]}
    rutas, errores = [], []
    for pid, p in sim["procesos"].items():
        texto = Diagrama(pid, p, sim["meta"], problemas).xml()
        esperados = {x["id"] for x in car["problemas"] if x["diagrama"] == pid}
        e = validar(texto, esperados)
        if e:
            errores += [f"{pid}: {x}" for x in e]
            continue
        ruta = SALIDA / f"{pid}.bpmn"
        ruta.write_text(texto, encoding="utf-8")
        rutas.append(ruta)
    if errores:
        raise BpmnError("; ".join(errores[:12]))
    return rutas


def main() -> int:
    car = yaml.safe_load((AQUI / "datos" / "procesos.yaml").read_text(encoding="utf-8"))
    sim = yaml.safe_load((AQUI / "simulacion.yaml").read_text(encoding="utf-8"))
    try:
        for r in escribir_todo(sim, car):
            print(f"{r.relative_to(AQUI.parents[1]).as_posix()} válido")
    except BpmnError as e:
        print(f"ERROR {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
