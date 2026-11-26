"""Tablas generadas del Entregable 3 de CE01 ({{tabla:id}} en gestion/e3/informe/*.md).

Leen gestion/e3/datos/plan.json (gestion/e3/plan.py), gestion/e3/datos/{agil,gobierno}.yaml, gestion/ce01.yaml y la
SMART del E2 a través de gestion/ce01_datos.py: ninguna cifra se escribe a mano.
TABLAS = {id: {"titulo", "fuente", "filas": función → [[cabecera], [fila], …]}}.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI))
import ce01_datos as cd  # noqa: E402
from ce01_datos import num, pct, usd  # noqa: E402

PROPIA = "Elaboración propia"
G = yaml.safe_load((AQUI / "datos" / "gobierno.yaml").read_text(encoding="utf-8"))
A = yaml.safe_load((AQUI / "datos" / "agil.yaml").read_text(encoding="utf-8"))
BC = yaml.safe_load((AQUI.parent / "e2" / "datos" / "business_case.yaml").read_text(encoding="utf-8"))
_PLAN = AQUI / "datos" / "plan.json"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def M() -> dict:
    if not _PLAN.exists():
        raise cd.DatosCE01Error("Falta gestion/e3/datos/plan.json: ejecute python gestion/e3/plan.py")
    return json.loads(_PLAN.read_text(encoding="utf-8"))["modelo"]


def _f(iso: str | None) -> str:
    if not iso:
        return "—"
    a, m, d = iso.split("-")
    return f"{int(d)} {MESES[int(m) - 1]} {a}"


def _edt() -> dict:
    return {p["id"]: p for p in cd.cargar()["edt"]["paquetes"]}


# ------------------------------------------------------------------------------------------------ 3.1
def acta():
    a, m = G["acta"], M()
    p = m["presupuesto"]
    return [["Campo", "Contenido"],
            ["Proyecto", a["proyecto"]],
            ["Sponsor", a["sponsor"]],
            ["Director del proyecto", a["director"]],
            ["Líder técnico", a["lider_tecnico"]],
            ["Propósito", a["proposito"]],
            ["Enfoque de gestión", a["enfoque"]],
            ["Duración", f"{_f(m['inicio'])} → {_f(m['fin'])} ({num(m['dias_laborables'])} días laborables)"],
            ["Presupuesto del proyecto", f"Línea base {usd(p['linea_base'])} (incluye contingencia de {usd(p['contingencia'])}); "
                                         f"reserva de gestión {usd(p['gestion'])} fuera de la línea base"],
            ["Hitos", "; ".join(f"{k} {v['nombre']} ({_f(v['fecha'])})" for k, v in m["hitos"].items())]]


def smart():
    pl = BC["smart"]["plazos"]
    return [["ID", "Específico", "Medible (indicador)", "Meta", "Plazo"]] + [
        [o["id"], o["necesidad"], o["indicador"], o["meta"], pl[o["id"]]["plazo"]] for o in cd.objetivos()]


def exito():
    return [["ID", "Criterio", "Medida de éxito"]] + [[c["id"], c["criterio"], c["medida"]] for c in G["acta"]["criterios_exito"]]


def restricciones():
    filas = [["ID", "Restricción o supuesto", "Fuente"]]
    d = json.loads(_PLAN.read_text(encoding="utf-8"))["datos"]
    for r in G["acta"]["restricciones"]:
        texto = r["texto"]
        if r["id"] == "R-2":
            texto += (f": sustentación de S1 el {d['e3_fin_s1']}, receso {d['e3_receso']}, inicio de S2 el {d['e3_inicio_s2']} "
                      f"y {d['e3_semanas_s2']} de S2 (valores del calendario del plan, por confirmar)")
        filas.append([r["id"], texto, r["fuente"]])
    for sid in G["acta"]["supuestos"]:
        t = cd.texto_supuesto(sid)
        filas.append([sid, f"{t.get('supuesto', t.get('tema', ''))}: {t['valor']}".strip(": "), "infra/trazabilidad.yaml"])
    return filas


def firmas():
    return [["Rol", "Nombre", "Firma", "Fecha"]] + [[f["rol"], f["nombre"], " ", " "] for f in G["acta"]["firmas"]]


# ------------------------------------------------------------------------------------------------ 3.2
def diccionario():
    m, e = M(), _edt()
    filas_act = {f["id"]: f for f in m["filas"]}
    pred_paq = {}
    for f in m["filas"]:
        if f["hito"] or not f["paquete"]:
            continue
        for p in f["preds"]:
            pid = p.split(" ")[0]
            q = filas_act.get(pid, {}).get("paquete")
            if q and q != f["paquete"]:
                pred_paq.setdefault(f["paquete"], set()).add(q)
    out = [["Código", "Paquete", "Descripción", "Criterio de aceptación", "Resp.", "Horas", "Costo", "Predecesoras"]]
    for pid, p in m["presupuesto"]["paquetes"].items():
        d = e[pid]
        pr = sorted(pred_paq.get(pid, set()), key=lambda x: [int(i) for i in x.split(".")])
        out.append([pid, d["nombre"], d["descripcion"], d["aceptacion"], d["responsable"], num(p["horas"]), usd(p["total"]),
                    ", ".join(pr) or "—"])
    return out


def raci():
    r = cd.cargar()["raci"]
    return [["Paquete"] + r["roles"]] + [[f["paquete"]] + f["asignacion"] for f in r["filas"]]


def cambios_nivel():
    return [["Tipo de cambio", "Aprueba"]] + [[n["cambio"], n["aprueba"]] for n in G["cambios"]["nivel"]]


# ------------------------------------------------------------------------------------------------ 3.3
def actividades():
    m = M()
    out = [["ID", "Actividad", "Días", "Inicio", "Fin", "Predecesoras", "Holgura", "Estado"]]
    for f in m["filas"]:
        if f["hito"]:
            continue
        estado = f"100 % ({f['commit']})" if f["hecha"] else ("Crítica" if f["critica"] else "Pendiente")
        out.append([f["id"], f["nombre"], num(f["dur"]), _f(f["inicio"]), _f(f["fin"]), ", ".join(f["preds"]) or "—",
                    "—" if f["holgura"] is None else num(f["holgura"]), estado])
    return out


def hitos():
    m = M()
    cond = {"H0": "Primer commit del repositorio", "H1": "Expediente de S1 consolidado y ensayado (6.1.1)",
            "HS2": "Inicio del semestre 2027-I; restricción «no comenzar antes del» en MS Project [confirmar con el calendario académico]",
            "H2": "Conformidad de la DTI y requerimientos del FortiGate atendidos [S-29]",
            "H3": "BHR del piloto frente a la meta de OB-1 (punto de decisión del E1)",
            "H4": "Ampliación terminada, expediente final y lecciones aprendidas"}
    return [["Hito", "Nombre", "Línea base", "Pronóstico", "Condición de cumplimiento"]] + [
        [k, v["nombre"], _f(v["lb"]), _f(v["fecha"]), cond[k]] for k, v in m["hitos"].items()]


def recursos():
    m = M()
    p = m["presupuesto"]
    from plan import plan as _plan
    out = [["Recurso", "Tipo", "Horas", "Tarifa", "Costo"]]
    for r in _plan()["recursos"]:
        h = p["horas_recurso"].get(r["id"], 0)
        eq = r["tipo"] == "equipo"
        out.append([r["nombre"], "Equipo (valorizado)" if eq else "Contraparte (aporte institucional)", num(h),
                    f"{usd(p['tarifa'])}/h" if eq else "—", usd(h * p["tarifa"]) if eq else "—"])
    return out


def msproject():
    m = M()
    r = m.get("msproject") or {}
    rc = [f["id"] for f in m["filas"] if f["critica"]]
    return [["Comprobación", "Python (CPM)", "Microsoft Project"],
            ["Tareas críticas", num(len(rc)), num(len(r.get("criticas", []))) if r.get("ok") else "pendiente (paso manual)"],
            ["Ruta crítica", " → ".join(rc), "igual" if r.get("ok") else "pendiente (paso manual)"],
            ["Costo total de las tareas", usd(m["presupuesto"]["bac"], 2),
             usd(r["proyecto"]["costo"], 2) if r.get("ok") else "pendiente (paso manual)"],
            ["Fin del proyecto", _f(m["fin"]), (_f(r["proyecto"]["fin"][:10]) if r.get("ok") else "pendiente (paso manual)")]]


# ------------------------------------------------------------------------------------------------ 3.4
def presupuesto():
    m = M()
    p = m["presupuesto"]
    out = [["Paquete", "Nombre", "Horas", "Horas × tarifa", "Hardware y AWS", "Total", "% del BAC"]]
    for pid, x in p["paquetes"].items():
        out.append([pid, x["nombre"], num(x["horas"]), usd(x["costo_horas"]), usd(x["costo_fijo"]) if x["costo_fijo"] else "—",
                    usd(x["total"]), pct(x["total"] / p["bac"], 1)])
    out.append(["", "Herramientas (licencias libres o educativas)", "—", "—", "—", usd(p["herramientas"]), pct(0)])
    out.append(["", "Total (BAC)", num(sum(x["horas"] for x in p["paquetes"].values())),
                usd(sum(x["costo_horas"] for x in p["paquetes"].values())),
                usd(sum(x["costo_fijo"] for x in p["paquetes"].values())), usd(p["bac"]), pct(1)])
    return out


def nivel1():
    m = M()
    p = m["presupuesto"]
    return [["Área (nivel 1)", "Horas", "Costo", "% del BAC"]] + [
        [f"{k} {v['nombre']}", num(v["horas"]), usd(v["total"]), pct(v["total"] / p["bac"], 1)] for k, v in p["nivel1"].items()]


def linea_base():
    m = M()
    p = m["presupuesto"]
    from plan import plan as _plan
    c = _plan()["costos"]
    return [["Concepto", "Cálculo", "Monto"],
            ["Presupuesto de las actividades (BAC)", "Σ paquetes de la EDT + herramientas", usd(p["bac"], 2)],
            ["Reserva de contingencia", f"{pct(c['contingencia'])} del BAC (riesgos identificados)", usd(p["contingencia"], 2)],
            ["Línea base de costos", "BAC + contingencia", usd(p["linea_base"], 2)],
            ["Reserva de gestión", f"{pct(c['gestion'])} de la línea base (riesgos no identificados)", usd(p["gestion"], 2)],
            ["Presupuesto total autorizado", "Línea base + reserva de gestión", usd(p["total_autorizado"], 2)]]


def proyecto_vs_e2():
    m = M()
    p = m["presupuesto"]
    c = cd.costos()
    return [["Aspecto", "Línea base del proyecto (E3)", "Inversión del business case (E2)"],
            ["Qué mide", "Lo que cuesta ejecutar el proyecto hasta el cierre", "Lo que cuesta y rinde el servicio en su horizonte"],
            ["Horizonte", f"{_f(m['inicio'])} → {_f(m['fin'])}", f"{cd.cargar()['economia']['horizonte_anios']} años de operación"],
            ["Componentes", "Horas del equipo, hardware del piloto, AWS durante el piloto, herramientas y contingencia",
             "Inversión inicial (CX-1…CX-4) y costo operativo anual (OX-1…OX-3)"],
            ["Monto", f"{usd(p['linea_base'])} (+ reserva de gestión {usd(p['gestion'])})",
             f"I₀ {usd(c['capex_total'])}; OPEX {usd(c['opex_total'])} por año"],
            ["Partida común", f"Hardware del rack: {usd(p['costos_fijos']['capex'])}", f"CAPEX: {usd(c['capex_total'])}"],
            ["Uso", "Control del proyecto (EVM)", "Decisión de invertir (VAN, TIR, payback)"]]


def costos_fijos():
    m = M()
    cf = m["presupuesto"]["costos_fijos"]
    from plan import plan as _plan
    aws = _plan()["costos"]["aws"]
    return [["Costo fijo", "Actividad", "Cálculo", "Monto"],
            ["Hardware del rack", "5.1.2", "CAPEX del E2 (S-08, S-37, S-38, S-39)", usd(cf["capex"], 2)],
            ["AWS efímero (Modo A) y simulacro", "5.5.2",
             f"{num(aws['horas_efimero'])} h × {usd(cf['_usd_h_efimero'], 4)}/h + {num(cf['_horas_simulacro'])} h × "
             f"{usd(cf['_usd_h_simulacro'], 4)}/h [S-12]", usd(cf["aws_efimero"], 2)],
            ["AWS 24×7 (EC2-GW, VPN y S3)", "5.5.3", f"{num(aws['meses_24x7'])} meses × {usd(cd.aws_mensual(), 2)}/mes (C1–C7) [S-12]",
             usd(cf["aws_24x7"], 2)]]


def evm():
    m = M()
    e = m["evm"]
    out = [["Corte", "PV", "EV", "AC", "SPI", "CPI", "SV", "Estado"]]
    for c in e["cortes"]:
        spi = "—" if c["spi"] is None else num(c["spi"], 2)
        cpi = "no medido" if c["ac"] == c["ev"] and c["ev"] else ("—" if c["cpi"] is None else num(c["cpi"], 2))
        alerta = (c["spi"] is not None and c["spi"] < e["umbral"])
        out.append([_f(c["fecha"]), usd(c["pv"]), usd(c["ev"]), usd(c["ac"]), spi, cpi, usd(c["sv"]),
                    "ALERTA (SPI < umbral)" if alerta else "En control"])
    return out


def umbrales():
    return [["Condición", "Estado", "Acción"]] + [[u["condicion"], u["estado"], u["accion"]] for u in G["control"]["umbrales"]]


# ------------------------------------------------------------------------------------------------ 3.5
def _rp():
    return cd.cargar()["riesgos_proyecto"]["lista"]


def riesgos_analisis():
    out = [["ID", "Causa", "Evento (riesgo)", "Efecto", "P", "I", "P × I", "Nivel", "Prioridad"]]
    orden = sorted(_rp(), key=lambda r: (-r["p"] * r["i"], -r["i"], r["id"]))
    prio = {r["id"]: k for k, r in enumerate(orden, start=1)}
    for r in _rp():
        sev = r["p"] * r["i"]
        out.append([r["id"], r["causa"], r["riesgo"], r["efecto"], str(r["p"]), str(r["i"]), str(sev), _nivel(sev), str(prio[r["id"]])])
    return out


def _nivel(sev: int) -> str:
    import estilo_ce01 as est
    return est.nivel_riesgo(sev)[1]


def riesgos_respuesta():
    dueno = {"Ambos": "Ambos", "Nick": "Nick", "Henyelrey": "Henyelrey"}
    return [["ID", "Estrategia", "Respuesta preventiva", "Plan de contingencia", "Disparador", "Dueño", "Estado"]] + [
        [r["id"], r["estrategia"], r["respuesta"], r["contingencia"], r["disparador"], dueno.get(r["dueno"], r["dueno"]), r["estado"]]
        for r in sorted(_rp(), key=lambda r: (-r["p"] * r["i"], r["id"]))]


# ------------------------------------------------------------------------------------------------ interesados
def compromiso():
    niveles = ["Desconocedor", "Reticente", "Neutral", "Partidario", "Líder"]
    out = [["Interesado"] + niveles + ["Acción para cerrar la brecha"]]
    for c in G["compromiso"]:
        fila = [c["interesado"]]
        for n in niveles:
            marca = ("C" if n == c["actual"] else "") + ("D" if n == c["deseado"] else "")
            fila.append(marca or "")
        out.append(fila + [c["accion"]])
    return out


def comunicaciones():
    return [["Qué", "A quién", "Frecuencia", "Canal", "Responsable"]] + [
        [c["que"], c["a_quien"], c["frecuencia"], c["canal"], c["responsable"]] for c in G["comunicaciones"]]


# ------------------------------------------------------------------------------------------------ 3.6
def backlog():
    m = M()
    ep = {e["id"]: e["nombre"] for e in A["epicas"]}
    return [["Rango", "ID", "Historia de usuario", "Épica", "REQ-F / CU", "MoSCoW", "Pts", "WSJF", "Sprint"]] + [
        [str(h["rango"]), h["id"], h["texto"], f"{h['epica']} {ep[h['epica']]}", ", ".join(h["req"] + h["cu"]), h["moscow"],
         str(h["puntos"]), num(h["wsjf_valor"], 2), str(h["sprint"]) if h["sprint"] else "—"] for h in m["agil"]["historias"]]


def gherkin():
    m = M()
    return [["ID", "Criterio de aceptación (Dado, cuando, entonces)"]] + [
        [h["id"], h["gherkin"]] for h in sorted(m["agil"]["historias"], key=lambda h: h["id"])]


def sprints():
    m = M()
    return [["Sprint", "Fechas", "Objetivo del sprint", "Historias", "Pts", "Incremento esperado"]] + [
        [str(s["n"]), f"{_f(s['inicio'])} → {_f(s['fin'])}", s["objetivo"], ", ".join(s["historias"]), str(s["puntos"]), s["incremento"]]
        for s in m["agil"]["sprints"]]


def dor_dod():
    n = max(len(A["dor"]), len(A["dod"]))
    return [["Definición de listo (DoR)", "Definición de terminado (DoD)"]] + [
        [A["dor"][k] if k < len(A["dor"]) else "", A["dod"][k] if k < len(A["dod"]) else ""] for k in range(n)]


def ceremonias():
    return [["Evento", "Cuándo", "Quién", "Salida"]] + [[c["nombre"], c["cuando"], c["quien"], c["salida"]] for c in A["ceremonias"]]


def metricas():
    return [["Métrica", "Definición", "Meta", "Uso"]] + [[x["nombre"], x["definicion"], x["meta"], x["uso"]] for x in A["metricas"]]


# ------------------------------------------------------------------------------------------------ control, cierre, anexos
def cambios_pasos():
    return [["Paso", "Qué se hace"]] + [[f"{p['n']}. {p['paso']}", p["detalle"]] for p in G["cambios"]["pasos"]]


def solicitud():
    return [["Campo", "Contenido"],
            ["Título del issue", "[cambio-alcance] Resumen del cambio"],
            ["Solicitante y fecha", "Nombre, rol y fecha"],
            ["Descripción del cambio", "Qué se agrega, quita o modifica"],
            ["Justificación", "Por qué es necesario; objetivo OB-x o requisito REQ-x afectado"],
            ["Paquetes de la EDT afectados", "Códigos del nivel 2"],
            ["Impacto en el cronograma", "Diferencia de H1–H4 y de la ruta crítica (salida de plan.py)"],
            ["Impacto en el costo", "Diferencia del BAC y de la contingencia disponible"],
            ["Impacto en riesgos y calidad", "Riesgos RP-xx nuevos o modificados; pruebas afectadas"],
            ["Alternativas evaluadas", "Incluida la de no hacer el cambio"],
            ["Decisión", "Aprobada / rechazada / diferida, por quién (nivel de aprobación) y fecha"],
            ["Registro", "CI-xx, commit y nueva línea base, si corresponde"]]


def lecciones():
    return [["Campo", "Contenido"]] + [[c["campo"], c["contenido"]] for c in G["lecciones"]["campos"]]


def lecciones_iniciales():
    return [["ID", "Situación", "Lección", "Acción"]] + [[x["id"], x["situacion"], x["leccion"], x["accion"]]
                                                        for x in G["lecciones"]["iniciales"]]



TABLAS = {
    "t-acta": {"titulo": "Acta de constitución del proyecto", "fuente": f"{PROPIA}; guía CE01 v0.4 B3.1; gestion/e3/datos/gobierno.yaml y plan.py", "filas": acta},
    "t-smart": {"titulo": "Objetivos SMART del proyecto", "fuente": f"{PROPIA}; metas de infra/trazabilidad.yaml; plazos del E2", "filas": smart},
    "t-exito": {"titulo": "Criterios de éxito medibles", "fuente": f"{PROPIA}; gestion/e3/datos/gobierno.yaml", "filas": exito},
    "t-restricciones": {"titulo": "Restricciones y supuestos del proyecto", "fuente": f"{PROPIA}; infra/trazabilidad.yaml → supuestos", "filas": restricciones},
    "t-firmas": {"titulo": "Aprobación del acta de constitución", "fuente": PROPIA, "filas": firmas},
    "t-diccionario": {"titulo": "Diccionario de la EDT", "fuente": f"{PROPIA}; gestion/ce01.yaml → edt; horas y costo de gestion/e3/plan.py", "filas": diccionario},
    "t-raci": {"titulo": "Matriz RACI del proyecto", "fuente": f"{PROPIA}; guía CE01 v0.4 B3.2 (CI-103)", "filas": raci},
    "t-cambios-pasos": {"titulo": "Pasos del control de cambios", "fuente": f"{PROPIA}; gestion/e3/datos/gobierno.yaml", "filas": cambios_pasos},
    "t-cambios-nivel": {"titulo": "Nivel de aprobación según el impacto del cambio", "fuente": f"{PROPIA}; gestion/e3/datos/gobierno.yaml", "filas": cambios_nivel},
    "t-actividades": {"titulo": "Lista de actividades con duración, fechas, predecesoras y holgura", "fuente": f"{PROPIA}; CPM de gestion/e3/plan.py", "filas": actividades},
    "t-hitos": {"titulo": "Hitos principales", "fuente": f"{PROPIA}; gestion/e3/plan.py; roadmap del E1", "filas": hitos},
    "t-recursos": {"titulo": "Recursos del proyecto y horas asignadas", "fuente": f"{PROPIA}; gestion/e3/datos/plan.yaml; tarifa S-07", "filas": recursos},
    "t-msproject": {"titulo": "Comparación de la ruta crítica de Python con la de Microsoft Project", "fuente": f"{PROPIA}; gestion/e3/msproject.py", "filas": msproject},
    "t-presupuesto": {"titulo": "Presupuesto detallado por paquete de la EDT", "fuente": f"{PROPIA}; gestion/e3/plan.py; Presupuesto_EVM_E3.xlsx", "filas": presupuesto},
    "t-nivel1": {"titulo": "Presupuesto por área de la EDT", "fuente": f"{PROPIA}; gestion/e3/plan.py", "filas": nivel1},
    "t-costos-fijos": {"titulo": "Costos fijos del proyecto: hardware y AWS", "fuente": f"{PROPIA}; infra/centro_datos.yaml; gestion/ce01.yaml → economia.capex", "filas": costos_fijos},
    "t-linea-base": {"titulo": "Línea base de costos y reservas", "fuente": f"{PROPIA}; guía CE01 v0.4 B3.5", "filas": linea_base},
    "t-proyecto-e2": {"titulo": "Diferencia entre la línea base del proyecto y la inversión del business case", "fuente": f"{PROPIA}; E2 y gestion/e3/plan.py", "filas": proyecto_vs_e2},
    "t-evm": {"titulo": "Control del valor ganado con el avance real de S1", "fuente": f"{PROPIA}; git log de main; regla 0/100", "filas": evm},
    "t-umbrales": {"titulo": "Umbrales de control y acciones", "fuente": f"{PROPIA}; guía CE01 v0.4 B3.5", "filas": umbrales},
    "t-riesgos-analisis": {"titulo": "Registro de riesgos: identificación y análisis cualitativo", "fuente": f"{PROPIA}; gestion/ce01.yaml → riesgos_proyecto", "filas": riesgos_analisis},
    "t-riesgos-respuesta": {"titulo": "Plan de respuesta a los riesgos, ordenado por severidad", "fuente": f"{PROPIA}; gestion/ce01.yaml → riesgos_proyecto", "filas": riesgos_respuesta},
    "t-compromiso": {"titulo": "Matriz de evaluación del compromiso de los interesados (C = actual, D = deseado)", "fuente": f"{PROPIA}; interesados del E1; valoración del equipo", "filas": compromiso},
    "t-comunicaciones": {"titulo": "Plan de comunicaciones", "fuente": f"{PROPIA}; gestion/e3/datos/gobierno.yaml", "filas": comunicaciones},
    "t-backlog": {"titulo": "Product backlog priorizado por WSJF", "fuente": f"{PROPIA}; REQ-F y CU del SRS de CE02; Backlog_E3.xlsx", "filas": backlog},
    "t-sprints": {"titulo": "Planificación de los sprints de la consola", "fuente": f"{PROPIA}; gestion/e3/datos/agil.yaml y cronograma 5.4.1–5.4.3", "filas": sprints},
    "t-dor-dod": {"titulo": "Definición de listo y definición de terminado", "fuente": f"{PROPIA}; guía CE01 v0.4 B3.7", "filas": dor_dod},
    "t-ceremonias": {"titulo": "Eventos de Scrumban", "fuente": f"{PROPIA}; adaptado de la Guía de Scrum [2]", "filas": ceremonias},
    "t-metricas": {"titulo": "Métricas de seguimiento ágil", "fuente": f"{PROPIA}; guía CE01 v0.4 B3.7", "filas": metricas},
    "t-gherkin": {"titulo": "Criterios de aceptación de las historias en formato Gherkin", "fuente": f"{PROPIA}; gestion/e3/datos/agil.yaml", "filas": gherkin},
    "t-solicitud": {"titulo": "Formato de solicitud de cambio (issue cambio-alcance)", "fuente": PROPIA, "filas": solicitud},
    "t-lecciones": {"titulo": "Plantilla del registro de lecciones aprendidas", "fuente": PROPIA, "filas": lecciones},
    "t-lecciones-iniciales": {"titulo": "Lecciones aprendidas registradas en S1", "fuente": f"{PROPIA}; 00 M8", "filas": lecciones_iniciales},
}
