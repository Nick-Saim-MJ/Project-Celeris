"""Exporta cada .drawio de entregables/CE0311/diagramas/ a PNG (escala 3, fondo blanco) y PDF vectorial,
ambos con el XML embebido para que sigan siendo editables en draw.io (P3).

Necesita draw.io Desktop (https://github.com/jgraph/drawio-desktop). Se busca en DRAWIO, en el PATH y en las
rutas de instalación habituales de Windows, macOS y Linux. Sin draw.io, termina con código 2 y no simula nada.

    python infra/gen/exportar_drawio.py [--dir entregables/CE0311/diagramas]
"""
from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import RAIZ  # noqa: E402

DIR = RAIZ / "entregables" / "CE0311" / "diagramas"
CANDIDATOS = [
    os.environ.get("DRAWIO", ""),
    shutil.which("drawio") or "", shutil.which("draw.io") or "",
    str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "draw.io" / "draw.io.exe"),
    r"C:\Program Files\draw.io\draw.io.exe",
    "/Applications/draw.io.app/Contents/MacOS/draw.io",
    "/usr/bin/drawio", "/opt/drawio/drawio", "/snap/bin/drawio",
]


def drawio() -> str | None:
    return next((c for c in CANDIDATOS if c and Path(c).is_file()), None)


# draw.io Desktop recorta el PNG cuando pasa de ~8192 px de ancho o de alto: dibuja solo una parte y deja el resto en blanco
# (se vio en DC-2: a escala 3 eran 8437 px y quedó con contenido solo en el 51 % superior; a 2,9 sale completo). Por eso la escala
# se calcula por figura: 3 si cabe y, si no, la mayor que deje ancho y alto bajo ANCHO_MAX_PX y el área bajo PIXELES_MAX.
ESCALA_PNG = 3.0
MARGEN_PX = 10
ANCHO_MAX_PX = 8000
PIXELES_MAX = int(2 ** 25 * 0.95)


def extension(origen: Path) -> tuple[float, float, float, float]:
    """Caja que ocupa el dibujo (x0, y0, x1, y1): celdas con geometría absoluta y puntos intermedios de los enlaces."""
    xs, ys = [], []
    for g in ET.parse(origen).getroot().iter("mxGeometry"):
        if g.get("width") is not None and g.get("relative") != "1":
            x, y, w, h = (float(g.get(k, 0)) for k in ("x", "y", "width", "height"))
            xs += [x, x + w]
            ys += [y, y + h]
        for pt in g.iter("mxPoint"):
            if pt.get("x") is not None and pt.get("y") is not None:
                xs.append(float(pt.get("x")))
                ys.append(float(pt.get("y")))
    if not xs:
        raise ValueError(f"{origen.name} no tiene celdas con geometría")
    return min(xs), min(ys), max(xs), max(ys)


def escala_png(origen: Path) -> float:
    x0, y0, x1, y1 = extension(origen)
    ancho, alto = x1 - x0 + 2 * MARGEN_PX, y1 - y0 + 2 * MARGEN_PX
    s = min(ESCALA_PNG, ANCHO_MAX_PX / ancho, ANCHO_MAX_PX / alto, math.sqrt(PIXELES_MAX / (ancho * alto)))
    return math.floor(s * 100) / 100


def exportar(exe: str, origen: Path) -> list[Path]:
    hechos = []
    base = [exe, "--no-sandbox", "--disable-gpu"] if sys.platform.startswith("linux") else [exe]
    trabajos = [
        (origen.with_suffix(".png"), ["-x", "-f", "png", "-s", f"{escala_png(origen):g}", "-b", str(MARGEN_PX), "-e"]),
        (origen.with_suffix(".pdf"), ["-x", "-f", "pdf", "-b", "10", "-e", "--crop"]),
    ]
    for destino, args in trabajos:
        r = subprocess.run(base + args + ["-o", str(destino), str(origen)], capture_output=True, text=True, timeout=180)
        if r.returncode != 0 or not destino.exists():
            raise RuntimeError(f"draw.io no exportó {destino.name}: {r.stderr.strip() or r.stdout.strip()}")
        hechos.append(destino)
    return hechos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(DIR))
    a = ap.parse_args(argv)
    exe = drawio()
    if not exe:
        print("error: no se encontró draw.io Desktop (defina DRAWIO=ruta al ejecutable). No se exportó nada.", file=sys.stderr)
        return 2
    for origen in sorted(Path(a.dir).glob("FIG-*.drawio")):
        for h in exportar(exe, origen):
            print(h.relative_to(RAIZ) if h.is_relative_to(RAIZ) else h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
