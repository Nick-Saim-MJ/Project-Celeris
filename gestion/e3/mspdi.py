"""Cronograma de Celeris en formato MSPDI (Microsoft Project XML): entregables/CE01/E3/Cronograma_Celeris.xml.

Lo llama gestion/e3/plan.py. Escribe el calendario (lunes a viernes, 08:00–17:00, con feriados y receso), la estructura
de la EDT como tareas resumen, las actividades con su paquete, duración, dependencias (FS/SS con desfase), restricciones,
avance real (lo terminado al 100 % con su fecha), costo fijo y línea base 0; los recursos con su tarifa (S-07 para el
equipo; 0 para las contrapartes) y las asignaciones con su trabajo. MS Project recalcula fechas, costos y holguras al
abrirlo; gestion/e3/msproject.py los compara con los de Python.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from xml.sax.saxutils import escape

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI))
import ce01_datos as cd  # noqa: E402
import plan as P  # noqa: E402

RUTA = P.SALIDA / "Cronograma_Celeris.xml"


def _t(d: dt.date, hora: str) -> str:
    return f"{d.isoformat()}T{hora}:00"


def _dur(dias: int) -> str:
    return f"PT{dias * 8}H0M0S"


def _horas(h: float) -> str:
    return f"PT{int(h)}H{int(round((h % 1) * 60))}M0S"


def _el(nombre: str, valor) -> str:
    return f"<{nombre}>{escape(str(valor))}</{nombre}>"


def escribir(m: dict, ruta: Path = RUTA) -> Path:
    cal = P.calendario()
    cfg = P.plan()
    y = cd.cargar()
    edt = {p["id"]: p for p in y["edt"]["paquetes"]}
    filas = {f["id"]: f for f in m["filas"]}
    acts = {a["id"]: a for a in P.actividades()}
    cron, lb = P.programar(), P.programar(linea_base=True)
    pres = m["presupuesto"]

    # ---------------------------------------------------------------- calendario
    jornada = '<WorkingTimes><WorkingTime><FromTime>08:00:00</FromTime><ToTime>12:00:00</ToTime></WorkingTime>' \
              '<WorkingTime><FromTime>13:00:00</FromTime><ToTime>17:00:00</ToTime></WorkingTime></WorkingTimes>'
    dias = "".join(f"<WeekDay><DayType>{k}</DayType><DayWorking>{0 if k in (1, 7) else 1}</DayWorking>"
                   f"{'' if k in (1, 7) else jornada}</WeekDay>" for k in range(1, 8))
    for e in cfg["calendario"]["excepciones"]:
        dias += (f"<WeekDay><DayType>0</DayType><DayWorking>0</DayWorking><TimePeriod>"
                 f"<FromDate>{e['desde']}T00:00:00</FromDate><ToDate>{e['hasta']}T23:59:00</ToDate></TimePeriod></WeekDay>")
    excep = "".join(f"<Exception><EnteredByOccurrences>0</EnteredByOccurrences><TimePeriod><FromDate>{e['desde']}T00:00:00</FromDate>"
                    f"<ToDate>{e['hasta']}T23:59:00</ToDate></TimePeriod><Occurrences>1</Occurrences>"
                    f"<Name>{escape(e['nombre'])}</Name><Type>1</Type><PeriodCount>1</PeriodCount><DaysOfWeek>0</DaysOfWeek>"
                    f"<MonthItem>0</MonthItem><MonthPosition>0</MonthPosition><Month>0</Month><MonthDay>0</MonthDay>"
                    f"<DayWorking>0</DayWorking></Exception>"
                    for e in cfg["calendario"]["excepciones"])
    calendarios = (f"<Calendars><Calendar><UID>3</UID><Name>{escape(cfg['calendario']['nombre'])}</Name>"
                   f"<IsBaseCalendar>1</IsBaseCalendar><IsBaselineCalendar>0</IsBaselineCalendar><BaseCalendarUID>-1</BaseCalendarUID>"
                   f"<WeekDays>{dias}</WeekDays>"
                   f"<Exceptions>{excep}</Exceptions></Calendar>"
                   + "".join(f"<Calendar><UID>{10 + k}</UID><Name>{escape(r['id'])}</Name><IsBaseCalendar>0</IsBaseCalendar>"
                             f"<BaseCalendarUID>3</BaseCalendarUID></Calendar>"
                             for k, r in enumerate(cfg["recursos"], start=1))
                   + "</Calendars>")

    # ---------------------------------------------------------------- tareas (resumen por la EDT + actividades)
    uid_de: dict[str, int] = {}
    orden: list[tuple[str, str, int]] = []          # (tipo, id, nivel)
    orden.append(("resumen", "H", 1))
    for a in m["filas"]:
        if a["hito"]:
            orden.append(("act", a["id"], 2))
    for n1 in [p for p in edt if "." not in p and p != "0"]:
        orden.append(("resumen", n1, 1))
        for n2 in [p for p in edt if p.startswith(n1 + ".") and p.count(".") == 1]:
            orden.append(("resumen", n2, 2))
            for a in m["filas"]:
                if a.get("paquete") == n2:
                    orden.append(("act", a["id"], 3))
    for k, (_, i, _) in enumerate(orden, start=1):
        uid_de[i] = k

    def hijos(rid: str) -> list[str]:
        if rid == "H":
            return [f["id"] for f in m["filas"] if f["hito"]]
        return [f["id"] for f in m["filas"] if f.get("paquete") and (f["paquete"] == rid or f["paquete"].startswith(rid + "."))]

    tareas, contador = [], {1: 0, 2: 0, 3: 0}
    numero = []
    for tipo, i, nivel in orden:
        contador[nivel] += 1
        for k in range(nivel + 1, 4):
            contador[k] = 0
        numero = ".".join(str(contador[k]) for k in range(1, nivel + 1))
        uid = uid_de[i]
        if tipo == "resumen":
            hs = [filas[h] for h in hijos(i)]
            ini = min(P.fecha(h["inicio"]) for h in hs)
            fin = max(P.fecha(h["fin"]) for h in hs)
            nombre = "Hitos del proyecto" if i == "H" else f"{i} {edt[i]['nombre']}"
            tareas.append("<Task>" + "".join([
                _el("UID", uid), _el("ID", uid), _el("Name", nombre), _el("Type", 1), _el("IsNull", 0),
                _el("WBS", "H" if i == "H" else i), _el("OutlineNumber", numero), _el("OutlineLevel", nivel),
                _el("Start", _t(ini, "08:00")), _el("Finish", _t(fin, "17:00")), _el("DurationFormat", 7),
                _el("Milestone", 0), _el("Summary", 1)]) + "</Task>")
            continue
        f, a = filas[i], acts[i]
        x = cron[i]
        ini = cal.dia(x["S"])
        fin = cal.dia(x["F"] - 1) if not a["hito"] else (cal.dia(x["S"]) if (x["snet"] or not a["preds"]) else cal.dia(x["S"] - 1))
        h_ini, h_fin = ("17:00", "17:00") if a["hito"] and a["preds"] and not x["snet"] else ("08:00", "08:00" if a["hito"] else "17:00")
        dur = 0 if a["hito"] else x["F"] - x["S"]
        partes = [_el("UID", uid), _el("ID", uid), _el("Name", f"{i} {a['nombre']}" if not a["hito"] else f"{i} {a['nombre']}"),
                  _el("Type", 1), _el("IsNull", 0), _el("WBS", i), _el("OutlineNumber", numero), _el("OutlineLevel", nivel),
                  _el("Start", _t(ini if not a["hito"] else fin, h_ini)), _el("Finish", _t(fin, h_fin)),
                  _el("Duration", _dur(dur)), _el("DurationFormat", 7)] +                  ([_el("Work", _horas(sum(a.get("horas", {}).values())))] if not a["hito"] and not a["hecha"] else []) + [
                  _el("EffortDriven", 0), _el("Estimated", 0),
                  _el("Milestone", 1 if a["hito"] else 0), _el("Summary", 0)]
        c = pres["actividades"].get(i)
        if c:      # lo terminado va sin asignaciones (MS Project recalcula su avance desde ellas): su costo, como costo fijo
            fijo = c["total"] if a["hecha"] else c["costo_fijo"]
            partes += [_el("FixedCost", round(fijo * 100)), _el("FixedCostAccrual", 3)]
        partes += [_el("PercentComplete", 100 if a["hecha"] else 0), _el("PercentWorkComplete", 100 if a["hecha"] else 0)]
        if a["hecha"]:
            partes += [_el("ActualStart", _t(ini if not a["hito"] else fin, "08:00")),
                       _el("ActualFinish", _t(fin, "08:00" if a["hito"] else "17:00")),
                       _el("ActualDuration", _dur(dur)), _el("RemainingDuration", _dur(0))]
        if x["snet"]:
            partes += [_el("ConstraintType", 4), _el("ConstraintDate", _t(x["snet"], "08:00"))]
        else:
            partes += [_el("ConstraintType", 0)]
        nota = []
        if a.get("real"):
            nota.append(f"Terminado: commit {a['real']['commit']} del {a['real']['fin']} (main).")
            if a.get("horas"):
                nota.append("Trabajo: " + ", ".join(f"{k} {v} h" for k, v in a["horas"].items())
                            + " (costo registrado como costo fijo: horas del equipo × tarifa S-07).")
        if f.get("costo_fijo_tipo"):
            nota.append(f"Costo fijo: {f['costo_fijo_tipo']} (gestion/e3/plan.py).")
        if nota:
            partes.append(_el("Notes", " ".join(nota)))
        for p, tipo_l, lag in a["preds"]:
            partes.append("<PredecessorLink>" + _el("PredecessorUID", uid_de[p]) + _el("Type", 1 if tipo_l == "FS" else 3)
                          + _el("CrossProject", 0) + _el("LinkLag", lag * 4800) + _el("LagFormat", 7) + "</PredecessorLink>")
        b = lb[i]
        b_ini = cal.dia(b["S"])
        b_fin = cal.dia(b["F"] - 1) if not a["hito"] else (cal.dia(b["S"]) if (b["snet"] or not a["preds"]) else cal.dia(b["S"] - 1))
        partes.append("<Baseline>" + _el("Number", 0) + _el("Start", _t(b_ini if not a["hito"] else b_fin, h_ini))
                      + _el("Finish", _t(b_fin, h_fin)) + _el("Duration", _dur(a["dur"])) + _el("DurationFormat", 7)
                      + (_el("Work", _horas(sum(a.get("horas", {}).values()))) if not a["hito"] else "")
                      + (_el("Cost", round(c["total"] * 100)) if c else "") + "</Baseline>")
        tareas.append("<Task>" + "".join(partes) + "</Task>")

    # ---------------------------------------------------------------- recursos y asignaciones
    rec_uid = {r["id"]: k for k, r in enumerate(cfg["recursos"], start=1)}
    recursos = "".join(
        "<Resource>" + "".join([_el("UID", rec_uid[r["id"]]), _el("ID", rec_uid[r["id"]]), _el("Name", r["nombre"]),
                                _el("Type", 1), _el("IsNull", 0), _el("Initials", r["id"][:3]), _el("MaxUnits", 1 if r["tipo"] == "equipo" else 4),
                                _el("StandardRate", P.tarifa() if r["tipo"] == "equipo" else 0), _el("StandardRateFormat", 2),
                                _el("CalendarUID", 10 + rec_uid[r["id"]])]) + "</Resource>"
        for r in cfg["recursos"])
    asig, k = [], 0
    for i, a in acts.items():
        if a["hito"] or a["hecha"]:
            continue
        x = cron[i]
        ini, fin = cal.dia(x["S"]), cal.dia(x["F"] - 1)
        dur_h = (x["F"] - x["S"]) * 8
        for rid, h in a.get("horas", {}).items():
            k += 1
            partes = [_el("UID", k), _el("TaskUID", uid_de[i]), _el("ResourceUID", rec_uid[rid]),
                      _el("PercentWorkComplete", 0)]
            partes += [_el("Finish", _t(fin, "17:00")), _el("RemainingWork", _horas(h)),
                       _el("Start", _t(ini, "08:00")), _el("Units", round(h / dur_h, 6)), _el("Work", _horas(h))]
            asig.append("<Assignment>" + "".join(partes) + "</Assignment>")

    fin_proy = P.fecha(m["fin"])
    cab = "".join([
        _el("SaveVersion", 14), _el("Name", ruta.name), _el("Title", "Celeris Edge — Plan de gestión del proyecto"),
        _el("Company", "Universidad Peruana Unión — Campus Juliaca"), _el("Author", "Equipo Celeris Edge"),
        _el("ScheduleFromStart", 1), _el("StartDate", _t(P.fecha(m["inicio"]), "08:00")),
        _el("FinishDate", _t(fin_proy, "17:00")), _el("FYStartDate", 1), _el("CriticalSlackLimit", 0),
        _el("CurrencyDigits", 2), _el("CurrencySymbol", "US$"), _el("CurrencyCode", "USD"), _el("CurrencySymbolPosition", 2),
        _el("CalendarUID", 3), _el("DefaultStartTime", "08:00:00"), _el("DefaultFinishTime", "17:00:00"),
        _el("MinutesPerDay", 480), _el("MinutesPerWeek", 2400), _el("DaysPerMonth", 20), _el("DefaultTaskType", 1),
        _el("DefaultFixedCostAccrual", 3), _el("DurationFormat", 7), _el("WorkFormat", 2), _el("EditableActualCosts", 0),
        _el("HonorConstraints", 1), _el("MultipleCriticalPaths", 0), _el("NewTasksEffortDriven", 0),
        _el("NewTasksEstimated", 0), _el("WeekStartDay", 1),
        _el("StatusDate", _t(P.fecha(P.plan()["meta"]["fecha_estado"]), "17:00")),
        _el("CurrentDate", _t(P.fecha(P.plan()["meta"]["fecha_estado"]), "17:00"))])
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Project xmlns="http://schemas.microsoft.com/project">' + cab + calendarios
           + "<Tasks>" + "".join(tareas) + "</Tasks><Resources>" + recursos + "</Resources><Assignments>"
           + "".join(asig) + "</Assignments></Project>\n")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(xml, encoding="utf-8")
    import xml.dom.minidom
    xml.dom.minidom.parseString(ruta.read_bytes())          # XML bien formado
    return ruta


def uids(m: dict) -> dict[int, str]:
    """UID de MS Project → id de la actividad (mismo orden que escribir())."""
    edt = {p["id"]: p for p in cd.cargar()["edt"]["paquetes"]}
    orden = ["H"] + [f["id"] for f in m["filas"] if f["hito"]]
    for n1 in [p for p in edt if "." not in p and p != "0"]:
        orden.append(n1)
        for n2 in [p for p in edt if p.startswith(n1 + ".") and p.count(".") == 1]:
            orden.append(n2)
            orden += [f["id"] for f in m["filas"] if f.get("paquete") == n2]
    return {k: i for k, i in enumerate(orden, start=1)}
