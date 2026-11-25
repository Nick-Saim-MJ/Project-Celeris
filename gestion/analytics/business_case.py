"""Modelo económico del Business Case de CE01 (Entregable 2).

    python gestion/analytics/business_case.py            # escribe resultados.json y el XLSX, y verifica el XLSX
    python gestion/analytics/business_case.py --sin-xlsx # solo el modelo (lo usan las pruebas)

Todo sale de gestion/ce01_datos.py (supuestos S-xx, CAPEX, OPEX, beneficios) y de gestion/e2/datos/business_case.yaml
(rangos de Monte Carlo, juicios AHP, fichas de alternativas, escenarios de estrés de los riesgos; CI-102). Calcula:

  - flujo de caja a 3 años, VAN, TIR, payback, B/C, ROI y punto de equilibrio (Mbps diferidos con VAN = 0);
  - simulación de Monte Carlo (10 000 iteraciones, semilla fija, distribuciones triangulares): P(VAN > 0), P5/P50/P95;
  - tornado (una variable a la vez en su mínimo y su máximo) y escenarios pesimista / base / optimista;
  - pesos AHP (media geométrica de filas) con índice y razón de consistencia: falla si CR ≥ 0,10;
  - TCO a 3 años de cada alternativa con las mismas partidas, matriz ponderada, sensibilidad de pesos y Pugh;
  - efecto económico de cada riesgo RE-xx (VAN con su escenario de estrés).

Salidas: gestion/e2/datos/resultados.json ({"datos": {clave: texto}} para {{dato:}} y "modelo" para tablas y figuras) y
entregables/CE01/E2/Business_Case_E2.xlsx (gestion/analytics/business_case_xlsx.py), con fórmulas vivas; el script
falla si el VAN que calcula Excel difiere del de Python en más de US$ 1.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import numpy_financial as npf
import yaml

AQUI = Path(__file__).resolve().parent
GESTION = AQUI.parent
sys.path.insert(0, str(GESTION))
sys.path.insert(0, str(AQUI))
import ce01_datos as cd  # noqa: E402
from ce01_datos import num, pct, s, usd  # noqa: E402

DATOS_E2 = GESTION / "e2" / "datos" / "business_case.yaml"
SALIDA_JSON = GESTION / "e2" / "datos" / "resultados.json"
SALIDA_XLSX = cd.RAIZ / "entregables" / "CE01" / "E2" / "Business_Case_E2.xlsx"
TOLERANCIA_USD = 1.0


class ModeloError(Exception):
    """El modelo no es coherente (AHP inconsistente, VAN distinto de ce01_datos, XLSX que no coincide…)."""


@lru_cache(maxsize=None)
def bc() -> dict:
    return yaml.safe_load(DATOS_E2.read_text(encoding="utf-8"))


def _valor(v) -> float:
    """Moda de una variable: número o lectura «S-xx.clave»."""
    return float(s(v)) if isinstance(v, str) else float(v)


# ==================================================================================================
# Modelo determinista
# ==================================================================================================
def parametros_base() -> dict:
    return {
        "bhr": s("S-04.bhr"), "usd_mbps": s("S-03.usd_mbps_mes"), "adopcion": 1.0, "f_aws": 1.0, "f_capex": 1.0,
        "factor_bn2": 1.0, "factor_bn1_anio1": 1.0, "factor_beneficio_anio1": 1.0,
        "horizonte_efectivo": cd.cargar()["economia"]["horizonte_anios"], "adopcion_labs": None, "aws_cantidades": {},
    }


def aws_mensual(cantidades: dict | None = None) -> float:
    lineas = cd.resolver(cd.cargar()["referencias"]["aws_lineas"])
    cantidades = cantidades or {}
    return sum(cantidades.get(l["id"], l["cantidad"]) * l["precio_unitario"] for l in lineas)


def evaluar(**cambios) -> dict:
    """Flujo e indicadores con los parámetros base modificados por `cambios` (los de riesgos_estres o del tornado)."""
    p = {**parametros_base(), **cambios}
    eco = cd.cargar()["economia"]
    n, k = eco["horizonte_anios"], s("S-10.cok")
    c = cd.costos()
    capex = c["capex_total"] * p["f_capex"]
    aws = aws_mensual(p["aws_cantidades"]) * 12 * p["f_aws"]
    energia = c["consumo_w"] * eco["horas_anio"] / 1000 * s("S-09.usd_kwh")
    mant = s("S-41.mant_fraccion") * capex
    opex = aws + energia + mant
    adop = p["adopcion"] if p["adopcion_labs"] is None else p["adopcion_labs"] / s("S-26.laboratorios")
    mbps = p["bhr"] * s("S-02.enlace_mbps") * adop
    bn1 = mbps * p["usd_mbps"] * 12
    bn2 = cd.beneficios()["lista"][1]["usd"] * p["factor_bn2"]
    anios = []
    for t in range(1, n + 1):
        activo = t <= p["horizonte_efectivo"]
        f1 = p["factor_bn1_anio1"] if t == 1 else 1.0
        fb = p["factor_beneficio_anio1"] if t == 1 else 1.0
        b1, b2 = (bn1 * f1 * fb, bn2 * fb) if activo else (0.0, 0.0)
        o = (aws, energia, mant) if activo else (0.0, 0.0, 0.0)
        anios.append({"anio": t, "bn1": b1, "bn2": b2, "aws": o[0], "energia": o[1], "mant": o[2],
                      "beneficio": b1 + b2, "opex": sum(o), "flujo": b1 + b2 - sum(o)})
    flujos = [-capex] + [a["flujo"] for a in anios]
    desc = [1 / (1 + k) ** t for t in range(n + 1)]
    van = float(npf.npv(k, flujos))
    tir = float(npf.irr(flujos))
    va_ben = sum(a["beneficio"] * desc[a["anio"]] for a in anios)
    va_opex = sum(a["opex"] * desc[a["anio"]] for a in anios)
    return {
        "param": p, "capex": capex, "aws": aws, "energia": energia, "mant": mant, "opex": opex,
        "mbps": mbps, "bn1": bn1, "bn2": bn2, "anios": anios, "flujos": flujos,
        "acumulado": list(np.cumsum(flujos)), "descontado": [f * d for f, d in zip(flujos, desc)],
        "van": van, "tir": None if math.isnan(tir) else tir, "payback_meses": _payback(flujos),
        "bc": va_ben / (capex + va_opex), "roi": (sum(flujos[1:]) - capex) / capex,
        "factor_anualidad": sum(desc[1:]), "va_beneficios": va_ben, "va_opex": va_opex,
    }


def _payback(flujos: list[float]) -> float | None:
    """Meses hasta recuperar la inversión, con el flujo de cada año repartido por igual entre sus 12 meses."""
    acum = flujos[0]
    for t, f in enumerate(flujos[1:], start=1):
        if f > 0 and acum + f >= 0:
            return (t - 1) * 12 + (-acum) / (f / 12)
        acum += f
    return None


def punto_equilibrio() -> dict:
    """Mbps diferidos (y BHR y costo por Mbps equivalentes) con los que el VAN es 0; el VAN es lineal en esos Mbps."""
    b = evaluar()
    necesario = b["capex"] / b["factor_anualidad"] + b["opex"] - b["bn2"]   # beneficio BN-1 anual que hace VAN = 0
    mbps = necesario / (s("S-03.usd_mbps_mes") * 12)
    return {"mbps": mbps, "bhr": mbps / s("S-02.enlace_mbps"), "usd_mbps": necesario / (b["mbps"] * 12),
            "bn1_anual": necesario}


# ==================================================================================================
# Monte Carlo, tornado y escenarios
# ==================================================================================================
def _variables() -> list[dict]:
    return [{**v, "moda": _valor(v["moda"])} for v in bc()["montecarlo"]["variables"]]


def montecarlo() -> dict:
    mc = bc()["montecarlo"]
    rng = np.random.default_rng(mc["semilla"])
    n_it = mc["iteraciones"]
    x = {v["id"]: rng.triangular(v["min"], v["moda"], v["max"], n_it) for v in _variables()}
    b = evaluar()
    eco = cd.cargar()["economia"]
    capex = b["capex"] * x["f_capex"]
    opex = b["aws"] * x["f_aws"] + b["energia"] + s("S-41.mant_fraccion") * capex
    bn1 = x["bhr"] * s("S-02.enlace_mbps") * x["adopcion"] * x["usd_mbps"] * 12
    van = -capex + b["factor_anualidad"] * (bn1 + b["bn2"] - opex)
    assert eco["horizonte_anios"] == len(b["anios"])
    p5, p50, p95 = np.percentile(van, [5, 50, 95])
    hist, bordes = np.histogram(van, bins=40)
    return {"iteraciones": n_it, "semilla": mc["semilla"], "p_van_positivo": float((van > 0).mean()),
            "p5": float(p5), "p50": float(p50), "p95": float(p95), "media": float(van.mean()), "desv": float(van.std()),
            "min": float(van.min()), "max": float(van.max()),
            "histograma": {"conteos": hist.tolist(), "bordes": bordes.tolist()},
            "muestra_control": {k: float(v[0]) for k, v in x.items()} | {"van": float(van[0])}}


def tornado() -> list[dict]:
    base = evaluar()["van"]
    filas = []
    for v in _variables():
        bajo, alto = evaluar(**{v["id"]: v["min"]})["van"], evaluar(**{v["id"]: v["max"]})["van"]
        filas.append({"id": v["id"], "nombre": v["nombre"], "supuesto": v["supuesto"], "min": v["min"], "max": v["max"],
                      "moda": v["moda"], "van_min": bajo, "van_max": alto, "rango": abs(alto - bajo), "base": base})
    return sorted(filas, key=lambda f: -f["rango"])


def _desfavorable(v: dict) -> float:
    """Extremo que reduce el VAN: el mínimo de un beneficio, el máximo de un costo."""
    return v["max"] if v["id"].startswith("f_") else v["min"]


def escenarios() -> list[dict]:
    vs = _variables()
    pes = {v["id"]: _desfavorable(v) for v in vs}
    opt = {v["id"]: (v["min"] if v["id"].startswith("f_") else v["max"]) for v in vs}
    out = []
    for nombre, cambios in (("Pesimista", pes), ("Base", {}), ("Optimista", opt)):
        r = evaluar(**cambios)
        out.append({"nombre": nombre, "param": {v["id"]: r["param"][v["id"]] for v in vs}, "van": r["van"],
                    "tir": r["tir"], "payback_meses": r["payback_meses"], "bc": r["bc"], "flujo": r["anios"][0]["flujo"],
                    "mbps": r["mbps"]})
    return out


# ==================================================================================================
# AHP, alternativas, matriz ponderada, sensibilidad y Pugh
# ==================================================================================================
def ahp() -> dict:
    a = bc()["ahp"]
    crit = [c["id"] for c in cd.cargar()["criterios"]["lista"]]
    n = len(crit)
    m = np.ones((n, n))
    vistos = set()
    for par in a["pares"]:
        i, j = crit.index(par["a"]), crit.index(par["b"])
        if i >= j:
            raise ModeloError(f"AHP: el par {par['a']}–{par['b']} debe ir en el triángulo superior")
        m[i, j], m[j, i] = par["v"], 1 / par["v"]
        vistos.add((i, j))
    faltan = [(crit[i], crit[j]) for i in range(n) for j in range(i + 1, n) if (i, j) not in vistos]
    if faltan:
        raise ModeloError(f"AHP: faltan comparaciones {faltan}")
    g = np.prod(m, axis=1) ** (1 / n)
    w = g / g.sum()
    lam = float(np.mean(m @ w / w))
    ci = (lam - n) / (n - 1)
    cr = ci / a["indice_aleatorio"][n]
    vals, vecs = np.linalg.eig(m)
    ev = np.abs(np.real(vecs[:, np.argmax(np.real(vals))]))
    ev = ev / ev.sum()
    if cr >= a["cr_max"]:
        raise ModeloError(f"AHP inconsistente: CR = {cr:.3f} ≥ {a['cr_max']}; revise las comparaciones de business_case.yaml")
    guia = [c["peso"] for c in cd.cargar()["criterios"]["lista"]]
    return {"criterios": crit, "matriz": m.tolist(), "pesos": w.tolist(), "pesos_guia": guia,
            "pesos_autovector": ev.tolist(), "lambda_max": lam, "ci": ci, "cr": cr, "ri": a["indice_aleatorio"][n],
            "dif_max_autovector": float(np.max(np.abs(ev - w)))}


def tco_alternativas() -> dict[str, dict]:
    c = cd.costos()
    n = cd.cargar()["economia"]["horizonte_anios"]
    fa = evaluar()["factor_anualidad"]
    capex = {x["id"]: x["usd"] for x in c["capex"]}
    opex = {x["id"]: x["usd"] for x in c["opex"]}
    ampliacion = cd.mbps_diferidos() * s("S-03.usd_mbps_mes") * 12
    out = {}
    for aid, a in bc()["alternativas"].items():
        cx = sum(capex[i] for i in a["costo"]["capex"])
        # El mantenimiento (OX-3) es el 10 % del hardware que la alternativa usa, no del de Celeris
        anual = sum(opex[i] for i in a["costo"]["opex"] if i != "OX-3")
        if "OX-3" in a["costo"]["opex"]:
            anual += s("S-41.mant_fraccion") * cx
        if a["costo"].get("ampliacion"):
            anual += ampliacion
        out[aid] = {"capex": cx, "opex_anual": anual, "tco": cx + anual * n, "tco_va": cx + anual * fa,
                    "cota_inferior": bool(a["costo"].get("cota_inferior"))}
    return out


def matriz_decision(pesos: list[float] | None = None) -> dict:
    y = cd.cargar()
    crit = [c["id"] for c in y["criterios"]["lista"]]
    j_tco = crit.index("C3")
    tco = tco_alternativas()
    vmax, vmin = max(t["tco"] for t in tco.values()), min(t["tco"] for t in tco.values())
    filas = {}
    for a in y["alternativas"]["lista"]:
        p = [float(x) for x in a["puntajes"]]
        guia_c3 = p[j_tco]
        p[j_tco] = round(1 + 4 * (vmax - tco[a["id"]]["tco"]) / (vmax - vmin), 1)
        filas[a["id"]] = {"nombre": a["nombre"], "puntajes": p, "c3_guia": guia_c3}
    w = pesos or ahp()["pesos"]
    for f in filas.values():
        f["total"] = float(np.dot(f["puntajes"], w))
    ranking = sorted(filas, key=lambda k: -filas[k]["total"])
    return {"criterios": crit, "pesos": list(w), "filas": filas, "ranking": ranking}


def sensibilidad_pesos(objetivo: str = "A4") -> dict:
    """Cambio mínimo del peso de un criterio (los demás se reescalan en proporción) con el que `objetivo` deja de ganar."""
    md = matriz_decision()
    w = np.array(md["pesos"])
    S = {k: np.array(f["puntajes"]) for k, f in md["filas"].items()}
    por_criterio, curvas = [], {}
    for j, cid in enumerate(md["criterios"]):
        def total(a, d):
            wj = w[j] + d
            resto = np.delete(S[a], j) @ np.delete(w, j) * (1 - wj) / (1 - w[j])
            return resto + S[a][j] * wj
        mejor = None
        for a in S:
            if a == objetivo:
                continue
            pend = (S[a][j] - np.delete(S[a], j) @ np.delete(w, j) / (1 - w[j])) - \
                   (S[objetivo][j] - np.delete(S[objetivo], j) @ np.delete(w, j) / (1 - w[j]))
            if abs(pend) < 1e-12:
                continue
            d = (total(objetivo, 0) - total(a, 0)) / pend
            if -w[j] <= d <= 1 - w[j] and (mejor is None or abs(d) < abs(mejor[0])):
                mejor = (float(d), a)
        por_criterio.append({"criterio": cid, "peso": float(w[j]), "delta": mejor[0] if mejor else None,
                             "peso_cruce": float(w[j] + mejor[0]) if mejor else None, "gana": mejor[1] if mejor else None})
        xs = np.linspace(0, 1, 51)
        curvas[cid] = {"x": xs.tolist(), "totales": {a: [float(total(a, x - w[j])) for x in xs] for a in S}}
    validos = [c for c in por_criterio if c["delta"] is not None]
    critico = min(validos, key=lambda c: abs(c["delta"])) if validos else None
    return {"objetivo": objetivo, "por_criterio": por_criterio, "critico": critico, "curvas": curvas}


def pugh(base: str = "A1") -> dict:
    md = matriz_decision()
    ref = md["filas"][base]["puntajes"]
    out = {}
    for aid, f in md["filas"].items():
        marcas = ["S" if abs(p - r) < 1e-9 else ("+" if p > r else "−") for p, r in zip(f["puntajes"], ref)]
        out[aid] = {"marcas": marcas, "mas": marcas.count("+"), "menos": marcas.count("−"), "iguales": marcas.count("S")}
    return {"base": base, "filas": out}


# ==================================================================================================
# Riesgos e indicadores de valor
# ==================================================================================================
def riesgos() -> list[dict]:
    base = evaluar()["van"]
    estres = bc()["riesgos_estres"]
    out = []
    for r in cd.cargar()["riesgos_estrategicos"]["lista"]:
        e = estres.get(r["id"])
        if e is None:
            raise ModeloError(f"{r['id']} no tiene escenario de estrés en business_case.yaml → riesgos_estres")
        v = evaluar(**e["cambios"])["van"]
        out.append({**r, "puntaje": r["p"] * r["i"], "efecto": e["efecto"], "cambios": e["cambios"],
                    "van": v, "delta_van": v - base})
    return out


def indicadores_valor() -> dict:
    b = evaluar()
    n = cd.cargar()["economia"]["horizonte_anios"]
    gb_mes = s("S-04.bhr") * s("S-05.tb_mes") * 1000
    costo_anual = b["opex"] + b["capex"] / n
    return {"gb_evitados_mes": gb_mes, "tb_evitados_anio": gb_mes * 12 / 1000,
            "costo_gb": costo_anual / (gb_mes * 12), "costo_anual_equivalente": costo_anual,
            "costo_gb_enlace": s("S-03.usd_mbps_mes") * 12 * b["mbps"] / (gb_mes * 12)}


# ==================================================================================================
# Ensamble y datos para el informe
# ==================================================================================================
def calcular() -> dict:
    b = evaluar()
    if abs(b["van"] - cd.van()) > 0.05:      # ce01_datos redondea el OPEX a centavos
        raise ModeloError(f"VAN del modelo {b['van']:.2f} ≠ ce01_datos.van() {cd.van():.2f}")
    return {"base": b, "equilibrio": punto_equilibrio(), "montecarlo": montecarlo(), "tornado": tornado(),
            "escenarios": escenarios(), "ahp": ahp(), "tco": tco_alternativas(), "decision": matriz_decision(),
            "decision_guia": matriz_decision([c["peso"] for c in cd.cargar()["criterios"]["lista"]]),
            "sensibilidad": sensibilidad_pesos(), "pugh": pugh(), "riesgos": riesgos(), "valor": indicadores_valor()}


def _min(t: str) -> str:
    return t[0].lower() + t[1:]


def _meses(x: float | None) -> str:
    return "no se recupera" if x is None else f"{num(x, 1)} meses"


def datos(r: dict) -> dict[str, str]:
    b, eq, mc, ah, dec = r["base"], r["equilibrio"], r["montecarlo"], r["ahp"], r["decision"]
    tor, esc, sen, val = r["tornado"], {e["nombre"]: e for e in r["escenarios"]}, r["sensibilidad"], r["valor"]
    nombres = {v["id"]: v for v in _variables()}
    crit = {c["id"]: c["nombre"] for c in cd.cargar()["criterios"]["lista"]}
    alt = bc()["alternativas"]
    rk = dec["ranking"]
    import importlib.util
    spec = importlib.util.spec_from_file_location("calculos_e1", GESTION / "e1" / "calculos.py")
    e1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e1)
    d = dict(e1.datos())             # cifras del problema (E1) que el E2 cita al justificar el proyecto
    d |= {
        "e2_van": usd(b["van"]), "e2_tir": pct(b["tir"]), "e2_payback": _meses(b["payback_meses"]),
        "e2_bc": num(b["bc"], 2), "e2_roi": pct(b["roi"]), "e2_flujo": usd(b["anios"][0]["flujo"]),
        "e2_beneficio": usd(b["anios"][0]["beneficio"]), "e2_opex": usd(b["opex"]), "e2_capex": usd(b["capex"]),
        "e2_bn1": usd(b["bn1"]), "e2_bn2": usd(b["bn2"]), "e2_mbps": f"{num(b['mbps'])} Mbps",
        "e2_fa": num(b["factor_anualidad"], 4), "e2_va_beneficios": usd(b["va_beneficios"]), "e2_va_opex": usd(b["va_opex"]),
        "e2_aws_anual": usd(b["aws"], 2), "e2_energia": usd(b["energia"], 2), "e2_mant": usd(b["mant"], 2),
        "e2_aws_anual_guia": usd(cd.resolver("infra/centro_datos.yaml#aws.costo_mensual.referencial_documento_usd") * 12),
        "e2_aws_mes_guia": usd(cd.resolver("infra/centro_datos.yaml#aws.costo_mensual.referencial_documento_usd")),
        "e2_tco": usd(r["tco"]["A4"]["tco"]), "e2_tco_va": usd(r["tco"]["A4"]["tco_va"]),
        "e2_eq_mbps": f"{num(eq['mbps'], 1)} Mbps", "e2_eq_bhr": pct(eq["bhr"], 1), "e2_eq_usd_mbps": usd(eq["usd_mbps"], 2),
        "e2_mc_iter": num(mc["iteraciones"]), "e2_mc_semilla": str(mc["semilla"]),
        "e2_mc_p": pct(mc["p_van_positivo"], 1), "e2_mc_p5": usd(mc["p5"]), "e2_mc_p50": usd(mc["p50"]),
        "e2_mc_p95": usd(mc["p95"]), "e2_mc_media": usd(mc["media"]), "e2_mc_neg": pct(1 - mc["p_van_positivo"], 1),
        "e2_ahp_cr": num(ah["cr"], 3), "e2_ahp_ci": num(ah["ci"], 3), "e2_ahp_lambda": num(ah["lambda_max"], 3),
        "e2_ahp_ri": num(ah["ri"], 2), "e2_ahp_crmax": num(bc()["ahp"]["cr_max"], 2),
        "e2_ahp_dif": f"{num(ah['dif_max_autovector'] * 100, 1)} puntos porcentuales",
        "e2_gana": f"{rk[0]} {alt[rk[0]]['corto']}", "e2_segunda": f"{rk[1]} {alt[rk[1]]['corto']}",
        "e2_total_gana": num(dec["filas"][rk[0]]["total"], 2), "e2_total_segunda": num(dec["filas"][rk[1]]["total"], 2),
        "e2_margen": num(dec["filas"][rk[0]]["total"] - dec["filas"][rk[1]]["total"], 2),
        "e2_gb_mes": f"{num(val['gb_evitados_mes'])} GB", "e2_tb_anio": f"{num(val['tb_evitados_anio'], 1)} TB",
        "e2_costo_gb": usd(val["costo_gb"], 3), "e2_costo_gb_enlace": usd(val["costo_gb_enlace"], 3),
        "e2_costo_anual_eq": usd(val["costo_anual_equivalente"]),
        "e2_ampliacion_tco": usd(r["tco"]["A0"]["tco"]),
    }
    for k, t in enumerate(tor[:3], start=1):
        d[f"e2_tornado_{k}"] = f"{_min(nombres[t['id']]['nombre'])} [{t['supuesto']}]" if t["supuesto"].startswith("S-") \
            else f"{_min(nombres[t['id']]['nombre'])} ({t['supuesto']})"
        d[f"e2_tornado_{k}_rango"] = usd(t["rango"])
        d[f"e2_tornado_{k}_min"] = usd(t["van_min"])
        d[f"e2_tornado_{k}_max"] = usd(t["van_max"])
    for v in _variables():
        es_pct = v["id"] in ("bhr", "adopcion") or v["id"].startswith("f_")
        fmt = (lambda x: pct(x)) if es_pct and not v["id"].startswith("f_") else \
              ((lambda x: f"{'+' if x > 1 else '−' if x < 1 else '±'}{num(abs(x - 1) * 100)} %") if v["id"].startswith("f_")
               else (lambda x: usd(x)))
        d[f"e2_mc_{v['id']}_min"], d[f"e2_mc_{v['id']}_max"] = fmt(v["min"]), fmt(v["max"])
        d[f"e2_mc_{v['id']}_moda"] = fmt(v["moda"])
    for e in ("Pesimista", "Optimista"):
        d[f"e2_esc_{e.lower()}_van"] = usd(esc[e]["van"])
    c = sen["critico"]
    d.update({"e2_sens_criterio": f"{c['criterio']} {crit[c['criterio']].lower()}", "e2_sens_peso": pct(c["peso"], 1),
              "e2_sens_cruce": pct(c["peso_cruce"], 1), "e2_sens_delta": f"{num(abs(c['delta']) * 100, 1)} puntos porcentuales",
              "e2_sens_gana": f"{c['gana']} {alt[c['gana']]['corto']}"})
    for j, cid in enumerate(ah["criterios"]):
        d[f"e2_peso_{cid.lower()}"] = pct(ah["pesos"][j], 1)
        d[f"e2_peso_guia_{cid.lower()}"] = pct(ah["pesos_guia"][j])
    rr = {x["id"]: x for x in r["riesgos"]}
    for rid, x in rr.items():
        d[f"e2_{rid.lower().replace('-', '')}_van"] = usd(x["van"])
        d[f"e2_{rid.lower().replace('-', '')}_delta"] = usd(x["delta_van"])
    peor = min(r["riesgos"], key=lambda x: x["delta_van"])
    d["e2_riesgo_peor"] = peor["id"]
    d["e2_riesgo_peor_van"] = usd(peor["van"])
    d["e2_riesgos_van_neg"] = num(sum(x["van"] < 0 for x in r["riesgos"]))
    d["e2_tco_a1"] = usd(r["tco"]["A1"]["tco"])
    d["e2_dif_tco_a4_a1"] = usd(r["tco"]["A4"]["tco"] - r["tco"]["A1"]["tco"])
    return d


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-xlsx", action="store_true")
    a = ap.parse_args(argv)
    try:
        r = calcular()
        d = datos(r)
    except (ModeloError, cd.DatosCE01Error) as e:
        print("FALLA:", e, file=sys.stderr)
        return 1
    SALIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_JSON.write_text(json.dumps({"fuente": "gestion/analytics/business_case.py", "datos": d, "modelo": _jsonable(r)},
                                      ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    b, mc = r["base"], r["montecarlo"]
    print(f"VAN {usd(b['van'], 2)} · TIR {pct(b['tir'], 1)} · payback {_meses(b['payback_meses'])} · B/C {num(b['bc'], 2)} "
          f"· ROI {pct(b['roi'])} · equilibrio {d['e2_eq_mbps']}")
    print(f"Monte Carlo ({mc['iteraciones']}): P(VAN>0) {pct(mc['p_van_positivo'], 1)} · P5 {usd(mc['p5'])} · "
          f"P50 {usd(mc['p50'])} · P95 {usd(mc['p95'])}")
    print("Tornado:", "; ".join(f"{t['id']} {usd(t['rango'])}" for t in r["tornado"]))
    print(f"AHP: CR {r['ahp']['cr']:.4f} · pesos " + ", ".join(f"{c} {w:.3f}" for c, w in zip(r['ahp']['criterios'], r['ahp']['pesos'])))
    print("Matriz:", ", ".join(f"{k} {r['decision']['filas'][k]['total']:.2f}" for k in r["decision"]["ranking"]))
    print(f"Sensibilidad: {d['e2_sens_criterio']} de {d['e2_sens_peso']} a {d['e2_sens_cruce']} → gana {d['e2_sens_gana']}")
    if a.sin_xlsx:
        return 0
    import business_case_xlsx as bx
    try:
        bx.escribir(r, SALIDA_XLSX)
        van_xlsx = bx.verificar(SALIDA_XLSX)
    except (ModeloError, RuntimeError) as e:
        print("FALLA:", e, file=sys.stderr)
        return 1
    if van_xlsx is None:
        print("AVISO: ni Excel ni LibreOffice disponibles; no se recalculó el XLSX", file=sys.stderr)
    elif abs(van_xlsx - b["van"]) > TOLERANCIA_USD:
        print(f"FALLA: VAN de Excel {van_xlsx:.2f} ≠ VAN de Python {b['van']:.2f} (tolerancia US$ {TOLERANCIA_USD:g})",
              file=sys.stderr)
        return 1
    else:
        print(f"XLSX: {SALIDA_XLSX.relative_to(cd.RAIZ).as_posix()} · VAN de Excel {usd(van_xlsx, 2)} (coincide con Python)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
