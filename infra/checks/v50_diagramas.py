"""Gancho V-50+ — Diagramas draw.io: componentes, IP, zonas, colores (Okabe-Ito), flujos F-nn y criticidad contra el inventario.

La lógica está en infra/gen/drawio_check.py (también se ejecuta solo con `make diagrams-check`). Este gancho la llama con el
`Infra` ya cargado por validate.py, convierte cada chequeo a `Resultado` y regenera docs/infra/e1/cobertura-figuras.md.
"""
import sys
from pathlib import Path

GRUPO = "P2"
PRIMER_ID = "V-50"
DESCRIPCION = "Diagramas draw.io: componentes, IP, zonas, colores (Okabe-Ito), flujos F-nn y criticidad contra el inventario"

_INFRA = Path(__file__).resolve().parents[1]
for _p in (str(_INFRA), str(_INFRA / "gen")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def run(infra):
    import drawio_check
    from validate import Hallazgo, Resultado

    chequeos, cobertura = drawio_check.comprobar(infra)
    drawio_check.escribir_informe(infra, chequeos, cobertura)
    return [Resultado(c.id, c.titulo, c.estado, [Hallazgo(h.nivel, h.mensaje, h.corregir) for h in c.hallazgos],
                      "Detalle y matriz componente × figura en docs/infra/e1/cobertura-figuras.md" if c.id == PRIMER_ID else "")
            for c in chequeos]
