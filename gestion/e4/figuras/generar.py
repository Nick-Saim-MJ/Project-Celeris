"""Figuras del Entregable 4 de CE01 (make figuras-ce01 --entregable E4).

    python gestion/e4/figuras/generar.py

Escribe en gestion/e4/figuras/:
  - draw.io (.drawio + PNG con draw.io Desktop): mapa de procesos de la universidad en lo que toca a los laboratorios;
  - BPMN: P1-AS-IS, P1-TO-BE, P2-AS-IS y P2-TO-BE. Si existe <diagrama>-bizagi.png (exportado de Bizagi Modeler, paso
    manual del README), se usa esa imagen; si no, se renderiza gestion/e4/bpmn/<diagrama>.bpmn con bpmn-js en Node
    (gestion/e4/herramientas/render/render.js). Si no se puede renderizar ni hay imagen de Bizagi, falla;
  - matplotlib (PNG 200 dpi): comparativo AS-IS frente a TO-BE (barras agrupadas) y dispersión del costo por ciclo
    (diagrama de caja de la simulación);
  - figuras.yaml: el registro que lee el generador del informe.

Las cifras salen de gestion/e4/datos/e4.json (gestion/e4/procesos.py, que se ejecuta primero); los colores, de
gestion/estilo_ce01.py (CI-100).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
E4 = AQUI.parent
GESTION = E4.parent
sys.path.insert(0, str(GESTION))
sys.path.insert(0, str(E4))
import estilo_ce01 as est  # noqa: E402
import procesos as P  # noqa: E402
from ce01_datos import num, usd  # noqa: E402

_spec = importlib.util.spec_from_file_location("figuras_e1", GESTION / "e1" / "figuras" / "generar.py")
g1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g1)

C = est.color
plt = est.configurar_matplotlib()
PROPIA = "Elaboración propia"
RENDER = E4 / "herramientas" / "render" / "render.js"
DIAGRAMAS = ("P1-AS-IS", "P1-TO-BE", "P2-AS-IS", "P2-TO-BE")

FIGURAS = {
    "fig-mapa": ("mapa-procesos.png", "Mapa de procesos de la universidad en lo que toca a los laboratorios",
                 f"{PROPIA}; cadena de valor del E1 (nombres a validar con la DTI)", True),
    "fig-p1-asis": ("P1-AS-IS.png", "BPMN del proceso P1 actual (AS-IS) con sus ineficiencias PD-01…PD-04",
                    f"{PROPIA}; BPMN 2.0 validado contra el esquema XSD de OMG", True),
    "fig-p2-asis": ("P2-AS-IS.png", "BPMN del proceso P2 actual (AS-IS) con sus ineficiencias PD-05…PD-09",
                    f"{PROPIA}; BPMN 2.0 validado contra el esquema XSD de OMG", True),
    "fig-p1-tobe": ("P1-TO-BE.png", "BPMN del proceso P1 propuesto (TO-BE) con el carril Celeris",
                    f"{PROPIA}; BPMN 2.0 validado contra el esquema XSD de OMG; requisitos del SRS de CE02", True),
    "fig-p2-tobe": ("P2-TO-BE.png", "BPMN del proceso P2 propuesto (TO-BE) con el carril Celeris",
                    f"{PROPIA}; BPMN 2.0 validado contra el esquema XSD de OMG; requisitos del SRS de CE02", True),
    "fig-comparativo": ("comparativo.png", "Comparativo AS-IS frente a TO-BE por indicador (AS-IS = 100)",
                        f"{PROPIA}; simulación de Monte Carlo [S-43, S-44]", True),
    "fig-dispersion": ("dispersion-costo.png", "Distribución del costo de personal por ciclo en la simulación",
                       f"{PROPIA}; simulación de Monte Carlo [S-07, S-43, S-44]", False),
}


def _png(fid):
    return AQUI / FIGURAS[fid][0]


def _modelo() -> dict:
    return json.loads((E4 / "datos" / "e4.json").read_text(encoding="utf-8"))["modelo"]


# ==================================================================================================
# draw.io: mapa de procesos
# ==================================================================================================
class Lienzo(g1.Lienzo):
    def guardar(self) -> Path:
        ruta_e1 = super().guardar()
        destino = AQUI / ruta_e1.name
        destino.write_text(ruta_e1.read_text(encoding="utf-8"), encoding="utf-8")
        ruta_e1.unlink()
        return destino


_b = g1._b


def mapa():
    mp = P.caracterizacion()["mapa"]
    sel = set(P.caracterizacion()["seleccion"]["seleccionados"])
    lz = Lienzo("mapa-procesos")
    X, W, ENT = 150, 1120, 130
    lz.caja(_b("Necesidades de formación de estudiantes y docentes"), 0, 150, ENT, 250, "azul_muy_claro", "azul_medio", 1, "fontSize=11;")
    lz.caja(_b("Estudiantes formados y clases sin esperas"), X + W + 20, 150, ENT, 250, "azul_muy_claro", "azul_medio", 1, "fontSize=11;")
    bandas = [("PROCESOS ESTRATÉGICOS", mp["estrategicos"], 0, 110), ("PROCESOS MISIONALES", mp["misionales"], 130, 110)]
    for titulo, items, y, h in bandas:
        lz.caja("", X, y, W, h, "blanco", "azul_upeu", 2, "arcSize=4;")
        lz.texto(_b(titulo), X + 12, y + 6, 400, 22, 12, "azul_upeu")
        ancho = (W - 40 - 20 * (len(items) - 1)) / len(items)
        for k, it in enumerate(items):
            relleno = "azul_medio" if titulo.endswith("MISIONALES") else "azul_claro"
            lz.caja(it, X + 20 + k * (ancho + 20), y + 36, ancho, 58, relleno, relleno, 1)
    ya, ha = 260, 300
    lz.caja("", X, ya, W, ha, "blanco", "azul_upeu", 2, "arcSize=3;")
    lz.texto(_b("PROCESOS DE APOYO"), X + 12, ya + 6, 400, 22, 12, "azul_upeu")
    soporte = next(a for a in mp["apoyo"] if a.get("subprocesos"))
    otros = [a for a in mp["apoyo"] if not a.get("subprocesos")]
    lz.caja("", X + 20, ya + 34, 820, ha - 50, "azul_muy_claro", "azul_medio", 1, "arcSize=3;")
    lz.texto(_b(soporte["nombre"]), X + 32, ya + 38, 600, 20, 11, "azul_upeu")
    sw = (820 - 40 - 4 * 12) / 5
    for k, sp in enumerate(soporte["subprocesos"]):
        elegido = sp["id"] in sel
        txt = (_b(f"{sp['id']} {sp['nombre']}") + "<br>ELEGIDO") if elegido else f"{sp['id']} {sp['nombre']}"
        lz.caja(txt, X + 40 + k * (sw + 12), ya + 72, sw, 150, "ambar_claro" if elegido else "blanco",
                "ambar_upeu" if elegido else "azul_claro", 3 if elegido else 1, "fontSize=11;")
    for k, a in enumerate(otros):
        lz.caja(a["nombre"], X + 860, ya + 34 + k * 128, W - 880, 112, "azul_claro", "azul_claro", 1)
    lz.texto("Ámbar con borde grueso y «ELEGIDO» = procesos modelados en el E4 (matriz de selección). P1 y P2 pertenecen al "
             "proceso de apoyo de la DTI, pero su efecto recae en el proceso misional «Enseñanza en laboratorios».",
             X, ya + ha + 10, W, 36, 11, "gris_texto")
    return lz.guardar()


# ==================================================================================================
# BPMN: imagen de Bizagi si existe; si no, bpmn-js
# ==================================================================================================
def bpmn_png(pid: str) -> tuple[str, str | None]:
    """(archivo PNG, error). Prefiere <pid>-bizagi.png."""
    biz = AQUI / f"{pid}-bizagi.png"
    if biz.exists():
        return biz.name, None
    destino = AQUI / f"{pid}.png"
    if not RENDER.exists() or not (RENDER.parent / "node_modules").exists():
        return destino.name, f"{pid}: no hay imagen de Bizagi ni bpmn-js instalado (README, paso 0)"
    p = subprocess.run(["node", str(RENDER), str(E4 / "bpmn" / f"{pid}.bpmn"), str(destino), "2"],
                       capture_output=True, text=True, timeout=180, encoding="utf-8")
    if p.returncode != 0 or not destino.exists():
        return destino.name, f"{pid}: bpmn-js terminó con {p.returncode}: {(p.stderr or p.stdout)[-300:]}"
    destino.with_suffix(".svg").unlink(missing_ok=True)        # el SVG intermedio no se versiona
    return destino.name, None


# ==================================================================================================
# matplotlib
# ==================================================================================================
def comparativo(m):
    c = m["comparativo"]
    filas = [
        ("Ocupación del\nlaboratorio", "ocupacion_h", lambda v: f"{num(v, 1)} h"),
        ("Horas de\npersonal", "horas_personal", lambda v: f"{num(v, 1)} h"),
        ("Costo por\nciclo", "costo", lambda v: usd(v, 2).replace("$", r"\$")),
        ("Tráfico por\nel enlace", "wan_gb", lambda v: f"{num(v)} GB"),
        ("Tiempo de\nciclo", "ciclo_h", lambda v: f"{num(v, 1)} h"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=est.tamano(True, 10.5), sharey=True)
    for ax, proc, titulo in ((axes[0], "P1", "P1 Actualización masiva de un laboratorio"),
                             (axes[1], "P2", "P2 Preparación de un laboratorio para una clase")):
        xs = range(len(filas))
        a = [100] * len(filas)
        b = [100 * c[proc][k]["tobe"] / c[proc][k]["asis"] for _, k, _ in filas]
        ba = ax.bar([x - 0.2 for x in xs], a, 0.4, color=C("azul_upeu"), label="AS-IS (= 100)")
        bb = ax.bar([x + 0.2 for x in xs], b, 0.4, color=C("ambar_upeu"), label="TO-BE")
        for bar, (_, k, f) in zip(ba, filas):
            ax.annotate(f(c[proc][k]["asis"]), (bar.get_x() + bar.get_width() / 2, 100), ha="center", va="bottom",
                        xytext=(0, 2), textcoords="offset points", fontsize=7, color=C("gris_texto"))
        for bar, (_, k, f) in zip(bb, filas):
            mej = c[proc][k]["mejora"]
            ax.annotate(f"{f(c[proc][k]['tobe'])}\n−{num(mej * 100)} %", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha="center", va="bottom", xytext=(0, 2), textcoords="offset points", fontsize=7, color=C("gris_texto"))
        ax.set_xticks(list(xs))
        ax.set_xticklabels([f[0] for f in filas], fontsize=7.5)
        ax.set_title(titulo, fontsize=9.5, color=C("azul_upeu"))
        ax.set_ylim(0, 125)
    axes[0].set_ylabel("Índice (AS-IS = 100)")
    axes[0].legend(loc="upper right", fontsize=8)
    est.guardar(fig, _png("fig-comparativo"))


def dispersion():
    datos = {pid: P.simular(pid)["costo"] for pid in DIAGRAMAS}
    fig, ax = plt.subplots(figsize=est.tamano(False, 9.5))
    caja = ax.boxplot([datos[p] for p in DIAGRAMAS], whis=(10, 90), showfliers=False, patch_artist=True, widths=0.55)
    for parche, pid in zip(caja["boxes"], DIAGRAMAS):
        parche.set_facecolor(C("azul_upeu") if pid.endswith("AS-IS") else C("ambar_upeu"))
        parche.set_edgecolor(C("gris_texto"))
    for med in caja["medians"]:
        med.set_color(C("blanco"))
        med.set_linewidth(1.6)
    for k, pid in enumerate(DIAGRAMAS, start=1):
        media = float(datos[pid].mean())
        ax.annotate(f"media {usd(media, 2)}".replace("$", r"\$"), (k, media), xytext=(28, 0), textcoords="offset points",
                    fontsize=7.5, va="center", color=C("gris_texto"))
    ax.set_xticks(range(1, len(DIAGRAMAS) + 1))
    ax.set_xticklabels([p.replace("-", " ", 1) for p in DIAGRAMAS], fontsize=8)
    ax.set_ylabel(r"Costo de personal por ciclo (US\$)")
    ax.text(0.01, 0.98, "Caja: percentiles 25–75; bigotes: 10–90; línea blanca: mediana.\nAzul = AS-IS; ámbar = TO-BE.",
            transform=ax.transAxes, va="top", fontsize=7.5, color=C("gris_texto"))
    est.guardar(fig, _png("fig-dispersion"))


def registro(archivos: dict[str, str]):
    reg = {}
    for fid, (a, t, f, h) in FIGURAS.items():
        a = archivos.get(fid, a)
        if a.endswith("-bizagi.png"):
            f = f"{PROPIA}; Bizagi Modeler"
        reg[fid] = {"archivo": a, "titulo": t, "fuente": f, "horizontal": h}
    (AQUI / "figuras.yaml").write_text(
        "# Registro de figuras del E4 (lo escribe gestion/e4/figuras/generar.py; no editar a mano).\n"
        + yaml.safe_dump(reg, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    return reg


def main() -> int:
    m = _modelo()
    comparativo(m)
    dispersion()
    errores = g1.exportar([mapa()])
    archivos = {}
    for pid in DIAGRAMAS:
        fid = "fig-" + pid.lower().replace("-as-is", "-asis").replace("-to-be", "-tobe")
        archivos[fid], err = bpmn_png(pid)
        if err:
            errores.append(err)
    reg = registro(archivos)
    faltan = [x["archivo"] for x in reg.values() if not (AQUI / x["archivo"]).exists()]
    for e in errores + [f"falta {a}" for a in faltan]:
        print(f"  ERROR {e}")
    return 1 if errores or faltan else 0


if __name__ == "__main__":
    sys.exit(main())
