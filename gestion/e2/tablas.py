"""Tablas generadas del Entregable 2 de CE01 ({{tabla:id}} en gestion/e2/informe/*.md).

Leen gestion/e2/datos/resultados.json (gestion/analytics/business_case.py), gestion/e2/datos/business_case.yaml,
gestion/ce01.yaml e infra/*.yaml a través de gestion/ce01_datos.py: ninguna cifra se escribe a mano.
TABLAS = {id: {"titulo", "fuente", "filas": función → [[cabecera], [fila], …]}}.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import ce01_datos as cd  # noqa: E402
from ce01_datos import num, pct, s, usd  # noqa: E402

BC = yaml.safe_load((AQUI / "datos" / "business_case.yaml").read_text(encoding="utf-8"))
_RES = AQUI / "datos" / "resultados.json"
PROPIA = "Elaboración propia"


def R() -> dict:
    if not _RES.exists():
        raise cd.DatosCE01Error("Falta gestion/e2/datos/resultados.json: ejecute python gestion/analytics/business_case.py")
    return json.loads(_RES.read_text(encoding="utf-8"))["modelo"]


def _crit() -> dict:
    return {c["id"]: c["nombre"] for c in cd.cargar()["criterios"]["lista"]}


def _alt(aid: str) -> str:
    return f"{aid} {BC['alternativas'][aid]['corto']}"


def _meses(x) -> str:
    return "no se recupera" if x is None else f"{num(x, 1)} meses"


def _pct_o(x) -> str:
    return "no existe" if x is None else pct(x, 1)


# ------------------------------------------------------------------------------------------------ 2.1
def smart():
    pl = BC["smart"]["plazos"]
    return [["ID", "Específico (necesidad)", "Medible (indicador)", "Alcanzable (meta)", "Relevante (por qué)", "Temporal (plazo)"]] + [
        [o["id"], o["necesidad"], o["indicador"], o["meta"], pl[o["id"]]["relevancia"], pl[o["id"]]["plazo"]]
        for o in cd.objetivos()]


# ------------------------------------------------------------------------------------------------ 2.2
def fichas():
    return [["Alternativa", "Descripción", "Qué resuelve", "Qué no resuelve"]] + [
        [_alt(a), x["descripcion"], x["resuelve"], x["no_resuelve"]] for a, x in BC["alternativas"].items()]


def fichas_riesgo():
    t = R()["tco"]
    return [["Alternativa", "Riesgos", "Madurez", "Inversión", "Costo anual", "TCO a 3 años"]] + [
        [_alt(a), x["riesgos"], x["madurez"], usd(t[a]["capex"]), usd(t[a]["opex_anual"]),
         usd(t[a]["tco"]) + (" (cota inferior)" if t[a]["cota_inferior"] else "")]
        for a, x in BC["alternativas"].items()]


def ahp_matriz():
    a = R()["ahp"]
    cab = ["Criterio"] + a["criterios"] + ["Peso AHP"]
    filas = [cab]
    for i, c in enumerate(a["criterios"]):
        celdas = []
        for v in a["matriz"][i]:
            celdas.append(num(v) if v >= 1 else f"1/{num(1 / v)}")
        filas.append([c] + celdas + [pct(a["pesos"][i], 1)])
    filas.append(["Consistencia", f"λmax = {num(a['lambda_max'], 3)}", f"CI = {num(a['ci'], 3)}", f"RI = {num(a['ri'], 2)}",
                  f"CR = {num(a['cr'], 3)}", "", "", "CR < 0,10"])
    return filas


def pesos():
    a = R()["ahp"]
    cr = _crit()
    return [["Criterio", "Peso de la guía", "Peso AHP", "Diferencia"]] + [
        [f"{c} {cr[c]}", pct(g), pct(w, 1), f"{'+' if w - g >= 0 else '−'}{num(abs(w - g) * 100, 1)} p. p."]
        for c, g, w in zip(a["criterios"], a["pesos_guia"], a["pesos"])]


def justificacion():
    d = R()["decision"]
    crit = d["criterios"]
    y = {a["id"]: a for a in cd.cargar()["alternativas"]["lista"]}
    filas = [["Alternativa"] + crit + ["Total"]]
    for aid, f in d["filas"].items():
        celdas = []
        for j, c in enumerate(crit):
            p = f["puntajes"][j]
            if c == "C3":
                t = R()["tco"][aid]
                txt = f"TCO {usd(t['tco'])}" + (", cota inferior" if t["cota_inferior"] else "") + \
                      f" (guía: {num(f['c3_guia'])})"
            else:
                txt = BC["alternativas"][aid]["justificacion"][c]
            celdas.append(f"{num(p, 1 if p % 1 else 0)}: {txt}")
        filas.append([_alt(aid)] + celdas + [num(f["total"], 2)])
    del y
    return filas


def sensibilidad():
    sen = R()["sensibilidad"]
    cr = _crit()
    filas = [["Criterio", "Peso AHP", "Peso con el que A4 deja de ganar", "Cambio necesario", "Alternativa que pasa a ganar"]]
    for c in sen["por_criterio"]:
        if c["delta"] is None:
            filas.append([f"{c['criterio']} {cr[c['criterio']]}", pct(c["peso"], 1), "A4 gana en todo el rango", "—", "—"])
        else:
            filas.append([f"{c['criterio']} {cr[c['criterio']]}", pct(c["peso"], 1), pct(c["peso_cruce"], 1),
                          f"{'+' if c['delta'] > 0 else '−'}{num(abs(c['delta']) * 100, 1)} p. p.", _alt(c["gana"])])
    return filas


# ------------------------------------------------------------------------------------------------ 2.3
def ben_cuant():
    b = R()["base"]
    fa = b["factor_anualidad"]
    return [["ID", "Beneficio", "Fórmula", "Supuestos", "US$/año", "Valor actual a 3 años"],
            ["BN-1", "Mbps de ampliación diferidos", f"BHR × enlace × US$/Mbps-mes × 12 = {num(b['mbps'])} Mbps × "
             f"{usd(s('S-03.usd_mbps_mes'))} × 12", "S-02, S-03, S-04, S-40", usd(b["bn1"]), usd(b["bn1"] * fa)],
            ["BN-2", "Horas técnicas ahorradas", f"PCs × ciclos × h por PC × tarifa = {num(s('S-01.pcs'))} × "
             f"{num(s('S-06.ciclos_anio'))} × {num(s('S-07.horas_pc_ciclo'), 2)} h × {usd(s('S-07.tarifa_usd_h'))}",
             "S-01, S-06, S-07", usd(b["bn2"]), usd(b["bn2"] * fa)],
            ["", "Total", "", "", usd(b["bn1"] + b["bn2"]), usd(b["va_beneficios"])]]


def ben_cual():
    return [["ID", "Beneficio cualitativo", "Cómo se observaría", "Objetivo"]] + [
        [x["id"], x["beneficio"], x["observacion"], x["ob"]] for x in BC["beneficios_cualitativos"]]


def indicadores():
    v = R()["valor"]
    obs = {o["id"]: o for o in cd.objetivos()}
    base = {"IV-1": f"{num(v['gb_evitados_mes'])} GB/mes", "IV-2": pct(s("S-04.bhr")) + " (supuesto)",
            "IV-3": usd(v["costo_gb"], 3) + " por GB", "IV-4": pct(1.0) + " (caso base)", "IV-5": "Se mide en el piloto"}
    meta = {"IV-1": "Crece con el BHR", "IV-2": obs["OB-1"]["meta"], "IV-3": f"Menor que {usd(v['costo_gb_enlace'], 3)} por GB "
            "(costo del enlace equivalente)", "IV-4": "Se fija tras el piloto", "IV-5": f"{obs['OB-2']['meta']} (OB-2)"}
    return [["ID", "Indicador", "Fórmula", "Supuestos", "Valor del caso base", "Meta o referencia", "Objetivo"]] + [
        [x["id"], x["indicador"], x["formula"], x["supuestos"], base[x["id"]], meta[x["id"]], x["ob"]]
        for x in BC["indicadores_valor"]]


# ------------------------------------------------------------------------------------------------ 2.4
def capex():
    c = cd.costos()
    filas = [["ID", "Concepto", "Supuesto", "US$"]] + [
        [x["id"], x["concepto"], x["de"].split(".")[0], usd(x["usd"])] for x in c["capex"]]
    return filas + [["", "Inversión inicial (I0)", "", usd(c["capex_total"])]]


def opex():
    c = cd.costos()
    filas = [["ID", "Tipo", "Concepto", "Cálculo", "US$/año"]]
    calc = {"OX-1": f"Suma de C1–C7 = {usd(c['aws_mensual'], 2)}/mes × 12 [S-12]",
            "OX-2": f"{num(c['consumo_w'])} W × {num(cd.cargar()['economia']['horas_anio'])} h ÷ 1000 × "
                    f"{usd(s('S-09.usd_kwh'), 2)}/kWh [S-09]",
            "OX-3": f"{pct(s('S-41.mant_fraccion'))} × {usd(c['capex_total'])} [S-41]"}
    for x in c["opex"]:
        filas.append([x["id"], "Operación" if x["tipo"] == "operacion" else "Mantenimiento", x["concepto"], calc[x["id"]],
                      usd(x["usd"], 2)])
    filas.append(["", "", "Subtotal de operación", "OX-1 + OX-2", usd(c["opex_operacion"], 2)])
    filas.append(["", "", "Subtotal de mantenimiento", "OX-3", usd(c["opex_mantenimiento"], 2)])
    filas.append(["", "", "Total OPEX anual", "", usd(c["opex_total"], 2)])
    return filas


def aws():
    lineas = cd.resolver(cd.cargar()["referencias"]["aws_lineas"])
    filas = [["ID", "Concepto", "Cantidad", "Precio unitario", "US$/mes"]] + [
        [l["id"], l["concepto"], f"{num(l['cantidad'])} {l['unidad']}", usd(l["precio_unitario"], 4),
         usd(l["cantidad"] * l["precio_unitario"], 2)] for l in lineas]
    return filas + [["", "Total mensual", "", "", usd(cd.costos()["aws_mensual"], 2)]]


def flujo():
    b = R()["base"]
    n = len(b["anios"])
    cab = ["Concepto"] + [f"Año {t}" for t in range(n + 1)]
    fil = [cab, ["Inversión inicial", usd(-b["capex"])] + ["—"] * n,
           ["BN-1 Mbps diferidos", "—"] + [usd(a["bn1"]) for a in b["anios"]],
           ["BN-2 Horas técnicas", "—"] + [usd(a["bn2"]) for a in b["anios"]],
           ["OPEX de operación", "—"] + [usd(-(a["aws"] + a["energia"])) for a in b["anios"]],
           ["OPEX de mantenimiento", "—"] + [usd(-a["mant"]) for a in b["anios"]],
           ["Flujo neto", ] + [usd(f) for f in b["flujos"]],
           ["Flujo descontado al COK", ] + [usd(f) for f in b["descontado"]],
           ["Flujo acumulado", ] + [usd(f) for f in b["acumulado"]]]
    return fil


def indicadores_eco():
    b, eq = R()["base"], R()["equilibrio"]
    return [["Indicador", "Valor", "Cálculo", "Lectura"],
            ["VAN", usd(b["van"]), f"−I0 + Σ flujo neto ÷ (1 + COK)^t; COK {pct(s('S-10.cok'))} [S-10]",
             "Positivo: el proyecto crea valor con los supuestos vigentes"],
            ["TIR", _pct_o(b["tir"]), "Tasa con la que el VAN es cero", "Muy superior al COK por la inversión reducida"],
            ["Payback simple", _meses(b["payback_meses"]), "I0 ÷ flujo neto mensual", "Se recupera dentro del primer año"],
            ["B/C", num(b["bc"], 2), "VA(beneficios) ÷ (I0 + VA(OPEX))", "Cada dólar de costo devuelve más de dos"],
            ["ROI a 3 años", pct(b["roi"]), "(Σ flujos netos − I0) ÷ I0, sin descontar", "Retorno acumulado del horizonte"],
            ["Punto de equilibrio", f"{num(eq['mbps'], 1)} Mbps ({pct(eq['bhr'], 1)} de BHR)",
             "Mbps diferidos con los que el VAN es cero", f"Equivale a {usd(eq['usd_mbps'], 2)} por Mbps-mes con los Mbps base"]]


def conciliacion():
    c, b = cd.costos(), R()["base"]
    ref_aws = cd.resolver("infra/centro_datos.yaml#aws.costo_mensual.referencial_documento_usd")
    return [["Partida", "Guía CE01 v0.4 (B2.4–B2.5)", "Este informe (repositorio)", "Causa", "Registro"],
            ["Consumo eléctrico", "400 W", f"{num(c['consumo_w'])} W", "El inventario de UPS01 usa el consumo medido del rack", "CI-77, CI-98"],
            ["Energía anual", "US$ 526", usd(b["energia"]), "Mayor consumo con la misma tarifa [S-09]", "CI-98"],
            ["AWS mensual", f"≈ {usd(ref_aws)}", usd(c["aws_mensual"], 2), "Suma exacta de las líneas C1–C7 [S-12]", "CI-98"],
            ["Mbps diferidos", "100 Mbps", f"{num(b['mbps'])} Mbps", "S-40 = BHR [S-04] × enlace [S-02]", "CI-97, CI-98"],
            ["OPEX anual", "US$ 1 896", usd(c["opex_total"]), "Energía y AWS anteriores", "CI-98"],
            ["VAN", "≈ US$ 15 606", usd(b["van"]), "Menos Mbps diferidos y más OPEX", "CI-98"],
            ["Payback", "≈ 7,3 meses", _meses(b["payback_meses"]), "Flujo neto menor", "CI-98"]]


def mc_variables():
    filas = [["Variable", "Supuesto", "Distribución", "Mínimo", "Moda", "Máximo", "Por qué ese rango"]]
    motivo = {"bhr": "Rango de la guía B2.5; el BHR real se mide en el piloto",
              "usd_mbps": "Rango de la guía B2.5; depende de la cotización del ISP",
              "adopcion": "Rango de la guía B2.5; la moda supone que todas las estaciones usan el PAC (D-05)",
              "f_aws": "±30 % por cambios de precio o de uso (guía B2.5)",
              "f_capex": "±15 % por variación de cotizaciones (prompt P2)"}
    for t in R()["tornado"]:
        es_f = t["id"].startswith("f_")
        f = (lambda x: f"×{num(x, 2)}") if es_f else ((lambda x: usd(x)) if t["id"] == "usd_mbps" else (lambda x: pct(x)))
        filas.append([t["nombre"], t["supuesto"], "Triangular", f(t["min"]), f(t["moda"]), f(t["max"]), motivo[t["id"]]])
    return filas


def escenarios():
    filas = [["Escenario", "BHR", "US$/Mbps-mes", "Adopción", "AWS", "I0", "VAN", "TIR", "Payback", "B/C"]]
    for e in R()["escenarios"]:
        p = e["param"]
        filas.append([e["nombre"], pct(p["bhr"]), usd(p["usd_mbps"]), pct(p["adopcion"]), f"×{num(p['f_aws'], 2)}",
                      f"×{num(p['f_capex'], 2)}", usd(e["van"]), _pct_o(e["tir"]), _meses(e["payback_meses"]), num(e["bc"], 2)])
    return filas


# ------------------------------------------------------------------------------------------------ 2.5
def riesgos_eco():
    import estilo_ce01 as est
    filas = [["ID", "Riesgo", "P", "I", "Nivel", "Escenario de estrés", "VAN", "ΔVAN", "Mitigación"]]
    for x in sorted(R()["riesgos"], key=lambda x: x["delta_van"]):
        filas.append([x["id"], x["riesgo"], str(x["p"]), str(x["i"]), est.nivel_riesgo(x["puntaje"])[1], x["efecto"],
                      usd(x["van"]), ("−" if x["delta_van"] < 0 else "+" if x["delta_van"] > 0 else "") + usd(abs(x["delta_van"])),
                      x["respuesta"]])
    return filas


# ------------------------------------------------------------------------------------------------ Anexos
def pugh():
    p = R()["pugh"]
    crit = R()["decision"]["criterios"]
    filas = [["Alternativa"] + crit + ["+", "S", "−"]]
    for aid, f in p["filas"].items():
        filas.append([_alt(aid) + (" (base)" if aid == p["base"] else "")] + f["marcas"] + [str(f["mas"]), str(f["iguales"]),
                                                                                              str(f["menos"])])
    return filas


def ahp_juicios():
    return [["Par", "Valor (Saaty)", "Lectura", "Motivo"]] + [
        [f"{x['a']} frente a {x['b']}", num(x["v"]),
         "Igual importancia" if x["v"] == 1 else f"{x['a']} moderadamente más importante" if x["v"] == 3 else
         f"{x['a']} ligeramente más importante", x["motivo"]] for x in BC["ahp"]["pares"]]


TABLAS = {
    "t-smart": {"titulo": "Objetivos SMART del proyecto", "fuente": "infra/trazabilidad.yaml (metas); guía CE01 v0.4 B2.1 (plazos)", "filas": smart},
    "t-fichas": {"titulo": "Fichas técnicas de las alternativas: alcance", "fuente": f"{PROPIA} a partir de la guía CE01 v0.4 B2.2", "filas": fichas},
    "t-fichas-riesgo": {"titulo": "Fichas técnicas de las alternativas: riesgos, madurez y costo", "fuente": f"{PROPIA}; costos de gestion/analytics/business_case.py", "filas": fichas_riesgo},
    "t-ahp": {"titulo": "Matriz AHP de comparación por pares y pesos resultantes", "fuente": f"{PROPIA} con el método de Saaty [1], [2]", "filas": ahp_matriz},
    "t-pesos": {"titulo": "Pesos de la guía frente a pesos AHP", "fuente": f"{PROPIA}; gestion/analytics/business_case.py", "filas": pesos},
    "t-justificacion": {"titulo": "Matriz comparativa: puntaje y justificación por celda", "fuente": f"{PROPIA}; puntajes de la guía CE01 v0.4 B2.2, C3 calculado", "filas": justificacion},
    "t-sensibilidad": {"titulo": "Sensibilidad de la decisión al peso de cada criterio", "fuente": f"{PROPIA}; gestion/analytics/business_case.py", "filas": sensibilidad},
    "t-ben-cuant": {"titulo": "Beneficios cuantificables", "fuente": f"{PROPIA}; gestion/ce01_datos.py", "filas": ben_cuant},
    "t-ben-cual": {"titulo": "Beneficios cualitativos y forma de observarlos", "fuente": f"{PROPIA} a partir de la guía CE01 v0.4 B2.3", "filas": ben_cual},
    "t-indicadores": {"titulo": "Indicadores de valor", "fuente": f"{PROPIA}; valores de gestion/analytics/business_case.py", "filas": indicadores},
    "t-capex": {"titulo": "Inversión inicial (CAPEX)", "fuente": "gestion/ce01.yaml → economia.capex; supuestos S-08, S-37, S-38 y S-39", "filas": capex},
    "t-aws": {"titulo": "Costo mensual de AWS por línea", "fuente": "infra/centro_datos.yaml → aws.costo_mensual (precios de lista [S-12])", "filas": aws},
    "t-opex": {"titulo": "Costos anuales de operación y de mantenimiento", "fuente": "gestion/ce01.yaml → economia.opex; gestion/ce01_datos.py", "filas": opex},
    "t-flujo": {"titulo": "Flujo de caja del caso base", "fuente": f"{PROPIA}; gestion/analytics/business_case.py", "filas": flujo},
    "t-indicadores-eco": {"titulo": "Indicadores de la evaluación económica", "fuente": f"{PROPIA}; gestion/analytics/business_case.py y Business_Case_E2.xlsx", "filas": indicadores_eco},
    "t-conciliacion": {"titulo": "Conciliación con la guía CE01 v0.4", "fuente": "Guía CE01 v0.4 B2.4–B2.5; docs/infra/e1/CAMBIOS-INVENTARIO.md", "filas": conciliacion},
    "t-mc-variables": {"titulo": "Variables de la simulación de Monte Carlo", "fuente": "gestion/e2/datos/business_case.yaml (CI-102)", "filas": mc_variables},
    "t-escenarios": {"titulo": "Escenarios pesimista, base y optimista", "fuente": f"{PROPIA}; gestion/analytics/business_case.py", "filas": escenarios},
    "t-riesgos-eco": {"titulo": "Riesgos estratégicos con efecto económico y mitigación", "fuente": f"{PROPIA}; P, I y respuesta de gestion/ce01.yaml; VAN del modelo (CI-102)", "filas": riesgos_eco},
    "t-pugh": {"titulo": "Matriz de Pugh con A1 como base", "fuente": f"{PROPIA} con el método de Pugh [4]", "filas": pugh},
    "t-ahp-juicios": {"titulo": "Juicios de la comparación AHP por pares", "fuente": "gestion/e2/datos/business_case.yaml; validar con la DTI", "filas": ahp_juicios},
}
