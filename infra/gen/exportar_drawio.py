"""Exporta cada .drawio de entregables/CE0311/diagramas/ a PNG (escala 3, fondo blanco) y PDF vectorial,
ambos con el XML embebido para que sigan siendo editables en draw.io (P3).

Necesita draw.io Desktop (https://github.com/jgraph/drawio-desktop). Se busca en DRAWIO, en el PATH y en las
rutas de instalación habituales de Windows, macOS y Linux. Sin draw.io, termina con código 2 y no simula nada.

    python infra/gen/exportar_drawio.py [--dir entregables/CE0311/diagramas]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
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


def exportar(exe: str, origen: Path) -> list[Path]:
    hechos = []
    base = [exe, "--no-sandbox", "--disable-gpu"] if sys.platform.startswith("linux") else [exe]
    trabajos = [
        (origen.with_suffix(".png"), ["-x", "-f", "png", "-s", "3", "-b", "10", "-e"]),
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
