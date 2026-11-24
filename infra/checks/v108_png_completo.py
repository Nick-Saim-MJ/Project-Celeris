"""Gancho V-108 — Los PNG de CE0311 y CE0331 están completos (lógica en infra/gen/png_completo_check.py)."""
import sys
from pathlib import Path

GRUPO = "E2"
PRIMER_ID = "V-108"
DESCRIPCION = "PNG de las figuras completos: contenido en todo el alto, proporción igual a la del dibujo y el PDF, todo celeris_id dibujado"

_INFRA = Path(__file__).resolve().parents[1]
for _p in (str(_INFRA), str(_INFRA / "gen")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def run(infra):
    import png_completo_check as chk
    from validate import Hallazgo, Resultado

    return [Resultado(c.id, c.titulo, c.estado, [Hallazgo(h.nivel, h.mensaje, h.corregir) for h in c.hallazgos]) for c in chk.comprobar(infra)]
