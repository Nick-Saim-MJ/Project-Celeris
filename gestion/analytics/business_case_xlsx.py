"""Libro del Business Case (CE01 E2): entregables/CE01/E2/Business_Case_E2.xlsx, con fórmulas vivas.

Lo llama gestion/analytics/business_case.py. Las hojas de cálculo determinista (Supuestos, AWS, CAPEX, OPEX, Beneficios,
Flujo, Indicadores, AHP, Matriz, TCO) usan fórmulas de Excel con nombres definidos (VNA/TIR = NPV/IRR); un cambio en la
hoja Supuestos se propaga a todo el libro. Monte Carlo, tornado, escenarios y riesgos son valores calculados en Python
(se rotulan así). verificar() recalcula el libro con Excel (COM) o LibreOffice y devuelve el VAN que calcula la hoja.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import ce01_datos as cd  # noqa: E402
import estilo_ce01 as est  # noqa: E402
from ce01_datos import s  # noqa: E402

USD = '"US$" #,##0.00'
USD0 = '"US$" #,##0'
PCT = "0.0%"


class _Libro:
    def __init__(self):
        self.wb = Workbook()
        self.wb.remove(self.wb.active)
        self.cab, self.banda = est.xlsx_estilos()

    def hoja(self, nombre: str, titulo: str, cabecera: list[str], anchos: list[int]):
        ws = self.wb.create_sheet(nombre)
        ws["A1"] = titulo
        ws["A1"].font = Font(name=est.fuentes()[0], bold=True, size=13, color=est.color("azul_upeu").lstrip("#"))
        for j, h in enumerate(cabecera, start=1):
            c = ws.cell(row=3, column=j, value=h)
            c.fill, c.font = self.cab["fill"], self.cab["font"]
            c.alignment = Alignment(wrap_text=True, vertical="center")
        for j, w in enumerate(anchos, start=1):
            ws.column_dimensions[get_column_letter(j)].width = w
        ws.freeze_panes = "A4"
        return ws

    def fila(self, ws, r: int, valores: list, formatos: dict | None = None):
        for j, v in enumerate(valores, start=1):
            c = ws.cell(row=r, column=j, value=v)
            c.font = Font(name=est.fuentes()[0], size=10)
            c.alignment = Alignment(wrap_text=isinstance(v, str) and not str(v).startswith("="), vertical="top")
            if (r - 4) % 2 == 1:
                c.fill = self.banda["fill"]
            if formatos and j in formatos:
                c.number_format = formatos[j]

    def nombre(self, nombre: str, ws, celda: str):
        col, fila = "".join(ch for ch in celda if ch.isalpha()), "".join(ch for ch in celda if ch.isdigit())
        self.wb.defined_names[nombre] = DefinedName(nombre, attr_text=f"'{ws.title}'!${col}${fila}")

    def nota(self, ws, r: int, texto: str):
        c = ws.cell(row=r, column=1, value=texto)
        c.font = Font(name=est.fuentes()[0], italic=True, size=9, color=est.color("gris_medio").lstrip("#"))


def escribir(r: dict, ruta: Path) -> Path:
    L = _Libro()
    y = cd.cargar()
    n = y["economia"]["horizonte_anios"]

    # ---------------------------------------------------------------- Supuestos
    ws = L.hoja("Supuestos", "Supuestos y parámetros del modelo (editar solo la columna C)",
                ["ID", "Parámetro", "Valor", "Unidad", "Fuente"], [9, 46, 14, 14, 60])
    params = [
        ("S-01", "PCs en alcance", "Pcs", s("S-01.pcs"), "PCs", None),
        ("S-02", "Enlace a Internet del campus", "Enlace", s("S-02.enlace_mbps"), "Mbps", None),
        ("S-03", "Costo de 1 Mbps adicional", "UsdMbps", s("S-03.usd_mbps_mes"), "US$/Mbps-mes", USD),
        ("S-04", "Byte hit ratio", "Bhr", s("S-04.bhr"), "fracción", PCT),
        ("S-06", "Ciclos de actualización por año", "Ciclos", s("S-06.ciclos_anio"), "por PC", None),
        ("S-07", "Horas técnicas ahorradas por PC y ciclo", "HorasPc", s("S-07.horas_pc_ciclo"), "h", None),
        ("S-07", "Tarifa de la hora técnica", "Tarifa", s("S-07.tarifa_usd_h"), "US$/h", USD),
        ("S-08", "Servidor físico ESX01", "Servidor", s("S-08.servidor_usd"), "US$", USD0),
        ("S-37", "Switch núcleo SW-CORE01", "Switch", s("S-37.switch_usd"), "US$", USD0),
        ("S-38", "UPS online UPS01", "Ups", s("S-38.ups_usd"), "US$", USD0),
        ("S-39", "Cableado y accesorios", "Cableado", s("S-39.cableado_usd"), "US$", USD0),
        ("S-09", "Tarifa eléctrica", "Kwh", s("S-09.usd_kwh"), "US$/kWh", USD),
        ("S-10", "COK", "Cok", s("S-10.cok"), "anual", PCT),
        ("S-41", "Mantenimiento anual del hardware", "Mant", s("S-41.mant_fraccion"), "fracción de I0", PCT),
        ("CI-77", "Consumo eléctrico del rack (centro_datos.yaml)", "ConsumoW", cd.costos()["consumo_w"], "W", None),
        ("—", "Horas por año", "HorasAnio", y["economia"]["horas_anio"], "h", None),
        ("CI-102", "Adopción del proxy (caso base)", "Adopcion", 1.0, "fracción", PCT),
        ("—", "Horizonte de evaluación", "Horizonte", n, "años", None),
    ]
    for k, (sid, txt, nom, val, uni, fmt) in enumerate(params):
        fila = 4 + k
        fuente = (cd.texto_supuesto(sid)["validacion"] if sid.startswith("S-") else
                  "infra/centro_datos.yaml → energia.consumo_w" if sid == "CI-77" else
                  "gestion/e2/datos/business_case.yaml (CI-102)" if sid == "CI-102" else "gestion/ce01.yaml → economia")
        L.fila(ws, fila, [sid, txt, val, uni, fuente], {3: fmt} if fmt else None)
        L.nombre(nom, ws, f"C{fila}")

    # ---------------------------------------------------------------- AWS
    ws = L.hoja("AWS", "Costo mensual AWS: líneas C1–C7 de infra/centro_datos.yaml [S-12]",
                ["ID", "Concepto", "Cantidad", "Unidad", "Precio unitario", "Subtotal"], [6, 44, 11, 11, 15, 15])
    lineas = cd.resolver(y["referencias"]["aws_lineas"])
    for k, l in enumerate(lineas):
        f = 4 + k
        L.fila(ws, f, [l["id"], l["concepto"], l["cantidad"], l["unidad"], l["precio_unitario"], f"=C{f}*E{f}"],
               {5: '"US$" #,##0.0000', 6: USD})
    ft = 4 + len(lineas)
    L.fila(ws, ft, ["", "Total mensual", "", "", "", f"=SUM(F4:F{ft - 1})"], {6: USD})
    L.fila(ws, ft + 1, ["", "Total anual (× 12)", "", "", "", f"=F{ft}*12"], {6: USD})
    L.nombre("AwsAnual", ws, f"F{ft + 1}")

    # ---------------------------------------------------------------- CAPEX
    ws = L.hoja("CAPEX", "Inversión inicial (I0)", ["ID", "Concepto", "US$", "Supuesto"], [8, 46, 14, 12])
    refs = {"S-08.servidor_usd": "Servidor", "S-37.switch_usd": "Switch", "S-38.ups_usd": "Ups", "S-39.cableado_usd": "Cableado"}
    for k, c in enumerate(y["economia"]["capex"]):
        L.fila(ws, 4 + k, [c["id"], c["concepto"], f"={refs[c['de']]}", c["de"].split(".")[0]], {3: USD0})
    ft = 4 + len(y["economia"]["capex"])
    L.fila(ws, ft, ["", "Total I0", f"=SUM(C4:C{ft - 1})", ""], {3: USD0})
    L.nombre("Capex", ws, f"C{ft}")

    # ---------------------------------------------------------------- OPEX
    ws = L.hoja("OPEX", "Costos anuales de operación y mantenimiento", ["ID", "Tipo", "Concepto", "US$/año", "Fórmula"],
                [8, 14, 36, 14, 50])
    forms = {"OX-1": "=AwsAnual", "OX-2": "=ConsumoW*HorasAnio/1000*Kwh", "OX-3": "=Mant*Capex"}
    for k, o in enumerate(y["economia"]["opex"]):
        L.fila(ws, 4 + k, [o["id"], o["tipo"], o["concepto"], forms[o["id"]], o["formula"]], {4: USD})
    ft = 4 + len(y["economia"]["opex"])
    L.fila(ws, ft, ["", "", "Total OPEX", f"=SUM(D4:D{ft - 1})", ""], {4: USD})
    L.nombre("Opex", ws, f"D{ft}")

    # ---------------------------------------------------------------- Beneficios
    ws = L.hoja("Beneficios", "Beneficios cuantificables anuales", ["ID", "Concepto", "US$/año", "Fórmula"], [8, 36, 14, 60])
    L.fila(ws, 4, ["BN-1", "Mbps de ampliación diferidos", "=Bhr*Enlace*Adopcion*UsdMbps*12",
                   "BHR [S-04] × enlace [S-02] × adopción (CI-102) × US$/Mbps-mes [S-03] × 12"], {3: USD})
    L.fila(ws, 5, ["BN-2", "Horas técnicas ahorradas", "=Pcs*Ciclos*HorasPc*Tarifa", "PCs [S-01] × ciclos [S-06] × h × tarifa [S-07]"],
           {3: USD})
    L.fila(ws, 6, ["", "Total", "=SUM(C4:C5)", ""], {3: USD})
    L.nombre("BenMbps", ws, "C4")
    L.nombre("BenHoras", ws, "C5")
    L.nombre("Beneficio", ws, "C6")

    # ---------------------------------------------------------------- Flujo
    ws = L.hoja("Flujo", "Flujo de caja del caso base", ["Concepto"] + [f"Año {t}" for t in range(n + 1)], [30] + [14] * (n + 1))
    cols = [get_column_letter(2 + t) for t in range(n + 1)]
    filas = [
        ("Inversión", ["=-Capex"] + [0] * n),
        ("Beneficios", [0] + ["=Beneficio"] * n),
        ("OPEX", [0] + ["=-Opex"] * n),
        ("Flujo neto", [f"=SUM({c}4:{c}6)" for c in cols]),
        ("Factor de descuento", [f"=1/(1+Cok)^{t}" for t in range(n + 1)]),
        ("Flujo descontado", [f"={c}7*{c}8" for c in cols]),
        ("Flujo acumulado", ["=B7"] + [f"={cols[t - 1]}10+{cols[t]}7" for t in range(1, n + 1)]),
    ]
    for k, (nom, vals) in enumerate(filas):
        L.fila(ws, 4 + k, [nom] + vals, {j: ("0.0000" if nom.startswith("Factor") else USD) for j in range(2, n + 3)})
    ultimo = cols[-1]

    # ---------------------------------------------------------------- Indicadores
    ws = L.hoja("Indicadores", "Indicadores del caso base (fórmulas de Excel) frente a Python",
                ["Indicador", "Excel", "Python", "Diferencia", "Fórmula"], [30, 16, 16, 14, 60])
    b = r["base"]
    ind = [
        ("VAN", f"=NPV(Cok,Flujo!C7:{ultimo}7)+Flujo!B7", b["van"], USD, "VNA(COK; flujos 1…n) + flujo 0"),
        ("TIR", f"=IRR(Flujo!B7:{ultimo}7)", b["tir"], PCT, "TIR(flujos 0…n)"),
        ("Payback (meses)", "=Capex/(Flujo!C7/12)", b["payback_meses"], "0.0", "I0 ÷ flujo neto mensual del año 1"),
        ("B/C", f"=NPV(Cok,Flujo!C5:{ultimo}5)/(Capex-NPV(Cok,Flujo!C6:{ultimo}6))", b["bc"], "0.00",
         "VA(beneficios) ÷ (I0 + VA(OPEX))"),
        ("ROI a 3 años", f"=(SUM(Flujo!C7:{ultimo}7)-Capex)/Capex", b["roi"], "0%", "(Σ flujos netos − I0) ÷ I0, sin descontar"),
        ("Factor de anualidad", f"=SUM(Flujo!C8:{ultimo}8)", b["factor_anualidad"], "0.0000", "Σ 1/(1+COK)^t"),
        ("Punto de equilibrio (Mbps)", "=(Capex/B9+Opex-BenHoras)/(UsdMbps*12)", r["equilibrio"]["mbps"], "0.0",
         "Mbps diferidos con VAN = 0"),
    ]
    for k, (nom, fx, py, fmt, txt) in enumerate(ind):
        f = 4 + k
        L.fila(ws, f, [nom, fx, py, f"=B{f}-C{f}", txt], {2: fmt, 3: fmt, 4: fmt})

    # ---------------------------------------------------------------- AHP
    ah = r["ahp"]
    crit = ah["criterios"]
    m = len(crit)
    ws = L.hoja("AHP", f"AHP: comparación por pares (Saaty); CR < {cd.num(0.10, 2)}",
                ["Criterio"] + crit + ["Media geométrica", "Peso", "(A·w)ᵢ", "λᵢ"], [10] + [8] * m + [16, 10, 10, 10])
    cg, cp, caw, cl = (get_column_letter(m + 2 + i) for i in range(4))
    for i, ci in enumerate(crit):
        f = 4 + i
        fila = [ci] + [float(x) for x in ah["matriz"][i]]
        fila += [f"=GEOMEAN(B{f}:{get_column_letter(m + 1)}{f})", f"={cg}{f}/SUM(${cg}$4:${cg}${3 + m})",
                 "=" + "+".join(f"{get_column_letter(2 + j)}{f}*${cp}${4 + j}" for j in range(m)), f"={caw}{f}/{cp}{f}"]
        L.fila(ws, f, fila, {**{j: "0.000" for j in range(2, m + 6)}})
    f0 = 4 + m + 1
    L.fila(ws, f0, ["λmax", f"=AVERAGE({cl}4:{cl}{3 + m})"], {2: "0.0000"})
    L.fila(ws, f0 + 1, ["CI", f"=(B{f0}-{m})/({m}-1)"], {2: "0.0000"})
    L.fila(ws, f0 + 2, ["RI", ah["ri"]], {2: "0.00"})
    L.fila(ws, f0 + 3, ["CR", f"=B{f0 + 1}/B{f0 + 2}", "Python:", ah["cr"]], {2: "0.0000", 4: "0.0000"})
    L.nombre("AhpCR", ws, f"B{f0 + 3}")

    # ---------------------------------------------------------------- TCO
    ws = L.hoja("TCO", "TCO a 3 años por alternativa (mismas partidas del modelo)",
                ["Alternativa", "Inversión", "Costo anual", "TCO nominal", "TCO valor actual", "Puntaje C3"],
                [34, 14, 14, 14, 16, 12])
    tco = r["tco"]
    ids = list(tco)
    for k, aid in enumerate(ids):
        f = 4 + k
        L.fila(ws, f, [f"{aid} {r['decision']['filas'][aid]['nombre']}", tco[aid]["capex"], tco[aid]["opex_anual"],
                       f"=B{f}+C{f}*Horizonte", f"=B{f}+C{f}*Indicadores!B9",
                       f"=ROUND(1+4*(MAX($D$4:$D${3 + len(ids)})-D{f})/(MAX($D$4:$D${3 + len(ids)})-MIN($D$4:$D${3 + len(ids)})),1)"],
               {2: USD0, 3: USD0, 4: USD0, 5: USD0, 6: "0.0"})
    L.nota(ws, 5 + len(ids), "Inversión y costo anual: partidas CX-x y OX-x que usa cada alternativa (business_case.yaml); "
                             "A0 compra los Mbps diferidos [S-40]; A5 es cota inferior [levantar con la DTI].")

    # ---------------------------------------------------------------- Matriz
    dec = r["decision"]
    ws = L.hoja("Matriz", "Matriz de decisión ponderada (pesos AHP)", ["Alternativa"] + crit + ["Total", "Puesto"],
                [34] + [8] * m + [10, 8])
    L.fila(ws, 4, ["Peso (AHP)"] + [f"=AHP!{cp}{4 + j}" for j in range(m)] + ["", ""], {j: "0.000" for j in range(2, m + 2)})
    for k, aid in enumerate(ids):
        f = 5 + k
        p = dec["filas"][aid]["puntajes"]
        valores = [f"{aid} {dec['filas'][aid]['nombre']}"] + p
        jc3 = crit.index("C3")
        valores[1 + jc3] = f"=TCO!F{4 + k}"
        valores += [f"=SUMPRODUCT(B{f}:{get_column_letter(m + 1)}{f},$B$4:${get_column_letter(m + 1)}$4)",
                    f"=RANK({get_column_letter(m + 2)}{f},${get_column_letter(m + 2)}$5:${get_column_letter(m + 2)}${4 + len(ids)})"]
        L.fila(ws, f, valores, {**{j: "0.0" for j in range(2, m + 2)}, m + 2: "0.00"})

    # ---------------------------------------------------------------- Valores calculados en Python
    mc = r["montecarlo"]
    ws = L.hoja("MonteCarlo", f"Monte Carlo: {mc['iteraciones']} iteraciones, semilla {mc['semilla']} (valores de Python)",
                ["Medida", "Valor"], [36, 16])
    for k, (nom, v, fmt) in enumerate([("P(VAN > 0)", mc["p_van_positivo"], PCT), ("P5", mc["p5"], USD0),
                                       ("P50", mc["p50"], USD0), ("P95", mc["p95"], USD0), ("Media", mc["media"], USD0),
                                       ("Desviación estándar", mc["desv"], USD0), ("Mínimo", mc["min"], USD0),
                                       ("Máximo", mc["max"], USD0)]):
        L.fila(ws, 4 + k, [nom, v], {2: fmt})
    f = 14
    L.fila(ws, f - 1, ["Variable (triangular)", "Mínimo", "Moda", "Máximo"])
    for k, t in enumerate(r["tornado"]):
        L.fila(ws, f + k, [f"{t['nombre']} [{t['supuesto']}]", t["min"], t["moda"], t["max"]])

    ws = L.hoja("Tornado", "Tornado: VAN con cada variable en su mínimo y su máximo (valores de Python)",
                ["Variable", "VAN en el mínimo", "VAN en el máximo", "Recorrido"], [36, 16, 16, 16])
    for k, t in enumerate(r["tornado"]):
        L.fila(ws, 4 + k, [f"{t['nombre']} [{t['supuesto']}]", t["van_min"], t["van_max"], f"=ABS(C{4 + k}-B{4 + k})"],
               {2: USD0, 3: USD0, 4: USD0})

    ws = L.hoja("Escenarios", "Escenarios pesimista, base y optimista (valores de Python)",
                ["Escenario", "BHR", "US$/Mbps", "Adopción", "AWS", "I0", "VAN", "TIR", "Payback (meses)", "B/C"],
                [14, 9, 10, 10, 8, 8, 14, 10, 14, 8])
    for k, e in enumerate(r["escenarios"]):
        p = e["param"]
        L.fila(ws, 4 + k, [e["nombre"], p["bhr"], p["usd_mbps"], p["adopcion"], p["f_aws"], p["f_capex"], e["van"],
                           e["tir"] if e["tir"] is not None else "—",
                           e["payback_meses"] if e["payback_meses"] is not None else "no se recupera", e["bc"]],
               {2: PCT, 3: USD, 4: PCT, 5: "0.00", 6: "0.00", 7: USD0, 8: PCT, 9: "0.0", 10: "0.00"})

    ws = L.hoja("Riesgos", "Efecto económico de RE-01…RE-12 (VAN con su escenario de estrés; valores de Python)",
                ["ID", "Riesgo", "P", "I", "P × I", "Nivel", "Escenario de estrés", "VAN", "ΔVAN"],
                [8, 44, 5, 5, 7, 9, 46, 14, 14])
    for k, x in enumerate(r["riesgos"]):
        f = 4 + k
        L.fila(ws, f, [x["id"], x["riesgo"], x["p"], x["i"], f"=C{f}*D{f}", f'=IF(E{f}>=15,"ALTO",IF(E{f}>=8,"MEDIO","BAJO"))',
                       x["efecto"], x["van"], f"=H{f}-Indicadores!B4"], {8: USD0, 9: USD0})

    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    L.wb.save(ruta)
    return ruta


# ==================================================================================================
# Recalcular con Excel (COM) o LibreOffice y leer el VAN
# ==================================================================================================
def _excel(ruta: Path) -> bool:
    if os.name != "nt" or not shutil.which("powershell"):
        return False
    ps = (f"$ErrorActionPreference='Stop'; $x = New-Object -ComObject Excel.Application; $x.Visible=$false; "
          f"$x.DisplayAlerts=$false; try {{ $wb = $x.Workbooks.Open('{ruta.resolve()}'); $x.CalculateFull(); $wb.Save(); "
          f"$wb.Close($true) }} finally {{ $x.Quit() }}")
    try:
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True,
                           timeout=180)
        return p.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def _libreoffice(ruta: Path) -> bool:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        return False
    with tempfile.TemporaryDirectory() as d:
        perfil = Path(d) / "perfil"
        try:
            subprocess.run([exe, f"-env:UserInstallation={perfil.as_uri()}", "--headless", "--calc", "--convert-to", "xlsx",
                            "--outdir", d, str(ruta)], check=True, capture_output=True, timeout=240)
        except (subprocess.SubprocessError, OSError):
            return False
        hecho = Path(d) / ruta.name
        if not hecho.exists():
            return False
        shutil.copyfile(hecho, ruta)
    return True


def verificar(ruta: Path) -> float | None:
    """Recalcula el libro (Excel o LibreOffice), lo deja guardado con los valores y devuelve el VAN de la hoja."""
    ruta = Path(ruta)
    if not (_excel(ruta) or _libreoffice(ruta)):
        return None
    wb = load_workbook(ruta, data_only=True)
    errores = [f"{ws.title}!{c.coordinate} = {c.value}" for ws in wb for fila in ws.iter_rows() for c in fila
               if isinstance(c.value, str) and c.value.startswith(("#VALUE", "#REF", "#NAME", "#DIV", "#N/A", "#NUM"))]
    if errores:
        raise RuntimeError("El XLSX tiene fórmulas con error: " + "; ".join(errores[:5]))
    ws = wb["Indicadores"]
    distintos = [f"{ws.cell(row=f, column=1).value}: Excel {ws.cell(row=f, column=2).value} ≠ Python {ws.cell(row=f, column=3).value}"
                 for f in range(5, ws.max_row + 1) if ws.cell(row=f, column=4).value is not None
                 and abs(ws.cell(row=f, column=4).value) > 1e-6 * max(1.0, abs(ws.cell(row=f, column=3).value or 0))]
    if distintos:
        raise RuntimeError("El XLSX y Python no coinciden: " + "; ".join(distintos))
    van = ws["B4"].value
    return float(van) if van is not None else None
