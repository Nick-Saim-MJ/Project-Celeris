"""Regenera las figuras de CE01 (make figuras-ce01).

    python gestion/figuras_ce01.py [--entregable E1]

Cada entregable deja su generador en gestion/eN/figuras/generar.py, con una función main() que escribe los PNG
(matplotlib) y los .drawio + PNG (draw.io Desktop) usando gestion/estilo_ce01.py. Este script solo los llama en
orden; si un entregable aún no tiene generador, lo informa y sigue.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entregable", choices=("E1", "E2", "E3", "E4"))
    a = ap.parse_args(argv)
    codigo = 0
    for ent in [a.entregable] if a.entregable else ["E1", "E2", "E3", "E4"]:
        gen = AQUI / ent.lower() / "figuras" / "generar.py"
        if not gen.exists():
            print(f"CE01 {ent}: sin generador de figuras todavía ({gen.relative_to(AQUI.parent).as_posix()})")
            continue
        spec = importlib.util.spec_from_file_location(f"figuras_{ent.lower()}", gen)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        r = mod.main() or 0
        print(f"CE01 {ent}: figuras {'regeneradas' if r == 0 else 'con errores'}")
        codigo = codigo or r
    return codigo


if __name__ == "__main__":
    sys.exit(main())
