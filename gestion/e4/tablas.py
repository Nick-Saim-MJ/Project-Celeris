"""Tablas generadas del Entregable 4 de CE01 ({{tabla:id}} en gestion/e4/informe/*.md).

Leen gestion/e4/datos/e4.json (gestion/e4/procesos.py), gestion/e4/datos/procesos.yaml, gestion/e4/simulacion.yaml y
los supuestos a través de gestion/ce01_datos.py: ninguna cifra se escribe a mano.
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
CAR = yaml.safe_load((AQUI / "datos" / "procesos.yaml").read_text(encoding="utf-8"))
SIM = yaml.safe_load((AQUI / "simulacion.yaml").read_text(encoding="utf-8"))
_E4 = AQUI / "datos" / "e4.json"
NOMBRES = {"P1": "Actualización masiva de las PCs de un laboratorio", "P2": "Preparación de un laboratorio para una clase",
           "C3": "Instalación de la imagen base al inicio del semestre", "C4": "Atención de incidencias de las PCs",
           "C5": "Gestión del acceso a Internet y del filtrado"}


def M() -> dict:
    if not _E4.exists():
        raise cd.DatosCE01Error("Falta gestion/e4/datos/e4.json: ejecute python gestion/e4/procesos.py")
    return json.loads(_E4.read_text(encoding="utf-8"))["modelo"]


def _h(x) -> str:
    if x is None:
        return "—"
    return f"{num(x * 60)} min" if x < 1 else f"{num(x, 1)} h"


def _mej(x) -> str:
    return "—" if x is None else ("−" if x > 0 else "+") + pct(abs(x))


def _kpi(kid: str) -> dict:
    return next(i for i in CAR["indicadores"] if i["id"] == kid)


# ------------------------------------------------------------------ 4.1.1 Identificación y caracterización
def seleccion():
    crit = CAR["seleccion"]["criterios"]
    filas = [["Proceso"] + [f"{c['id']} {c['nombre']} ({pct(c['peso'])})" for c in crit] + ["Puntaje ponderado", "Motivo"]]
    for r in M()["seleccion"]:
        filas.append([f"{r['id']} {NOMBRES[r['id']]}"] + [str(x) for x in r["puntajes"]] + [num(r["total"], 2), r["motivo"]])
    return filas


def ficha():
    m = M()
    frec = {"P1": f"{num(m['anual']['P1'])} ciclos al año ({num(cd.s('S-06.ciclos_anio'))} por laboratorio [S-06] × "
                  f"{num(cd.s('S-26.laboratorios'))} laboratorios [S-26])",
            "P2": f"{num(m['anual']['P2'])} pedidos al año ({num(cd.s('S-45.pedidos_semana'))} por laboratorio y semana × "
                  f"{num(cd.s('S-45.semanas_anio'))} semanas × {num(cd.s('S-26.laboratorios'))} laboratorios [S-45, S-26])"}
    filas = [["Atributo", f"P1 {NOMBRES['P1']}", f"P2 {NOMBRES['P2']}"]]
    for etiqueta, clave in (("Objetivo", "objetivo"), ("Dueño", "dueno"), ("Disparador", "disparador")):
        filas.append([etiqueta, CAR["sipoc"]["P1"][clave], CAR["sipoc"]["P2"][clave]])
    filas.append(["Frecuencia", frec["P1"], frec["P2"]])
    filas.append(["Indicadores (KPI)"] + ["; ".join(f"{k} {_kpi(k)['nombre']}" for k in CAR["sipoc"][p]["kpi"]) for p in ("P1", "P2")])
    return filas


def sipoc():
    filas = [["Proceso", "Proveedores (S)", "Entradas (I)", "Proceso (P)", "Salidas (O)", "Clientes (C)"]]
    for p in ("P1", "P2"):
        s = CAR["sipoc"][p]
        filas.append([p, "; ".join(s["proveedores"]), "; ".join(s["entradas"]), " → ".join(s["pasos"]),
                      "; ".join(s["salidas"]), "; ".join(s["clientes"])])
    return filas


# ------------------------------------------------------------------ 4.1.3 Indicadores actuales
def indicadores_asis():
    m = M()
    r, k, c = m["resultados"], m["calculos"], m["comparativo"]
    val = {
        "KPI-1": (f"{_h(k['wan_lab'])} [S-26, S-27, S-42]", f"{_h(k['wan_lab'])} [S-26, S-27, S-42]", "Calculado"),
        "KPI-2": (f"{num(c['P1']['wan_gb']['asis'])} GB (con lo pendiente)", f"{num(c['P2']['wan_gb']['asis'])} GB", "Calculado y simulado"),
        "KPI-3": ("—", f"{_h(c['P2']['habilitar_h']['asis'])} (P90 {_h(r['P2-AS-IS']['habilitar_h']['p90'])})", "Estimado [S-43, S-44]"),
        "KPI-4": ("—", pct(c["P2"]["listo"]["asis"]), "Estimado [S-43, S-44]"),
        "KPI-5": (num(c["P1"]["interrupciones"]["asis"], 2), "—", "Estimado [S-44]"),
        "KPI-6": (_h(c["P1"]["horas_personal"]["asis"]), _h(c["P2"]["horas_personal"]["asis"]), "Estimado [S-43, S-44]"),
        "KPI-7": (usd(c["P1"]["costo"]["asis"], 2), usd(c["P2"]["costo"]["asis"], 2), "Estimado [S-07, S-43]"),
        "KPI-8": (_h(c["P1"]["ocupacion_h"]["asis"]), _h(c["P2"]["ocupacion_h"]["asis"]), "Estimado [S-43, S-44]"),
    }
    n = CAR["cronometraje"]["observaciones_min"]
    filas = [["Indicador", "Fórmula", "Método de medición", "Observaciones mínimas", "P1 (línea base)", "P2 (línea base)", "Estado"]]
    for i in CAR["indicadores"]:
        a, b, estado = val[i["id"]]
        filas.append([f"{i['id']} {i['nombre']}", i["formula"], i["medicion_asis"], f"≥ {n}", a, b, estado])
    return filas


# ------------------------------------------------------------------ 4.1.5 Problemas detectados
def problemas():
    filas = [["PD", "Diagrama · actividad", "Problema", "Causa (Ishikawa del E1)", "Efecto", "Indicador afectado"]]
    for p in CAR["problemas"]:
        nodo = next(n for n in SIM["procesos"][p["diagrama"]]["nodos"] if n["id"] == p["nodo"])
        filas.append([p["id"], f"{p['diagrama']} · {nodo['nombre']}", p["problema"], f"{p['categoria']}: {p['causa']}",
                      p["efecto"], ", ".join(f"{k} {_kpi(k)['nombre']}" for k in p["kpi"])])
    return filas


# ------------------------------------------------------------------ 4.2 TO-BE
def eliminadas():
    filas = [["Proceso", "Tarea del AS-IS eliminada o sustituida", "Motivo en el TO-BE"]]
    for pid in ("P1-TO-BE", "P2-TO-BE"):
        for e in SIM["procesos"][pid].get("eliminadas", []):
            filas.append([pid.split("-")[0], e["tarea"], e["motivo"]])
    return filas


def automatizaciones():
    filas = [["ID", "Tarea del AS-IS", "Cambio", "Tecnología", "Requisito (SRS de CE02)", "Prueba", "Elimina"]]
    for a in CAR["automatizaciones"]:
        filas.append([a["id"], a["tarea"], a["cambio"], a["tecnologia"], ", ".join(a["req"]), ", ".join(a["prueba"]), ", ".join(a["pd"])])
    return filas


def indicadores_tobe():
    m = M()
    c, ob = m["comparativo"], m["metas"]
    meta = {
        "KPI-1": f"{ob['OB-2_texto']} frente al AS-IS (OB-2); simulado {_mej(m['kpi1']['mejora'])}",
        "KPI-2": f"Una descarga por contenido: {num(m['calculos']['gb_pc'])} GB por ciclo (OB-1)",
        "KPI-3": f"{ob['OB-3_texto']} sin descifrar (OB-3); simulado: {pct(m['habilitar_en_meta']['P2-TO-BE'])} de los pedidos",
        "KPI-4": f"≥ {pct(_kpi('KPI-4')['meta_pct'])} ({_kpi('KPI-4')['meta_fuente']}); simulado {pct(c['P2']['listo']['tobe'])}",
        "KPI-5": f"≤ {num(c['P1']['interrupciones']['tobe'], 2)} por ciclo (valor simulado, a recalibrar)",
        "KPI-6": f"P1 ≤ {_h(c['P1']['horas_personal']['tobe'])}; P2 ≤ {_h(c['P2']['horas_personal']['tobe'])} (simulado)",
        "KPI-7": f"P1 ≤ {usd(c['P1']['costo']['tobe'], 2)}; P2 ≤ {usd(c['P2']['costo']['tobe'], 2)} (simulado)",
        "KPI-8": f"P1 ≤ {_h(c['P1']['ocupacion_h']['tobe'])}; P2 ≤ {_h(c['P2']['ocupacion_h']['tobe'])} (simulado)",
    }
    filas = [["Indicador", "Meta", "Fórmula", "Fuente del dato", "Frecuencia"]]
    for i in CAR["indicadores"]:
        filas.append([f"{i['id']} {i['nombre']}", meta[i["id"]], i["formula"], i["fuente_tobe"], i["frecuencia"]])
    return filas


def mejora():
    m = M()
    r = m["resultados"]
    medidas = [("Tiempo de ciclo", "ciclo_h", _h), ("Ocupación del laboratorio", "ocupacion_h", _h),
               ("Horas del técnico", "horas_tecnico", _h), ("Horas del encargado", "horas_encargado", _h),
               ("Costo de personal", "costo", lambda v: usd(v, 2)), ("Tráfico por el enlace", "wan_gb", lambda v: f"{num(v)} GB")]
    filas = [["Proceso", "Medida", "AS-IS: media (P10–P90)", "TO-BE: media (P10–P90)", "Mejora de la media"]]
    for proc in ("P1", "P2"):
        a, b = r[f"{proc}-AS-IS"], r[f"{proc}-TO-BE"]
        for etiqueta, k, f in medidas:
            fa = f"{f(a[k]['media'])} ({f(a[k]['p10'])}–{f(a[k]['p90'])})"
            fb = f"{f(b[k]['media'])} ({f(b[k]['p10'])}–{f(b[k]['p90'])})"
            filas.append([proc, etiqueta, fa, fb, _mej(m["comparativo"][proc][k]["mejora"])])
    return filas


# ------------------------------------------------------------------ 4.3 Comparativo
def tiempos():
    m = M()
    c, k = m["comparativo"], m["kpi1"]
    v = "Cronometraje (AS-IS) y consola P-05 (TO-BE)"
    return [
        ["Indicador", "AS-IS", "TO-BE", "Mejora", "Método de verificación"],
        ["KPI-1 Descarga para dejar listo un laboratorio (P1 y P2)", _h(k["asis"]), _h(k["tobe"]), _mej(k["mejora"]), v],
        ["KPI-8 Ocupación del laboratorio, P1", _h(c["P1"]["ocupacion_h"]["asis"]), _h(c["P1"]["ocupacion_h"]["tobe"]),
         _mej(c["P1"]["ocupacion_h"]["mejora"]), "Cronometraje por fase y registro del técnico"],
        ["KPI-8 Ocupación del laboratorio, P2", _h(c["P2"]["ocupacion_h"]["asis"]), _h(c["P2"]["ocupacion_h"]["tobe"]),
         _mej(c["P2"]["ocupacion_h"]["mejora"]), "Cronometraje por fase y consola"],
        ["KPI-3 Habilitar contenido o acceso, P2 (media)", _h(c["P2"]["habilitar_h"]["asis"]), _h(c["P2"]["habilitar_h"]["tobe"]),
         _mej(c["P2"]["habilitar_h"]["mejora"]), "Ticket o correo a la DTI (AS-IS); auditoría de la consola (TO-BE)"],
        ["Tiempo de ciclo, P1", _h(c["P1"]["ciclo_h"]["asis"]), _h(c["P1"]["ciclo_h"]["tobe"]), _mej(c["P1"]["ciclo_h"]["mejora"]),
         "Fechas de inicio y fin del ciclo"],
        ["Tiempo de ciclo, P2", _h(c["P2"]["ciclo_h"]["asis"]), _h(c["P2"]["ciclo_h"]["tobe"]), _mej(c["P2"]["ciclo_h"]["mejora"]),
         "Hora del pedido y hora de laboratorio listo"],
    ]


def costos():
    m = M()
    c, k = m["comparativo"], m["calculos"]
    filas = [["Concepto", "AS-IS", "TO-BE", "Mejora", "Método de verificación"]]
    for proc, n in (("P1", "ciclo"), ("P2", "preparación")):
        filas.append([f"KPI-7 Costo de personal por {n}, {proc}", usd(c[proc]["costo"]["asis"], 2), usd(c[proc]["costo"]["tobe"], 2),
                      _mej(c[proc]["costo"]["mejora"]), f"Horas cronometradas × tarifa {usd(k['tarifa'])}/h [S-07]"])
        filas.append([f"Costo de personal al año, {proc} ({num(m['anual'][proc])} ejecuciones)", usd(c[proc]["costo_anio"]["asis"]),
                      usd(c[proc]["costo_anio"]["tobe"]), _mej(c[proc]["costo"]["mejora"]), "Hoja de cálculo sobre el registro de horas"])
    ta = c["P1"]["costo_anio"]["asis"] + c["P2"]["costo_anio"]["asis"]
    tb = c["P1"]["costo_anio"]["tobe"] + c["P2"]["costo_anio"]["tobe"]
    filas.append(["Total al año, P1 + P2", usd(ta), usd(tb), _mej((ta - tb) / ta), "Suma de las filas anteriores"])
    filas.append([f"Tráfico por el enlace al año, P1 + P2", f"{num(c['P1']['wan_gb_anio']['asis'] + c['P2']['wan_gb_anio']['asis'])} GB",
                  f"{num(c['P1']['wan_gb_anio']['tobe'] + c['P2']['wan_gb_anio']['tobe'])} GB",
                  _mej(1 - (c['P1']['wan_gb_anio']['tobe'] + c['P2']['wan_gb_anio']['tobe']) /
                       (c['P1']['wan_gb_anio']['asis'] + c['P2']['wan_gb_anio']['asis'])),
                  "Contadores del FortiGate; su valor económico ya está en el beneficio BN-1 del E2"])
    return filas


def calidad():
    m = M()
    c = m["comparativo"]
    return [
        ["Indicador", "AS-IS", "TO-BE", "Meta", "Método de verificación"],
        ["KPI-4 Preparaciones listas al inicio de la clase (P2)", pct(c["P2"]["listo"]["asis"]), pct(c["P2"]["listo"]["tobe"]),
         f"≥ {pct(_kpi('KPI-4')['meta_pct'])}", "Registro del encargado (AS-IS); estado de la precarga en la consola (TO-BE)"],
        ["KPI-5 Interrupciones por ciclo (P1)", num(c["P1"]["interrupciones"]["asis"], 2), num(c["P1"]["interrupciones"]["tobe"], 2),
         "Reducir", "Registro del técnico; entregas pendientes en la consola"],
        [f"KPI-3 Pedidos habilitados en {m['metas']['OB-3_texto']} (P2)", pct(m["habilitar_en_meta"]["P2-AS-IS"]),
         pct(m["habilitar_en_meta"]["P2-TO-BE"]), f"OB-3: {m['metas']['OB-3_texto']}", "Auditoría de la consola (P-08)"],
        ["Pedidos y cambios con registro", "Ninguno", "Todos", "Trazabilidad completa", "Auditoría de la consola (REQ-F-24)"],
    ]


def e2():
    m = M()
    d = json.loads(_E4.read_text(encoding="utf-8"))["datos"]
    return [
        ["Concepto", "Business case (E2)", "Modelo de procesos (E4)", "Uso"],
        ["Horas de personal ahorradas por PC y ciclo de actualización (P1)", f"{d['e4_horas_pc_e2']} [S-07]", d["e4_ahorro_h_pc"],
         "Reemplaza a S-07 en el E2 cuando se mida"],
        ["Beneficio anual BN-2 (S-01 × S-06 × horas × tarifa)", d["e4_bn2_e2"], d["e4_bn2_e4"], "Comparación"],
        ["Horas ahorradas al año en P2", "No incluido", d["e4_ahorro_h_p2_anio"], "Beneficio adicional no valorizado en el E2"],
        ["Valor de esas horas a la tarifa de S-07", "No incluido", d["e4_ahorro_usd_p2_anio"], "Beneficio adicional no valorizado en el E2"],
    ]


# ------------------------------------------------------------------ Anexo
def parametros():
    cars = SIM["meta"]["carriles"]
    filas = [["Diagrama", "Tarea o evento", "Carril", "Duración (h): mín / moda / máx o fórmula", "Recurso"]]
    for pid, p in SIM["procesos"].items():
        for n in p["nodos"]:
            if "tri" in n:
                a, mo, b = n["tri"]
                dur = f"{num(a, 3)} / {num(mo, 3)} / {num(b, 3)}" + (" por PC" if n.get("por_pc") else "") + " [S-43]"
            elif "calculo" in n:
                dur = {"wan_lab": "GB del laboratorio por el enlace [S-26, S-27, S-42]", "lan_lab": "GB del laboratorio por la LAN [S-14]",
                       "wan_precarga": "GB de una PC con el límite de T50"}[n["calculo"]] + (" × la mitad pendiente [S-44]" if n.get("factor") else "")
            else:
                continue
            filas.append([pid, n["nombre"], cars[n["carril"]], dur, cars.get(n.get("recurso"), "—") if n.get("recurso") else "—"])
    return filas


def compuertas():
    m = M()
    k = m["calculos"]
    return [
        ["Compuerta", "Diagramas", "Probabilidad", "Fuente"],
        ["¿Terminó antes de la siguiente clase? (No)", "P1-AS-IS", pct(k["p_interrupcion"]), "S-44"],
        ["¿Terminó antes de la siguiente clase? (No)", "P1-TO-BE", pct(k["p_interrupcion_tobe"], 1),
         "S-44 escalada por la duración de la entrega (LAN frente a Internet)"],
        ["¿Llega con un día de anticipación? (No)", "P2-AS-IS, P2-TO-BE", pct(cd.s("S-44.p_mismo_dia")), "S-44"],
        ["¿Requiere una fuente nueva o un cambio de acceso? (Sí)", "P2-AS-IS, P2-TO-BE", pct(cd.s("S-44.p_cambio")), "S-44"],
        ["¿La fuente requiere descifrar? (Sí)", "P2-TO-BE", pct(cd.s("S-44.p_descifrar")), "S-44"],
        ["Frecuencia de llegada de P1", "P1", f"{num(k['ciclos_p1_anio'])} ciclos al año", "S-06, S-26"],
        ["Frecuencia de llegada de P2", "P2", f"{num(k['pedidos_p2_anio'])} pedidos al año", "S-45, S-26"],
        ["Costo de los recursos con costo (técnico, encargado)", "Todos", f"{usd(k['tarifa'])}/h", "S-07"],
    ]



TABLAS = {
    "t-seleccion": {"titulo": "Matriz de selección de procesos (escala 1–5, pesos del equipo)", "fuente": f"{PROPIA}; gestion/e4/datos/procesos.yaml → seleccion", "filas": seleccion},
    "t-ficha": {"titulo": "Ficha de caracterización de P1 y P2", "fuente": f"{PROPIA}; guía CE01 v0.4 B4.1; supuestos S-06, S-26 y S-45", "filas": ficha},
    "t-sipoc": {"titulo": "SIPOC de P1 y P2 (situación actual)", "fuente": f"{PROPIA}; gestion/e4/datos/procesos.yaml → sipoc", "filas": sipoc},
    "t-indicadores-asis": {"titulo": "Indicadores actuales (línea base) con su método de medición", "fuente": f"{PROPIA}; gestion/e4/procesos.py sobre simulacion.yaml", "filas": indicadores_asis},
    "t-problemas": {"titulo": "Problemas detectados en el AS-IS, causa y efecto", "fuente": f"{PROPIA}; Ishikawa y problemas PO-x del E1 (gestion/e1/datos/diagnostico.yaml)", "filas": problemas},
    "t-eliminadas": {"titulo": "Tareas del AS-IS eliminadas o sustituidas en el TO-BE", "fuente": f"{PROPIA}; gestion/e4/simulacion.yaml → eliminadas", "filas": eliminadas},
    "t-automatizaciones": {"titulo": "Automatizaciones propuestas: tarea, tecnología, requisito y prueba", "fuente": f"{PROPIA}; SRS de CE02 (docs/software/e1/srs) e infra/pruebas.yaml", "filas": automatizaciones},
    "t-indicadores-tobe": {"titulo": "Nuevos indicadores del TO-BE con meta, fuente y frecuencia", "fuente": f"{PROPIA}; metas de infra/trazabilidad.yaml (OB-1…OB-3) y guía CE01 v0.4 B4.5", "filas": indicadores_tobe},
    "t-mejora": {"titulo": "Resultados de la simulación de Monte Carlo (media y percentiles 10–90)", "fuente": f"{PROPIA}; gestion/e4/procesos.py [S-07, S-43, S-44]", "filas": mejora},
    "t-tiempos": {"titulo": "Reducción de tiempos", "fuente": f"{PROPIA}; gestion/e4/procesos.py", "filas": tiempos},
    "t-costos": {"titulo": "Reducción de costos de personal y de tráfico", "fuente": f"{PROPIA}; gestion/e4/procesos.py [S-07]", "filas": costos},
    "t-calidad": {"titulo": "Mejora en calidad del servicio", "fuente": f"{PROPIA}; gestion/e4/procesos.py; metas OB-3 y guía CE01 v0.4 B4.5", "filas": calidad},
    "t-e2": {"titulo": "Horas ahorradas: business case frente al modelo de procesos", "fuente": f"{PROPIA}; gestion/e4/datos/resultados.json y E2", "filas": e2},
    "t-parametros": {"titulo": "Parámetros de duración de la simulación (para Bizagi)", "fuente": f"{PROPIA}; gestion/e4/simulacion.yaml [S-43]", "filas": parametros},
    "t-compuertas": {"titulo": "Probabilidades, frecuencias y costos de la simulación", "fuente": f"{PROPIA}; supuestos S-06, S-07, S-26, S-44 y S-45", "filas": compuertas},
}
