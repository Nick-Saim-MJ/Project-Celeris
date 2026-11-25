"""Tablas generadas del Entregable 1 de CE01 ({{tabla:id}} en gestion/e1/informe/*.md).

Cada tabla lee gestion/e1/datos/*.yaml, gestion/ce01.yaml, infra/trazabilidad.yaml o gestion/e1/calculos.py: ninguna
cifra se escribe a mano. TABLAS = {id: {"titulo", "fuente", "filas": función → [[cabecera], [fila], …]}}.
También las usa gestion/e1/xlsx_matrices.py para el libro de matrices.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI))
import calculos  # noqa: E402
import ce01_datos as cd  # noqa: E402
import estilo_ce01 as est  # noqa: E402

D = yaml.safe_load((AQUI / "datos" / "diagnostico.yaml").read_text(encoding="utf-8"))
M = yaml.safe_load((AQUI / "datos" / "madurez.yaml").read_text(encoding="utf-8"))
OB = {o["id"]: o for o in cd.objetivos()}
PROPIA = "Elaboración propia"


def _ob(oid: str) -> str:
    return f"{oid} {OB[oid]['necesidad']} ({OB[oid]['meta']})"


def porter():
    return [["Fuerza", "Intensidad", "Hecho que la sustenta", "Fuente"]] + [
        [f["fuerza"], f["intensidad"].upper(), f["hecho"], f["fuente"]] for f in D["porter"]["fuerzas"]]


def conectividad():
    return [["Aspecto", "Campus Juliaca (altiplano)", "Referencia de la costa"]] + [
        [f["aspecto"], f["altiplano"], f["costa"]] for f in D["conectividad"]["filas"]]


def cadena_valor():
    return [["Tipo", "Actividad", "Dependencia de los laboratorios", "Por qué", "Cómo se manifiesta el problema"]] + [
        [a["tipo"], a["actividad"], a["dependencia"].upper(), a["por_que"], a["problema"]]
        for a in D["cadena_valor"]["actividades"]]


def stakeholders():
    return [["Stakeholder", "Poder", "Interés", "Estrategia", "Qué espera"]] + [
        [s["nombre"], s["poder"], s["interes"], s["estrategia"], s["espera"]] for s in D["stakeholders"]["lista"]]


def identidad():
    i = D["identidad"]
    filas = [["Elemento", "Texto", "Estado"], ["Misión", i["mision"], "Pendiente"], ["Visión", i["vision"], "Pendiente"]]
    for o in i["objetivos"]:
        filas.append([f"Objetivo {o['id']}", o["texto"], f"{o['estado']}; lo sirven {', '.join(o['ob'])}"])
    return filas


def foda():
    f = D["foda"]
    lista = lambda k: "; ".join(f"{x['id']} {x['texto']} ({x['fuente']})" for x in f[k])
    return [["", "Positivo", "Negativo"],
            ["Interno", f"FORTALEZAS: {lista('F')}", f"DEBILIDADES: {lista('D')}"],
            ["Externo", f"OPORTUNIDADES: {lista('O')}", f"AMENAZAS: {lista('A')}"]]


def tows():
    return [["Tipo", "ID", "Cruza", "Estrategia", "Componente o decisión de Celeris"]] + [
        [e["tipo"], e["id"], e["cruza"], e["estrategia"], e["apunta_a"]] for e in D["tows"]["estrategias"]]


def pestel():
    return [["Factor", "Hecho o norma", "Fuente", "Efecto en el proyecto"]] + [
        [f["factor"], f["hecho"], f["fuente"], f["efecto"]] for f in D["pestel"]["factores"]]


def fce():
    filas = [["ID", "Factor crítico de éxito", "KPI", "Meta", "Fuente de medición", "Riesgo"]]
    for f in D["fce"]["lista"]:
        meta = f"{OB[f['meta_ob']]['meta']} ({f['meta_ob']})" if f.get("meta_ob") else f["meta"]
        filas.append([f["id"], f["factor"], f["kpi"], meta, f["medicion"], f["riesgo"]])
    return filas


def inventario():
    return [["Sistema", "Dueño", "Versión / alcance", "Soporte", "Depend. de Internet", "Criticidad", "Estado del dato"]] + [
        [s["sistema"], s["dueno"], s["version"], s["soporte"], s["internet"], s["criticidad"], s["estado"]]
        for s in D["inventario"]["sistemas"]]


def cobit():
    return [["Objetivo COBIT", "Pregunta guía", "Actual", "Objetivo", "Evidencia esperada"]] + [
        [f"{o['id']} {o['nombre']}", o["pregunta"], "Pendiente de entrevista" if o["actual"] is None else str(o["actual"]),
         str(o["objetivo"]), o["evidencia_esperada"]] for o in M["objetivos"]]


def brechas():
    return [["ID", "COBIT", "Situación actual", "Estado deseado", "Acción", "Componente Celeris", "Objetivo"]] + [
        [b["id"], b["cobit"], b["actual"], b["deseado"], b["accion"], b["componente"], b["ob"]]
        for b in D["brechas"]["lista"]]


def ya_resuelto():
    return [["Qué se necesita", "Quién lo resuelve hoy", "Decisión"]] + [
        [x["que"], x["quien"], x["decision"]] for x in D["brechas"]["ya_resuelto"]]


def problemas():
    filas = [["ID", "Problema operativo", "Impacto", "Frecuencia", "Puntaje", "Nivel", "Evidencia a levantar"]]
    for p in D["problemas"]["lista"]:
        pt = p["impacto"] * p["frecuencia"]
        filas.append([p["id"], p["problema"], str(p["impacto"]), str(p["frecuencia"]), str(pt), est.nivel_riesgo(pt)[1],
                      p["evidencia"]])
    return filas


def w5h2():
    d = calculos.datos()
    cuanto = (f"{d['gb_ciclo_lab']} por laboratorio en cada ciclo ({d['pcs_lab']} PCs × {d['gb_pc']}) [S-26, S-27]; "
              f"{d['gb_repetidos_anio']} repetidos al año en los {d['labs']} laboratorios; al menos {d['min_lab']} "
              f"de descarga por laboratorio aun utilizando la totalidad del enlace de {d['enlace']} [S-02]")
    return [["Pregunta", "Respuesta"]] + [
        [f["pregunta"], cuanto if f["respuesta"] == "calc" else f["respuesta"]] for f in D["w5h2"]["filas"]]


def cinco_porques():
    c = D["cinco_porques"]
    return [["Nivel", "Pregunta", "Respuesta"]] + [
        [str(k), p["porque"], p["respuesta"]] for k, p in enumerate(c["pasos"], 1)] + [["Raíz", "—", c["raiz"]]]


def impacto():
    d = calculos.datos()
    c = cd.datos()
    return [["Indicador", "Valor", "Cómo se calcula", "Supuestos"],
            ["GB por laboratorio y ciclo", d["gb_ciclo_lab"], f"{d['pcs_lab']} PCs × {d['gb_pc']} por PC", "S-26, S-27"],
            ["GB repetidos por laboratorio y ciclo", d["gb_repetidos_lab"],
             f"Todas las copias excepto la primera ({d['fraccion_repetida']} del volumen)", "S-26, S-27"],
            ["GB repetidos al año (todo el alcance)", d["gb_repetidos_anio"],
             f"Repetidos por laboratorio × {d['labs']} laboratorios × {d['ciclos']} ciclos", "S-06, S-26, S-27"],
            ["Tiempo mínimo de descarga de un laboratorio", f"{d['horas_lab']} ({d['min_lab']})",
             f"{d['gb_ciclo_lab']} a {d['enlace']}, con todo el enlace (cota inferior)", "S-02, S-26, S-27"],
            ["Horas técnicas por año", d["horas_tecnicas_anio"], "PCs × ciclos × horas por PC y ciclo", "S-01, S-06, S-07"],
            ["Costo de esas horas por año", d["usd_horas_anio"], "Horas técnicas × tarifa", "S-07"],
            ["Mbps que habría que ampliar", c["mbps_diferidos"], "BHR × enlace", "S-40 (S-04 × S-02)"],
            ["Costo anual de esa ampliación", d["usd_enlace_anio"], "Mbps × costo por Mbps-mes × 12", "S-03, S-40"],
            [f"Costo de no actuar en {c['horizonte_anios']}", d["usd_no_actuar"],
             "(Ampliación + horas técnicas) × horizonte, sin descontar", "S-03, S-07, S-40"],
            ["Horas de clase perdidas", "Sin dato", "Registro de clases retrasadas por descargas", "[levantar con la DTI y los docentes]"]]


def caso_negocio():
    c = cd.datos()
    return [["Concepto", "Valor (caso base)", "Detalle en el E2"],
            ["Inversión inicial (I0)", c["capex_total"], "Servidor, switch, UPS y cableado [S-08, S-37, S-38, S-39]"],
            ["Costo anual de operación y mantenimiento", c["opex_total"], "AWS, energía y mantenimiento [S-09, S-41]"],
            ["Beneficio anual", c["beneficio_total"], "Ampliación del enlace diferida y horas técnicas [S-03, S-07, S-40]"],
            ["Flujo neto anual", c["flujo_neto_anual"], "Beneficio − costo anual"],
            [f"VAN a {c['horizonte_anios']} (COK {c['cok']})", c["van"], "Descontado al COK [S-10]; el E2 agrega Monte Carlo y tornado"],
            ["Recuperación de la inversión", c["payback_meses"], "I0 ÷ flujo neto mensual"]]


def alineamiento():
    return [["Objetivo estratégico", "Capacidad requerida", "Brecha", "Componente Celeris", "KPI", "Objetivo del proyecto", "Fila de 00 M7"]] + [
        [f["oe"], f["capacidad"], f["brecha"], f["componente"], f["kpi"], _ob(f["ob"]), f["m7"]]
        for f in D["alineamiento"]["filas"]]


def roadmap():
    import datetime as dt
    filas = [["Horizonte", "Iniciativa", "Inicio", "Fin"]]
    for h in D["roadmap"]["horizontes"]:
        for t in h["tareas"]:
            ini = dt.date.fromisoformat(t["inicio"])
            filas.append([h["nombre"], t["nombre"], t["inicio"], (ini + dt.timedelta(days=t["dias"])).isoformat()])
    for h in D["roadmap"]["hitos"]:
        filas.append([h["horizonte"], f"Hito: {h['nombre']} ({h['nota']})", h["fecha"], h["fecha"]])
    return filas


def riesgos():
    filas = [["ID", "Riesgo", "P", "I", "P × I", "Nivel", "Respuesta", "Dueño", "Disparador"]]
    for r in cd.cargar()["riesgos_estrategicos"]["lista"]:
        pt = r["p"] * r["i"]
        filas.append([r["id"], r["riesgo"], str(r["p"]), str(r["i"]), str(pt), est.nivel_riesgo(pt)[1], r["respuesta"],
                      r["dueno"], r["disparador"]])
    return filas


def _t(titulo, fuente, filas):
    return {"titulo": titulo, "fuente": fuente, "filas": filas}


TABLAS = {
    "t-porter": _t("Cinco fuerzas de Porter adaptadas al campus", D["porter"]["fuente"], porter),
    "t-conectividad": _t("Oferta de conectividad del campus frente a la costa", D["conectividad"]["fuente"], conectividad),
    "t-cadena-valor": _t("Cadena de valor y dependencia de los laboratorios", D["cadena_valor"]["fuente"], cadena_valor),
    "t-stakeholders": _t("Stakeholders: poder, interés, estrategia y expectativa", D["stakeholders"]["fuente"], stakeholders),
    "t-identidad": _t("Ficha de identidad estratégica", D["identidad"]["fuente"], identidad),
    "t-foda": _t("Análisis FODA", D["foda"]["fuente"], foda),
    "t-tows": _t("FODA cruzado (TOWS): estrategias y su componente en Celeris", D["tows"]["fuente"], tows),
    "t-pestel": _t("Análisis PESTEL con hecho o norma por factor", D["pestel"]["fuente"], pestel),
    "t-fce": _t("Factores críticos de éxito, KPI y meta", D["fce"]["fuente"], fce),
    "t-inventario": _t("Inventario de sistemas de información existentes", D["inventario"]["fuente"], inventario),
    "t-cobit": _t("Instrumento de madurez COBIT 2019 por objetivo", M["fuente"], cobit),
    "t-brechas": _t("Análisis de brechas (gap analysis)", D["brechas"]["fuente"], brechas),
    "t-ya-resuelto": _t("Lo que la infraestructura actual ya resuelve", f"{PROPIA}; [S-29]", ya_resuelto),
    "t-problemas": _t("Problemas operativos asociados a TI", D["problemas"]["fuente"], problemas),
    "t-5w2h": _t("Definición estructurada del problema (5W2H)", D["w5h2"]["fuente"], w5h2),
    "t-5porques": _t("Cinco porqués de la causa principal", D["cinco_porques"]["fuente"], cinco_porques),
    "t-impacto": _t("Impacto cuantificado del problema", f"{PROPIA}; gestion/e1/calculos.py y gestion/ce01_datos.py", impacto),
    "t-caso-negocio": _t("Resumen del caso de negocio (CE0113)", f"{PROPIA}; gestion/ce01_datos.py (detalle en el E2)", caso_negocio),
    "t-alineamiento": _t("Matriz de alineamiento estratégico", D["alineamiento"]["fuente"], alineamiento),
    "t-roadmap": _t("Iniciativas e hitos del roadmap", D["roadmap"]["fuente"], roadmap),
    "t-riesgos": _t("Matriz de riesgos estratégicos", cd.cargar()["riesgos_estrategicos"]["fuente"], riesgos),
}
