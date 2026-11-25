"""Figuras del Entregable 1 de CE01 (make figuras-ce01).

    python gestion/e1/figuras/generar.py

Escribe en gestion/e1/figuras/:
  - matplotlib (PNG 200 dpi): Mendelow, radar COBIT, brechas, impacto × frecuencia, roadmap, mapa de calor de RE-xx;
  - draw.io (.drawio + PNG con draw.io Desktop): organigrama, cadena de valor, Ishikawa, árbol de problemas, mapa
    estratégico;
  - ArchiMate: llama a gestion/e1/archimate/generar.py (XML de intercambio y, si Archi está instalado, la vista PNG);
  - figuras.yaml: el registro que lee el generador del informe (título, fuente, orientación).

Todo sale de gestion/e1/datos/*.yaml, gestion/ce01.yaml e infra/*.yaml; los colores, de gestion/estilo_ce01.py (CI-100).
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import subprocess
import sys
from collections import defaultdict
from html import escape
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
E1 = AQUI.parent
GESTION = E1.parent
sys.path.insert(0, str(GESTION))
sys.path.insert(0, str(E1))
sys.path.insert(0, str(GESTION.parent / "infra" / "gen"))
import calculos  # noqa: E402
import ce01_datos as cd  # noqa: E402
import estilo_ce01 as est  # noqa: E402

D = yaml.safe_load((E1 / "datos" / "diagnostico.yaml").read_text(encoding="utf-8"))
M = yaml.safe_load((E1 / "datos" / "madurez.yaml").read_text(encoding="utf-8"))
C = est.color
PROPIA = "Elaboración propia"

# id → (archivo, título, fuente, horizontal)
FIGURAS = {
    "fig-organigrama": ("organigrama.png", "Organigrama del campus y áreas que toca Celeris",
                        f"{PROPIA} a partir de la guía CE01 v0.4 B1.2; dependencias por confirmar con la DTI", True),
    "fig-cadena-valor": ("cadena-valor.png", "Cadena de valor de la universidad y dependencia de los laboratorios",
                         f"{PROPIA}, adaptado de Porter [1]", True),
    "fig-mendelow": ("mendelow.png", "Matriz poder × interés de los stakeholders",
                     f"{PROPIA}, adaptado de Mendelow [3]; niveles: valoración del equipo", False),
    "fig-mapa-estrategico": ("mapa-estrategico.png", "Mapa estratégico de Celeris Edge en cuatro perspectivas",
                             f"{PROPIA}, adaptado de Kaplan y Norton [4]; objetivos OB-x de infra/trazabilidad.yaml", True),
    "fig-radar-cobit": ("radar-cobit.png", "Nivel de capacidad COBIT 2019 objetivo y actual",
                        f"{PROPIA} con la escala de capacidad de COBIT 2019 [5]; gestion/e1/datos/madurez.yaml", False),
    "fig-brechas": ("brechas.png", "Brechas cuantificadas entre la situación actual y la meta",
                    f"{PROPIA}; supuestos S-02, S-26 y S-27, metas OB-x de infra/trazabilidad.yaml", True),
    "fig-impacto-frecuencia": ("impacto-frecuencia.png", "Problemas operativos asociados a TI: impacto × frecuencia",
                               f"{PROPIA}; valoración del equipo, a confirmar con datos de la DTI", False),
    "fig-ishikawa": ("ishikawa.png", "Diagrama de Ishikawa del problema de las descargas repetidas",
                     f"{PROPIA} a partir de 00 M2.2 y la guía CE01 v0.4 B1.5", True),
    "fig-arbol": ("arbol-problemas.png", "Árbol de problemas: causas, problema central y efectos",
                  f"{PROPIA} a partir de 00 M2.1 y M2.2", True),
    "fig-motivacion": ("motivacion-archi.png", "Vista de motivación ArchiMate 3.2: de la estrategia al componente",
                       f"{PROPIA} en Archi 5.12 [6]; gestion/e1/archimate/celeris-motivacion.xml", True),
    "fig-roadmap": ("roadmap.png", "Roadmap de tecnología de Celeris Edge en tres horizontes",
                    f"{PROPIA} a partir de la guía CE01 v0.4 B1.7 y 00 M9", True),
    "fig-mapa-calor": ("mapa-calor.png", "Mapa de calor de los riesgos estratégicos RE-01…RE-12",
                       f"{PROPIA}; P e I de gestion/ce01.yaml (guía CE01 v0.4 B1.8)", False),
}


# ==================================================================================================
# matplotlib
# ==================================================================================================
plt = est.configurar_matplotlib()


def _png(fid):
    return AQUI / FIGURAS[fid][0]


def mendelow():
    niveles = ["Bajo", "Medio", "Alto"]
    estrategias = ["Gestionar de cerca", "Mantener satisfecha", "Mantener informados", "Consultar", "Monitorear"]
    col = {e: est.serie(i) for i, e in enumerate(estrategias)}
    col["Mantener informados"] = C("azul_claro")
    col["Monitorear"] = C("gris_medio")
    celdas = defaultdict(list)
    for s_ in D["stakeholders"]["lista"]:
        celdas[(niveles.index(s_["interes"]), niveles.index(s_["poder"]))].append(s_)
    fig, ax = plt.subplots(figsize=est.tamano(False, 12.5))
    ax.grid(False)
    for i in range(4):
        ax.axhline(i, color=C("gris_claro"), lw=1)
        ax.axvline(i, color=C("gris_claro"), lw=1)
    for (x, y), lista in celdas.items():
        for k, s_ in enumerate(lista):
            yy = y + 0.78 - k * 0.27
            ax.scatter([x + 0.1], [yy], s=70, color=col[s_["estrategia"]], edgecolor=C("azul_upeu"), lw=0.6, zorder=3)
            ax.text(x + 0.18, yy, f"{s_['nombre']}\n{s_['estrategia']}", va="center", fontsize=7.6, color=C("gris_texto"))
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_xticks([0.5, 1.5, 2.5], [f"Interés {n.lower()}" for n in niveles])
    ax.set_yticks([0.5, 1.5, 2.5], [f"Poder {n.lower()}" for n in niveles])
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlabel("Interés en el proyecto")
    ax.set_ylabel("Poder sobre el proyecto")
    est.guardar(fig, _png("fig-mendelow"))


def radar():
    obj = M["objetivos"]
    n = len(obj)
    import numpy as np
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=est.tamano(False, 11), subplot_kw={"polar": True})
    meta = [o["objetivo"] for o in obj] + [obj[0]["objetivo"]]
    ax.plot(ang, meta, color=C("azul_upeu"), lw=2, label="Objetivo al cierre del piloto")
    ax.fill(ang, meta, color=C("azul_upeu"), alpha=0.12)
    medido = all(o["actual"] is not None for o in obj)
    if medido:
        act = [o["actual"] for o in obj] + [obj[0]["actual"]]
        ax.plot(ang, act, color=C("ambar_upeu"), lw=2, label="Actual (entrevista)")
        ax.fill(ang, act, color=C("ambar_upeu"), alpha=0.25)
    ax.set_xticks(ang[:-1], [f"{o['id']}\nobjetivo {o['objetivo']} · actual "
                             f"{o['actual'] if o['actual'] is not None else 'pendiente'}" for o in obj], fontsize=8)
    ax.set_ylim(0, 5)
    ax.set_yticks(range(0, 6), [str(i) for i in range(6)], fontsize=7, color=C("gris_medio"))
    ax.set_rlabel_position(90)
    if not medido:
        ax.text(0, 0, "ACTUAL:\nPENDIENTE DE\nENTREVISTA", ha="center", va="center", fontsize=8.5, weight="bold",
                color=C("ambar_upeu"), bbox=dict(boxstyle="round", fc=C("blanco"), ec=C("ambar_upeu")))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8)
    est.guardar(fig, _png("fig-radar-cobit"))


def brechas():
    c = calculos.calcular()
    m = c["metas"]
    fig, axs = plt.subplots(1, 4, figsize=est.tamano(True, 9.5))
    paneles = [
        ("GB que cruzan el enlace\npor laboratorio y ciclo", ["Hoy (40 copias)", "Con caché (1 copia)"],
         [c["gb_ciclo_lab"], c["gb_pc"]], lambda v: f"{cd.num(v)} GB"),
        ("Minutos de descarga para dejar\nlisto un laboratorio (cota inferior)", ["Hoy", f"Meta OB-2 (−{cd.pct(m['OB-2'])})"],
         [c["horas_lab"] * 60, c["horas_lab_meta"] * 60], lambda v: f"{cd.num(v)} min"),
        ("PCs con aviso antes\nde instalar la CA", ["Hoy", "Meta OB-4"], [0, m["OB-4"] * 100], lambda v: f"{cd.num(v)} %"),
    ]
    for ax, (tit, etiquetas, valores, fmt) in zip(axs, paneles):
        barras = ax.bar(etiquetas, valores, color=[C("azul_upeu"), C("ambar_upeu")], width=0.6)
        est.etiquetar_barras(ax, barras, fmt)
        ax.set_title(tit, fontsize=9.5)
        ax.set_ylim(0, max(valores) * 1.25 or 1)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(axis="x", visible=False)
    ax = axs[3]
    ids = [o["id"] for o in M["objetivos"]]
    obj = [o["objetivo"] for o in M["objetivos"]]
    barras = ax.barh(ids, obj, color=C("azul_upeu"), height=0.55, label="Objetivo")
    est.etiquetar_barras(ax, barras, lambda v: f"obj. {v:g}", horizontal=True)
    for i, o in enumerate(M["objetivos"]):
        if o["actual"] is None:
            ax.text(0.1, i, "actual: pendiente", va="center", fontsize=7.5, color=C("blanco"))
        else:
            ax.barh(i, o["actual"], color=C("ambar_upeu"), height=0.3)
    ax.set_xlim(0, 5)
    ax.invert_yaxis()
    ax.set_title("Brecha COBIT 2019\n(objetivo − actual)", fontsize=9.5)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    est.guardar(fig, _png("fig-brechas"))


def _matriz_5x5(ax, puntos, xlabel, ylabel):
    for i in range(1, 6):
        for p in range(1, 6):
            fondo, nivel, _ = est.nivel_riesgo(i * p)
            ax.add_patch(plt.Rectangle((i - 0.5, p - 0.5), 1, 1, facecolor=fondo, alpha=0.35, edgecolor=C("blanco"), lw=1.5))
            ax.text(i - 0.44, p + 0.44, nivel, ha="left", va="top", fontsize=5.5, color=C("gris_medio"))
            ax.text(i + 0.44, p - 0.44, f"{i * p}", ha="right", va="bottom", fontsize=6, color=C("gris_medio"))
    for (x, y), ids in puntos.items():
        ax.text(x, y - 0.02, "\n".join(ids), ha="center", va="center", fontsize=7.5 if len(ids) > 2 else 8.5,
                weight="bold", color=C("gris_texto"), linespacing=1.05)
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_xticks(range(1, 6))
    ax.set_yticks(range(1, 6))
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(False)
    ax.set_aspect("equal")
    import matplotlib.patches as mp
    niv = sorted(cd.estilo()["semaforo_riesgo"].values(), key=lambda n: -n["umbral_min"])
    rangos = [f"≥ {niv[0]['umbral_min']}"] + [f"{n['umbral_min']}–{niv[k]['umbral_min'] - 1}" for k, n in enumerate(niv[1:])]
    rangos[-1] = f"≤ {niv[-2]['umbral_min'] - 1}"
    ax.legend(handles=[mp.Patch(color=n["color"], alpha=0.6, label=f"{n['texto']} (puntaje {r})") for n, r in zip(niv, rangos)],
              loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, fontsize=8)


def impacto_frecuencia():
    puntos = defaultdict(list)
    for p in D["problemas"]["lista"]:
        puntos[(p["frecuencia"], p["impacto"])].append(p["id"])
    fig, ax = plt.subplots(figsize=est.tamano(False, 11))
    _matriz_5x5(ax, puntos, "Frecuencia (1 = rara vez, 5 = cada clase)", "Impacto (1 = leve, 5 = crítico)")
    est.guardar(fig, _png("fig-impacto-frecuencia"))


def mapa_calor():
    puntos = defaultdict(list)
    for r in cd.cargar()["riesgos_estrategicos"]["lista"]:
        puntos[(r["p"], r["i"])].append(r["id"])
    fig, ax = plt.subplots(figsize=est.tamano(False, 11))
    _matriz_5x5(ax, puntos, "Probabilidad (1–5)", "Impacto (1–5)")
    est.guardar(fig, _png("fig-mapa-calor"))


def roadmap():
    import matplotlib.dates as md
    colores = {"H1": C("azul_upeu"), "H2": C("ambar_upeu"), "H3": C("azul_claro")}
    filas = []
    for h in D["roadmap"]["horizontes"]:
        for t in h["tareas"]:
            ini = dt.date.fromisoformat(t["inicio"])
            filas.append((h["id"], h["nombre"], t["nombre"], ini, ini + dt.timedelta(days=t["dias"])))
    fig, ax = plt.subplots(figsize=est.tamano(True, 9))
    for k, (hid, hnom, tnom, ini, fin) in enumerate(filas):
        ax.barh(k, (fin - ini).days, left=md.date2num(ini), color=colores[hid], height=0.55)
        ax.text(md.date2num(fin) + 4, k, f"{hid} · {tnom}", va="center", fontsize=8, color=C("gris_texto"))
    for j, h in enumerate(D["roadmap"]["hitos"]):
        f = md.date2num(dt.date.fromisoformat(h["fecha"]))
        y = len(filas) - 0.2 + j * 0.5
        ax.scatter([f], [y], marker="D", s=40, color=C("azul_medio"), zorder=3)
        ax.text(f + 6, y, f"Hito: {h['nombre']} ({h['fecha']})", va="center", fontsize=7.5, color=C("azul_medio"))
    hoy = md.date2num(dt.date.fromisoformat(cd.cargar()["meta"]["fecha"]))
    ax.axvline(hoy, color=C("gris_medio"), ls="--", lw=1)
    ax.text(hoy, -0.8, "Fecha del informe", fontsize=7.5, color=C("gris_medio"), ha="center")
    ax.set_yticks([])
    ax.set_ylim(-1.1, len(filas) + 1.3)
    ax.invert_yaxis()
    ax.xaxis.set_major_locator(md.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(md.DateFormatter("%Y-%m"))
    ax.set_xlim(md.date2num(dt.date(2026, 11, 1)), md.date2num(dt.date(2028, 9, 30)))
    ax.grid(axis="y", visible=False)
    import matplotlib.patches as mp
    ax.legend(handles=[mp.Patch(color=colores[h["id"]], label=h["nombre"]) for h in D["roadmap"]["horizontes"]],
              loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=3, fontsize=8)
    est.guardar(fig, _png("fig-roadmap"))


# ==================================================================================================
# draw.io
# ==================================================================================================
class Lienzo:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.celdas: list[str] = []
        self.n = 0

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def caja(self, texto, x, y, w, h, relleno="blanco", borde="azul_upeu", grosor=1, extra="", cid=None):
        cid = cid or self._id()
        self.celdas.append(f'<mxCell id="{cid}" value="{escape(texto)}" style="{est.drawio(relleno, borde, grosor, extra)}" '
                           f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def texto(self, texto, x, y, w, h, tam=12, color="gris_texto", extra=""):
        cid = self._id()
        estilo = (f"text;html=1;whiteSpace=wrap;fontFamily={est.fuentes()[0]};fontSize={tam};fontColor={C(color)};"
                  f"strokeColor=none;fillColor=none;{extra}")
        self.celdas.append(f'<mxCell id="{cid}" value="{escape(texto)}" style="{estilo}" vertex="1" parent="1">'
                           f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def flecha(self, o, d, color="gris_medio", grosor=1.5, extra="", puntos=None):
        cid = self._id()
        estilo = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeColor={C(color)};"
                  f"strokeWidth={grosor};{extra}")
        pts = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in (puntos or []))
        geo = (f'<mxGeometry relative="1" as="geometry"><Array as="points">{pts}</Array></mxGeometry>' if pts
               else '<mxGeometry relative="1" as="geometry"/>')
        self.celdas.append(f'<mxCell id="{cid}" style="{estilo}" edge="1" parent="1" source="{o}" target="{d}">{geo}</mxCell>')
        return cid

    def linea(self, x1, y1, x2, y2, color="azul_upeu", grosor=2, flecha=False):
        cid = self._id()
        fin = "endArrow=block;endFill=1;" if flecha else "endArrow=none;"
        self.celdas.append(f'<mxCell id="{cid}" style="html=1;{fin}strokeColor={C(color)};strokeWidth={grosor};" edge="1" parent="1">'
                           f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/>'
                           f'<mxPoint x="{x2}" y="{y2}" as="targetPoint"/></mxGeometry></mxCell>')

    def guardar(self) -> Path:
        xml = ('<mxfile host="Celeris CE01"><diagram id="d1" name="' + escape(self.nombre) + '">'
               '<mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
               'fold="1" page="0" pageScale="1" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
               + "".join(self.celdas) + '</root></mxGraphModel></diagram></mxfile>\n')
        ruta = AQUI / f"{self.nombre}.drawio"
        ruta.write_text(xml, encoding="utf-8")
        return ruta


def _b(t):     # negrita en el HTML de draw.io (el texto se escapa al guardar)
    return f"<b>{t}</b>"


def organigrama():
    lz = Lienzo("organigrama")
    uni = {u["id"]: u for u in D["organigrama"]["unidades"]}
    niveles = {"dir": 0, "fac": 1, "dti": 1, "odp": 1, "ep": 2, "inf": 2, "sop": 2, "sis": 2, "enc": 3}
    xs = {"dir": 520, "fac": 120, "dti": 520, "odp": 920, "ep": 120, "inf": 370, "sop": 600, "sis": 830, "enc": 600}
    W, H = 210, 78
    ids = {}
    for uid, u in uni.items():
        y = 20 + niveles[uid] * 130
        if u.get("toca"):
            txt = f"{_b(u['nombre'])}<br>TOCA CELERIS: {u.get('rol', '')}"
            extra = "dashed=1;" if u.get("dudoso") else ""
            if u.get("dudoso"):
                txt += "<br><i>[levantar con la DTI]</i>"
            ids[uid] = lz.caja(txt, xs[uid] - W / 2, y, W, H + (14 if u.get("dudoso") else 0), "ambar_claro", "ambar_upeu", 3, extra)
        else:
            ids[uid] = lz.caja(_b(u["nombre"]), xs[uid] - W / 2, y, W, H, "blanco", "azul_upeu", 1)
    for uid, u in uni.items():
        if u["padre"]:
            lz.flecha(ids[u["padre"]], ids[uid], "azul_upeu", 1.5, "endArrow=none;exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    lz.caja(f"{_b('Leyenda')}<br>Relleno ámbar y borde grueso = área que toca Celeris (con su rol)<br>"
            "Borde discontinuo = dependencia por confirmar con la DTI", 760, 420, 330, 80, "blanco", "gris_medio", 1,
            "align=left;spacingLeft=8;")
    return lz.guardar()


def cadena_valor():
    lz = Lienzo("cadena-valor")
    acts = D["cadena_valor"]["actividades"]
    estilo = {"Alta": ("ambar_upeu", "ambar_upeu", 3), "Media": ("ambar_claro", "ambar_upeu", 2),
              "Baja": ("azul_muy_claro", "azul_medio", 1)}
    apoyo = [a for a in acts if a["tipo"] == "Apoyo"]
    prim = [a for a in acts if a["tipo"] == "Primaria"]
    lz.texto(_b("ACTIVIDADES DE APOYO"), 20, 10, 300, 24, 13, "azul_upeu")
    for k, a in enumerate(apoyo):
        r, b, g = estilo[a["dependencia"]]
        lz.caja(f"{_b(a['actividad'])} — DEPENDENCIA DE LOS LABORATORIOS: {a['dependencia'].upper()}<br>{a['por_que']}",
                20, 40 + k * 78, 900, 66, r, b, g, "align=left;spacingLeft=10;")
    lz.texto(_b("ACTIVIDADES PRIMARIAS"), 20, 210, 300, 24, 13, "azul_upeu")
    for k, a in enumerate(prim):
        r, b, g = estilo[a["dependencia"]]
        lz.caja(f"{_b(a['actividad'])}<br>DEPENDENCIA: {a['dependencia'].upper()}<br><br>{a['por_que']}",
                20 + k * 305, 240, 290, 150, r, b, g, "shape=step;perimeter=stepPerimeter;fixedSize=1;size=24;"
                "align=center;spacingLeft=26;spacingRight=20;")
    lz.caja(f"{_b('VALOR')}<br>Formación con laboratorios listos a tiempo", 935, 40, 165, 350, "azul_upeu", "azul_upeu", 1,
            "shape=step;perimeter=stepPerimeter;fixedSize=1;size=24;spacingLeft=28;spacingRight=18;")
    lz.caja(f"{_b('Leyenda')}: ámbar intenso y borde de 3 px = dependencia ALTA; ámbar claro y 2 px = MEDIA; "
            "azul claro y 1 px = BAJA", 20, 405, 1070, 34, "blanco", "gris_medio", 1)
    return lz.guardar()


def ishikawa():
    lz = Lienzo("ishikawa")
    cats = D["ishikawa"]["categorias"]
    espina_y, x0, x1 = 270, 20, 1080
    lz.linea(x0, espina_y, x1, espina_y, "azul_upeu", 4, flecha=True)
    lz.caja(_b(D["ishikawa"]["efecto"]), x1 + 5, espina_y - 70, 220, 140, "azul_upeu", "azul_upeu", 2)
    for k, cat in enumerate(cats):
        arriba = k < 3
        col = k % 3
        xh = 150 + col * 330                      # cabeza de la espina
        y_head = 10 if arriba else 490
        lz.caja(_b(cat["nombre"].upper()), xh - 85, y_head, 170, 40, "ambar_upeu", "ambar_upeu", 2)
        ya = y_head + 40 if arriba else y_head    # extremo de la espina junto a la cabeza
        xe, ye = xh + 130, espina_y               # extremo sobre la espina central
        lz.linea(xh, ya, xe, ye, "azul_medio", 2)
        n = len(cat["causas"])
        for m, causa in enumerate(cat["causas"]):
            f = (m + 1) / (n + 1)
            bx, by = xh + (xe - xh) * f, ya + (ye - ya) * f
            lz.linea(bx - 40, by, bx, by, "azul_medio", 1)
            lz.texto(f"• {causa}", bx - 300, by - 20, 258, 40, 11, "gris_texto", "align=right;verticalAlign=middle;")
    return lz.guardar()


def arbol():
    lz = Lienzo("arbol-problemas")
    a = D["arbol"]
    lz.texto(_b("EFECTOS"), 20, 10, 200, 24, 13, "azul_upeu")
    W = 200
    ef = [lz.caja(e, 20 + k * 220, 40, W, 70, "azul_muy_claro", "azul_medio", 1) for k, e in enumerate(a["efectos"])]
    lz.texto(_b("PROBLEMA CENTRAL"), 20, 150, 300, 24, 13, "azul_upeu")
    pc = lz.caja(_b(a["problema"]), 240, 180, 640, 80, "azul_upeu", "azul_upeu", 3)
    lz.texto(_b("CAUSAS"), 20, 300, 200, 24, 13, "azul_upeu")
    ca = [lz.caja(c, 20 + k * 275, 330, 255, 80, "ambar_claro", "ambar_upeu", 2) for k, c in enumerate(a["causas"])]
    for k, c in enumerate(ca):
        lz.flecha(c, pc, "gris_medio", 1.5, f"exitX=0.5;exitY=0;entryX={(k + 0.5) / len(ca):.3f};entryY=1;")
    for k, e in enumerate(ef):
        lz.flecha(pc, e, "gris_medio", 1.5, f"exitX={(k + 0.5) / len(ef):.3f};exitY=0;entryX=0.5;entryY=1;")
    return lz.guardar()


def mapa_estrategico():
    lz = Lienzo("mapa-estrategico")
    persp = D["mapa_estrategico"]["perspectivas"]
    ids = {}
    BAND_H, X0, W_LBL = 120, 20, 170
    lz.caja(f"{_b('Objetivos estratégicos de la UPeU que el proyecto afecta')}<br>"
            "OE-a infraestructura para la enseñanza · OE-b calidad académica · OE-c gestión eficiente · OE-d seguridad y "
            "cumplimiento <i>[confirmar con el plan estratégico]</i>", X0, 10, 1080, 56, "azul_upeu", "azul_upeu", 1)
    for k, p in enumerate(persp):
        y = 80 + k * (BAND_H + 10)
        lz.caja(_b(p["nombre"]), X0, y, W_LBL, BAND_H, "azul_muy_claro", "azul_medio", 1)
        lz.caja("", X0 + W_LBL, y, 1080 - W_LBL, BAND_H, "blanco", "azul_muy_claro", 1)
        n = len(p["objetivos"])
        ancho = (1080 - W_LBL - 20) / n
        for j, o in enumerate(p["objetivos"]):
            ids[o["id"]] = lz.caja(f"{o['texto']}<br>{_b(o['ob'])}", X0 + W_LBL + 10 + j * ancho + 10, y + 25,
                                   ancho - 20, BAND_H - 50, "ambar_claro", "ambar_upeu", 2, "arcSize=40;")
    banda = {o["id"]: k for k, p in enumerate(persp) for o in p["objetivos"]}
    for o, d in D["mapa_estrategico"]["enlaces"]:
        if abs(banda[o] - banda[d]) >= 2:     # salta una perspectiva: rodea por la izquierda para no cruzar cajas
            yo = 80 + banda[o] * (BAND_H + 10) + BAND_H / 2
            yd = 80 + banda[d] * (BAND_H + 10) + BAND_H / 2
            lz.flecha(ids[o], ids[d], "azul_medio", 1.5, "exitX=0;exitY=0.5;entryX=0;entryY=0.5;",
                      puntos=[(X0 + W_LBL + 12, yo), (X0 + W_LBL + 12, yd)])
        else:
            lz.flecha(ids[o], ids[d], "azul_medio", 1.5, "edgeStyle=none;curved=0;")
    return lz.guardar()


def exportar(rutas: list[Path]) -> list[str]:
    spec = importlib.util.spec_from_file_location("exportar_drawio", GESTION.parent / "infra" / "gen" / "exportar_drawio.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    exe = mod.drawio()
    if not exe:
        return [f"draw.io Desktop no está instalado: no se exportó {r.name}" for r in rutas]
    errores = []
    for r in rutas:
        destino = r.with_suffix(".png")
        p = subprocess.run([exe, "-x", "-f", "png", "-s", f"{min(2.5, mod.escala_png(r)):g}", "-b", "12", "-o",
                            str(destino), str(r)], capture_output=True, text=True, timeout=180)
        if p.returncode != 0 or not destino.exists():
            errores.append(f"{r.name}: draw.io terminó con {p.returncode} {p.stderr[-200:]}")
    return errores


def registro():
    reg = {fid: {"archivo": a, "titulo": t, "fuente": f, "horizontal": h} for fid, (a, t, f, h) in FIGURAS.items()}
    (AQUI / "figuras.yaml").write_text(
        "# Registro de figuras del E1 (lo escribe gestion/e1/figuras/generar.py; no editar a mano).\n"
        + yaml.safe_dump(reg, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")


def main() -> int:
    calculos.main()                     # refresca gestion/e1/datos/e1.json (cifras del informe)
    for f in (mendelow, radar, brechas, impacto_frecuencia, mapa_calor, roadmap):
        f()
    errores = exportar([organigrama(), cadena_valor(), ishikawa(), arbol(), mapa_estrategico()])
    spec = importlib.util.spec_from_file_location("archimate_e1", E1 / "archimate" / "generar.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()
    registro()
    faltan = [a for a, *_ in FIGURAS.values() if not (AQUI / a).exists()]
    for e in errores + [f"falta {a}" for a in faltan]:
        print(f"  ERROR {e}")
    return 1 if errores or faltan else 0


if __name__ == "__main__":
    sys.exit(main())
