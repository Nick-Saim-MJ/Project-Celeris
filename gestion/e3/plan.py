"""Modelo del Plan de Gestión del Proyecto (CE01 E3): cronograma, presupuesto, línea base, curva S y EVM.

    python gestion/e3/plan.py [--sin-msproject] [--sin-xlsx]

Lee gestion/e3/datos/plan.yaml (actividades), gestion/ce01.yaml (EDT, RACI, riesgos) e infra/*.yaml (precios) a través
de gestion/ce01_datos.py, y:

  1. Programa el proyecto con el método de la ruta crítica (CPM) en días laborables, con el calendario del plan
     (feriados y receso entre semestres). Lo terminado usa la fecha real del commit; lo pendiente no empieza antes de la
     fecha de corte. Calcula la holgura total de cada actividad pendiente: holgura 0 = ruta crítica.
  2. Programa la línea base (duraciones planificadas, sin avance real) para el valor planificado del EVM.
  3. Presupuesta cada actividad (horas del equipo × tarifa S-07 + costos fijos de hardware y AWS), lo agrega por paquete
     de la EDT y falla si la suma de los paquetes no cuadra con la línea base, si una actividad no pertenece a un paquete
     de nivel 2 o si un paquete no tiene costo.
  4. Calcula la curva S semanal y el EVM a la fecha de corte (regla 0/100).
  5. Escribe gestion/e3/datos/plan.json ({"datos": {{dato:}}, "modelo": …}), el XML de MS Project
     (entregables/CE01/E3/Cronograma_Celeris.xml), lo verifica con MS Project si está instalado (ruta crítica igual a la
     de Python) y escribe los libros Presupuesto_EVM_E3.xlsx y Backlog_E3.xlsx.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from functools import lru_cache
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
GESTION = AQUI.parent
RAIZ = GESTION.parent
sys.path.insert(0, str(GESTION))
import ce01_datos as cd  # noqa: E402
from ce01_datos import num, pct, s, usd  # noqa: E402

DATOS = AQUI / "datos"
SALIDA = RAIZ / "entregables" / "CE01" / "E3"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
               "noviembre", "diciembre"]


class PlanError(Exception):
    pass


@lru_cache(maxsize=None)
def plan() -> dict:
    return yaml.safe_load((DATOS / "plan.yaml").read_text(encoding="utf-8"))


def fecha(t: str | dt.date) -> dt.date:
    return t if isinstance(t, dt.date) else dt.date.fromisoformat(str(t))


def f_corta(d: dt.date) -> str:
    """«18 nov 2026»."""
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def f_larga(d: dt.date) -> str:
    """«18 de diciembre de 2026»."""
    return f"{d.day} de {MESES_LARGO[d.month - 1]} de {d.year}"


# ==================================================================================================
# Calendario
# ==================================================================================================
class Calendario:
    """Días laborables (lunes a viernes menos las excepciones). Un tiempo de trabajo se expresa como desplazamiento
    entero: el desplazamiento k es el inicio (08:00) del k-ésimo día laborable; el fin de ese día es k + 1."""

    def __init__(self, cfg: dict):
        self.no_laborables: set[dt.date] = set()
        for e in cfg["excepciones"]:
            d, h = fecha(e["desde"]), fecha(e["hasta"])
            while d <= h:
                self.no_laborables.add(d)
                d += dt.timedelta(days=1)
        ini = fecha(cfg["inicio_proyecto"]) - dt.timedelta(days=7)
        self.dias = [ini + dt.timedelta(days=i) for i in range(900) if self.laborable(ini + dt.timedelta(days=i))]
        self.indice = {d: k for k, d in enumerate(self.dias)}

    def laborable(self, d: dt.date) -> bool:
        return d.weekday() < 5 and d not in self.no_laborables

    def inicio(self, d: dt.date) -> int:
        """Desplazamiento del inicio del primer día laborable ≥ d."""
        while d not in self.indice:
            d += dt.timedelta(days=1)
        return self.indice[d]

    def fin(self, d: dt.date) -> int:
        """Desplazamiento del fin del último día laborable ≤ d."""
        while d not in self.indice:
            d -= dt.timedelta(days=1)
        return self.indice[d] + 1

    def dia(self, k: int) -> dt.date:
        return self.dias[k]

    def laborables_entre(self, a: dt.date, b: dt.date) -> int:
        return max(0, self.fin(b) - self.inicio(a))


@lru_cache(maxsize=None)
def calendario() -> Calendario:
    return Calendario(plan()["calendario"])


# ==================================================================================================
# Actividades y CPM
# ==================================================================================================
def _preds(a: dict) -> list[tuple[str, str, int]]:
    out = []
    for p in a.get("pred", []):
        out.append((p, "FS", 0) if isinstance(p, str) else (p[0], p[1], int(p[2])))
    return out


def actividades() -> list[dict]:
    acts = [dict(a) for a in plan()["actividades"]]
    ids = [a["id"] for a in acts]
    if len(ids) != len(set(ids)):
        raise PlanError("Hay actividades con el mismo id en plan.yaml")
    for a in acts:
        a["hito"] = bool(a.get("hito"))
        a["dur"] = 0 if a["hito"] else int(a["dur"])
        a["preds"] = _preds(a)
        a["hecha"] = "real" in a
        for p, tipo, _ in a["preds"]:
            if p not in ids:
                raise PlanError(f"{a['id']}: la predecesora {p} no existe")
            if tipo not in ("FS", "SS"):
                raise PlanError(f"{a['id']}: tipo de dependencia {tipo} no soportado (FS o SS)")
    return acts


def _orden(acts: list[dict]) -> list[dict]:
    por_id = {a["id"]: a for a in acts}
    vistos, orden = set(), []

    def visitar(a, pila=()):
        if a["id"] in pila:
            raise PlanError(f"Dependencia circular: {' → '.join(pila + (a['id'],))}")
        if a["id"] in vistos:
            return
        for p, *_ in a["preds"]:
            visitar(por_id[p], pila + (a["id"],))
        vistos.add(a["id"])
        orden.append(a)

    for a in acts:
        visitar(a)
    return orden


def programar(linea_base: bool = False) -> dict[str, dict]:
    """CPM. Devuelve {id: {S, F, LS, LF, holgura, critica, inicio, fin, snet_corte}} en desplazamientos de días
    laborables. Con linea_base=True ignora el avance real y usa la duración planificada de todo."""
    cal = calendario()
    cfg = plan()["calendario"]
    acts = _orden(actividades())
    corte = cal.inicio(fecha(plan()["meta"]["fecha_estado"]) + dt.timedelta(days=1))
    inicio = cal.inicio(fecha(cfg["inicio_proyecto"]))
    r: dict[str, dict] = {}
    for a in acts:
        real = a.get("real") if not linea_base else None
        if real:
            S, F = cal.inicio(fecha(real["inicio"])), cal.fin(fecha(real["fin"]))
            F = max(F, S + (0 if a["hito"] else 1))
            r[a["id"]] = {"S": S, "F": F, "snet": None}
            continue
        S, snet = inicio, None
        for p, tipo, lag in a["preds"]:
            S = max(S, (r[p]["F"] if tipo == "FS" else r[p]["S"]) + lag)
        if a.get("snet"):
            lim = cal.inicio(fecha(cfg["academico"][a["snet"]]))
            if lim >= S:
                S, snet = lim, fecha(cfg["academico"][a["snet"]])
        if not linea_base and S < corte:                 # el trabajo pendiente no se programa en el pasado
            S, snet = corte, cal.dia(corte)
        r[a["id"]] = {"S": S, "F": S + a["dur"], "snet": snet}
    fin_proy = max(x["F"] for x in r.values())
    suc: dict[str, list] = {a["id"]: [] for a in acts}
    for a in acts:
        for p, tipo, lag in a["preds"]:
            suc[p].append((a["id"], tipo, lag))
    por_id = {a["id"]: a for a in acts}
    for a in reversed(acts):
        LF = fin_proy
        for sid, tipo, lag in suc[a["id"]]:
            if por_id[sid]["hecha"] and not linea_base:
                continue
            LF = min(LF, r[sid]["LS"] - lag if tipo == "FS" else r[sid]["LS"] - lag + a["dur"])
        r[a["id"]]["LF"], r[a["id"]]["LS"] = LF, LF - a["dur"]
        r[a["id"]]["holgura"] = r[a["id"]]["LS"] - r[a["id"]]["S"]
        pendiente = linea_base or not a["hecha"]
        r[a["id"]]["critica"] = pendiente and r[a["id"]]["holgura"] == 0
    for a in acts:
        x = r[a["id"]]
        if a["hito"]:                                   # hito: al fin de su predecesora (17:00) o en su restricción (08:00)
            x["inicio"] = x["fin"] = cal.dia(x["S"]) if (x["snet"] or not a["preds"]) else cal.dia(x["S"] - 1)
        else:
            x["inicio"], x["fin"] = cal.dia(x["S"]), cal.dia(x["F"] - 1)
        if a.get("real") and not linea_base:            # se muestran las fechas reales del commit
            x["inicio"], x["fin"] = fecha(a["real"]["inicio"]), fecha(a["real"]["fin"])
    return r


# ==================================================================================================
# Costos
# ==================================================================================================
def tarifa() -> float:
    return s("S-07.tarifa_usd_h")


def equipo() -> list[str]:
    return [x["id"] for x in plan()["recursos"] if x["tipo"] == "equipo"]


def costos_fijos() -> dict[str, float]:
    aws = plan()["costos"]["aws"]
    efim = cd.resolver("infra/centro_datos.yaml#aws.costo_mensual.laboratorio_efimero")
    sim = cd.resolver("infra/centro_datos.yaml#aws.costo_mensual.simulacro")
    usd_h_efim = sum(l["cantidad"] * l["precio_hora"] for l in efim["lineas"])
    usd_h_sim = sum(l["cantidad"] * l["precio_hora"] for l in sim["lineas"])
    return {
        "capex": cd.costos()["capex_total"],
        "aws_efimero": aws["horas_efimero"] * usd_h_efim + sim["horas"] * usd_h_sim,
        "aws_24x7": aws["meses_24x7"] * cd.aws_mensual(),
        "_usd_h_efimero": usd_h_efim, "_usd_h_simulacro": usd_h_sim, "_horas_simulacro": sim["horas"],
    }


def presupuesto() -> dict:
    """Costo por actividad y por paquete, línea base y reservas. Falla si algo no cuadra."""
    y = cd.cargar()
    edt = {p["id"]: p for p in y["edt"]["paquetes"]}
    nivel2 = [pid for pid in edt if pid.count(".") == 1]
    cf = costos_fijos()
    eq, t = equipo(), tarifa()
    acts = actividades()
    por_act, errores = {}, []
    for a in acts:
        if a["hito"]:
            continue
        if a.get("paquete") not in nivel2:
            errores.append(f"{a['id']}: el paquete {a.get('paquete')} no es un paquete de nivel 2 de la EDT")
            continue
        h_eq = sum(v for k, v in a.get("horas", {}).items() if k in eq)
        fijo = cf[a["costo_fijo"]] if a.get("costo_fijo") else 0.0
        por_act[a["id"]] = {"horas_equipo": h_eq, "horas_contraparte": sum(v for k, v in a.get("horas", {}).items() if k not in eq),
                            "costo_horas": h_eq * t, "costo_fijo": fijo, "total": h_eq * t + fijo, "paquete": a["paquete"]}
    paquetes = {}
    for pid in nivel2:
        filas = [v for v in por_act.values() if v["paquete"] == pid]
        tot = sum(v["total"] for v in filas)
        if not filas or tot <= 0:
            errores.append(f"Paquete {pid} «{edt[pid]['nombre']}» sin actividades o sin costo")
        h = sum(v["horas_equipo"] for v in filas)
        if edt[pid].get("esfuerzo_h") is not None and abs(h - edt[pid]["esfuerzo_h"]) > 1e-9:
            errores.append(f"Paquete {pid}: el diccionario de la EDT dice {edt[pid]['esfuerzo_h']} h y las actividades suman {h} h")
        paquetes[pid] = {"nombre": edt[pid]["nombre"], "horas": h, "costo_horas": sum(v["costo_horas"] for v in filas),
                         "costo_fijo": sum(v["costo_fijo"] for v in filas), "total": tot,
                         "actividades": [k for k, v in por_act.items() if v["paquete"] == pid]}
    c = plan()["costos"]
    bac = sum(v["total"] for v in por_act.values()) + c["herramientas_usd"]
    if abs(sum(p["total"] for p in paquetes.values()) + c["herramientas_usd"] - bac) > 0.005:
        errores.append("La suma de los paquetes no cuadra con el presupuesto de las actividades")
    contingencia = c["contingencia"] * bac
    linea_base = bac + contingencia
    gestion = c["gestion"] * linea_base
    nivel1 = {}
    for pid, p in paquetes.items():
        n1 = pid.split(".")[0]
        nivel1.setdefault(n1, {"nombre": edt[n1]["nombre"], "total": 0.0, "horas": 0.0})
        nivel1[n1]["total"] += p["total"]
        nivel1[n1]["horas"] += p["horas"]
    if abs(sum(v["total"] for v in nivel1.values()) * (1 + c["contingencia"]) + c["herramientas_usd"] * (1 + c["contingencia"]) - linea_base) > 0.005:
        errores.append("La línea base no cuadra con la suma de los paquetes de nivel 1 más la contingencia")
    if errores:
        raise PlanError("Alcance, cronograma y costos no son coherentes:\n  - " + "\n  - ".join(errores))
    horas_rec = {}
    for a in acts:
        for k, v in a.get("horas", {}).items():
            horas_rec[k] = horas_rec.get(k, 0) + v
    return {"actividades": por_act, "paquetes": paquetes, "nivel1": nivel1, "bac": bac, "contingencia": contingencia,
            "linea_base": linea_base, "gestion": gestion, "total_autorizado": linea_base + gestion,
            "horas_recurso": horas_rec, "costos_fijos": cf, "tarifa": t, "herramientas": c["herramientas_usd"]}


# ==================================================================================================
# Curva S y EVM
# ==================================================================================================
def _acumulado(cron: dict, pres: dict, hasta: dt.date, linea_base: bool) -> float:
    """Costo planificado acumulado al fin del día `hasta`, prorrateado por día laborable de cada actividad."""
    cal = calendario()
    k_hasta = cal.fin(hasta)
    tot = 0.0
    for aid, c in pres["actividades"].items():
        x = cron[aid]
        d = x["F"] - x["S"]
        if d <= 0:
            continue
        hechos = min(max(k_hasta - x["S"], 0), d)
        tot += c["total"] * hechos / d
    return tot


def evm(cron_lb: dict, cron: dict, pres: dict) -> dict:
    corte = fecha(plan()["meta"]["fecha_estado"])
    acts = {a["id"]: a for a in actividades()}

    def ev(hasta: dt.date) -> float:            # regla 0/100
        return sum(c["total"] for aid, c in pres["actividades"].items()
                   if acts[aid]["hecha"] and fecha(acts[aid]["real"]["fin"]) <= hasta)

    semanas = []
    ini = fecha(plan()["calendario"]["inicio_proyecto"])
    viernes = ini + dt.timedelta(days=(4 - ini.weekday()) % 7)
    fin_proy = max(x["fin"] for x in cron_lb.values())
    d = viernes
    while d <= fin_proy + dt.timedelta(days=6):
        semanas.append({"fecha": d.isoformat(), "pv": _acumulado(cron_lb, pres, d, True)})
        d += dt.timedelta(days=7)
    cortes = []
    for d in sorted({viernes, corte}):
        pv, e = _acumulado(cron_lb, pres, d, True), ev(d)
        ac = e                                      # sin registro de horas todavía: AC = EV (CPI no medido)
        cortes.append({"fecha": d.isoformat(), "pv": pv, "ev": e, "ac": ac,
                       "spi": e / pv if pv else None, "cpi": e / ac if ac else None,
                       "sv": e - pv, "cv": e - ac})
    ult = cortes[-1]
    bac = pres["bac"]
    return {"semanas": semanas, "cortes": cortes, "bac": bac, "corte": corte.isoformat(),
            "avance_planificado": ult["pv"] / bac, "avance_real": ult["ev"] / bac,
            "eac": bac / ult["cpi"] if ult["cpi"] else None, "umbral": plan()["costos"]["umbral_alerta"]}


# ==================================================================================================
# Ensamblado
# ==================================================================================================
def ruta_critica(cron: dict) -> list[str]:
    acts = _orden(actividades())
    return [a["id"] for a in sorted(acts, key=lambda a: (cron[a["id"]]["S"], cron[a["id"]]["F"])) if cron[a["id"]]["critica"]]


def calcular() -> dict:
    cal = calendario()
    cron, cron_lb = programar(), programar(linea_base=True)
    pres = presupuesto()
    e = evm(cron_lb, cron, pres)
    acts = actividades()
    aca = plan()["calendario"]["academico"]
    h = plan()["hitos"]
    avisos = []
    if cron["H1"]["fin"] != fecha(aca["fin_s1"]):
        avisos.append(f"H1 cae el {cron['H1']['fin']}, no el {aca['fin_s1']} previsto para el cierre de S1")
    fin_s2 = fecha(aca["inicio_s2"]) + dt.timedelta(weeks=aca["semanas_s2"]) - dt.timedelta(days=3)
    if cron["H4"]["fin"] != fin_s2:
        avisos.append(f"H4 cae el {cron['H4']['fin']}, no el {fin_s2} (fin de la semana {aca['semanas_s2']} de S2)")
    filas = []
    for a in _orden(acts):
        x, b = cron[a["id"]], cron_lb[a["id"]]
        c = pres["actividades"].get(a["id"], {})
        filas.append({
            "id": a["id"], "nombre": a["nombre"], "paquete": a.get("paquete"), "hito": a["hito"],
            "dur": a["dur"], "dur_real": (x["F"] - x["S"]) if a["hecha"] and not a["hito"] else None,
            "inicio": x["inicio"].isoformat(), "fin": x["fin"].isoformat(),
            "lb_inicio": b["inicio"].isoformat(), "lb_fin": b["fin"].isoformat(),
            "holgura": None if a["hecha"] else x["holgura"], "critica": x["critica"], "hecha": a["hecha"],
            "avance": 100 if a["hecha"] else 0, "commit": a.get("real", {}).get("commit"),
            "snet": x["snet"].isoformat() if x["snet"] else None,
            "preds": [f"{p}{'' if t == 'FS' and not l else ' ' + t}{'+' + str(l) if l else ''}" for p, t, l in a["preds"]],
            "horas": a.get("horas", {}), "costo": c.get("total", 0.0), "costo_fijo_tipo": a.get("costo_fijo"),
            "sprints": a.get("sprints"),
        })
    sys.path.insert(0, str(AQUI))
    import agil
    ag = agil.modelo(cron, cal, acts, PlanError)
    return {"filas": filas, "ruta_critica": ruta_critica(cron), "presupuesto": pres, "evm": e, "agil": ag,
            "hitos": {k: {"nombre": v, "fecha": cron[k]["fin"].isoformat(), "lb": cron_lb[k]["fin"].isoformat()}
                      for k, v in h.items()},
            "inicio": fecha(plan()["calendario"]["inicio_proyecto"]).isoformat(),
            "fin": cron["H4"]["fin"].isoformat(), "avisos": avisos,
            "dias_laborables": cal.laborables_entre(fecha(plan()["calendario"]["inicio_proyecto"]), cron["H4"]["fin"])}


def datos(m: dict) -> dict[str, str]:
    p, e = m["presupuesto"], m["evm"]
    ult = e["cortes"][-1]
    rc = [f for f in m["filas"] if f["critica"] and not f["hito"]]
    acts = [f for f in m["filas"] if not f["hito"]]
    hechas = [f for f in acts if f["hecha"]]
    cf = p["costos_fijos"]
    d = {
        "e3_inicio": f_larga(fecha(m["inicio"])), "e3_fin": f_larga(fecha(m["fin"])),
        "e3_h1": f_larga(fecha(m["hitos"]["H1"]["fecha"])), "e3_hs2": f_larga(fecha(m["hitos"]["HS2"]["fecha"])),
        "e3_h2": f_larga(fecha(m["hitos"]["H2"]["fecha"])), "e3_h3": f_larga(fecha(m["hitos"]["H3"]["fecha"])),
        "e3_h4": f_larga(fecha(m["hitos"]["H4"]["fecha"])), "e3_corte": f_larga(fecha(e["corte"])),
        "e3_n_actividades": num(len(acts)), "e3_n_hitos": num(len([f for f in m["filas"] if f["hito"]])),
        "e3_n_hechas": num(len(hechas)), "e3_n_criticas": num(len(rc)),
        "e3_n_paquetes": num(len(p["paquetes"])),
        "e3_dias": f"{num(m['dias_laborables'])} días laborables",
        "e3_horas_equipo": f"{num(sum(v for k, v in p['horas_recurso'].items() if k in equipo()))} h",
        "e3_horas_nick": f"{num(p['horas_recurso'].get('Nick', 0))} h",
        "e3_horas_henyelrey": f"{num(p['horas_recurso'].get('Henyelrey', 0))} h",
        "e3_horas_contraparte": f"{num(sum(v for k, v in p['horas_recurso'].items() if k not in equipo()))} h",
        "e3_tarifa": f"{usd(p['tarifa'])}/h",
        "e3_bac": usd(p["bac"]), "e3_contingencia": usd(p["contingencia"]), "e3_linea_base": usd(p["linea_base"]),
        "e3_gestion": usd(p["gestion"]), "e3_total": usd(p["total_autorizado"]),
        "e3_cont_pct": pct(plan()["costos"]["contingencia"]), "e3_gest_pct": pct(plan()["costos"]["gestion"]),
        "e3_costo_horas": usd(sum(v["costo_horas"] for v in p["actividades"].values())),
        "e3_hardware": usd(cf["capex"]), "e3_aws": usd(cf["aws_efimero"] + cf["aws_24x7"]),
        "e3_aws_efimero": usd(cf["aws_efimero"], 2), "e3_aws_24x7": usd(cf["aws_24x7"], 2),
        "e3_aws_horas_efimero": f"{num(plan()['costos']['aws']['horas_efimero'])} h",
        "e3_aws_meses": f"{num(plan()['costos']['aws']['meses_24x7'])} meses",
        "e3_pv": usd(ult["pv"]), "e3_ev": usd(ult["ev"]), "e3_ac": usd(ult["ac"]),
        "e3_spi": num(ult["spi"], 2), "e3_cpi": num(ult["cpi"], 2), "e3_sv": usd(ult["sv"]),
        "e3_avance_plan": pct(e["avance_planificado"], 1), "e3_avance_real": pct(e["avance_real"], 1),
        "e3_umbral": num(e["umbral"], 1),
        "e3_ruta_critica": " → ".join(f["id"] for f in rc),
        "e3_capex_e2": usd(cd.costos()["capex_total"]),
        "e3_opex_e2": usd(cd.costos()["opex_total"]),
        "e3_semana1_spi": num(e["cortes"][0]["spi"], 2) if e["cortes"][0]["spi"] is not None else "no calculable",
        "e3_semana1": f_larga(fecha(e["cortes"][0]["fecha"])),
    }
    for k, v in p["nivel1"].items():
        d[f"e3_n1_{k}"] = usd(v["total"])
    for k, v in p["paquetes"].items():
        d[f"e3_p_{k.replace('.', '_')}"] = usd(v["total"])
    ag = m["agil"]
    d.update({
        "e3_hu_total": num(len(ag["historias"])), "e3_hu_sprint": num(len([h for h in ag["historias"] if h["sprint"]])),
        "e3_pts_comprometidos": f"{num(ag['comprometido'])} puntos", "e3_pts_must": f"{num(ag['must'])} puntos",
        "e3_pts_alcance": f"{num(ag['alcance_total'])} puntos", "e3_capacidad": f"{num(ag['capacidad'])} puntos",
        "e3_velocidad": f"{num(ag['velocidad_plan'], 1)} puntos", "e3_n_sprints": num(len(ag["sprints"])),
        "e3_hu_fuera": ", ".join(ag["fuera"]), "e3_n_req": num(len(ag["requisitos"])),
        "e3_sprint1_inicio": f_larga(fecha(ag["sprints"][0]["inicio"])),
        "e3_sprint6_fin": f_larga(fecha(ag["sprints"][-1]["fin"])),
        "e3_hu_primera": ag["historias"][0]["id"],
    })
    cron_rc = [f for f in m["filas"] if f["critica"]]
    d["e3_rc_s1"] = " → ".join(f["id"] for f in cron_rc if not f["hito"] and f["fin"] <= m["hitos"]["H1"]["fecha"])
    d["e3_rc_s2"] = " → ".join(f["id"] for f in cron_rc if not f["hito"] and f["inicio"] >= m["hitos"]["HS2"]["fecha"])
    d["e3_holgura_512"] = f"{num(next(f['holgura'] for f in m['filas'] if f['id'] == '5.1.2'))} días laborables"
    d["e3_reserva_pct_bac"] = pct(p["gestion"] / p["bac"], 1)
    cal_cfg = plan()["calendario"]
    aca = cal_cfg["academico"]

    def _rango(e):
        a, b = fecha(e["desde"]), fecha(e["hasta"])
        if a == b:
            return f_larga(a)
        if a.year == b.year and a.month == b.month:
            return f"{a.day} y {b.day} de {MESES_LARGO[a.month - 1]} de {a.year}" if (b - a).days == 1 else f"del {a.day} al {f_larga(b)}"
        return f"del {f_larga(a)} al {f_larga(b)}"

    exc = cal_cfg["excepciones"]
    receso = [e for e in exc if "Receso" in e["nombre"]]
    feriados = [e for e in exc if "Receso" not in e["nombre"]]
    d.update({
        "e3_fin_s1": f_larga(fecha(aca["fin_s1"])), "e3_inicio_s2": f_larga(fecha(aca["inicio_s2"])),
        "e3_semanas_s2": f"{num(aca['semanas_s2'])} semanas",
        "e3_receso": _rango(receso[0]) if receso else "sin receso",
        "e3_feriados": " y del ".join(f"{_rango(e)} ({e['nombre'].split('(')[-1].rstrip(')')})" if "(" in e["nombre"] else _rango(e)
                                for e in feriados),
        "e3_jornada": f"de {cal_cfg['jornada']['inicio']} a {cal_cfg['jornada']['fin']}",
    })
    e2 = RAIZ / "gestion" / "e2" / "datos" / "resultados.json"
    if e2.exists():
        de2 = json.loads(e2.read_text(encoding="utf-8")).get("datos", {})
        for k in ("e2_van", "e2_tir", "e2_payback", "e2_gana", "e2_capex", "e2_opex"):
            if k in de2:
                d[k] = de2[k]
    if "msproject" in m and m["msproject"].get("ok"):
        d["e3_msproject"] = m["msproject"]["resumen"]
    return d


def escribir_json(m: dict) -> Path:
    DATOS.mkdir(exist_ok=True)
    ruta = DATOS / "plan.json"
    ruta.write_text(json.dumps({"datos": datos(m), "modelo": m}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return ruta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-msproject", action="store_true", help="no abre el XML con MS Project")
    ap.add_argument("--sin-xlsx", action="store_true", help="no escribe ni verifica los libros XLSX")
    a = ap.parse_args(argv)
    try:
        m = calcular()
        for av in m["avisos"]:
            print(f"  AVISO {av}")
        escribir_json(m)
        sys.path.insert(0, str(AQUI))
        import mspdi
        xml = mspdi.escribir(m)
        print(f"CE01 E3: cronograma {xml.relative_to(RAIZ).as_posix()} · ruta crítica {' → '.join(m['ruta_critica'])}")
        if not a.sin_msproject:
            import msproject
            res = msproject.verificar(xml, m)
            print(f"CE01 E3: MS Project {res['resumen']}")
            m["msproject"] = res
            escribir_json(m)
        if not a.sin_xlsx:
            import xlsx_e3
            for ruta in xlsx_e3.escribir_todo(m):
                print(f"CE01 E3: {ruta.relative_to(RAIZ).as_posix()} verificado")
        p = m["presupuesto"]
        print(f"CE01 E3: BAC {usd(p['bac'])} · línea base {usd(p['linea_base'])} · reserva de gestión {usd(p['gestion'])} · "
              f"SPI {num(m['evm']['cortes'][-1]['spi'], 2)} al {m['evm']['corte']}")
    except (PlanError, cd.DatosCE01Error, RuntimeError) as e:
        print(f"ERROR {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
