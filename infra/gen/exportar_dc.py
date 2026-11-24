"""Exporta los .drawio de entregables/CE0331/diagramas/ a PNG (escala 3, margen 10; menor si el PNG pasaría de ~8000 px, límite de draw.io
Desktop: ver exportar_drawio.escala_png y V-108) y PDF vectorial, ambos con el XML embebido.

Orden de preferencia (igual que CE0311, infra/gen/exportar_drawio.py):
 1. draw.io Desktop, si está (variable DRAWIO, PATH o rutas habituales): es el método de CE0311.
 2. Sin draw.io: el respaldo de este módulo. Lee el mismo .drawio, lo dibuja en HTML/SVG (cajas, bordes, textos, enlaces y
    glifos simples en lugar de los stencils de draw.io) y lo exporta con Microsoft Edge o Chrome sin interfaz. El .drawio sigue siendo
    el editable: al abrirlo en draw.io se ven los íconos de redes y de AWS. Lo exportado así se rotula en docs/infra/e2/exportacion.json.

    python infra/gen/exportar_dc.py [--dir entregables/CE0331/diagramas] [--forzar-respaldo]
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from celeris_infra import RAIZ  # noqa: E402
import exportar_drawio as ed  # noqa: E402

DIR = RAIZ / "entregables" / "CE0331" / "diagramas"
REGISTRO = RAIZ / "docs" / "infra" / "e2" / "exportacion.json"
ESCALA = 3
MARGEN = 10
NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/microsoft-edge", "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

GLIFOS = {   # glifos de 24×24 (trazo currentColor) para los stencils de draw.io que el respaldo no puede dibujar
    "server": '<rect x="3" y="3" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><circle cx="7" cy="6.5" r="1"/><circle cx="7" cy="16.5" r="1"/>',
    "virtual_server": '<rect x="3" y="3" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M12 10v3M8 6.5h8M8 16.5h8"/>',
    "switch": '<rect x="2" y="8" width="20" height="8" rx="1.5"/><path d="M6 12h12M15 10l3 2-3 2M9 10l-3 2 3 2"/>',
    "firewall": '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9.3h18M3 14.6h18M9 4v5.3M15 9.3v5.3M9 14.6V20"/>',
    "ups_enterprise": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M13 7l-4 6h4l-2 4"/>',
    "terminal": '<rect x="3" y="4" width="18" height="13" rx="1.5"/><path d="M7 9l3 2.5L7 14M12 14h5M9 20h6"/>',
    "laptop": '<rect x="5" y="5" width="14" height="10" rx="1"/><path d="M2 19h20l-2-4H4z"/>',
    "pc": '<rect x="3" y="4" width="18" height="12" rx="1"/><path d="M9 20h6M12 16v4"/>',
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="1"/><path d="M9 20h6M12 16v4"/>',
    "proxy_server": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 12h10M13 8l4 4-4 4"/>',
    "web_server": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    "secured": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    "wireless_hub": '<path d="M3 9c5-5 13-5 18 0M6 12.5c3.5-3.5 8.5-3.5 12 0M9 16c1.7-1.7 4.3-1.7 6 0"/><circle cx="12" cy="19" r="1"/>',
    "nas_filer": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18"/>',
}
SIGLAS_AWS = {"ec2": "EC2", "s3": "S3", "vpn_gateway": "VGW", "vpn_connection": "VPN"}


def navegador() -> str | None:
    return next((c for c in [os.environ.get("NAVEGADOR", "")] + NAVEGADORES if c and Path(c).is_file()), None)


# --------------------------------------------------------------------------------------------------
# .drawio → HTML
# --------------------------------------------------------------------------------------------------
def estilo(s: str) -> dict[str, str]:
    d = {}
    for p in (s or "").split(";"):
        if not p:
            continue
        k, _, v = p.partition("=")
        d[k] = v if _ else "1"
    return d


def num(v, defecto=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return defecto


def leer(ruta: Path):
    raiz = ET.parse(ruta).getroot()
    modelo = raiz.find("diagram/mxGraphModel")
    celdas = []
    for nodo in modelo.find("root"):
        if nodo.tag == "object":
            cell, label = nodo.find("mxCell"), nodo.get("label", "")
        else:
            cell, label = nodo, nodo.get("value", "")
        if cell is None or cell.get("id") in ("0", "1") or cell.get("style") is None:
            continue
        g = cell.find("mxGeometry")
        celdas.append({"id": nodo.get("id") or cell.get("id"), "label": label, "estilo": estilo(cell.get("style")), "geo": g,
                       "arista": cell.get("edge") == "1", "origen": cell.get("source"), "destino": cell.get("target")})
    return celdas, modelo


def glifo(st: dict[str, str]) -> str | None:
    shape = st.get("shape", "")
    if shape.startswith("mxgraph.networks."):
        clave = shape.split(".", 2)[2]
        trazo = GLIFOS.get(clave)
        return f'<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="{st.get("strokeColor", "#4D4D4D")}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{trazo}</svg>' if trazo else None
    if shape.startswith("mxgraph.aws4.resourceIcon"):
        sig = SIGLAS_AWS.get(st.get("resIcon", "").split(".")[-1], "AWS")
        return f'<div style="width:100%;height:100%;background:{st.get("fillColor", "#ED7100")};border-radius:3px;color:#fff;font:bold 7px Arial;display:flex;align-items:center;justify-content:center">{sig}</div>'
    return None


def caja_html(c: dict) -> str:
    st, g = c["estilo"], c["geo"]
    x, y, w, h = (num(g.get(k)) for k in ("x", "y", "width", "height"))
    ico = glifo(st)
    if ico is not None and not c["label"]:
        return f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px">{ico}</div>'
    if st.get("shape") == "cloud" or st.get("ellipse") == "1" and st.get("shape") == "cloud":
        radio = "45%"
    elif st.get("ellipse") == "1":
        radio = "50%"
    elif st.get("rounded") == "1":
        radio = f"{min(w, h) * num(st.get('arcSize', '10')) / 100:.0f}px"
    else:
        radio = "0"
    fill = st.get("fillColor", "none")
    stroke = st.get("strokeColor", "none")
    sw = num(st.get("strokeWidth", "1"), 1)
    borde = "none" if stroke == "none" else f"{sw}px {'dashed' if st.get('dashed') == '1' else 'solid'} {stroke}"
    if st.get("dashed") == "1" and st.get("dashPattern", "").startswith(("1 ", "2 ", "3 ")):
        borde = f"{sw}px dotted {stroke}"
    ali = {"left": "flex-start", "center": "center", "right": "flex-end"}.get(st.get("align", "center"), "center")
    ver = {"top": "flex-start", "middle": "center", "bottom": "flex-end"}.get(st.get("verticalAlign", "middle"), "center")
    txt_al = st.get("align", "center")
    pad = f"padding:{num(st.get('spacingTop', '0'))}px {num(st.get('spacingRight', '0')) + 4}px 0 {num(st.get('spacingLeft', '0')) + 4}px;"
    fs = num(st.get("fontSize", "12"), 12)
    estilo_css = (f"position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;border:{borde};border-radius:{radio};"
                  f"background:{'transparent' if fill == 'none' else fill};{pad}display:flex;flex-direction:column;justify-content:{ver};"
                  f"align-items:{ali};text-align:{txt_al};font:{fs}px/{fs * 1.22:.1f}px Helvetica,Arial,sans-serif;color:{st.get('fontColor', '#1A1A1A')};")
    return f'<div style="{estilo_css}"><div style="width:100%">{c["label"]}</div></div>'


def arista_html(c: dict, por_id: dict) -> str:
    st, g = c["estilo"], c["geo"]
    pts = []
    if g is not None:
        sp = g.find("mxPoint[@as='sourcePoint']")
        tp = g.find("mxPoint[@as='targetPoint']")
        mid = [(num(p.get("x")), num(p.get("y"))) for p in g.findall("Array[@as='points']/mxPoint")]
        if sp is not None and tp is not None:
            pts = [(num(sp.get("x")), num(sp.get("y")))] + mid + [(num(tp.get("x")), num(tp.get("y")))]
    if not pts and c["origen"] in por_id and c["destino"] in por_id:
        a, b = por_id[c["origen"]]["geo"], por_id[c["destino"]]["geo"]
        pts = [(num(a.get("x")) + num(a.get("width")) / 2, num(a.get("y")) + num(a.get("height")) / 2),
               (num(b.get("x")) + num(b.get("width")) / 2, num(b.get("y")) + num(b.get("height")) / 2)]
    if len(pts) < 2:
        return ""
    color, sw = st.get("strokeColor", "#1A1A1A"), num(st.get("strokeWidth", "1"), 1)
    dash = ""
    if st.get("dashed") == "1":
        dash = f' stroke-dasharray="{st.get("dashPattern", "6 4").replace(" ", ",")}"'
    fin = st.get("endArrow", "none")
    marca = f' marker-end="url(#{"cruz" if fin == "cross" else "punta"})"' if fin in ("block", "cross") else ""
    d = " ".join(("M" if i == 0 else "L") + f"{px},{py}" for i, (px, py) in enumerate(pts))
    salida = f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{dash}{marca} stroke-linejoin="round"/>'
    if c["label"]:     # etiqueta en el medio del tramo más largo
        tramos = list(zip(pts, pts[1:]))
        (x1, y1), (x2, y2) = max(tramos, key=lambda t: abs(t[1][0] - t[0][0]) + abs(t[1][1] - t[0][1]))
        fs = num(st.get("fontSize", "10"), 10)
        salida += (f'<foreignObject x="{(x1 + x2) / 2 - 300}" y="{(y1 + y2) / 2 - 10}" width="600" height="20"><div xmlns="http://www.w3.org/1999/xhtml" '
                   f'style="display:flex;justify-content:center"><span style="background:#fff;padding:0 3px;font:{fs}px Helvetica,Arial,sans-serif;'
                   f'color:#1A1A1A;white-space:nowrap">{c["label"]}</span></div></foreignObject>')
    return salida


def a_html(ruta: Path) -> tuple[str, int, int]:
    celdas, modelo = leer(ruta)
    por_id = {c["id"]: c for c in celdas if not c["arista"]}
    ancho = alto = 0
    for c in celdas:
        g = c["geo"]
        if g is None:
            continue
        if not c["arista"]:
            ancho = max(ancho, num(g.get("x")) + num(g.get("width")))
            alto = max(alto, num(g.get("y")) + num(g.get("height")))
    W, H = int(ancho + 2 * MARGEN), int(alto + 2 * MARGEN)
    partes = []
    for c in celdas:
        if c["arista"]:
            a = arista_html(c, por_id)
            if a:
                partes.append(f'<svg style="position:absolute;left:0;top:0;overflow:visible" width="{W}" height="{H}"><defs>'
                              '<marker id="punta" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#1A1A1A"/></marker>'
                              '<marker id="cruz" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M1,1 L9,9 M9,1 L1,9" stroke="#1A1A1A" stroke-width="2"/></marker>'
                              f'</defs>{a}</svg>')
        elif c["geo"] is not None:
            partes.append(caja_html(c))
    cuerpo = "\n".join(partes)
    doc = (f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{html.escape(ruta.stem)}</title><style>@page{{size:{W}px {H}px;margin:0}}'
           f'html,body{{margin:0;padding:0;background:#fff}}#l{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#fff}}'
           f'#i{{position:absolute;left:{MARGEN}px;top:{MARGEN}px}}</style></head><body><div id="l"><div id="i">{cuerpo}</div></div></body></html>')
    return doc, W, H


# --------------------------------------------------------------------------------------------------
# Exportar
# --------------------------------------------------------------------------------------------------
def incrustar_png(png: Path, xml: str) -> None:
    from PIL import Image
    from PIL.PngImagePlugin import PngInfo
    meta = PngInfo()
    meta.add_text("mxfile", urllib.parse.quote(xml, safe=""))
    with Image.open(png) as im:
        im.load()
        Image.MAX_IMAGE_PIXELS = None
        im.save(png, pnginfo=meta, optimize=True)


def incrustar_pdf(pdf: Path, xml: str) -> None:
    import fitz
    doc = fitz.open(pdf)
    meta = doc.metadata or {}
    meta["subject"] = urllib.parse.quote(xml, safe="")
    doc.set_metadata(meta)
    tmp = pdf.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=0, deflate=True)
    doc.close()
    tmp.replace(pdf)


def exportar_respaldo(nav: str, origen: Path) -> list[Path]:
    xml = origen.read_text(encoding="utf-8")
    doc, W, H = a_html(origen)
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "figura.html"
        pagina.write_text(doc, encoding="utf-8")
        url = pagina.as_uri()
        png, pdf = origen.with_suffix(".png"), origen.with_suffix(".pdf")
        base = [nav, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", f"--user-data-dir={Path(tmp) / 'perfil'}"]
        r = subprocess.run(base + [f"--screenshot={png}", f"--window-size={W},{H}", f"--force-device-scale-factor={ESCALA}", url],
                           capture_output=True, text=True, timeout=240)
        if not png.exists():
            raise RuntimeError(f"El navegador no exportó {png.name}: {r.stderr.strip()[-300:]}")
        r = subprocess.run(base + [f"--print-to-pdf={pdf}", "--no-pdf-header-footer", "--virtual-time-budget=2000", url],
                           capture_output=True, text=True, timeout=240)
        if not pdf.exists():
            raise RuntimeError(f"El navegador no exportó {pdf.name}: {r.stderr.strip()[-300:]}")
    incrustar_png(png, xml)
    incrustar_pdf(pdf, xml)
    return [png, pdf]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(DIR))
    ap.add_argument("--forzar-respaldo", action="store_true", help="no usar draw.io aunque esté instalado")
    a = ap.parse_args(argv)
    exe = None if a.forzar_respaldo else ed.drawio()
    nav = navegador()
    if not exe and not nav:
        print("error: no hay draw.io Desktop ni Edge/Chrome. No se exportó nada (defina DRAWIO o NAVEGADOR).", file=sys.stderr)
        return 2
    motor = "draw.io Desktop" if exe else f"respaldo propio con {Path(nav).stem} sin interfaz (sin draw.io Desktop)"
    escalas = {}
    for origen in sorted(Path(a.dir).glob("DC-*.drawio")):
        hechos = ed.exportar(exe, origen) if exe else exportar_respaldo(nav, origen)
        escalas[origen.stem] = ed.escala_png(origen) if exe else ESCALA
        for h in hechos:
            print(h.relative_to(RAIZ) if h.is_relative_to(RAIZ) else h)
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(json.dumps({"motor": motor, "escala_png": escalas, "nota": "Con el respaldo, los stencils de draw.io se dibujan como glifos; "
                                    "el .drawio conserva los íconos de draw.io y es el editable. Con draw.io Desktop: python infra/gen/exportar_dc.py"},
                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"motor: {motor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
