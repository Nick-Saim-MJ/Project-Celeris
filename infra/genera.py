#!/usr/bin/env python3
"""Genera los artefactos del laboratorio emulado desde infra/*.yaml (Etapa 1).

    python infra/genera.py [nftables|vpn|pac|todo] [--salida lab/generated] [--modo piloto|gestionado]
                           [--ventana] [--wan-ip IP] [--aws-peer IP --aws-peer IP] [--secretos DIR]

`lab` genera lab/celeris.clab.yml, lab/generated/ y la PKI de laboratorio (lab/.run/, fuera de git). `vpn` y `todo` necesitan las IP públicas de los dos extremos AWS (--aws-peer ×2): el inventario solo dice
«asignadas por AWS» (CI-23). Las llaves precompartidas se generan al vuelo en --secretos (fuera del control de versiones).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from celeris_infra import RAIZ, Infra  # noqa: E402
from gen import lab, nftables, pac, vpn  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("que", nargs="?", default="todo", choices=["nftables", "vpn", "pac", "todo", "lab"])
    ap.add_argument("--salida", default=str(RAIZ / "lab" / "generated"))
    ap.add_argument("--secretos", default=str(RAIZ / "lab" / ".run" / "secretos"))
    ap.add_argument("--modo", default="piloto", choices=["piloto", "gestionado"])
    ap.add_argument("--ventana", action="store_true", help="activa F24 (señuelo): exige autorización escrita de la DTI")
    ap.add_argument("--wan-ip")
    ap.add_argument("--aws-peer", action="append", default=[])
    a = ap.parse_args(argv)
    x = Infra.cargar()
    salida = Path(a.salida)
    hechos = []
    if a.que in ("nftables", "todo"):
        hechos.append(nftables.main(x, salida, modo=a.modo, ventana=a.ventana, wan_ip=a.wan_ip, aws_peers=a.aws_peer or None))
    if a.que in ("pac", "todo"):
        hechos.append(pac.main(x, salida))
    if a.que in ("vpn", "todo"):
        if not a.aws_peer:
            print("error: --aws-peer (×2) es obligatorio para la VPN: el inventario no fija las IP públicas de AWS (CI-23)", file=sys.stderr)
            return 2
        hechos += vpn.main(x, salida, a.aws_peer, a.wan_ip, Path(a.secretos))
    if a.que == "lab":
        hechos += lab.generar_todo(x, RAIZ / "lab", RAIZ / "docs" / "AVISO.md")
    for h in hechos:
        print(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
