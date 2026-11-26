"""Figuras del Entregable 3 de CE01 (make figuras-ce01).

    python gestion/e3/figuras/generar.py

Escribe en gestion/e3/figuras/:
  - draw.io (.drawio + PNG con draw.io Desktop): EDT de tres niveles, procedimiento de control de cambios y tablero
    Kanban al iniciar el sprint 1;
  - matplotlib (PNG 200 dpi): Gantt de S1 y de S2 con la ruta crítica y los hitos (rombos), curva S con la línea base
    y el valor ganado, mapa de calor de los riesgos RP-01…RP-10 y burn-up planificado de la consola;
  - figuras.yaml: el registro que lee el generador del informe.

Si existe gestion/e3/figuras/gantt-msproject.png (exportado de MS Project, paso manual del README), el Gantt de S2 usa
esa imagen; si no, el de matplotlib. Las cifras salen de gestion/e3/datos/plan.json (gestion/e3/plan.py, que se ejecuta
primero); los colores, de gestion/estilo_ce01.py (CI-100).
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
E3 = AQUI.parent
GESTION = E3.parent
sys.path.insert(0, str(GESTION))
sys.path.insert(0, str(E3))
import ce01_datos as cd  # noqa: E402
import estilo_ce01 as est  # noqa: E402
import plan as P  # noqa: E402
from ce01_datos import num, usd  # noqa: E402

_spec = importlib.util.spec_from_file_location("figuras_e1", GESTION / "e1" / "figuras" / "generar.py")
g1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g1)

C = est.color
plt = est.configurar_matplotlib()
PROPIA = "Elaboración propia"
MSP = AQUI / "gantt-msproject.png"
AG = yaml.safe_load((E3 / "datos" / "agil.yaml").read_text(encoding="utf-8"))

FIGURAS = {
    "fig-edt": ("edt.png", "Estructura de desglose del trabajo (EDT) del proyecto Celeris Edge",
                f"{PROPIA}; paquetes de gestion/ce01.yaml → edt (guía CE01 v0.4 B3.3, ampliada con 5.4–5.6 en CI-103)", True),
    "fig-cambios": ("control-cambios.png", "Procedimiento de control integrado de cambios",
                    f"{PROPIA}, adaptado del control integrado de cambios del PMBOK [1]; gestion/e3/datos/gobierno.yaml", True),
    "fig-gantt-s1": ("gantt-s1.png", "Diagrama de Gantt de S1 con la ruta crítica y los hitos",
                     f"{PROPIA}; CPM de gestion/e3/plan.py sobre gestion/e3/datos/plan.yaml; fechas reales de los commits de main", True),
    "fig-gantt-s2": ("gantt-s2.png", "Diagrama de Gantt de S2 con la ruta crítica y los hitos",
                     f"{PROPIA}; CPM de gestion/e3/plan.py, verificado con Microsoft Project", True),
    "fig-curva-s": ("curva-s.png", "Curva S de la línea base, reservas y valor ganado a la fecha de corte",
                    f"{PROPIA}; gestion/e3/plan.py y entregables/CE01/E3/Presupuesto_EVM_E3.xlsx", True),
    "fig-riesgos": ("riesgos-proyecto.png", "Mapa de calor de los riesgos del proyecto RP-01…RP-10",
                    f"{PROPIA}; P e I de gestion/ce01.yaml → riesgos_proyecto (escala de la guía CE01 v0.4 B3.6)", False),
    "fig-kanban": ("kanban.png", "Tablero Kanban de la consola al iniciar el sprint 1 (planificado)",
                   f"{PROPIA}; backlog y límites WIP de gestion/e3/datos/agil.yaml", True),
    "fig-burnup": ("burnup.png", "Burn-up planificado de la consola por sprint",
                   f"{PROPIA}; puntos de historia de gestion/e3/datos/agil.yaml (estimación del equipo)", False),
}


def _png(fid):
    return AQUI / FIGURAS[fid][0]


def _u(x: float, dec: int = 0) -> str:
    return usd(x, dec).replace("$", r"\$")


def _modelo() -> dict:
    return json.loads((E3 / "datos" / "plan.json").read_text(encoding="utf-8"))["modelo"]


# ==================================================================================================
# draw.io
# ==================================================================================================
class Lienzo(g1.Lienzo):
    def guardar(self) -> Path:
        ruta_e1 = super().guardar()
        destino = AQUI / ruta_e1.name
        destino.write_text(ruta_e1.read_text(encoding="utf-8"), encoding="utf-8")
        ruta_e1.unlink()
        return destino


_b = g1._b


def edt(m):
    paq = cd.cargar()["edt"]["paquetes"]
    p_by = {p["id"]: p for p in paq}
    hechas, etapas = defaultdict(list), defaultdict(set)
    h1 = m["hitos"]["H1"]["fecha"]
    for f in m["filas"]:
        if f["paquete"]:
            hechas[f["paquete"]].append(f["hecha"])
            if not f["hecha"]:
                etapas[f["paquete"]].add("S1" if f["fin"] <= h1 else "S2")
    costo = m["presupuesto"]["paquetes"]
    s2 = {"5.4", "5.5", "5.6"}
    lz = Lienzo("edt")
    n1 = [p for p in paq if p["id"].count(".") == 0 and p["id"] != "0"]
    W, DX = 196, 214
    ancho = DX * len(n1) - (DX - W)
    raiz = lz.caja(_b(f"0 {p_by['0']['nombre']}") + f"<br>Línea base {usd(m['presupuesto']['linea_base'])}",
                   ancho / 2 - 160, 0, 320, 60, "azul_upeu", "azul_upeu", 3)
    for k, p in enumerate(n1):
        x = k * DX
        c1 = lz.caja(_b(f"{p['id']} {p['nombre']}"), x, 110, W, 52, "azul_medio", "azul_medio", 2)
        lz.flecha(raiz, c1, "azul_upeu", 1.5, "endArrow=none;exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
        hijos = [q for q in paq if q["id"].startswith(p["id"] + ".") and q["id"].count(".") == 1]
        for j, q in enumerate(hijos):
            y = 200 + j * 86
            fin = all(hechas[q["id"]]) and hechas[q["id"]]
            estado = "TERMINADO" if fin else " y ".join(sorted(etapas[q["id"]]))
            relleno, borde = ("azul_muy_claro", "azul_claro") if fin else ("ambar_claro", "ambar_upeu") if q["id"] in s2 \
                else ("blanco", "azul_upeu")
            txt = f"{_b(q['id'] + ' ' + q['nombre'])}<br>{usd(costo[q['id']]['total'])} · {estado}"
            c2 = lz.caja(txt, x + 18, y, W - 18, 66, relleno, borde, 1, "fontSize=11;")
            lz.flecha(c1, c2, "gris_medio", 1, "endArrow=none;edgeStyle=none;exitX=0.046;exitY=1;entryX=0;entryY=0.5;",
                      puntos=[(x + 9, y + 33)])
    yl = 200 + 6 * 86
    lz.texto("Nivel 0: proyecto · Nivel 1: áreas · Nivel 2: paquetes de trabajo con su costo (actividades en el diccionario). "
             "TERMINADO = todas sus actividades en main al corte; S1 / S2 = semestre de sus actividades pendientes; ámbar = paquetes nuevos de S2.",
             0, yl, ancho, 36, 11, "gris_texto")
    return lz.guardar()


def control_cambios():
    g = yaml.safe_load((E3 / "datos" / "gobierno.yaml").read_text(encoding="utf-8"))["cambios"]
    lz = Lienzo("control-cambios")
    W, DX = 200, 236
    cajas = []
    for k, p in enumerate(g["pasos"]):
        relleno, borde = ("azul_upeu", "azul_upeu") if p["paso"] == "Decisión" else ("blanco", "azul_upeu")
        cajas.append(lz.caja(f"{_b(str(p['n']) + '. ' + p['paso'])}<br><font style=\"font-size:10px\">{p['detalle']}</font>",
                             k * DX, 0, W, 130, relleno, borde, 2))
    for a, b in zip(cajas, cajas[1:]):
        lz.flecha(a, b, "azul_upeu", 2, "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    x0 = 2 * DX - 120
    lz.texto(_b("Quién aprueba según el impacto"), x0, 160, 440, 22, 12, "azul_upeu")
    for j, n in enumerate(g["nivel"]):
        relleno, borde, gros = [("blanco", "azul_claro", 1), ("azul_muy_claro", "azul_medio", 2), ("ambar_claro", "ambar_upeu", 3)][j]
        c = lz.caja(f"{_b(n['aprueba'])}: {n['cambio']}", x0, 190 + j * 62, 440, 52, relleno, borde, gros, "fontSize=11;align=left;spacingLeft=6;")
        if j == 0:
            lz.flecha(cajas[2], c, "gris_medio", 1.2, "dashed=1;exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    lz.texto("Rechazada: se cierra el issue con el motivo. Aprobada: nueva línea base en plan.yaml y en el XML de MS Project.",
             0, 390, 1150, 24, 11, "gris_texto")
    return lz.guardar()


def kanban(m):
    hs = {h["id"]: h for h in m["agil"]["historias"]}
    orden = [h["id"] for h in m["agil"]["historias"]]
    s1 = [h for h in orden if hs[h]["sprint"] == 1]
    listo = [h for h in orden if hs[h]["sprint"] == 2][:4]
    en_curso = [h for h in s1 if not set(hs[h].get("depende") or []) & set(s1)][:1]
    listo = [h for h in s1 if h not in en_curso] + listo
    col_wip = {c["nombre"]: c["wip"] for c in AG["kanban"]["columnas"]}
    wip_listo = col_wip["Listo (DoR)"]
    listo = listo[:wip_listo]
    usadas = set(en_curso) | set(listo)
    backlog = [h for h in orden if h not in usadas]
    contenido = {"Backlog": backlog, "Listo (DoR)": listo, "En curso": en_curso, "Revisión": [], "Terminado (DoD)": []}
    lz = Lienzo("kanban")
    W, DX = 214, 228
    for k, c in enumerate(AG["kanban"]["columnas"]):
        x = k * DX
        wip = f"WIP {c['wip']}" if c["wip"] else "sin límite WIP"
        lz.caja(f"{_b(c['nombre'])}<br><font style=\"font-size:10px\">{wip}</font>", x, 0, W, 46, "azul_upeu", "azul_upeu", 2)
        lz.caja("", x, 52, W, 560, "gris_claro", "gris_claro", 1, "rounded=0;")
        items = contenido[c["nombre"]]
        if not items:
            lz.texto("<i>vacía al iniciar el sprint 1</i>", x + 10, 70, W - 20, 24, 10, "gris_medio", "align=center;")
        alto = 54 if len(items) <= 9 else 40
        for j, hid in enumerate(items):
            h = hs[hid]
            sprint = f"sprint {h['sprint']}" if h["sprint"] else ("excluida" if h["moscow"] == "Won't" else "sin sprint")
            relleno, borde, gros = (("ambar_claro", "ambar_upeu", 2) if h["moscow"] == "Must" else
                                    ("blanco", "gris_medio", 1) if h["moscow"] == "Won't" else ("blanco", "azul_upeu", 1))
            dash = "dashed=1;" if h["moscow"] == "Won't" else ""
            txt = (f"{_b(hid)} · {h['moscow'].upper()} · {h['puntos']} pts<br>"
                   f"<font style=\"font-size:9px\">{h['req'][0]} · {sprint}</font>")
            lz.caja(txt, x + 8, 60 + j * (alto + 6), W - 16, alto, relleno, borde, gros, f"fontSize=10;{dash}")
    lz.texto("Tarjetas: MUST = borde ámbar grueso; SHOULD = borde azul; WON'T = discontinua. Orden de la columna Backlog = "
             "rango WSJF. En curso: una historia por integrante; Revisión: pull request revisado por el otro integrante.",
             0, 620, 5 * DX, 36, 11, "gris_texto")
    return lz.guardar()


# ==================================================================================================
# matplotlib
# ==================================================================================================
def _gantt(m, filas, fid, desde, hasta, titulo_corte=True):
    import matplotlib.dates as md
    import matplotlib.patches as mp
    cal = P.calendario()
    n = len(filas)
    fig, ax = plt.subplots(figsize=est.tamano(True, min(13.4, 2.2 + 0.42 * n)))
    pos = {}
    d = desde
    while d <= hasta:                                   # días no laborables sombreados
        if not cal.laborable(d):
            ax.axvspan(md.date2num(d), md.date2num(d + dt.timedelta(days=1)), color=C("gris_claro"), lw=0, zorder=0)
        d += dt.timedelta(days=1)
    for k, f in enumerate(filas):
        pos[f["id"]] = k
        ini, fin = P.fecha(f["inicio"]), P.fecha(f["fin"])
        if f["hito"]:
            x = md.date2num(fin) + (0.0 if f.get("snet") or not f["preds"] else 1.0)
            ax.plot([x], [k], marker="D", ms=8, color=C("ambar_upeu") if f["critica"] else C("azul_upeu"),
                    mec=C("gris_texto"), zorder=4)
            ax.annotate(f"{f['id']} {P.f_corta(fin)}", (x, k), xytext=(7, 0), textcoords="offset points", va="center",
                        fontsize=7.5, weight="bold", color=C("gris_texto"))
            continue
        x0, ancho = md.date2num(ini), md.date2num(fin + dt.timedelta(days=1)) - md.date2num(ini)
        if f["hecha"]:
            color, txt, tc = C("azul_claro"), "100 %", C("gris_texto")
        elif f["critica"]:
            color, txt, tc = C("ambar_upeu"), "RC", C("gris_texto")
        else:
            color, txt, tc = C("azul_upeu"), f"h {num(f['holgura'])} d", C("blanco")
        ax.barh(k, ancho, left=x0, height=0.56, color=color, edgecolor=C("gris_texto") if f["critica"] else color,
                lw=1.2 if f["critica"] else 0, zorder=3)
        if not f["hecha"] and (f["lb_inicio"] != f["inicio"] or f["lb_fin"] != f["fin"]):
            lb0, lb1 = P.fecha(f["lb_inicio"]), P.fecha(f["lb_fin"])
            ax.barh(k + 0.36, md.date2num(lb1 + dt.timedelta(days=1)) - md.date2num(lb0), left=md.date2num(lb0), height=0.12,
                    color=C("gris_medio"), zorder=2)
        ax.text(x0 + ancho + 0.4, k, txt, va="center", fontsize=6.8, color=C("gris_texto"), zorder=5)
    rc = set(m["ruta_critica"])
    for f in filas:                                     # enlaces de la ruta crítica
        if f["id"] not in rc:
            continue
        for p in f["preds"]:
            pid = p.split(" ")[0]
            if pid in rc and pid in pos:
                pf = next(x for x in filas if x["id"] == pid)
                x1 = md.date2num(P.fecha(pf["fin"]) + dt.timedelta(days=0 if pf["hito"] else 1))
                x2 = md.date2num(P.fecha(f["inicio"])) if not f["hito"] else md.date2num(P.fecha(f["fin"])) + 1
                ax.annotate("", xy=(x2, pos[f["id"]]), xytext=(x1, pos[pid]),
                            arrowprops=dict(arrowstyle="-|>", color=C("ambar_upeu"), lw=1, shrinkA=0, shrinkB=3,
                                            connectionstyle="arc3,rad=0"), zorder=4)
    corte = P.fecha(m["evm"]["corte"])
    if titulo_corte and desde <= corte <= hasta:
        ax.axvline(md.date2num(corte + dt.timedelta(days=1)), color=C("gris_texto"), lw=1, ls="--", zorder=5)
        ax.text(md.date2num(corte + dt.timedelta(days=1)), -0.9, f" corte {P.f_corta(corte)}", fontsize=7.5,
                color=C("gris_texto"), va="bottom")
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{f['id']}  {f['nombre'][:62]}" for f in filas], fontsize=7)
    ax.set_ylim(n - 0.4, -1.2)
    ax.set_xlim(md.date2num(desde), md.date2num(hasta + dt.timedelta(days=1)))
    ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.MO))
    ax.xaxis.set_major_formatter(md.DateFormatter("%d/%m"))
    ax.tick_params(axis="x", labelsize=7.5)
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[mp.Patch(color=C("azul_claro"), label="Terminada (100 %, fecha del commit)"),
                       mp.Patch(facecolor=C("ambar_upeu"), edgecolor=C("gris_texto"), label="Ruta crítica (RC, holgura 0)"),
                       mp.Patch(color=C("azul_upeu"), label="Con holgura (h = días laborables)"),
                       mp.Patch(color=C("gris_medio"), label="Línea base (si difiere)"),
                       plt.Line2D([], [], marker="D", ls="", color=C("ambar_upeu"), mec=C("gris_texto"), label="Hito")],
              loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=5, fontsize=7.5)
    est.guardar(fig, _png(fid))


def gantt_s1(m):
    h1 = P.fecha(m["hitos"]["H1"]["fecha"])
    filas = [f for f in m["filas"] if P.fecha(f["fin"]) <= h1]
    filas.sort(key=lambda f: (P.fecha(f["inicio"]), f["hito"] is False, f["id"]))
    _gantt(m, filas, "fig-gantt-s1", P.fecha(m["inicio"]) - dt.timedelta(days=2), h1 + dt.timedelta(days=2))


def gantt_s2(m):
    hs2 = P.fecha(m["hitos"]["HS2"]["fecha"])
    filas = [f for f in m["filas"] if P.fecha(f["inicio"]) >= hs2]
    filas.sort(key=lambda f: (P.fecha(f["inicio"]), f["id"]))
    _gantt(m, filas, "fig-gantt-s2", hs2 - dt.timedelta(days=2), P.fecha(m["fin"]) + dt.timedelta(days=3), False)


def curva_s(m):
    import matplotlib.dates as md
    e, p = m["evm"], m["presupuesto"]
    x = [md.date2num(P.fecha(s["fecha"])) for s in e["semanas"]]
    y = [s["pv"] for s in e["semanas"]]
    fig, ax = plt.subplots(figsize=est.tamano(True, 11.5))
    ax.plot(x, y, color=C("azul_upeu"), lw=2.2, marker="o", ms=3, label="PV acumulado (línea base de las actividades)", zorder=3)
    for val, nombre, col, ls in ((p["bac"], "BAC", C("azul_medio"), ":"), (p["linea_base"], "Línea base (BAC + contingencia)", C("azul_upeu"), "--"),
                                 (p["total_autorizado"], "Total autorizado (+ reserva de gestión)", C("ambar_upeu"), "-.")):
        ax.axhline(val, color=col, lw=1.2, ls=ls, zorder=2)
        ax.text(x[-1], val, f"{nombre}: {_u(val)} ", va="bottom", ha="right", fontsize=8, color=C("gris_texto"))
    for k, c in enumerate(e["cortes"]):
        xc = md.date2num(P.fecha(c["fecha"]))
        ax.plot([xc], [c["ev"]], marker="s", ms=7, color=C("ambar_upeu"), mec=C("gris_texto"), zorder=4)
        spi = "sin SPI" if c["spi"] is None else f"SPI {num(c['spi'], 2)}"
        ax.annotate(f"EV {_u(c['ev'])} · {spi}", (xc, c["ev"]), xytext=(70, 4) if k == 0 else (40, 56), textcoords="offset points",
                    fontsize=8, color=C("gris_texto"), arrowprops=dict(arrowstyle="-", color=C("gris_medio"), lw=0.6))
    ax.plot([], [], marker="s", ls="", color=C("ambar_upeu"), mec=C("gris_texto"), label="EV en cada corte (regla 0/100)")
    hs2 = md.date2num(P.fecha(m["hitos"]["HS2"]["fecha"]))
    h1 = md.date2num(P.fecha(m["hitos"]["H1"]["fecha"]))
    ax.axvspan(h1 + 1, hs2, color=C("gris_claro"), lw=0, zorder=0)
    ax.text((h1 + hs2) / 2, p["bac"] * 0.45, "Receso entre semestres\n(sin trabajo planificado)", ha="center", fontsize=8,
            color=C("gris_medio"))
    ax.xaxis.set_major_locator(md.MonthLocator())
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{P.MESES[md.num2date(v).month - 1]} {md.num2date(v).year}"))
    ax.set_ylabel("US$ acumulados")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: num(v)))
    ax.set_ylim(0, p["total_autorizado"] * 1.1)
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.42), fontsize=8)
    est.guardar(fig, _png("fig-curva-s"))


def riesgos():
    puntos = defaultdict(list)
    for r in cd.cargar()["riesgos_proyecto"]["lista"]:
        puntos[(r["p"], r["i"])].append(r["id"])
    fig, ax = plt.subplots(figsize=est.tamano(False, 11.5))
    g1._matriz_5x5(ax, puntos, "Probabilidad (1–5)", "Impacto (1–5)")
    est.guardar(fig, _png("fig-riesgos"))


def burnup(m):
    ag = m["agil"]
    xs = [b["sprint"] for b in ag["burnup"]]
    fig, ax = plt.subplots(figsize=est.tamano(False, 10))
    barras = ax.bar(xs, [b["plan"] for b in ag["burnup"]], color=C("azul_upeu"), width=0.6, label="Plan acumulado (puntos)")
    est.etiquetar_barras(ax, barras, lambda v: f"{v:g}")
    ax.axhline(ag["alcance_total"], color=C("ambar_upeu"), lw=1.6, ls="--", label=f"Alcance total sin Won't: {ag['alcance_total']} pts")
    ax.axhline(ag["must"], color=C("azul_medio"), lw=1.4, ls=":", label=f"Alcance Must: {ag['must']} pts")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"Sprint {s}\n{P.f_corta(P.fecha(b['fin']))}" for s, b in zip(xs, ag["burnup"])], fontsize=7.5)
    ax.set_ylabel("Puntos de historia")
    ax.set_ylim(0, ag["alcance_total"] * 1.15)
    ax.legend(loc="upper left", fontsize=8)
    est.guardar(fig, _png("fig-burnup"))


def registro():
    reg = {}
    for fid, (a, t, f, h) in FIGURAS.items():
        if fid == "fig-gantt-s2" and MSP.exists():
            a, f = MSP.name, f"{PROPIA}; vista Gantt de Microsoft Project sobre entregables/CE01/E3/Cronograma_Celeris.xml"
        reg[fid] = {"archivo": a, "titulo": t, "fuente": f, "horizontal": h}
    (AQUI / "figuras.yaml").write_text(
        "# Registro de figuras del E3 (lo escribe gestion/e3/figuras/generar.py; no editar a mano).\n"
        + yaml.safe_dump(reg, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    return reg


def main() -> int:
    m = _modelo()
    for f in (gantt_s1, gantt_s2, curva_s, burnup):
        f(m)
    riesgos()
    errores = g1.exportar([edt(m), control_cambios(), kanban(m)])
    reg = registro()
    faltan = [x["archivo"] for x in reg.values() if not (AQUI / x["archivo"]).exists()]
    for e in errores + [f"falta {a}" for a in faltan]:
        print(f"  ERROR {e}")
    return 1 if errores or faltan else 0


if __name__ == "__main__":
    sys.exit(main())
