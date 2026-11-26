"""Plantilla de cronometraje de CE01 E4 (CE0132, CI-104): gestion/e4/instrumentos/registro-tiempos.xlsx.

    python gestion/e4/instrumentos.py

Hojas: «Instrucciones», «Registro» (una fila por observación; la duración en minutos es una fórmula), «Resumen»
(observaciones, media, mínimo y máximo por proceso y fase con COUNTIFS/AVERAGEIFS/MINIFS/MAXIFS; estado «Medido» con
≥ 30 observaciones o «Estimado [S-43]»; estimación del modelo para comparar) y «Fases» (qué se cronometra en cada fase).
La estimación del modelo es la media de las triangulares de gestion/e4/simulacion.yaml, o la fórmula de descarga de
gestion/e4/procesos.py: no se escribe a mano.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI))
import estilo_ce01 as est  # noqa: E402

SALIDA = AQUI / "instrumentos" / "registro-tiempos.xlsx"
FILAS = 400


def _estimacion_min(nodos: list[str], pid: str, sim: dict, k: dict) -> float | None:
    if not nodos:
        return None
    ns = {n["id"]: n for n in sim["procesos"][pid]["nodos"]}
    total = 0.0
    for nid in nodos:
        n = ns[nid]
        if "calculo" in n:
            total += k[n["calculo"]]
        else:
            total += sum(n["tri"]) / 3 * (k["pcs"] if n.get("por_pc") else 1)
    return total * 60


def escribir(car: dict, sim: dict | None = None, k: dict | None = None) -> Path:
    import procesos
    sim = sim or procesos.sim()
    k = k or procesos.calculos()
    cab, banda = est.xlsx_estilos()
    obs_min = car["cronometraje"]["observaciones_min"]
    fases = car["cronometraje"]["fases"]
    wb = Workbook()

    ws = wb.active
    ws.title = "Instrucciones"
    lineas = [
        ("Registro de tiempos de los procesos P1 y P2 (CE01 E4)", True),
        ("Para qué: reemplazar las duraciones estimadas [S-43] del modelo por duraciones medidas.", False),
        (f"Regla: una fase pasa de «Estimado [S-43]» a «Medido» con al menos {obs_min} observaciones (hoja Resumen).", False),
        ("Cómo: en la hoja Registro, una fila por fase observada; anote la hora de inicio y de fin (hh:mm) y la duración se calcula sola.", False),
        ("Proceso: P1 = actualización masiva de un laboratorio; P2 = preparación de un laboratorio para una clase.", False),
        ("Escenario: AS-IS hasta el piloto; TO-BE durante el piloto (S2), con la misma plantilla.", False),
        ("Interrumpida: «Sí» si una clase cortó la descarga (P1); alimenta el indicador KPI-5 y la probabilidad de S-44.", False),
        ("No registre nombres de estudiantes ni datos personales: solo el rol del responsable (técnico, encargado, docente).", False),
        ("Fuente de las estimaciones: gestion/e4/simulacion.yaml y gestion/e4/procesos.py (no editar a mano).", False),
    ]
    for i, (t, negrita) in enumerate(lineas, start=1):
        ws.cell(i, 1, t).font = Font(name=est.fuentes()[0], bold=negrita, size=13 if negrita else 11)
    ws.column_dimensions["A"].width = 120

    wr = wb.create_sheet("Registro")
    cabecera = ["N.º", "Fecha", "Proceso", "Escenario", "Laboratorio", "Fase", "Inicio (hh:mm)", "Fin (hh:mm)",
                "Duración (min)", "PCs", "Interrumpida", "Responsable (rol)", "Observaciones"]
    for j, h in enumerate(cabecera, start=1):
        c = wr.cell(1, j, h)
        c.fill, c.font = cab["fill"], cab["font"]
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i in range(2, FILAS + 2):
        wr.cell(i, 1, i - 1)
        wr.cell(i, 2).number_format = "dd/mm/yyyy"
        wr.cell(i, 7).number_format = "hh:mm"
        wr.cell(i, 8).number_format = "hh:mm"
        wr.cell(i, 9, f'=IF(AND(G{i}<>"",H{i}<>""),ROUND(MOD(H{i}-G{i},1)*1440,1),"")')
        if i % 2 == 0:
            for j in range(1, len(cabecera) + 1):
                wr.cell(i, j).fill = banda["fill"]
    for col, w in zip("ABCDEFGHIJKLM", (6, 12, 9, 10, 13, 14, 12, 12, 12, 7, 12, 18, 40)):
        wr.column_dimensions[col].width = w
    wr.freeze_panes = "A2"
    for col, opciones in (("C", "P1,P2"), ("D", "AS-IS,TO-BE"), ("F", ",".join(f["fase"] for f in fases)), ("K", "Sí,No"),
                          ("L", "Técnico,Encargado,Docente")):
        dv = DataValidation(type="list", formula1=f'"{opciones}"', allow_blank=True)
        wr.add_data_validation(dv)
        dv.add(f"{col}2:{col}{FILAS + 1}")

    rs = wb.create_sheet("Resumen")
    cab_r = ["Proceso", "Fase", "Observaciones", "Media medida (min)", "Mínimo (min)", "Máximo (min)", "Estado",
             "Estimación del modelo (min)", "Diferencia"]
    for j, h in enumerate(cab_r, start=1):
        c = rs.cell(1, j, h)
        c.fill, c.font = cab["fill"], cab["font"]
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    rango = f"Registro!$I$2:$I${FILAS + 1}"
    r = 2
    for proc, pid, clave in (("P1", "P1-AS-IS", "nodos_p1"), ("P2", "P2-AS-IS", "nodos_p2")):
        for f in fases:
            if not f[clave]:
                continue
            cond = f'Registro!$C$2:$C${FILAS + 1},"{proc}",Registro!$D$2:$D${FILAS + 1},"AS-IS",Registro!$F$2:$F${FILAS + 1},"{f["fase"]}"'
            est_min = _estimacion_min(f[clave], pid, sim, k)
            fila = [proc, f["fase"], f"=COUNTIFS({cond})", f'=IFERROR(AVERAGEIFS({rango},{cond}),"—")',
                    f'=IF(C{r}=0,"—",MINIFS({rango},{cond}))', f'=IF(C{r}=0,"—",MAXIFS({rango},{cond}))',
                    f'=IF(C{r}>={obs_min},"Medido","Estimado [S-43]")', round(est_min, 1),
                    f'=IF(ISNUMBER(D{r}),D{r}/H{r}-1,"—")']
            for j, v in enumerate(fila, start=1):
                c = rs.cell(r, j, v)
                if j == 9:
                    c.number_format = "0%"
                if r % 2 == 1:
                    c.fill = banda["fill"]
            r += 1
    for col, w in zip("ABCDEFGHI", (9, 14, 14, 18, 13, 13, 17, 22, 12)):
        rs.column_dimensions[col].width = w
    rs.cell(r + 1, 1, "La estimación del modelo es la media de la distribución triangular de cada tarea [S-43] o la fórmula "
                      "de descarga [S-26, S-27, S-42]. La espera de la DTI (fase Decisión de P2) se mide en minutos de calendario.")

    wf = wb.create_sheet("Fases")
    for j, h in enumerate(["Fase", "Qué se cronometra en P1", "Qué se cronometra en P2"], start=1):
        c = wf.cell(1, j, h)
        c.fill, c.font = cab["fill"], cab["font"]
    for i, f in enumerate(fases, start=2):
        for j, v in enumerate((f["fase"], f["p1"], f["p2"]), start=1):
            wf.cell(i, j, v)
    for col, w in zip("ABC", (14, 50, 50)):
        wf.column_dimensions[col].width = w

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    wb.save(SALIDA)
    return SALIDA


if __name__ == "__main__":
    car = yaml.safe_load((AQUI / "datos" / "procesos.yaml").read_text(encoding="utf-8"))
    print(escribir(car))
