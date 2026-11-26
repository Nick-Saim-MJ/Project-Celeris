"""Backlog y sprints de la consola (CE01 E3 §3.6): WSJF, MoSCoW, capacidad y coherencia con el SRS y el cronograma.

Lo llama gestion/e3/plan.py (calcular). Lee gestion/e3/datos/agil.yaml y docs/software/e1/srs (03 y 06). Falla
(PlanError) si una historia cita un REQ-F o un CU que no existe, si su MoSCoW no es la prioridad del requisito principal en
el SRS, si un sprint supera la capacidad, si una historia queda en un sprint anterior a otra de la que depende o si un
sprint no cae dentro de la actividad del cronograma que lo contiene.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SRS = RAIZ / "docs" / "software" / "e1" / "srs"
MOSCOW = {"M": "Must", "S": "Should", "C": "Could", "W": "Won't"}


@lru_cache(maxsize=None)
def agil() -> dict:
    return yaml.safe_load((AQUI / "datos" / "agil.yaml").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def requisitos() -> dict[str, dict]:
    """{REQ-F-xx: {texto, prioridad}} de la primera tabla del SRS donde aparece con prioridad M/S/C/W."""
    out = {}
    for ln in (SRS / "03-requisitos-funcionales.md").read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) >= 3 and re.fullmatch(r"REQ-F-\d+", c[0]) and c[2] in MOSCOW and c[0] not in out:
            out[c[0]] = {"texto": c[1], "prioridad": c[2]}
    return out


@lru_cache(maxsize=None)
def casos_uso() -> dict[str, str]:
    out = {}
    for ln in (SRS / "06-casos-de-uso.md").read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) >= 2 and re.fullmatch(r"CU-\d+", c[0]) and c[0] not in out:
            out[c[0]] = c[1]
    return out


def modelo(cron: dict, cal, acts: list[dict], error) -> dict:
    """Backlog ordenado por WSJF, sprints con fechas y verificación. `cron` = programar() de plan.py; `cal` = Calendario;
    `acts` = actividades() de plan.py; `error` = clase de excepción a lanzar."""
    a = agil()
    req, cu = requisitos(), casos_uso()
    errores = []
    hist = []
    for h in a["historias"]:
        for r in h["req"]:
            if r not in req:
                errores.append(f"{h['id']}: {r} no existe en el SRS (docs/software/e1/srs/03-requisitos-funcionales.md)")
        for c in h["cu"]:
            if c not in cu:
                errores.append(f"{h['id']}: {c} no existe en el SRS (06-casos-de-uso.md)")
        esperado = MOSCOW[req[h["req"][0]]["prioridad"]] if h["req"][0] in req else None
        moscow = h.get("moscow", esperado)
        if moscow != esperado and not h.get("justificacion"):
            errores.append(f"{h['id']}: MoSCoW {moscow} ≠ prioridad {esperado} de {h['req'][0]} en el SRS, sin justificación")
        if moscow == "Won't" and h.get("sprint"):
            errores.append(f"{h['id']}: una historia Won't no puede tener sprint")
        w = h["wsjf"]
        cod = w["valor"] + w["tiempo"] + w["riesgo"]
        hist.append({**h, "moscow": moscow, "cod": cod, "wsjf_valor": cod / h["puntos"],
                     "texto": f"Como {h['rol']}, quiero {h['quiero']}, para {h['para']}.", "sprint": h.get("sprint")})
    por_id = {h["id"]: h for h in hist}
    for h in hist:
        for d in h.get("depende") or []:
            if d not in por_id:
                errores.append(f"{h['id']}: depende de {d}, que no existe")
            elif h["sprint"] and (not por_id[d]["sprint"] or por_id[d]["sprint"] > h["sprint"]):
                errores.append(f"{h['id']} (sprint {h['sprint']}) depende de {d} (sprint {por_id[d]['sprint']})")
    orden = sorted(hist, key=lambda h: (h["moscow"] == "Won't", -h["wsjf_valor"], h["id"]))
    for k, h in enumerate(orden, start=1):
        h["rango"] = k

    # Sprints: cada actividad 5.4.x con `sprints: [a, b]` aloja sprints de 5 días laborables desde su inicio.
    actividades = {aid: x for aid, x in cron.items()}
    plan_sprints = {}
    for act in acts:
        if act.get("sprints"):
            ini, fin = act["sprints"]
            if (fin - ini + 1) * 5 != act["dur"]:
                errores.append(f"{act['id']}: {fin - ini + 1} sprints de 5 días no suman su duración de {act['dur']} días")
            for n in range(ini, fin + 1):
                S = actividades[act["id"]]["S"] + (n - ini) * 5
                plan_sprints[n] = {"actividad": act["id"], "inicio": cal.dia(S), "fin": cal.dia(S + 4)}
    sprints = []
    cap = a["capacidad_puntos"]
    for sp in a["sprints"]:
        n = sp["n"]
        hs = [h for h in hist if h["sprint"] == n]
        pts = sum(h["puntos"] for h in hs)
        if n not in plan_sprints:
            errores.append(f"Sprint {n}: ninguna actividad del cronograma lo contiene")
            continue
        if pts > cap:
            errores.append(f"Sprint {n}: {pts} puntos superan la capacidad de {cap}")
        if not hs:
            errores.append(f"Sprint {n}: sin historias")
        sprints.append({**sp, **plan_sprints[n], "historias": [h["id"] for h in hs], "puntos": pts})
    for h in hist:
        if h["sprint"] and h["sprint"] not in {s["n"] for s in sprints}:
            errores.append(f"{h['id']}: el sprint {h['sprint']} no existe")
        if h["moscow"] == "Must" and not h["sprint"]:
            errores.append(f"{h['id']}: una historia Must debe tener sprint en S2")
    if errores:
        raise error("El backlog no es coherente con el SRS o el cronograma:\n  - " + "\n  - ".join(errores))
    comprometido = sum(s["puntos"] for s in sprints)
    acumulado, burn = 0, []
    for s in sprints:
        acumulado += s["puntos"]
        burn.append({"sprint": s["n"], "fin": s["fin"].isoformat(), "plan": acumulado})
    return {
        "historias": orden, "sprints": [{**s, "inicio": s["inicio"].isoformat(), "fin": s["fin"].isoformat()} for s in sprints],
        "comprometido": comprometido, "capacidad": cap,
        "velocidad_plan": comprometido / len(sprints),
        "alcance_total": sum(h["puntos"] for h in hist if h["moscow"] != "Won't"),
        "must": sum(h["puntos"] for h in hist if h["moscow"] == "Must"),
        "fuera": [h["id"] for h in orden if not h["sprint"]], "burnup": burn,
        "requisitos": sorted({r for h in hist for r in h["req"]}, key=lambda r: int(r.split("-")[-1])),
    }
