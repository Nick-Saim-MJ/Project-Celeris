"""Libro de matrices del E1: entregables/CE01/E1/Matrices_Diagnostico_E1.xlsx.

    python gestion/e1/xlsx_matrices.py

Una hoja por matriz larga del informe (FODA/TOWS, PESTEL, FCE, inventario, brechas, problemas, riesgos), con los mismos
datos que las tablas del DOCX (gestion/e1/tablas.py). Donde hay cálculo, la celda tiene fórmula viva: puntaje = P × I
(o impacto × frecuencia) y nivel = SI(puntaje ≥ 15; «ALTO»; SI(puntaje ≥ 8; «MEDIO»; «BAJO»)). Estilo de la paleta UPeU
(gestion/estilo_ce01.py, CI-100).
"""
from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent))
import ce01_datos as cd  # noqa: E402
import estilo_ce01 as est  # noqa: E402
import tablas  # noqa: E402

SALIDA = cd.RAIZ / "entregables" / "CE01" / "E1" / "Matrices_Diagnostico_E1.xlsx"

HOJAS = [
    ("FODA", "t-foda", None),
    ("TOWS", "t-tows", None),
    ("PESTEL", "t-pestel", None),
    ("FCE", "t-fce", None),
    ("Inventario", "t-inventario", None),
    ("Brechas", "t-brechas", None),
    ("Problemas", "t-problemas", ("Impacto", "Frecuencia", "Puntaje", "Nivel")),
    ("Riesgos", "t-riesgos", ("P", "I", "P × I", "Nivel")),
]


def _hoja(wb, nombre, tid, calculo):
    spec = tablas.TABLAS[tid]
    filas = spec["filas"]()
    ws = wb.create_sheet(nombre)
    ws["A1"] = spec["titulo"]
    ws["A1"].font = Font(name=est.fuentes()[0], bold=True, size=13, color=est.color("azul_upeu").lstrip("#"))
    ws["A2"] = f"Fuente: {spec['fuente']}"
    ws["A2"].font = Font(name=est.fuentes()[0], italic=True, size=9, color=est.color("gris_medio").lstrip("#"))
    cab, banda = est.xlsx_estilos()
    r0 = 4
    for c, v in enumerate(filas[0], 1):
        cel = ws.cell(r0, c, v)
        cel.fill, cel.font = cab["fill"], cab["font"]
        cel.alignment = Alignment(wrap_text=True, vertical="center")
    idx = {}
    if calculo:
        idx = {k: filas[0].index(k) + 1 for k in calculo}
    for i, fila in enumerate(filas[1:], 1):
        r = r0 + i
        for c, v in enumerate(fila, 1):
            if calculo and c in (idx[calculo[0]], idx[calculo[1]]):
                v = int(v)
            ws.cell(r, c, v)
        if calculo:
            a, b = get_column_letter(idx[calculo[0]]), get_column_letter(idx[calculo[1]])
            p = get_column_letter(idx[calculo[2]])
            ws.cell(r, idx[calculo[2]], f"={a}{r}*{b}{r}")
            ws.cell(r, idx[calculo[3]], f'=IF({p}{r}>=15,"ALTO",IF({p}{r}>=8,"MEDIO","BAJO"))')
        for c in range(1, len(fila) + 1):
            cel = ws.cell(r, c)
            cel.alignment = Alignment(wrap_text=True, vertical="top")
            cel.font = Font(name=est.fuentes()[0], size=10)
            if i % 2 == 0:
                cel.fill = banda["fill"]
    if calculo:
        col = get_column_letter(idx[calculo[3]])
        rng = f"{col}{r0 + 1}:{col}{r0 + len(filas) - 1}"
        for texto, nivel in (("ALTO", "alto"), ("MEDIO", "medio"), ("BAJO", "bajo")):
            color = cd.estilo()["semaforo_riesgo"][nivel]["color"].lstrip("#")
            ws.conditional_formatting.add(rng, FormulaRule(formula=[f'{col}{r0 + 1}="{texto}"'],
                                                           fill=PatternFill("solid", fgColor=color)))
    for c in range(1, len(filas[0]) + 1):
        largo = max(len(str(f[c - 1])) for f in filas)
        ws.column_dimensions[get_column_letter(c)].width = max(8, min(60, largo * 0.9))
    ws.freeze_panes = ws.cell(r0 + 1, 1)


def main() -> int:
    wb = Workbook()
    ws = wb.active
    ws.title = "Léame"
    ws["A1"] = "Matrices del Entregable 1 — Diagnóstico organizacional y alineamiento estratégico (CE01)"
    ws["A1"].font = Font(name=est.fuentes()[0], bold=True, size=14, color=est.color("azul_upeu").lstrip("#"))
    for k, t in enumerate([
        "Generado por gestion/e1/xlsx_matrices.py desde gestion/e1/datos/*.yaml, gestion/ce01.yaml e infra/trazabilidad.yaml.",
        "No editar aquí: los cambios se hacen en las fuentes y se regenera (make informe-ce01-e1).",
        "Fórmulas vivas: Problemas y Riesgos calculan el puntaje (columna × columna) y el nivel (ALTO ≥ 15, MEDIO 8–14, BAJO ≤ 7).",
        "Marcas: [S-xx] supuesto del registro común; [levantar con la DTI] dato institucional pendiente.",
    ], 3):
        ws.cell(k, 1, t).font = Font(name=est.fuentes()[0], size=10)
    ws.column_dimensions["A"].width = 120
    for nombre, tid, calculo in HOJAS:
        _hoja(wb, nombre, tid, calculo)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    wb.save(SALIDA)
    print(f"  {SALIDA.relative_to(cd.RAIZ).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
