"""Figuras del Entregable 2 de CE01 (make figuras-ce01).

    python gestion/e2/figuras/generar.py

Escribe en gestion/e2/figuras/:
  - draw.io (.drawio + PNG con draw.io Desktop): árbol de objetivos (espejo del árbol de problemas del E1) y red de
    dependencia de beneficios (BDN);
  - matplotlib (PNG 200 dpi): TCO por alternativa, matriz ponderada como mapa de calor, sensibilidad de pesos, flujo de
    caja, histograma de Monte Carlo, tornado y mapa de calor de riesgos con su efecto en el VAN;
  - figuras.yaml: el registro que lee el generador del informe.

Las cifras salen de gestion/e2/datos/resultados.json (gestion/analytics/business_case.py, que se ejecuta primero); los
colores, de gestion/estilo_ce01.py (CI-100).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
E2 = AQUI.parent
GESTION = E2.parent
sys.path.insert(0, str(GESTION))
sys.path.insert(0, str(GESTION / "analytics"))
import business_case  # noqa: E402
import ce01_datos as cd  # noqa: E402
import estilo_ce01 as est  # noqa: E402
from ce01_datos import num, usd  # noqa: E402

_spec = importlib.util.spec_from_file_location("figuras_e1", GESTION / "e1" / "figuras" / "generar.py")
g1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g1)

C = est.color
plt = est.configurar_matplotlib()
PROPIA = "Elaboración propia"
BC = yaml.safe_load((E2 / "datos" / "business_case.yaml").read_text(encoding="utf-8"))
D1 = yaml.safe_load((GESTION / "e1" / "datos" / "diagnostico.yaml").read_text(encoding="utf-8"))

FIGURAS = {
    "fig-arbol-objetivos": ("arbol-objetivos.png", "Árbol de objetivos: medios, objetivo central y fines",
                            f"{PROPIA}; espejo del árbol de problemas del E1 (Figura 1.9)", True),
    "fig-tco": ("tco-alternativas.png", "Costo total de propiedad a tres años por alternativa",
                f"{PROPIA}; partidas CX-x y OX-x de gestion/ce01.yaml; supuestos S-03, S-08…S-12, S-37…S-41", False),
    "fig-matriz": ("matriz-ponderada.png", "Matriz de decisión ponderada con pesos AHP",
                   f"{PROPIA}; puntajes de la guía CE01 v0.4 B2.2, C3 calculado con el TCO y pesos AHP [1]", True),
    "fig-sensibilidad": ("sensibilidad-pesos.png", "Sensibilidad de la decisión al peso de cada criterio",
                         f"{PROPIA}; gestion/analytics/business_case.py", True),
    "fig-bdn": ("bdn.png", "Red de dependencia de beneficios: habilitador, cambio, beneficio y objetivo",
                f"{PROPIA}, adaptado de Ward y Daniel [3]; objetivos OB-x de infra/trazabilidad.yaml", True),
    "fig-flujo": ("flujo-caja.png", "Flujo de caja del caso base y flujo acumulado",
                  f"{PROPIA}; gestion/analytics/business_case.py", False),
    "fig-montecarlo": ("montecarlo.png", "Distribución del VAN en la simulación de Monte Carlo",
                       f"{PROPIA}; distribuciones triangulares de gestion/e2/datos/business_case.yaml (CI-102)", False),
    "fig-tornado": ("tornado.png", "Diagrama de tornado del VAN",
                    f"{PROPIA}; una variable a la vez en los extremos de su rango (CI-102)", False),
    "fig-riesgos-van": ("riesgos-van.png", "Mapa de calor de los riesgos RE-01…RE-12 con su efecto en el VAN",
                        f"{PROPIA}; P e I de gestion/ce01.yaml; ΔVAN de los escenarios de estrés (CI-102)", False),
}


def _png(fid):
    return AQUI / FIGURAS[fid][0]


def _u(x: float, dec: int = 0) -> str:
    """US$ para matplotlib: «$» escapado (si no, se interpreta como fórmula) y signo menos tipográfico."""
    return ("−" if x < 0 else "") + usd(abs(x), dec).replace("$", r"\$")


def _k(x: float) -> str:
    """US$ en miles con signo, para etiquetas cortas («−20,8 k»)."""
    return ("−" if x < 0 else "+" if x > 0 else "±") + f"{num(abs(x) / 1000, 1)} k"


# ==================================================================================================
# draw.io
# ==================================================================================================
class Lienzo(g1.Lienzo):
    def guardar(self) -> Path:
        ruta_e1 = super().guardar()                  # escribe en gestion/e1/figuras: se mueve a gestion/e2/figuras
        destino = AQUI / ruta_e1.name
        destino.write_text(ruta_e1.read_text(encoding="utf-8"), encoding="utf-8")
        ruta_e1.unlink()
        return destino


_b = g1._b


def arbol_objetivos():
    a, p = BC["arbol_objetivos"], D1["arbol"]
    if len(a["medios"]) != len(p["causas"]) or len(a["fines"]) != len(p["efectos"]):
        raise SystemExit("arbol_objetivos: debe tener un medio por causa y un fin por efecto del árbol de problemas del E1")
    lz = Lienzo("arbol-objetivos")
    lz.texto(_b("FINES"), 20, 10, 200, 24, 13, "azul_upeu")
    W = 200
    fi = [lz.caja(e, 20 + k * 220, 40, W, 70, "azul_muy_claro", "azul_medio", 1) for k, e in enumerate(a["fines"])]
    lz.texto(_b("OBJETIVO CENTRAL"), 20, 150, 300, 24, 13, "azul_upeu")
    oc = lz.caja(_b(a["objetivo"]), 240, 180, 640, 80, "azul_upeu", "azul_upeu", 3)
    lz.texto(_b("MEDIOS"), 20, 300, 200, 24, 13, "azul_upeu")
    me = [lz.caja(c, 20 + k * 275, 330, 255, 80, "ambar_claro", "ambar_upeu", 2) for k, c in enumerate(a["medios"])]
    for k, c in enumerate(me):
        lz.flecha(c, oc, "gris_medio", 1.5, f"exitX=0.5;exitY=0;entryX={(k + 0.5) / len(me):.3f};entryY=1;")
    for k, e in enumerate(fi):
        lz.flecha(oc, e, "gris_medio", 1.5, f"exitX={(k + 0.5) / len(fi):.3f};exitY=0;entryX=0.5;entryY=1;")
    return lz.guardar()


def bdn():
    b = BC["bdn"]
    obs = {o["id"]: o for o in cd.objetivos()}
    lz = Lienzo("bdn")
    columnas = [("HABILITADORES (entregables)", b["habilitadores"], "blanco", "azul_upeu", 1),
                ("CAMBIOS EN LA OPERACIÓN", b["cambios"], "azul_muy_claro", "azul_medio", 1),
                ("BENEFICIOS", b["beneficios"], "ambar_claro", "ambar_upeu", 2),
                ("OBJETIVOS DEL PROYECTO", [{**o, "texto": f"{o['id']} {obs[o['id']]['necesidad']}"} for o in b["objetivos"]],
                 "azul_upeu", "azul_upeu", 2)]
    ids, X, W, H, DX = {}, 20, 230, 56, 300
    for c, (titulo, items, relleno, borde, grosor) in enumerate(columnas):
        x = X + c * DX
        lz.texto(_b(titulo), x, 0, W, 24, 12, "azul_upeu", "align=center;")
        paso = 470 / max(len(items), 1)
        for k, it in enumerate(items):
            texto = it["texto"] if c == 3 or it["id"].startswith("OB") else f"<b>{it['id']}</b> {it['texto']}"
            ids[it["id"]] = lz.caja(texto, x, 34 + k * paso + (paso - H) / 2, W, H, relleno, borde, grosor)
    for items in (b["cambios"], b["beneficios"], b["objetivos"]):
        for it in items:
            for o in it["de"]:
                lz.flecha(ids[o], ids[it["id"]], "gris_medio", 1.2, "edgeStyle=none;curved=0;exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    return lz.guardar()


# ==================================================================================================
# matplotlib
# ==================================================================================================
def tco(r):
    t, alt = r["tco"], BC["alternativas"]
    orden = sorted(t, key=lambda a: t[a]["tco"])
    fig, ax = plt.subplots(figsize=est.tamano(False, 9.5))
    y = range(len(orden))
    cap = [t[a]["capex"] for a in orden]
    ope = [t[a]["tco"] - t[a]["capex"] for a in orden]
    b1 = ax.barh(y, cap, color=C("azul_upeu"), label="Inversión inicial")
    ax.barh(y, ope, left=cap, color=C("ambar_upeu"), label="Costos anuales × 3 años")
    for k, a in enumerate(orden):
        txt = _u(t[a]["tco"]) + (" (cota inferior)" if t[a]["cota_inferior"] else "")
        ax.text(t[a]["tco"] + 300, k, txt, va="center", fontsize=8.5, color=C("gris_texto"))
    ax.set_yticks(list(y), [f"{a} {alt[a]['corto']}" for a in orden])
    ax.set_xlabel("US$ a 3 años (sin descontar)")
    ax.xaxis.set_major_formatter(lambda v, _: num(v))
    ax.set_xlim(0, max(t[a]["tco"] for a in orden) * 1.32)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=8)
    del b1
    est.guardar(fig, _png("fig-tco"))


def matriz(r):
    import numpy as np
    d, alt = r["decision"], BC["alternativas"]
    crit = d["criterios"]
    nombres = {c["id"]: c["nombre"] for c in cd.cargar()["criterios"]["lista"]}
    filas = list(d["filas"])
    M = np.array([d["filas"][a]["puntajes"] for a in filas])
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=est.tamano(True, 10.5), gridspec_kw={"width_ratios": [6, 1.3]})
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("upeu", [C("blanco"), C("azul_claro"), C("azul_upeu")])
    ax.imshow(M, cmap=cmap, vmin=1, vmax=5, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, num(M[i, j], 1 if M[i, j] % 1 else 0), ha="center", va="center", fontsize=10, weight="bold",
                    color=C("blanco") if M[i, j] >= 3.6 else C("gris_texto"))
    cortos = {"C1": "Eficacia", "C2": "Seguridad y\nprivacidad", "C3": "TCO a 3 años", "C4": "Autonomía del\nencargado",
              "C5": "Soporte", "C6": "Valor\nacadémico"}
    etiquetas = [f"{c} {cortos.get(c, nombres[c])}\npeso {num(w * 100, 1)} %" for c, w in zip(crit, d["pesos"])]
    ax.set_xticks(range(len(crit)), etiquetas, fontsize=7.5)
    ax.set_yticks(range(len(filas)), [f"{a} {alt[a]['corto']}" for a in filas], fontsize=9)
    ax.grid(False)
    ax.tick_params(length=0)
    ax.xaxis.tick_top()
    tot = [d["filas"][a]["total"] for a in filas]
    gana = d["ranking"][0]
    cols = [C("ambar_upeu") if a == gana else C("gris_medio") for a in filas]
    barras = ax2.barh(range(len(filas)), tot, color=cols)
    ax2.set_ylim(len(filas) - 0.5, -0.5)
    ax2.set_yticks([])
    ax2.set_xlim(0, 5)
    ax2.set_title("Total ponderado", fontsize=9)
    ax2.grid(axis="y", visible=False)
    est.etiquetar_barras(ax2, barras, fmt=lambda v: num(v, 2), horizontal=True)
    fig.tight_layout()
    est.guardar(fig, _png("fig-matriz"))


def sensibilidad(r):
    sen, alt = r["sensibilidad"], BC["alternativas"]
    crit = r["decision"]["criterios"]
    nombres = {c["id"]: c["nombre"].split(" (")[0] for c in cd.cargar()["criterios"]["lista"]}
    fig, axs = plt.subplots(2, 3, figsize=est.tamano(True, 13), sharey=True)
    orden = list(r["decision"]["filas"])
    trazo = {"A0": (C("gris_medio"), "-", 1.2), "A1": (C("azul_upeu"), "-", 2.4), "A2": (C("azul_claro"), "--", 1.4),
             "A3": (C("azul_medio"), "-.", 1.4), "A4": (C("ambar_upeu"), "-", 2.8), "A5": (C("gris_texto"), ":", 1.6)}

    for ax, cid, pc in zip(axs.flat, crit, sen["por_criterio"]):
        cur = sen["curvas"][cid]
        for a in orden:
            col, ls, lw = trazo.get(a, (C("gris_medio"), "-", 1.2))
            ax.plot(cur["x"], cur["totales"][a], color=col, ls=ls, lw=lw,
                    label=f"{a} {alt[a]['corto']}")
        ax.axvline(pc["peso"], color=C("gris_texto"), lw=1, ls="--")
        txt = f"actual {num(pc['peso'] * 100, 1)} %"
        if pc["peso_cruce"] is not None:
            ax.axvline(pc["peso_cruce"], color="#C0392B", lw=1.2, ls=":")
            txt += f"\ncruce {num(pc['peso_cruce'] * 100, 1)} % → {pc['gana']}"
        else:
            txt += "\nA4 gana en todo el rango"
        ax.text(0.98, 0.04, txt, transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5, color=C("gris_texto"),
                bbox=dict(boxstyle="round", fc=C("blanco"), ec=C("gris_claro")))
        ax.set_title(f"{cid} {nombres[cid]}", fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_ylim(1, 5)
        ax.xaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f} %")
        ax.tick_params(labelsize=7.5)
    for ax in axs[1]:
        ax.set_xlabel("Peso del criterio", fontsize=8)
    for ax in axs[:, 0]:
        ax.set_ylabel("Total ponderado", fontsize=8)
    h, l = axs.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, fontsize=7.5, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    est.guardar(fig, _png("fig-sensibilidad"))


def flujo(r):
    b = r["base"]
    fig, ax = plt.subplots(figsize=est.tamano(False, 9.5))
    anios = list(range(len(b["flujos"])))
    cols = [C("azul_upeu") if f >= 0 else "#C0392B" for f in b["flujos"]]
    barras = ax.bar(anios, b["flujos"], color=cols, width=0.55, label="Flujo neto del año")
    for x, v in zip(anios, b["flujos"]):
        ax.annotate(_u(v), (x + 0.15, v), xytext=(0, 3 if v >= 0 else -3), textcoords="offset points", ha="left",
                    va="bottom" if v >= 0 else "top", fontsize=8, color=C("gris_texto"))
    ax.plot(anios, b["acumulado"], color=C("ambar_upeu"), marker="o", lw=2, label="Flujo acumulado")
    for x, v in zip(anios[1:], b["acumulado"][1:]):
        ax.annotate(f"acumulado {_u(v)}", (x, v), xytext=(-8, 6), textcoords="offset points", ha="right", fontsize=7.5,
                    color=C("ambar_upeu"), weight="bold")
    ax.axhline(0, color=C("gris_medio"), lw=0.8)
    ax.set_xticks(anios, [f"Año {t}" for t in anios])
    ax.set_ylabel("US$")
    ax.yaxis.set_major_formatter(lambda v, _: num(v))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", fontsize=8)
    est.guardar(fig, _png("fig-flujo"))


def montecarlo(r):
    mc = r["montecarlo"]
    h = mc["histograma"]
    fig, ax = plt.subplots(figsize=est.tamano(False, 9.5))
    bordes = h["bordes"]
    centros = [(a + b) / 2 for a, b in zip(bordes[:-1], bordes[1:])]
    ancho = bordes[1] - bordes[0]
    cols = [C("azul_upeu") if c >= 0 else "#C0392B" for c in centros]
    ax.bar(centros, h["conteos"], width=ancho * 0.95, color=cols)
    for clave, et, ls, alto in (("p5", "P5", ":", 1.13), ("p50", "P50", "--", 1.02), ("p95", "P95", ":", 1.02)):
        ax.axvline(mc[clave], color=C("ambar_upeu"), lw=1.5, ls=ls)
        ax.text(mc[clave], max(h["conteos"]) * alto, f"{et}\n{_u(mc[clave])}", ha="center", va="bottom", fontsize=7.5,
                color=C("gris_texto"), bbox=dict(boxstyle="round,pad=0.2", fc=C("blanco"), ec="none"))
    ax.axvline(0, color="#C0392B", lw=1.2)
    ax.text(0.98, 0.80, f"P(VAN > 0) = {num(mc['p_van_positivo'] * 100, 1)} %\n{num(mc['iteraciones'])} iteraciones",
            transform=ax.transAxes, va="top", ha="right", fontsize=8.5, color=C("gris_texto"),
            bbox=dict(boxstyle="round", fc=C("blanco"), ec=C("gris_claro")))
    ax.set_ylim(0, max(h["conteos"]) * 1.3)
    ax.set_xlabel("VAN (US$); en rojo, VAN negativo")
    ax.set_ylabel("Iteraciones")
    ax.xaxis.set_major_formatter(lambda v, _: num(v))
    ax.grid(axis="x", visible=False)
    est.guardar(fig, _png("fig-montecarlo"))


def tornado(r):
    tor = list(reversed(r["tornado"]))
    base = tor[0]["base"]
    fig, ax = plt.subplots(figsize=est.tamano(False, 8.5))
    fmt = {"bhr": lambda x: f"{num(x * 100)} %", "adopcion": lambda x: f"{num(x * 100)} %",
           "usd_mbps": lambda x: _u(x), "f_aws": lambda x: f"×{num(x, 2)}", "f_capex": lambda x: f"×{num(x, 2)}"}
    for k, t in enumerate(tor):
        bajo, alto = min(t["van_min"], t["van_max"]), max(t["van_min"], t["van_max"])
        ax.barh(k, base - bajo, left=bajo, color="#C0392B", alpha=0.85)
        ax.barh(k, alto - base, left=base, color=C("azul_upeu"))
        f = fmt[t["id"]]
        izq, der = (t["min"], t["max"]) if t["van_min"] <= t["van_max"] else (t["max"], t["min"])
        ax.text(bajo, k, f"{f(izq)}  {_u(bajo)} ", ha="right", va="center", fontsize=7.5, color=C("gris_texto"))
        ax.text(alto, k, f" {_u(alto)}  {f(der)}", ha="left", va="center", fontsize=7.5, color=C("gris_texto"))
    ax.axvline(base, color=C("gris_texto"), lw=1)
    ax.text(base, len(tor) - 0.35, f"Caso base {_u(base)}", ha="center", fontsize=8, color=C("gris_texto"))
    ax.set_yticks(range(len(tor)), [f"{t['nombre']}\n[{t['supuesto']}]" for t in tor], fontsize=8)
    lo = min(min(t["van_min"], t["van_max"]) for t in tor)
    hi = max(max(t["van_min"], t["van_max"]) for t in tor)
    ax.set_xlim(lo - (hi - lo) * 0.45, hi + (hi - lo) * 0.45)
    ax.set_ylim(-0.6, len(tor) - 0.1)
    ax.set_xlabel("VAN (US$)")
    ax.xaxis.set_major_formatter(lambda v, _: num(v))
    ax.grid(axis="y", visible=False)
    est.guardar(fig, _png("fig-tornado"))


def riesgos_van(r):
    puntos = defaultdict(list)
    for x in r["riesgos"]:
        puntos[(x["p"], x["i"])].append(f"{x['id']} {_k(x['delta_van'])}")
    fig, ax = plt.subplots(figsize=est.tamano(False, 11.5))
    g1._matriz_5x5(ax, puntos, "Probabilidad (1–5)", "Impacto (1–5)")
    for t in ax.texts:
        if "RE-" in t.get_text():
            t.set_fontsize(6.6)
    est.guardar(fig, _png("fig-riesgos-van"))


def registro():
    reg = {fid: {"archivo": a, "titulo": t, "fuente": f, "horizontal": h} for fid, (a, t, f, h) in FIGURAS.items()}
    (AQUI / "figuras.yaml").write_text(
        "# Registro de figuras del E2 (lo escribe gestion/e2/figuras/generar.py; no editar a mano).\n"
        + yaml.safe_dump(reg, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")


def main() -> int:
    if business_case.main([]) != 0:              # refresca resultados.json y el XLSX (y verifica el VAN de Excel)
        return 1
    r = json.loads(business_case.SALIDA_JSON.read_text(encoding="utf-8"))["modelo"]
    for f in (tco, matriz, sensibilidad, flujo, montecarlo, tornado, riesgos_van):
        f(r)
    errores = g1.exportar([arbol_objetivos(), bdn()])
    registro()
    faltan = [a for a, *_ in FIGURAS.values() if not (AQUI / a).exists()]
    for e in errores + [f"falta {a}" for a in faltan]:
        print(f"  ERROR {e}")
    return 1 if errores or faltan else 0


if __name__ == "__main__":
    sys.exit(main())
