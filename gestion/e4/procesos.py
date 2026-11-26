"""Modelo de procesos de CE01 E4 (CE0131–CE0135, CI-104): descarga, simulación AS-IS / TO-BE y comparativo.

    python gestion/e4/procesos.py [--sin-render] [--sin-xlsx]

Lee gestion/e4/simulacion.yaml (procesos P1 y P2, AS-IS y TO-BE), gestion/e4/datos/procesos.yaml (caracterización) y los
supuestos de infra/trazabilidad.yaml a través de gestion/ce01_datos.py. Escribe:

| Salida | Contenido |
| --- | --- |
| gestion/e4/bpmn/*.bpmn | BPMN 2.0 de los cuatro diagramas, validados contra el XSD de OMG (gestion/e4/bpmn.py) |
| gestion/e4/datos/e4.json | {"datos": …} para {{dato:}} del informe y "modelo" para tablas y figuras |
| gestion/e4/datos/resultados.json | horas técnicas ahorradas, para que el E2 las use en lugar de S-07 cuando se midan |
| gestion/e4/instrumentos/registro-tiempos.xlsx | plantilla de cronometraje por fase (gestion/e4/instrumentos.py) |

La simulación es de Monte Carlo: cada iteración recorre el diagrama desde el evento de inicio, muestrea la duración de
cada tarea (triangular [S-43] o fórmula con supuestos) y elige la salida de cada compuerta con su probabilidad [S-44].
Falla (PlanError) si un nodo no tiene duración, una probabilidad no suma 1, un PD-xx no está en el diagrama o una
automatización no tiene REQ-F del SRS ni prueba. Si existen resultados de Bizagi (gestion/e4/datos/bizagi/resultados.yaml)
y difieren más de 10 % de los de Python, lo informa como aviso para revisar parámetros.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI.parent))
import ce01_datos as cd  # noqa: E402
from ce01_datos import num, pct, s, usd  # noqa: E402

SIM = AQUI / "simulacion.yaml"
DATOS = AQUI / "datos"
SRS = RAIZ / "docs" / "software" / "e1" / "srs" / "03-requisitos-funcionales.md"
PRUEBAS = RAIZ / "infra" / "pruebas.yaml"
BIZAGI = DATOS / "bizagi" / "resultados.yaml"
TOLERANCIA_BIZAGI = 0.10
MEDIDAS = ("ciclo_h", "ocupacion_h", "descarga_h", "wan_gb", "interrupciones", "horas_tecnico", "horas_encargado",
           "horas_docente", "horas_personal", "costo", "listo", "habilitar_h")


class PlanError(Exception):
    pass


def sim() -> dict:
    return yaml.safe_load(SIM.read_text(encoding="utf-8"))


def caracterizacion() -> dict:
    return yaml.safe_load((DATOS / "procesos.yaml").read_text(encoding="utf-8"))


# ==================================================================================================
# Cálculos con supuestos (sin simulación)
# ==================================================================================================
def _mbps_precarga() -> float:
    """Límite de la precarga en la ventana nocturna: el que verifica la prueba T50 («sin pasar 50 Mbps»)."""
    t50 = next(t for t in yaml.safe_load(PRUEBAS.read_text(encoding="utf-8"))["pruebas"] if t["id"] == "T50")
    m = re.search(r"sin pasar (\d+) Mbps", t50["resultado_esperado"])
    if not m:
        raise PlanError("T50 ya no fija el límite de la precarga («sin pasar N Mbps»): revise infra/pruebas.yaml")
    return float(m.group(1))


def calculos() -> dict:
    pcs = s("S-26.pcs_lab")
    gb_pc = s("S-27.gb_pc")
    gb_lab = pcs * gb_pc
    mbps_wan = s("S-42.mbps_disponible")
    gbps_lan = float(cd.resolver("infra/centro_datos.yaml#host.enlace_acceso.velocidad_gbps"))
    mbps_pre = _mbps_precarga()
    horas = lambda gb, mbps: gb * 8 * 1000 / mbps / 3600          # GB decimales → Gb → Mb / Mbps → s → h
    wan_lab = horas(gb_lab, mbps_wan)
    lan_lab = horas(gb_lab, gbps_lan * 1000)
    wan_pre = horas(gb_pc, mbps_pre)
    # Guía CE01 v0.4 B4.3: 3 GB por el enlace (a S-42) + el resto por la LAN, todo de día, sin precarga.
    guia_tobe = horas(gb_pc, mbps_wan) + horas(gb_lab - gb_pc, gbps_lan * 1000)
    p_int = s("S-44.p_interrupcion")
    return {
        "pcs": pcs, "gb_pc": gb_pc, "gb_lab": gb_lab, "mbps_wan": mbps_wan, "gbps_lan": gbps_lan, "mbps_precarga": mbps_pre,
        "wan_lab": wan_lab, "lan_lab": lan_lab, "wan_precarga": wan_pre, "guia_tobe": guia_tobe,
        # La probabilidad de que una clase interrumpa la entrega crece con lo que dura: se escala con la duración [S-44].
        "p_interrupcion": p_int, "p_interrupcion_tobe": p_int * lan_lab / wan_lab,
        "ciclos_p1_anio": s("S-06.ciclos_anio") * s("S-26.laboratorios"),
        "pedidos_p2_anio": s("S-45.pedidos_semana") * s("S-45.semanas_anio") * s("S-26.laboratorios"),
        "tarifa": s("S-07.tarifa_usd_h"),
        "horas_pc_ciclo_e2": s("S-07.horas_pc_ciclo"),
    }


def _p(ref, k: dict) -> float:
    if isinstance(ref, (int, float)):
        return float(ref)
    if ref in k:
        return float(k[ref])
    if isinstance(ref, str) and ref.startswith("S-"):
        return float(s(ref))
    raise PlanError(f"Probabilidad o factor desconocido: {ref}")


# ==================================================================================================
# Grafo y simulación
# ==================================================================================================
def grafo(pid: str, d: dict | None = None) -> dict:
    d = d or sim()
    p = d["procesos"][pid]
    nodos = {n["id"]: n for n in p["nodos"]}
    flujos = []
    for f in p["flujos"]:
        f = {"de": f[0], "a": f[1]} if isinstance(f, list) else dict(f)
        for x in (f["de"], f["a"]):
            if x not in nodos:
                raise PlanError(f"{pid}: el flujo {f['de']} → {f['a']} nombra un nodo inexistente «{x}»")
        flujos.append(f)
    salidas = {n: [f for f in flujos if f["de"] == n] for n in nodos}
    for nid, n in nodos.items():
        if n["tipo"] in ("tarea", "tarea_usuario", "tarea_servicio", "temporizador") and "tri" not in n and "calculo" not in n:
            raise PlanError(f"{pid}: «{nid}» no tiene duración (tri o calculo)")
        if n["tipo"] != "fin" and not salidas[nid]:
            raise PlanError(f"{pid}: «{nid}» no tiene flujo de salida")
        if n["tipo"] == "xor" and len(salidas[nid]) < 2:
            raise PlanError(f"{pid}: la compuerta «{nid}» necesita al menos dos salidas")
    inicio = [n for n in nodos.values() if n["tipo"].startswith("inicio")]
    if len(inicio) != 1:
        raise PlanError(f"{pid}: necesita exactamente un evento de inicio")
    return {"id": pid, "proc": p, "nodos": nodos, "flujos": flujos, "salidas": salidas, "inicio": inicio[0]["id"]}


def _probs(g: dict, nid: str, k: dict) -> list[float]:
    fs = g["salidas"][nid]
    ps = [None if f.get("p") == "complemento" else _p(f["p"], k) for f in fs]
    if ps.count(None) > 1:
        raise PlanError(f"{g['id']}: la compuerta «{nid}» tiene más de una salida «complemento»")
    resto = 1 - sum(x for x in ps if x is not None)
    ps = [resto if x is None else x for x in ps]
    if abs(sum(ps) - 1) > 1e-9 or min(ps) < 0:
        raise PlanError(f"{g['id']}: las probabilidades de «{nid}» no suman 1 ({ps})")
    return ps


def _duracion(n: dict, k: dict, rng) -> float:
    if "calculo" in n:
        base = k[n["calculo"]]
        return base * (_p(n["factor"], k) if "factor" in n else 1.0)
    a, m, b = n["tri"]
    x = a if a == b else rng.triangular(a, m, b)
    return x * (k["pcs"] if n.get("por_pc") else 1)


def simular(pid: str, n_iter: int | None = None, semilla: int | None = None, k: dict | None = None) -> dict:
    """Arreglos por iteración de cada medida (MEDIDAS)."""
    d = sim()
    g = grafo(pid, d)
    k = k or calculos()
    n_iter = n_iter or d["meta"]["iteraciones"]
    rng = np.random.default_rng(d["meta"]["semilla"] if semilla is None else semilla)
    con_costo = set(d["meta"]["recursos_con_costo"])
    out = {m: np.zeros(n_iter) for m in MEDIDAS}
    out["habilitar_h"][:] = np.nan
    out["listo"][:] = np.nan
    probs = {nid: _probs(g, nid, k) for nid, n in g["nodos"].items() if n["tipo"] == "xor"}
    for i in range(n_iter):
        t = occ = desc = wan = 0.0
        hab = None
        listo_t = margen = None
        trabajo = {"tecnico": 0.0, "encargado": 0.0, "docente": 0.0}
        inter = 0
        nid, pasos = g["inicio"], 0
        while True:
            pasos += 1
            if pasos > 200:
                raise PlanError(f"{pid}: el recorrido no termina (¿ciclo sin salida?)")
            n = g["nodos"][nid]
            if n["tipo"] in ("tarea", "tarea_usuario", "tarea_servicio", "temporizador"):
                dur = _duracion(n, k, rng)
                t += dur
                if n.get("recurso"):
                    trabajo[n["recurso"]] += dur
                if n.get("ocupa_lab"):
                    occ += dur
                if n.get("calculo") in ("wan_lab", "lan_lab"):
                    desc += dur
                if n.get("wan"):
                    wan += (k["gb_lab"] if n["calculo"] == "wan_lab" else k["gb_pc"]) * (_p(n["factor"], k) if "factor" in n else 1)
                if n.get("habilitar"):
                    hab = (hab or 0.0) + dur
                if n.get("listo"):
                    listo_t = t
            if n["tipo"] == "fin":
                break
            fs = g["salidas"][nid]
            f = fs[0] if len(fs) == 1 else fs[rng.choice(len(fs), p=probs[nid])]
            if "interrupcion" in str(f.get("p", "")):
                inter += 1
            if f.get("margen") == "anticipacion":
                margen = s("S-44.anticipacion_h")
            elif f.get("margen") == "mismo_dia":
                margen = rng.triangular(s("S-44.margen_min_h"), s("S-44.margen_moda_h"), s("S-44.margen_max_h"))
            nid = f["a"]
        out["ciclo_h"][i] = t
        out["ocupacion_h"][i] = occ
        out["descarga_h"][i] = desc
        out["wan_gb"][i] = wan
        out["interrupciones"][i] = inter
        for r in trabajo:
            out[f"horas_{r}"][i] = trabajo[r]
        out["horas_personal"][i] = sum(trabajo[r] for r in con_costo)
        out["costo"][i] = out["horas_personal"][i] * k["tarifa"]
        if hab is not None:
            out["habilitar_h"][i] = hab
        if listo_t is not None and margen is not None:
            out["listo"][i] = 1.0 if listo_t <= margen else 0.0
    return out


def resumir(x: np.ndarray) -> dict:
    x = x[~np.isnan(x)]
    if not len(x):
        return {"media": None, "p10": None, "p50": None, "p90": None, "n": 0}
    return {"media": float(x.mean()), "p10": float(np.percentile(x, 10)), "p50": float(np.percentile(x, 50)),
            "p90": float(np.percentile(x, 90)), "n": int(len(x))}


# ==================================================================================================
# Coherencia de la caracterización con los diagramas, el SRS y las pruebas
# ==================================================================================================
def _req_srs() -> dict[str, str]:
    """{REQ-F-xx: fila completa de la tabla del SRS}."""
    filas = {}
    for linea in SRS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(REQ-F-\d+)\s*\|", linea)
        if m and m.group(1) not in filas:
            filas[m.group(1)] = linea
    return filas


def _ishikawa() -> set[str]:
    e1 = yaml.safe_load((RAIZ / "gestion" / "e1" / "datos" / "diagnostico.yaml").read_text(encoding="utf-8"))
    return {(c["nombre"], causa) for c in e1["ishikawa"]["categorias"] for causa in c["causas"]}


def verificar(car: dict, d: dict) -> list[str]:
    err = []
    nodos = {pid: {n["id"]: n for n in p["nodos"]} for pid, p in d["procesos"].items()}
    pds = {p["id"]: p for p in car["problemas"]}
    for pid, ns in nodos.items():
        for n in ns.values():
            if n.get("pd") and n["pd"] not in pds:
                err.append(f"{pid}.{n['id']}: {n['pd']} no está en la tabla de problemas")
    ish = _ishikawa()
    for p in car["problemas"]:
        n = nodos.get(p["diagrama"], {}).get(p["nodo"])
        if not n or n.get("pd") != p["id"]:
            err.append(f"{p['id']}: no aparece en el diagrama {p['diagrama']} sobre el nodo {p['nodo']}")
        if (p["categoria"], p["causa"]) not in ish:
            err.append(f"{p['id']}: la causa «{p['causa']}» ({p['categoria']}) no está en el Ishikawa del E1")
    srs = _req_srs()
    ts = {t["id"] for t in yaml.safe_load(PRUEBAS.read_text(encoding="utf-8"))["pruebas"]}
    usados = set()
    for a in car["automatizaciones"]:
        if not a["req"] or not a["prueba"]:
            err.append(f"{a['id']}: toda automatización necesita REQ-F y prueba")
        for r in a["req"]:
            if r not in srs:
                err.append(f"{a['id']}: {r} no existe en el SRS")
        for t in a["prueba"]:
            ok = t in ts if re.fullmatch(r"T\d{2}", t) else any(t in srs[r] for r in a["req"] if r in srs)
            if not ok:
                err.append(f"{a['id']}: la prueba {t} no existe en infra/pruebas.yaml ni en la fila del SRS de {', '.join(a['req'])}")
        usados |= set(a["pd"])
    for pid in pds:
        if pid not in usados:
            err.append(f"{pid}: ninguna automatización lo elimina")
    for pid, ns in nodos.items():
        for n in ns.values():
            for r in n.get("req", []):
                if r not in srs:
                    err.append(f"{pid}.{n['id']}: {r} no existe en el SRS")
    cand = car["seleccion"]
    if abs(sum(c["peso"] for c in cand["criterios"]) - 1) > 1e-9:
        err.append("seleccion: los pesos no suman 1")
    return err


def seleccion(car: dict) -> list[dict]:
    pesos = [c["peso"] for c in car["seleccion"]["criterios"]]
    filas = [{**c, "total": sum(p * x for p, x in zip(pesos, c["puntajes"]))} for c in car["seleccion"]["candidatos"]]
    filas.sort(key=lambda r: -r["total"])
    top = {r["id"] for r in filas[:len(car["seleccion"]["seleccionados"])]}
    if top != set(car["seleccion"]["seleccionados"]):
        raise PlanError(f"La matriz de selección no da {car['seleccion']['seleccionados']} como los de mayor puntaje ({sorted(top)})")
    return filas


# ==================================================================================================
# Modelo completo
# ==================================================================================================
def _mejora(a, b):
    return None if a in (None, 0) or b is None else (a - b) / a


def calcular(n_iter: int | None = None) -> dict:
    d, car, k = sim(), caracterizacion(), calculos()
    err = verificar(car, d)
    if err:
        raise PlanError("; ".join(err))
    sims = {pid: simular(pid, n_iter, k=k) for pid in d["procesos"]}
    res = {pid: {m: resumir(v) for m, v in x.items()} for pid, x in sims.items()}
    anual = {"P1": k["ciclos_p1_anio"], "P2": k["pedidos_p2_anio"]}
    comp = {}
    for proc in ("P1", "P2"):
        a, b = res[f"{proc}-AS-IS"], res[f"{proc}-TO-BE"]
        comp[proc] = {m: {"asis": a[m]["media"], "tobe": b[m]["media"], "mejora": _mejora(a[m]["media"], b[m]["media"])}
                      for m in MEDIDAS}
        for m in ("costo", "horas_personal", "wan_gb"):
            comp[proc][f"{m}_anio"] = {x: (comp[proc][m][x] * anual[proc] if comp[proc][m][x] is not None else None)
                                       for x in ("asis", "tobe")}
    # KPI-1 sin simulación: descarga del laboratorio de día (AS-IS por el enlace; TO-BE solo por la LAN, la WAN va de noche).
    kpi1 = {"asis": k["wan_lab"], "tobe": k["lan_lab"], "mejora": _mejora(k["wan_lab"], k["lan_lab"]), "guia_tobe": k["guia_tobe"]}
    ahorro_pc = (comp["P1"]["horas_personal"]["asis"] - comp["P1"]["horas_personal"]["tobe"]) / k["pcs"]
    m = {"calculos": k, "resultados": res, "comparativo": comp, "kpi1": kpi1, "anual": anual,
         "seleccion": seleccion(car), "ahorro_h_pc_ciclo": ahorro_pc,
         "ahorro_h_p2_anio": (comp["P2"]["horas_personal"]["asis"] - comp["P2"]["horas_personal"]["tobe"]) * anual["P2"],
         "iteraciones": n_iter or d["meta"]["iteraciones"], "semilla": d["meta"]["semilla"], "avisos": []}
    # Metas de infra/trazabilidad.yaml → objetivos_proyecto (no se copian): OB-2 «−70 %» y OB-3 «≤ 5 min».
    ob = metas()
    m["metas"] = ob
    m["kpi1"]["cumple_ob2"] = kpi1["mejora"] >= ob["OB-2"]
    for pid in ("P2-AS-IS", "P2-TO-BE"):
        h = sims[pid]["habilitar_h"]
        h = h[~np.isnan(h)]
        m.setdefault("habilitar_en_meta", {})[pid] = float((h <= ob["OB-3"] / 60).mean())
    m["avisos"] += comparar_bizagi(res)
    return m


def metas() -> dict:
    """OB-2 como fracción de reducción y OB-3 en minutos, leídas del texto de la meta en infra/trazabilidad.yaml."""
    ob = {o["id"]: o["meta"] for o in cd.objetivos()}
    m2 = re.search(r"[−-]\s*(\d+)\s*%", ob["OB-2"])
    m3 = re.search(r"≤\s*(\d+)\s*min", ob["OB-3"])
    if not m2 or not m3:
        raise PlanError(f"No se pudo leer la meta de OB-2 («{ob['OB-2']}») u OB-3 («{ob['OB-3']}»)")
    return {"OB-2": int(m2.group(1)) / 100, "OB-3": float(m3.group(1)), "OB-2_texto": ob["OB-2"], "OB-3_texto": ob["OB-3"]}


def comparar_bizagi(res: dict) -> list[str]:
    """Resultados de Bizagi transcritos a mano (README, paso 9): {diagrama: {ciclo_h, costo}}; avisa si difieren > 10 %."""
    if not BIZAGI.exists():
        return []
    biz = yaml.safe_load(BIZAGI.read_text(encoding="utf-8")) or {}
    avisos = []
    for pid, vals in biz.items():
        for med, v in (vals or {}).items():
            py = res.get(pid, {}).get(med, {}).get("media")
            if py and v is not None and abs(v - py) / py > TOLERANCIA_BIZAGI:
                avisos.append(f"Bizagi difiere > 10 % en {pid}.{med}: Bizagi {v:g} frente a Python {py:.3g}; revise los parámetros")
    return avisos


# ==================================================================================================
# Salidas
# ==================================================================================================
def _h(x: float | None) -> str:
    """Duración legible: minutos si es menos de una hora; horas con una decimal si no."""
    if x is None:
        return "—"
    return f"{num(x * 60)} min" if x < 1 else f"{num(x, 1)} h"


def _pct_mejora(x: float | None) -> str:
    return "—" if x is None else ("−" if x > 0 else "+") + pct(abs(x))


def datos(m: dict) -> dict[str, str]:
    k, c, r = m["calculos"], m["comparativo"], m["resultados"]
    d = {
        "e4_pcs": f"{num(k['pcs'])} PCs",
        "e4_gb_pc": f"{num(k['gb_pc'])} GB",
        "e4_gb_lab": f"{num(k['gb_lab'])} GB",
        "e4_mbps_wan": f"{num(k['mbps_wan'])} Mbps",
        "e4_mbps_precarga": f"{num(k['mbps_precarga'])} Mbps",
        "e4_lan": f"{num(k['gbps_lan'])} Gbps",
        "e4_wan_lab": _h(k["wan_lab"]),
        "e4_lan_lab": _h(k["lan_lab"]),
        "e4_wan_precarga": _h(k["wan_precarga"]),
        "e4_guia_tobe": _h(k["guia_tobe"]),
        "e4_kpi1_mejora": _pct_mejora(m["kpi1"]["mejora"]),
        "e4_p_int": pct(k["p_interrupcion"]),
        "e4_p_int_tobe": pct(k["p_interrupcion_tobe"], 1),
        "e4_ciclos_p1": f"{num(k['ciclos_p1_anio'])} ciclos",
        "e4_pedidos_p2": f"{num(k['pedidos_p2_anio'])} pedidos",
        "e4_tarifa": usd(k["tarifa"]) + "/h",
        "e4_iteraciones": num(m["iteraciones"]),
        "e4_semilla": str(m["semilla"]),
        "e4_ahorro_h_pc": f"{num(m['ahorro_h_pc_ciclo'], 2)} h",
        "e4_horas_pc_e2": f"{num(k['horas_pc_ciclo_e2'], 2)} h",
        "e4_ahorro_h_p2_anio": f"{num(m['ahorro_h_p2_anio'])} h",
        "e4_ahorro_usd_p2_anio": usd(m["ahorro_h_p2_anio"] * k["tarifa"]),
        "e4_bn2_e4": usd(s("S-01.pcs") * s("S-06.ciclos_anio") * m["ahorro_h_pc_ciclo"] * k["tarifa"]),
        "e4_bn2_e2": usd(s("S-01.pcs") * s("S-06.ciclos_anio") * k["horas_pc_ciclo_e2"] * k["tarifa"]),
        "e4_n_pd": str(len(caracterizacion()["problemas"])),
        "e4_n_au": str(len(caracterizacion()["automatizaciones"])),
        "e4_obs_min": str(caracterizacion()["cronometraje"]["observaciones_min"]),
        "e4_meta_listo": pct(next(i for i in caracterizacion()["indicadores"] if i["id"] == "KPI-4")["meta_pct"]),
    }
    for proc in ("P1", "P2"):
        p = proc.lower()
        for med in ("ciclo_h", "ocupacion_h", "horas_personal", "habilitar_h"):
            d[f"e4_{p}_{med}_asis"] = _h(c[proc][med]["asis"])
            d[f"e4_{p}_{med}_tobe"] = _h(c[proc][med]["tobe"])
            d[f"e4_{p}_{med}_mejora"] = _pct_mejora(c[proc][med]["mejora"])
        d[f"e4_{p}_costo_asis"] = usd(c[proc]["costo"]["asis"], 2)
        d[f"e4_{p}_costo_tobe"] = usd(c[proc]["costo"]["tobe"], 2)
        d[f"e4_{p}_costo_mejora"] = _pct_mejora(c[proc]["costo"]["mejora"])
        d[f"e4_{p}_costo_anio_asis"] = usd(c[proc]["costo_anio"]["asis"])
        d[f"e4_{p}_costo_anio_tobe"] = usd(c[proc]["costo_anio"]["tobe"])
        d[f"e4_{p}_wan_asis"] = f"{num(c[proc]['wan_gb']['asis'])} GB"
        d[f"e4_{p}_wan_tobe"] = f"{num(c[proc]['wan_gb']['tobe'])} GB"
        d[f"e4_{p}_wan_mejora"] = _pct_mejora(c[proc]["wan_gb"]["mejora"])
        d[f"e4_{p}_wan_anio_asis"] = f"{num(c[proc]['wan_gb_anio']['asis'])} GB"
        d[f"e4_{p}_wan_anio_tobe"] = f"{num(c[proc]['wan_gb_anio']['tobe'])} GB"
    d["e4_p1_inter_asis"] = num(c["P1"]["interrupciones"]["asis"], 2)
    d["e4_p1_inter_tobe"] = num(c["P1"]["interrupciones"]["tobe"], 2)
    d["e4_p2_listo_asis"] = pct(c["P2"]["listo"]["asis"])
    d["e4_p2_listo_tobe"] = pct(c["P2"]["listo"]["tobe"])
    d["e4_p2_habilitar_p90_asis"] = _h(r["P2-AS-IS"]["habilitar_h"]["p90"])
    d["e4_p2_habilitar_p90_tobe"] = _h(r["P2-TO-BE"]["habilitar_h"]["p90"])
    d["e4_p2_habilitar_p50_tobe"] = _h(r["P2-TO-BE"]["habilitar_h"]["p50"])
    total_asis = c["P1"]["costo_anio"]["asis"] + c["P2"]["costo_anio"]["asis"]
    total_tobe = c["P1"]["costo_anio"]["tobe"] + c["P2"]["costo_anio"]["tobe"]
    d["e4_costo_anio_asis"] = usd(total_asis)
    d["e4_costo_anio_tobe"] = usd(total_tobe)
    d["e4_costo_anio_ahorro"] = usd(total_asis - total_tobe)
    d["e4_costo_anio_mejora"] = _pct_mejora(_mejora(total_asis, total_tobe))
    d["e4_meta_ob2"] = m["metas"]["OB-2_texto"]
    d["e4_meta_ob3"] = m["metas"]["OB-3_texto"]
    d["e4_hab_meta_asis"] = pct(m["habilitar_en_meta"]["P2-AS-IS"])
    d["e4_hab_meta_tobe"] = pct(m["habilitar_en_meta"]["P2-TO-BE"])
    sel = m["seleccion"]
    d["e4_sel_p1"] = num(next(x for x in sel if x["id"] == "P1")["total"], 2)
    d["e4_sel_p2"] = num(next(x for x in sel if x["id"] == "P2")["total"], 2)
    d["e4_sel_tercero"] = num(sel[2]["total"], 2)
    return d


def escribir_json(m: dict) -> None:
    DATOS.mkdir(parents=True, exist_ok=True)
    (DATOS / "e4.json").write_text(json.dumps({"datos": datos(m), "modelo": m}, ensure_ascii=False, indent=1, default=float),
                                   encoding="utf-8")
    k = m["calculos"]
    (DATOS / "resultados.json").write_text(json.dumps({
        "estado": "estimado por simulación (S-43, S-44); reemplaza a S-07 en el E2 solo cuando se mida con ≥ 30 observaciones",
        "fuente": "gestion/e4/procesos.py sobre gestion/e4/simulacion.yaml",
        "horas_pc_ciclo_ahorradas": round(m["ahorro_h_pc_ciclo"], 4),
        "horas_pc_ciclo_e2_supuesto": k["horas_pc_ciclo_e2"],
        "horas_anio_ahorradas_p2": round(m["ahorro_h_p2_anio"], 1),
        "ciclos_p1_anio": k["ciclos_p1_anio"], "pedidos_p2_anio": k["pedidos_p2_anio"],
    }, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-render", action="store_true", help="no renderiza los BPMN a PNG (bpmn-js)")
    ap.add_argument("--sin-xlsx", action="store_true", help="no escribe la plantilla de cronometraje")
    a = ap.parse_args(argv)
    try:
        m = calcular()
        for av in m["avisos"]:
            print(f"  AVISO {av}")
        escribir_json(m)
        sys.path.insert(0, str(AQUI))
        import bpmn
        for ruta in bpmn.escribir_todo(sim(), caracterizacion()):
            print(f"CE01 E4: {ruta.relative_to(RAIZ).as_posix()} válido contra el XSD BPMN 2.0")
        if not a.sin_xlsx:
            import instrumentos
            print(f"CE01 E4: {instrumentos.escribir(caracterizacion()).relative_to(RAIZ).as_posix()}")
        c = m["comparativo"]
        print(f"CE01 E4: descarga {_h(m['kpi1']['asis'])} → {_h(m['kpi1']['tobe'])} ({_pct_mejora(m['kpi1']['mejora'])}); "
              f"costo P1 {usd(c['P1']['costo']['asis'], 2)} → {usd(c['P1']['costo']['tobe'], 2)}; "
              f"P2 listas {pct(c['P2']['listo']['asis'])} → {pct(c['P2']['listo']['tobe'])}")
    except (PlanError, cd.DatosCE01Error) as e:
        print(f"ERROR {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
