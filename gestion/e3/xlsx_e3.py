"""Libros del Plan de Gestión (CE01 E3), con fórmulas vivas, verificados con Excel (COM) o LibreOffice.

    entregables/CE01/E3/Presupuesto_EVM_E3.xlsx  presupuesto por actividad y por paquete de la EDT, línea base, reservas,
                                                 valor planificado semanal (curva S) y EVM a la fecha de corte
    entregables/CE01/E3/Backlog_E3.xlsx          backlog con WSJF, sprints, capacidad, burn-up, DoR, DoD y métricas

Lo llama gestion/e3/plan.py. Las horas, duraciones, fechas de la línea base y parámetros son entradas (hoja Parámetros y
columnas de horas); el resto son fórmulas de Excel con nombres definidos (DIAS.LAB = NETWORKDAYS con la lista de feriados
del calendario del plan). La hoja Control compara cada total de Excel con el de Python: si una diferencia supera el
céntimo, verificar() falla.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

AQUI = Path(__file__).resolve().parent
GESTION = AQUI.parent
sys.path.insert(0, str(GESTION))
sys.path.insert(0, str(AQUI))
import plan as P  # noqa: E402

_spec = importlib.util.spec_from_file_location("bc_xlsx", GESTION / "analytics" / "business_case_xlsx.py")
bx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bx)

USD, USD0, PCT, FECHA = bx.USD, bx.USD0, bx.PCT, "dd/mm/yyyy"
PRESUPUESTO = P.SALIDA / "Presupuesto_EVM_E3.xlsx"
BACKLOG = P.SALIDA / "Backlog_E3.xlsx"
ERRORES_XL = ("#VALUE", "#REF", "#NAME", "#DIV", "#N/A", "#NUM")


def _d(t) -> dt.date:
    return P.fecha(t)


def _control(L, filas: list[tuple[str, str, float]]):
    """Hoja Control: concepto, fórmula de Excel, valor de Python y diferencia."""
    ws = L.hoja("Control", "Control: Excel frente a Python (la diferencia debe ser 0)",
                ["Concepto", "Excel", "Python", "Diferencia"], [52, 16, 16, 14])
    for k, (txt, formula, py) in enumerate(filas):
        f = 4 + k
        L.fila(ws, f, [txt, formula, py, f"=B{f}-C{f}"], {2: "#,##0.00", 3: "#,##0.00", 4: "0.0000"})
    return ws


# ==================================================================================================
# Presupuesto y EVM
# ==================================================================================================
def presupuesto(m: dict, ruta: Path = PRESUPUESTO) -> Path:
    L = bx._Libro()
    cfg = P.plan()
    pres, ev = m["presupuesto"], m["evm"]
    cf = pres["costos_fijos"]
    eq = P.equipo()

    # ------------------------------------------------------------ Parámetros
    ws = L.hoja("Parámetros", "Parámetros del presupuesto (editar solo la columna C)",
                ["ID", "Parámetro", "Valor", "Unidad", "Fuente"], [9, 46, 14, 14, 62])
    aws = cfg["costos"]["aws"]
    params = [
        ("S-07", "Tarifa de la hora del equipo", "Tarifa", pres["tarifa"], "US$/h", USD),
        ("B3.5", "Reserva de contingencia (dentro de la línea base)", "Contingencia", cfg["costos"]["contingencia"], "del BAC", PCT),
        ("B3.5", "Reserva de gestión (fuera de la línea base)", "Gestion", cfg["costos"]["gestion"], "de la línea base", PCT),
        ("B3.5", "Umbral de alerta de CPI y SPI", "Umbral", cfg["costos"]["umbral_alerta"], "índice", "0.00"),
        ("B3.5", "Herramientas (licencias libres o educativas)", "Herramientas", pres["herramientas"], "US$", USD),
        ("E2", "Hardware del rack (CAPEX del business case)", "Hardware", cf["capex"], "US$", USD),
        ("CI-103", "Horas del Modo A durante el despliegue del piloto", "HorasEfimero", aws["horas_efimero"], "h", None),
        ("S-12", "Costo por hora del laboratorio efímero (Modo A)", "UsdHoraEfimero", cf["_usd_h_efimero"], "US$/h", '"US$" #,##0.0000'),
        ("T59", "Horas del simulacro de recuperación", "HorasSimulacro", cf["_horas_simulacro"], "h", None),
        ("S-12", "Costo por hora del simulacro", "UsdHoraSimulacro", cf["_usd_h_simulacro"], "US$/h", '"US$" #,##0.0000'),
        ("CI-103", "Meses de EC2-GW, VPN y S3 durante el piloto", "Meses247", aws["meses_24x7"], "meses", None),
        ("S-12", "Costo mensual de AWS 24×7 (C1–C7)", "AwsMensual", P.cd.aws_mensual(), "US$/mes", USD),
    ]
    for k, (sid, txt, nom, val, uni, fmt) in enumerate(params):
        f = 4 + k
        L.fila(ws, f, [sid, txt, val, uni, "gestion/e3/datos/plan.yaml; infra/centro_datos.yaml; gestion/ce01.yaml"],
               {3: fmt} if fmt else None)
        L.nombre(nom, ws, f"C{f}")
    f = 4 + len(params) + 1
    L.fila(ws, f, ["", "Costo fijo «capex»", "=Hardware", "US$", "Actividad 5.1.2"], {3: USD})
    L.nombre("CF_capex", ws, f"C{f}")
    L.fila(ws, f + 1, ["", "Costo fijo «aws_efimero»", "=HorasEfimero*UsdHoraEfimero+HorasSimulacro*UsdHoraSimulacro", "US$",
                       "Actividad 5.5.2"], {3: USD})
    L.nombre("CF_aws_efimero", ws, f"C{f + 1}")
    L.fila(ws, f + 2, ["", "Costo fijo «aws_24x7»", "=Meses247*AwsMensual", "US$", "Actividad 5.5.3"], {3: USD})
    L.nombre("CF_aws_24x7", ws, f"C{f + 2}")

    # ------------------------------------------------------------ Feriados (calendario del plan)
    ws = L.hoja("Feriados", "Días no laborables del calendario del plan (feriados y receso)", ["Fecha", "Motivo"], [14, 70])
    fila = 4
    for e in cfg["calendario"]["excepciones"]:
        d, h = _d(e["desde"]), _d(e["hasta"])
        while d <= h:
            if d.weekday() < 5:
                L.fila(ws, fila, [d, e["nombre"]], {1: FECHA})
                fila += 1
            d += dt.timedelta(days=1)
    L.wb.defined_names["Feriados"] = bx.DefinedName("Feriados", attr_text=f"'Feriados'!$A$4:$A${fila - 1}")

    # ------------------------------------------------------------ Actividades
    cab = ["ID", "Paquete", "Actividad", "Inicio LB", "Fin LB", "Días", "Horas Nick", "Horas Henyelrey",
           "Horas equipo", "Costo horas", "Tipo costo fijo", "Costo fijo", "Total", "Terminada", "Fin real", "Python"]
    ws = L.hoja("Actividades", "Presupuesto por actividad (línea base: duraciones planificadas)", cab,
                [8, 8, 46, 12, 12, 7, 9, 10, 9, 12, 14, 12, 12, 10, 12, 12])
    acts = [f for f in m["filas"] if not f["hito"]]
    for k, a in enumerate(acts):
        r = 4 + k
        h = a["horas"]
        tipo = a["costo_fijo_tipo"] or ""
        L.fila(ws, r, [a["id"], a["paquete"], a["nombre"], _d(a["lb_inicio"]), _d(a["lb_fin"]),
                       f"=NETWORKDAYS(D{r},E{r},Feriados)", h.get("Nick", 0), h.get("Henyelrey", 0),
                       f"=G{r}+H{r}", f"=I{r}*Tarifa", tipo, f'=IF(K{r}="",0,INDIRECT("CF_"&K{r}))', f"=J{r}+L{r}",
                       "Sí" if a["hecha"] else "No", _d(a["fin"]) if a["hecha"] else None, a["costo"]],
               {4: FECHA, 5: FECHA, 10: USD, 12: USD, 13: USD, 15: FECHA, 16: USD})
    ult = 3 + len(acts)
    L.fila(ws, ult + 1, ["", "", "Total de actividades", "", "", "", f"=SUM(G4:G{ult})", f"=SUM(H4:H{ult})",
                         f"=SUM(I4:I{ult})", f"=SUM(J4:J{ult})", "", f"=SUM(L4:L{ult})", f"=SUM(M4:M{ult})"],
           {10: USD, 12: USD, 13: USD})
    for c in ws[ult + 1]:
        c.font = Font(name=c.font.name, bold=True, size=10)
    L.nota(ws, ult + 3, "Solo se valorizan las horas del equipo (S-07). Las de la DTI, los encargados y el docente son aporte "
                        "institucional y están en el XML de MS Project, sin costo. Días = DIAS.LAB con la hoja Feriados.")
    rng = lambda col: f"Actividades!${col}$4:${col}${ult}"

    # ------------------------------------------------------------ Paquetes de la EDT
    ws = L.hoja("Paquetes", "Presupuesto por paquete de la EDT (nivel 2) y por área (nivel 1)",
                ["Paquete", "Nombre", "Horas equipo", "Costo horas", "Costo fijo", "Total", "% del BAC", "Python"],
                [9, 40, 12, 13, 13, 13, 10, 13])
    paq = list(pres["paquetes"].items())
    for k, (pid, p) in enumerate(paq):
        r = 4 + k
        L.fila(ws, r, [pid, p["nombre"], f'=SUMIF({rng("B")},A{r},{rng("I")})', f'=SUMIF({rng("B")},A{r},{rng("J")})',
                       f'=SUMIF({rng("B")},A{r},{rng("L")})', f"=D{r}+E{r}", f"=F{r}/BAC", p["total"]],
               {4: USD, 5: USD, 6: USD, 7: PCT, 8: USD})
    up = 3 + len(paq)
    L.fila(ws, up + 1, ["", "Total de paquetes", f"=SUM(C4:C{up})", f"=SUM(D4:D{up})", f"=SUM(E4:E{up})", f"=SUM(F4:F{up})",
                        f"=SUM(G4:G{up})"], {4: USD, 5: USD, 6: USD, 7: PCT})
    r0 = up + 3
    L.fila(ws, r0, ["Nivel 1", "Área", "Horas equipo", "", "", "Total", "% del BAC"])
    for c in ws[r0]:
        c.font = Font(name=c.font.name, bold=True, size=10)
    for k, (n1, v) in enumerate(pres["nivel1"].items()):
        r = r0 + 1 + k
        L.fila(ws, r, [n1, v["nombre"], f'=SUMPRODUCT((LEFT($A$4:$A${up},LEN(A{r})+1)=A{r}&".")*$C$4:$C${up})', "", "",
                       f'=SUMPRODUCT((LEFT($A$4:$A${up},LEN(A{r})+1)=A{r}&".")*$F$4:$F${up})', f"=F{r}/BAC", v["total"]],
               {6: USD, 7: PCT, 8: USD})

    # ------------------------------------------------------------ Línea base
    ws = L.hoja("Línea base", "Línea base de costos y reservas (el proyecto, no el servicio del business case)",
                ["Concepto", "Fórmula", "US$", "Python"], [44, 40, 15, 15])
    filas = [
        ("Presupuesto de las actividades (BAC)", "Σ paquetes + herramientas", f"=Paquetes!F{up + 1}+Herramientas", pres["bac"], "BAC"),
        ("Reserva de contingencia", "BAC × contingencia", "=BAC*Contingencia", pres["contingencia"], "Reserva_cont"),
        ("Línea base de costos", "BAC + contingencia", "=BAC+Reserva_cont", pres["linea_base"], "Linea_base"),
        ("Reserva de gestión (fuera de la línea base)", "Línea base × gestión", "=Linea_base*Gestion", pres["gestion"], "Reserva_gest"),
        ("Presupuesto total autorizado", "Línea base + reserva de gestión", "=Linea_base+Reserva_gest", pres["total_autorizado"], "Total_aut"),
    ]
    for k, (txt, fx, formula, py, nom) in enumerate(filas):
        r = 4 + k
        L.fila(ws, r, [txt, fx, formula, py], {3: USD, 4: USD})
        L.nombre(nom, ws, f"C{r}")
    r = 4 + len(filas) + 1
    c = P.cd.costos()
    L.fila(ws, r, ["Comparación con el business case (E2)", "", "", ""])
    ws.cell(row=r, column=1).font = Font(name=bx.est.fuentes()[0], bold=True, size=10)
    L.fila(ws, r + 1, ["Inversión inicial del servicio (I₀, E2)", "CX-1…CX-4", c["capex_total"], ""], {3: USD})
    L.fila(ws, r + 2, ["Costo operativo anual del servicio (E2)", "OX-1…OX-3", c["opex_total"], ""], {3: USD})
    L.fila(ws, r + 3, ["Parte de la línea base que es inversión del E2", "Hardware / línea base", "=Hardware/Linea_base", ""], {3: PCT})
    L.nota(ws, r + 5, "La línea base mide lo que cuesta ejecutar el proyecto hasta el cierre; el business case mide lo que "
                      "cuesta y rinde el servicio en su horizonte. Solo el hardware es común a ambos.")

    # ------------------------------------------------------------ PV por semana (curva S)
    semanas = [_d(s["fecha"]) for s in ev["semanas"]]
    cortes = [_d(c["fecha"]) for c in ev["cortes"]]
    columnas = semanas + [d for d in cortes if d not in semanas]
    ws = L.hoja("PV semanal", "Valor planificado por actividad al cierre de cada viernes (y en cada corte)",
                ["ID", "Total", "Inicio LB", "Fin LB"] + [d.strftime("%d/%m/%Y") for d in columnas],
                [8, 11, 11, 11] + [11] * len(columnas))
    for j, d in enumerate(columnas):
        ws.cell(row=2, column=5 + j, value=d).number_format = FECHA
    for k, a in enumerate(acts):
        r = 4 + k
        fa = 4 + k
        vals = [f"=Actividades!A{fa}", f"=Actividades!M{fa}", f"=Actividades!D{fa}", f"=Actividades!E{fa}"]
        for j in range(len(columnas)):
            col = get_column_letter(5 + j)
            vals.append(f"=IF({col}$2<$C{r},0,$B{r}*NETWORKDAYS($C{r},MIN({col}$2,$D{r}),Feriados)/NETWORKDAYS($C{r},$D{r},Feriados))")
        L.fila(ws, r, vals, {2: USD, 3: FECHA, 4: FECHA, **{5 + j: USD for j in range(len(columnas))}})
    up_pv = 3 + len(acts)
    tot = ["", "PV acumulado", "", ""] + [f"=SUM({get_column_letter(5 + j)}4:{get_column_letter(5 + j)}{up_pv})"
                                          for j in range(len(columnas))]
    L.fila(ws, up_pv + 1, tot, {5 + j: USD for j in range(len(columnas))})
    col_de = {d: get_column_letter(5 + j) for j, d in enumerate(columnas)}

    ws = L.hoja("Curva S", "Curva S: valor planificado acumulado por semana (línea base)",
                ["Semana (viernes)", "PV acumulado", "% del BAC", "Línea base", "Python"], [16, 15, 11, 15, 15])
    for k, s in enumerate(ev["semanas"]):
        r = 4 + k
        d = _d(s["fecha"])
        L.fila(ws, r, [d, f"='PV semanal'!{col_de[d]}{up_pv + 1}", f"=B{r}/BAC", "=Linea_base", s["pv"]],
               {1: FECHA, 2: USD, 3: PCT, 4: USD, 5: USD})
    us = 3 + len(ev["semanas"])

    # ------------------------------------------------------------ EVM
    ws = L.hoja("EVM", "Control del valor ganado (regla 0/100) a cada fecha de corte",
                ["Corte", "PV", "EV", "AC", "SPI", "CPI", "SV", "CV", "EAC", "Estado", "SPI Python"],
                [12, 13, 13, 13, 8, 8, 13, 13, 13, 14, 11])
    for k, c in enumerate(ev["cortes"]):
        r = 4 + k
        d = _d(c["fecha"])
        L.fila(ws, r, [d, f"='PV semanal'!{col_de[d]}{up_pv + 1}",
                       f'=SUMIFS({rng("M")},{rng("N")},"Sí",{rng("O")},"<="&A{r})', f"=C{r}",
                       f'=IF(B{r}=0,"—",C{r}/B{r})', f'=IF(D{r}=0,"—",C{r}/D{r})', f"=C{r}-B{r}", f"=C{r}-D{r}",
                       f"=IF(ISNUMBER(F{r}),BAC/F{r},BAC)",
                       f'=IF(B{r}=0,"Sin PV",IF(OR(AND(ISNUMBER(E{r}),E{r}<Umbral),AND(ISNUMBER(F{r}),F{r}<Umbral)),"ALERTA","En control"))', c["spi"] if c["spi"] is not None else "—"],
               {1: FECHA, 2: USD, 3: USD, 4: USD, 5: "0.00", 6: "0.00", 7: USD, 8: USD, 9: USD, 11: "0.00"})
    ue = 3 + len(ev["cortes"])
    L.nota(ws, ue + 2, "AC = EV mientras no se registren horas reales (el CPI no se mide todavía). Desde la aprobación del "
                       "plan (1.2.1) las horas se registran en el issue semanal y AC pasa a ser un dato.")
    L.nota(ws, ue + 3, "Estado: ALERTA si CPI o SPI < Umbral (hoja Parámetros). Una semana con PV = 0 no tiene SPI.")

    # ------------------------------------------------------------ Control
    filas = [("BAC", "=BAC", pres["bac"]), ("Contingencia", "=Reserva_cont", pres["contingencia"]),
             ("Línea base", "=Linea_base", pres["linea_base"]), ("Reserva de gestión", "=Reserva_gest", pres["gestion"]),
             ("Horas del equipo", f"=Actividades!I{ult + 1}", sum(v for k, v in pres["horas_recurso"].items() if k in eq)),
             ("Costo de las horas", f"=Actividades!J{ult + 1}", sum(v["costo_horas"] for v in pres["actividades"].values())),
             ("Costos fijos", f"=Actividades!L{ult + 1}", sum(v["costo_fijo"] for v in pres["actividades"].values())),
             ("Días laborables de la línea base (suma)", f"=SUM(Actividades!F4:F{ult})",
              float(sum(a["dur"] for a in acts)))]
    for k, (pid, p) in enumerate(paq):
        filas.append((f"Paquete {pid}", f"=Paquetes!F{4 + k}", p["total"]))
    for k, s in enumerate(ev["semanas"]):
        filas.append((f"PV al {s['fecha']}", f"='Curva S'!B{4 + k}", s["pv"]))
    for k, c in enumerate(ev["cortes"]):
        filas += [(f"EV al {c['fecha']}", f"=EVM!C{4 + k}", c["ev"]), (f"PV al corte {c['fecha']}", f"=EVM!B{4 + k}", c["pv"])]
    _control(L, filas)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    L.wb.save(ruta)
    return ruta


# ==================================================================================================
# Backlog
# ==================================================================================================
def backlog(m: dict, ruta: Path = BACKLOG) -> Path:
    import agil
    L = bx._Libro()
    ag, a = m["agil"], agil.agil()
    epica = {e["id"]: e for e in a["epicas"]}
    ws = L.hoja("Backlog", "Product backlog de la consola (S2), priorizado por WSJF y MoSCoW",
                ["Rango", "ID", "Épica", "Paquete EDT", "Historia de usuario", "REQ-F", "CU", "MoSCoW", "Valor",
                 "Criticidad temporal", "Reducción de riesgo", "Costo de demora", "Puntos", "WSJF", "Sprint", "Depende de",
                 "Criterio de aceptación (Gherkin)", "WSJF Python"],
                [7, 8, 30, 9, 60, 22, 14, 9, 7, 10, 10, 9, 8, 8, 8, 14, 70, 10])
    hs = ag["historias"]
    for k, h in enumerate(hs):
        r = 4 + k
        e = epica[h["epica"]]
        L.fila(ws, r, [h["rango"], h["id"], f"{e['id']} {e['nombre']}", e["paquete"], h["texto"], ", ".join(h["req"]),
                       ", ".join(h["cu"]), h["moscow"], h["wsjf"]["valor"], h["wsjf"]["tiempo"], h["wsjf"]["riesgo"],
                       f"=I{r}+J{r}+K{r}", h["puntos"], f"=L{r}/M{r}", h["sprint"] or "—",
                       ", ".join(h.get("depende") or []) or "—", h["gherkin"], h["wsjf_valor"]], {14: "0.00", 18: "0.00"})
    ub = 3 + len(hs)
    L.nota(ws, ub + 2, "WSJF = (valor + criticidad temporal + reducción de riesgo) / puntos (Reinertsen). El orden de los "
                       "sprints respeta las dependencias: una historia habilitadora va antes aunque su WSJF sea menor.")
    L.nota(ws, ub + 3, "MoSCoW = prioridad del requisito principal en el SRS (M → Must, S → Should); Won't con justificación.")
    rb = lambda col: f"Backlog!${col}$4:${col}${ub}"

    ws = L.hoja("Sprints", "Sprints de una semana (5 días laborables) dentro de las actividades 5.4.1–5.4.3",
                ["Sprint", "Actividad", "Inicio", "Fin", "Objetivo del sprint", "Historias", "Puntos", "Capacidad",
                 "Holgura", "Incremento esperado", "Python"], [8, 10, 12, 12, 50, 22, 8, 10, 9, 60, 9])
    for k, s in enumerate(ag["sprints"]):
        r = 4 + k
        L.fila(ws, r, [s["n"], s["actividad"], _d(s["inicio"]), _d(s["fin"]), s["objetivo"], ", ".join(s["historias"]),
                       f'=SUMIF({rb("O")},A{r},{rb("M")})', a["capacidad_puntos"], f"=H{r}-G{r}", s["incremento"], s["puntos"]],
               {3: FECHA, 4: FECHA})
    us = 3 + len(ag["sprints"])
    L.fila(ws, us + 1, ["", "", "", "", "Total comprometido", "", f"=SUM(G4:G{us})", "", "", "Velocidad planificada:",
                        f"=G{us + 1}/COUNT(A4:A{us})"], {11: "0.0"})

    ws = L.hoja("Burn-up", "Burn-up planificado (los puntos reales se registran al cierre de cada sprint)",
                ["Sprint", "Fin", "Plan acumulado", "Real acumulado", "Alcance total (sin Won't)", "Alcance Must"],
                [8, 12, 14, 14, 18, 14])
    for k, b in enumerate(ag["burnup"]):
        r = 4 + k
        L.fila(ws, r, [b["sprint"], _d(b["fin"]), f"=SUM(Sprints!G$4:G{4 + k})", None,
                       f'=SUMIF({rb("H")},"<>Won\'t",{rb("M")})', f'=SUMIF({rb("H")},"Must",{rb("M")})'], {2: FECHA})

    ws = L.hoja("Kanban", "Tablero Kanban: columnas, límites WIP y reglas", ["Columna", "Límite WIP", "Regla de entrada"],
                [20, 12, 70])
    for k, c in enumerate(a["kanban"]["columnas"]):
        L.fila(ws, 4 + k, [c["nombre"], c["wip"] if c["wip"] is not None else "Sin límite", c["regla"]])
    ws = L.hoja("DoR y DoD", "Definición de listo (DoR) y definición de terminado (DoD)", ["Tipo", "N.º", "Criterio"], [10, 6, 90])
    r = 4
    for tipo, lista in (("DoR", a["dor"]), ("DoD", a["dod"])):
        for k, t in enumerate(lista, start=1):
            L.fila(ws, r, [tipo, k, t])
            r += 1
    ws = L.hoja("Métricas", "Métricas de seguimiento ágil", ["Métrica", "Definición", "Meta", "Uso"], [18, 50, 36, 50])
    for k, x in enumerate(a["metricas"]):
        L.fila(ws, 4 + k, [x["nombre"], x["definicion"], x["meta"], x["uso"]])

    filas = [("Puntos comprometidos", f"=Sprints!G{us + 1}", float(ag["comprometido"])),
             ("Alcance total (sin Won't)", "='Burn-up'!E4", float(ag["alcance_total"])),
             ("Alcance Must", "='Burn-up'!F4", float(ag["must"]))]
    for k, s in enumerate(ag["sprints"]):
        filas.append((f"Puntos del sprint {s['n']}", f"=Sprints!G{4 + k}", float(s["puntos"])))
    for k, h in enumerate(hs):
        filas.append((f"WSJF {h['id']}", f"=Backlog!N{4 + k}", h["wsjf_valor"]))
    _control(L, filas)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    L.wb.save(ruta)
    return ruta


# ==================================================================================================
# Verificación
# ==================================================================================================
def verificar(ruta: Path) -> bool | None:
    """Recalcula con Excel o LibreOffice; falla si hay errores de fórmula o si Control no da 0. None si no hay motor."""
    if not (bx._excel(ruta) or bx._libreoffice(ruta)):
        return None
    wb = load_workbook(ruta, data_only=True)
    errores = [f"{ws.title}!{c.coordinate} = {c.value}" for ws in wb for fila in ws.iter_rows() for c in fila
               if isinstance(c.value, str) and c.value.startswith(ERRORES_XL)]
    if errores:
        raise RuntimeError(f"{ruta.name}: fórmulas con error: " + "; ".join(errores[:6]))
    ws = wb["Control"]
    dif = []
    for r in range(4, ws.max_row + 1):
        exc, py = ws.cell(row=r, column=2).value, ws.cell(row=r, column=3).value
        if py is None:
            continue
        if exc is None or abs(float(exc) - float(py)) > 0.005:
            dif.append(f"{ws.cell(row=r, column=1).value}: Excel {exc} ≠ Python {py}")
    if dif:
        raise RuntimeError(f"{ruta.name}: Excel y Python no coinciden: " + "; ".join(dif[:8]))
    return True


def escribir_todo(m: dict) -> list[Path]:
    rutas = [presupuesto(m), backlog(m)]
    for r in rutas:
        if verificar(r) is None:
            print(f"  AVISO {r.name}: sin Excel ni LibreOffice; fórmulas no recalculadas (paso manual del README)")
    return rutas
