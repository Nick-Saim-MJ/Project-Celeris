"""Gancho V-60+ — XLSX de componentes: 100 % del inventario, IP, zona, criticidad, por qué, aporta y si falla.

Lee entregables/CE0311/Matriz_Componentes_Red_v<versión>.xlsx (lo genera infra/gen/xlsx_componentes.py con `make matrices`):
    V-60  El archivo existe, abre y tiene las 6 hojas.
    V-61  Hoja Matriz: una fila por componente, 1 a 1 con el inventario (ID, nombre, IP planeada, zona, criticidad, estado).
    V-62  Todo componente dibujado en los .drawio (cobertura-figuras.json de P3) está en la matriz, con sus figuras.
    V-63  Ninguna celda obligatoria vacía.
    V-64  Ningún «Por qué existe» repetido entre componentes.
    V-65  Las fórmulas recalculan sin #REF!, #VALUE!, #NAME?… (docs/infra/e1/recalculo-xlsx-componentes.json, del mismo archivo).
    V-66  «Por qué», «Qué aporta» y «Si falla» citan algo verificable (ID, flujo, zona, IP, puerto o cifra) — advertencia.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

GRUPO = "P3"
PRIMER_ID = "V-60"
DESCRIPCION = "XLSX de componentes: 100 % del inventario, IP, zona, criticidad, por qué, aporta y si falla"

_INFRA = Path(__file__).resolve().parents[1]
for _p in (str(_INFRA), str(_INFRA / "gen")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

HOJAS = ["Portada", "Matriz", "Plan de direccionamiento", "Cobertura", "Resumen", "Trazabilidad R6"]
GENERAR = "make matrices (python infra/gen/xlsx_componentes.py --verificar)"


def run(infra):
    from openpyxl import load_workbook
    from validate import E, Resultado, W, estado_de

    import xlsx_componentes as gx

    ruta = gx.SALIDA / f"Matriz_Componentes_Red_v{infra.inv['meta']['inventario_version']}.xlsx"
    rel = ruta.relative_to(infra.raiz).as_posix()
    res = []

    def resultado(cid, titulo, hs, detalle=""):
        res.append(Resultado(cid, titulo, estado_de(hs), hs, detalle))

    h60 = []
    try:
        wb = load_workbook(ruta)
    except FileNotFoundError:
        resultado("V-60", "Matriz de componentes: archivo y hojas", [E(f"No existe {rel}", GENERAR)])
        return res
    except Exception as exc:  # archivo corrupto
        resultado("V-60", "Matriz de componentes: archivo y hojas", [E(f"{rel} no abre: {exc!r}", GENERAR)])
        return res
    faltan = [h for h in HOJAS if h not in wb.sheetnames]
    if faltan:
        h60.append(E(f"Faltan hojas: {', '.join(faltan)}", GENERAR))
    resultado("V-60", "Matriz de componentes: archivo y hojas", h60, rel)
    if "Matriz" not in wb.sheetnames:
        return res

    ws = wb["Matriz"]
    cab = [c.value for c in ws[1]]
    col = {n: cab.index(n) for n in cab if n}
    filas = [r for r in ws.iter_rows(min_row=2, values_only=True) if any(v not in (None, "") for v in r)]
    por_id = {r[col["ID"]]: r for r in filas}

    # V-61: 1 a 1 con el inventario
    h61 = []
    plantilla = ["Componente", "IP planeada", "Zona", "Función", "Criticidad"]
    if cab[:5] != plantilla:
        h61.append(E(f"Las 5 primeras columnas deben ser las de la plantilla {plantilla}; hay {cab[:5]}", GENERAR))
    ids_xlsx = [r[col["ID"]] for r in filas]
    if len(ids_xlsx) != len(set(ids_xlsx)):
        h61.append(E("IDs repetidos en la hoja Matriz", GENERAR))
    for cid in sorted(set(infra.componentes) - set(ids_xlsx)):
        h61.append(E(f"{cid} está en el inventario y falta en la matriz", GENERAR))
    for cid in sorted(set(ids_xlsx) - set(infra.componentes), key=str):
        h61.append(E(f"{cid} está en la matriz y no en el inventario", GENERAR))
    for cid, comp in infra.componentes.items():
        r = por_id.get(cid)
        if not r:
            continue
        esperado = {"Componente": comp["nombre"], "IP planeada": gx.ip_planeada(comp), "Zona": ", ".join(comp["zonas"]),
                    "Criticidad": comp["criticidad"], "Estado": gx.ESTADO.get(comp["estado"], comp["estado"])}
        for campo, valor in esperado.items():
            if (r[col[campo]] or "").replace("\r\n", "\n") != valor:
                h61.append(E(f"{cid}: «{campo}» = {r[col[campo]]!r}; inventario: {valor!r}", GENERAR))
    resultado("V-61", "Matriz 1 a 1 con el inventario (ID, nombre, IP, zona, criticidad, estado)", h61,
              f"{len(filas)} filas · {len(infra.componentes)} componentes en el inventario")

    # V-62: 100 % de lo dibujado
    h62 = []
    cob_json = infra.raiz / "docs" / "infra" / "e1" / "cobertura-figuras.json"
    if not cob_json.exists():
        h62.append(W("No existe docs/infra/e1/cobertura-figuras.json: no se puede cruzar con lo dibujado",
                     "make diagrams-check (P3) y luego make matrices"))
    else:
        cob = json.loads(cob_json.read_text(encoding="utf-8"))
        dibujados = {c for c, figs in cob["componentes"].items() if figs} | {c for v in cob.get("agrupados", {}).values() for c in v}
        for cid in sorted(dibujados - set(ids_xlsx)):
            h62.append(E(f"{cid} está dibujado y no está en la matriz", GENERAR))
        for cid, figs in cob["componentes"].items():
            r = por_id.get(cid)
            if r and (r[col["Figuras donde aparece"]] or "—") != (", ".join(figs) or "—"):
                h62.append(E(f"{cid}: «Figuras donde aparece» = {r[col['Figuras donde aparece']]!r}; dibujado en {figs}", GENERAR))
        if cob_json.stat().st_mtime > ruta.stat().st_mtime + 1:
            h62.append(W("cobertura-figuras.json es más nuevo que la matriz", GENERAR))
    resultado("V-62", "Componentes dibujados en los .drawio = 100 % en la matriz", h62)

    # V-63: celdas obligatorias
    h63 = []
    obligatorias = [n for n, _, ob in gx.COLUMNAS if ob]
    for r in filas:
        for n in obligatorias:
            if r[col[n]] in (None, ""):
                h63.append(E(f"{r[col['ID']]}: «{n}» vacía", "Complete el dato en infra/inventory.yaml o use «—» con motivo"))
    resultado("V-63", "Ninguna celda obligatoria vacía en la hoja Matriz", h63)

    # V-64: por qué único
    h64 = []
    vistos = {}
    for r in filas:
        clave = re.sub(r"\W+", " ", (r[col["Por qué existe"]] or "").lower()).strip()
        if clave in vistos:
            h64.append(E(f"{r[col['ID']]} repite el «Por qué existe» de {vistos[clave]}",
                         "Escriba un por qué específico en infra/inventory.yaml (registre la propuesta en CAMBIOS-INVENTARIO.md)"))
        vistos[clave] = r[col["ID"]]
    resultado("V-64", "Ningún «Por qué existe» repetido", h64)

    # V-65: recálculo
    h65 = []
    rj = gx.RECALCULO_JSON
    sha = hashlib.sha256(ruta.read_bytes()).hexdigest()
    if not rj.exists():
        h65.append(W("La matriz no se ha recalculado nunca", GENERAR))
    else:
        rec = json.loads(rj.read_text(encoding="utf-8"))
        if rec.get("sha256") != sha:
            h65.append(W("El último recálculo es de otra versión del archivo", GENERAR))
        elif not rec.get("motor"):
            h65.append(W(f"No se pudo recalcular (sin LibreOffice ni Excel): {rec.get('nota')}",
                         "Instale LibreOffice (soffice en el PATH) y repita make matrices"))
        else:
            for e in rec.get("errores", []):
                h65.append(E(f"Fórmula con error: {e}", "Corrija la fórmula en infra/gen/xlsx_componentes.py"))
            if rec.get("sin_valor"):
                h65.append(W(f"{rec['sin_valor']} fórmulas sin valor tras recalcular"))
    detalle = ""
    if rj.exists():
        rec = json.loads(rj.read_text(encoding="utf-8"))
        detalle = f"{rec.get('motor') or 'sin motor'} · {rec.get('formulas', 0)} fórmulas · {len(rec.get('errores', []))} errores"
    resultado("V-65", "Las fórmulas recalculan sin errores", h65, detalle)

    # V-66: textos verificables (heurística)
    h66 = []
    claves = set(infra.componentes) | set(infra.zonas) | set(infra.flujos)
    verificable = re.compile(r"\d|\b(?:" + "|".join(re.escape(k) for k in sorted(claves, key=len, reverse=True)) + r")\b")
    for r in filas:
        for n in ("Por qué existe", "Qué aporta al diseño", "Si falla: impacto y mitigación"):
            if not verificable.search(r[col[n]] or ""):
                h66.append(W(f"{r[col['ID']]}: «{n}» no cita ningún ID, flujo, zona, IP, puerto ni cifra",
                             "Propón un texto concreto en CAMBIOS-INVENTARIO.md"))
    resultado("V-66", "«Por qué», «Qué aporta» y «Si falla» citan algo verificable", h66)
    return res
