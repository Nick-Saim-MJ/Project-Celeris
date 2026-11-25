"""Identidad visual única de CE01 (CI-100): una paleta institucional UPeU para todas las figuras.

Toda figura de CE01 toma sus colores de aquí, sea un gráfico de matplotlib, un .drawio, un .bpmn o una hoja XLSX.
La paleta vive en gestion/ce01.yaml → estilo: si la universidad entrega su manual de marca, se cambia solo ahí.

Reglas que este módulo hace cumplir:
  - el color nunca va solo: etiquetar_barras() escribe el valor en cada barra y nivel_riesgo() da el texto del nivel;
  - el texto sobre un relleno usa el color de `texto_sobre` (contraste suficiente);
  - PNG de 200 dpi, Calibri (o Arial), ancho útil 25,7 cm × alto máximo 13,4 cm en horizontal (CI-90).
"""
from __future__ import annotations

from pathlib import Path

from ce01_datos import estilo

CM = 1 / 2.54


def _e() -> dict:
    return estilo()


def color(nombre: str) -> str:
    """Hex de un color de la paleta («azul_upeu» → «#003865»)."""
    return _e()["paleta"][nombre]


def texto_sobre(nombre: str) -> str:
    """Color de texto legible sobre el relleno `nombre`."""
    return color(_e()["texto_sobre"].get(nombre, "gris_texto"))


def serie(i: int) -> str:
    """Color de la i-ésima serie de un gráfico (cíclico)."""
    s = _e()["series"]
    return color(s[i % len(s)])


def nivel_riesgo(puntaje: int) -> tuple[str, str, str]:
    """(color de fondo, texto del nivel, color del texto) para un puntaje P × I (semáforo con texto obligatorio)."""
    niveles = sorted(_e()["semaforo_riesgo"].values(), key=lambda n: -n["umbral_min"])
    for n in niveles:
        if puntaje >= n["umbral_min"]:
            oscuro = n["texto"] != "MEDIO"
            return n["color"], n["texto"], color("blanco") if oscuro else color("gris_texto")
    n = niveles[-1]
    return n["color"], n["texto"], color("blanco")


def fuentes() -> list[str]:
    t = _e()["tipografia"]
    return [t["principal"], t["alternativa"], "DejaVu Sans"]


# ==================================================================================================
# matplotlib
# ==================================================================================================
def configurar_matplotlib():
    """Aplica la identidad de CE01 a matplotlib y devuelve pyplot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from cycler import cycler
    f = _e()["figura"]
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": fuentes(),
        "font.size": 10,
        "axes.prop_cycle": cycler(color=[serie(i) for i in range(len(_e()["series"]))]),
        "axes.edgecolor": color("gris_medio"),
        "axes.labelcolor": color("gris_texto"),
        "axes.titlecolor": color("azul_upeu"),
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": color("gris_claro"),
        "grid.linewidth": 0.6,
        "xtick.color": color("gris_texto"),
        "ytick.color": color("gris_texto"),
        "legend.frameon": False,
        "savefig.dpi": f["dpi"],
        "savefig.facecolor": color("blanco"),
        "figure.dpi": 100,
    })
    return plt


def tamano(horizontal: bool = True, alto_cm: float | None = None) -> tuple[float, float]:
    """figsize en pulgadas: ancho útil de la página y alto (por defecto el máximo de CI-90)."""
    f = _e()["figura"]
    ancho = f["ancho_h_cm"] if horizontal else f["ancho_v_cm"]
    return ancho * CM, min(alto_cm or f["alto_max_cm"], f["alto_max_cm"]) * CM


def guardar(fig, ruta: Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=_e()["figura"]["dpi"], bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return ruta


def etiquetar_barras(ax, barras, fmt=lambda v: f"{v:g}", dentro: bool = False, horizontal: bool = False):
    """Escribe el valor en cada barra (el color nunca va solo). `dentro` lo centra en la barra, en blanco."""
    for b in barras:
        if horizontal:
            v = b.get_width()
            pos = (b.get_x() + (v / 2 if dentro else v), b.get_y() + b.get_height() / 2)
            ha, va, off = ("center" if dentro else "left"), "center", (0 if dentro else 3, 0)
        else:
            v = b.get_height()
            pos = (b.get_x() + b.get_width() / 2, b.get_y() + (v / 2 if dentro else v))
            ha, va, off = "center", ("center" if dentro else "bottom"), (0, 0 if dentro else 2)
        ax.annotate(fmt(v), pos, ha=ha, va=va, xytext=off, textcoords="offset points", fontsize=8.5,
                    color=color("blanco") if dentro else color("gris_texto"))


# ==================================================================================================
# draw.io, BPMN y XLSX
# ==================================================================================================
def drawio(relleno: str = "blanco", borde: str = "azul_upeu", grosor: int = 1, extra: str = "") -> str:
    """Estilo de celda de draw.io con la paleta de CE01 («azul_upeu» rellena con texto blanco, etc.)."""
    return (f"rounded=1;whiteSpace=wrap;html=1;fillColor={color(relleno)};strokeColor={color(borde)};"
            f"strokeWidth={grosor};fontColor={texto_sobre(relleno)};fontFamily={fuentes()[0]};fontSize=12;{extra}")


def bpmn_colores() -> dict[str, dict[str, str]]:
    """Colores BPMN (extensión bioc/color de BPMN-in-Color, que Bizagi y bpmn-js respetan)."""
    return {
        "pool":     {"fill": color("azul_muy_claro"), "stroke": color("azul_upeu")},
        "carril":   {"fill": color("blanco"),         "stroke": color("azul_medio")},
        "celeris":  {"fill": color("ambar_claro"),    "stroke": color("ambar_upeu")},   # carril nuevo del TO-BE
        "tarea":    {"fill": color("blanco"),         "stroke": color("azul_upeu")},
        "servicio": {"fill": color("ambar_claro"),    "stroke": color("ambar_upeu")},   # tareas automatizadas
        "evento":   {"fill": color("blanco"),         "stroke": color("azul_upeu")},
        "dolor":    {"fill": color("blanco"),         "stroke": "#C0392B"},           # anotación PD-xx
    }


def xlsx_estilos():
    """(cabecera, banda) como objetos openpyxl: cabecera azul UPeU con texto blanco, banda alterna azul muy claro."""
    from openpyxl.styles import Font, PatternFill
    hexa = lambda n: color(n).lstrip("#").upper()
    cab = {"fill": PatternFill("solid", fgColor=hexa("azul_upeu")),
           "font": Font(name=fuentes()[0], bold=True, color=hexa("blanco"))}
    banda = {"fill": PatternFill("solid", fgColor=hexa("azul_muy_claro"))}
    return cab, banda
