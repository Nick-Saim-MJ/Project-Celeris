"""V-108 — Cada PNG exportado está completo: es el dibujo entero y no una parte.

Por qué existe: draw.io Desktop recorta el PNG cuando pasa de ~8192 px de ancho o de alto (DC-2 a escala 3 midió 8437 px y solo tenía
contenido en el 51 % superior, sin error de exportación; el PDF y el .drawio seguían bien, así que V-50 y V-100 no lo vieron).

Para CADA .drawio de entregables/CE0311/diagramas/ y entregables/CE0331/diagramas/ se comprueba sobre el PNG:
  a) tiene la misma proporción que el dibujo (caja de las celdas + margen de exportación), con 1,5 % de tolerancia;
  b) tiene la misma proporción que el PDF (que se exporta recortado al dibujo), con 3 % de tolerancia;
  c) hay contenido no blanco hasta ≥ 90 % del alto y del ancho;
  d) todo `celeris_id` de una celda del .drawio tiene contenido no blanco en su rectángulo del PNG (es decir, se dibujó).
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from celeris_infra import RAIZ  # noqa: E402
import drawio_check as dc  # noqa: E402
import exportar_drawio as ed  # noqa: E402

DIRECTORIOS = [RAIZ / "entregables" / "CE0311" / "diagramas", RAIZ / "entregables" / "CE0331" / "diagramas"]
UMBRAL_BLANCO = 245          # un píxel con luminosidad < 245 cuenta como contenido
TOL_DIBUJO = 0.015
TOL_PDF = 0.03
MIN_CUBIERTO = 0.90


def celdas_con_id(ruta: Path) -> list[tuple[str, float, float, float, float]]:
    salida = []
    for nodo in ET.parse(ruta).getroot().iter():
        if nodo.tag != "object" or not nodo.get("celeris_id"):
            continue
        celda = nodo.find("mxCell")
        if celda is None or celda.get("edge") == "1":
            continue
        g = celda.find("mxGeometry")
        if g is None or g.get("width") is None:
            continue
        salida.append((nodo.get("celeris_id"), *(float(g.get(k, 0)) for k in ("x", "y", "width", "height"))))
    return salida


def comprobar_figura(ruta: Path, c: "dc.Chequeo") -> dict:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    png, pdf = ruta.with_suffix(".png"), ruta.with_suffix(".pdf")
    if not png.exists():
        return {}                                   # lo avisan V-50 y V-100
    x0, y0, x1, y1 = ed.extension(ruta)
    bw, bh = x1 - x0 + 2 * ed.MARGEN_PX, y1 - y0 + 2 * ed.MARGEN_PX
    with Image.open(png) as im:
        w, h = im.size
        mascara = im.convert("L").point(lambda p: 255 if p < UMBRAL_BLANCO else 0)
    info = {"px": [w, h], "proporcion": round(w / h, 3)}
    esperada = bw / bh
    if abs(w / h - esperada) / esperada > TOL_DIBUJO:
        c.e(f"{png.name}: proporción {w / h:.3f} ≠ {esperada:.3f} del dibujo (¿recortado o con otro encuadre?)", "python infra/gen/exportar_dc.py (o exportar_drawio.py)")
    if pdf.exists():
        try:
            from pypdf import PdfReader
            mb = PdfReader(str(pdf)).pages[0].mediabox
            rp = float(mb.width) / float(mb.height)
            info["proporcion_pdf"] = round(rp, 3)
            if abs(w / h - rp) / rp > TOL_PDF:
                c.e(f"{png.name}: proporción {w / h:.3f} ≠ {rp:.3f} de {pdf.name}", "Vuelva a exportar PNG y PDF juntos")
        except ImportError:
            c.w("Falta pypdf: no se comparó el PNG con el PDF", "pip install -r infra/requirements.txt")
    caja = mascara.getbbox()
    if caja is None:
        c.e(f"{png.name}: está en blanco", "Vuelva a exportar")
        return info
    cubierto_y, cubierto_x = caja[3] / h, caja[2] / w
    info["contenido_alto_pct"], info["contenido_ancho_pct"] = round(cubierto_y * 100), round(cubierto_x * 100)
    if cubierto_y < MIN_CUBIERTO or cubierto_x < MIN_CUBIERTO:
        c.e(f"{png.name}: solo tiene contenido en el {cubierto_y * 100:.0f} % del alto y el {cubierto_x * 100:.0f} % del ancho (mín. {MIN_CUBIERTO * 100:.0f} %)",
            "draw.io recorta pasado ~8192 px: python infra/gen/exportar_dc.py baja la escala por figura")
    ex, ey = w / bw, h / bh
    ausentes = []
    ids = celdas_con_id(ruta)
    for cid, x, y, cw, ch in ids:
        r = (int((x - x0 + ed.MARGEN_PX + 2) * ex), int((y - y0 + ed.MARGEN_PX + 2) * ey),
             int((x - x0 + ed.MARGEN_PX + cw - 2) * ex), int((y - y0 + ed.MARGEN_PX + ch - 2) * ey))
        r = (max(r[0], 0), max(r[1], 0), min(max(r[2], r[0] + 1), w), min(max(r[3], r[1] + 1), h))
        if mascara.crop(r).getbbox() is None:
            ausentes.append(cid)
    info["ids"] = len(ids)
    info["ids_ausentes"] = len(ausentes)
    if ausentes:
        c.e(f"{png.name}: {len(ausentes)} de {len(ids)} celeris_id del .drawio no están dibujados en el PNG ({', '.join(ausentes[:8])}{'…' if len(ausentes) > 8 else ''})",
            "Vuelva a exportar; si persiste, baje ESCALA_PNG en infra/gen/exportar_drawio.py")
    return info


def comprobar(infra=None, directorios: list[Path] | None = None):
    c = dc.Chequeo("V-108", "PNG de cada figura (CE0311 y CE0331) completo: contenido en todo el alto y ancho, misma proporción que el dibujo y el PDF, todo celeris_id dibujado")
    resumen = {}
    n = 0
    for d in directorios or DIRECTORIOS:
        for ruta in sorted(d.glob("*.drawio")):
            n += 1
            resumen[ruta.stem] = comprobar_figura(ruta, c)
    if n == 0:
        c.e("No hay ningún .drawio que revisar", "Genere los diagramas")
    else:
        c.hallazgos.append(dc.Hallazgo("info", f"{n} figuras revisadas · escala de exportación por figura: máx. {ed.ESCALA_PNG:g}, ancho/alto ≤ {ed.ANCHO_MAX_PX} px", ""))
    return [c]


def main() -> int:
    mal = False
    for c in comprobar():
        print(f"{c.id} {c.estado}: {c.titulo}")
        for h in c.hallazgos:
            print(f"   [{h.nivel}] {h.mensaje} {('→ ' + h.corregir) if h.corregir else ''}")
        mal |= c.estado == "FALLA"
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main())
