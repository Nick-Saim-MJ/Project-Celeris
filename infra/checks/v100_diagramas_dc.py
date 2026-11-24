"""Gancho V-100+ — Diagramas DC-0…DC-3 del Entregable 2 contra centro_datos.yaml y el inventario (lógica en infra/gen/drawio_dc_check.py)."""
import sys
from pathlib import Path

GRUPO = "E2"
PRIMER_ID = "V-100"
DESCRIPCION = "Diagramas del centro de datos (DC-0…DC-3): archivos, IDs, cobertura, IP, criticidad, VLAN y recursos"

_INFRA = Path(__file__).resolve().parents[1]
for _p in (str(_INFRA), str(_INFRA / "gen")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def run(infra):
    import drawio_dc_check as chk
    from validate import Hallazgo, Resultado

    chequeos, cob = chk.comprobar(infra)
    chk.escribir(cob)
    return [Resultado(c.id, c.titulo, c.estado, [Hallazgo(h.nivel, h.mensaje, h.corregir) for h in c.hallazgos]) for c in chequeos]
