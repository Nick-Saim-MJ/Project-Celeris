"""Gancho V-70+ — XLSX de pruebas (P4): filas, referencias, cobertura, ensayo en laboratorio emulado, fórmulas y actualidad.

Lee el XLSX generado (entregables/CE0311/Matriz_Pruebas_Conectividad_v<versión>.xlsx) y lo compara con infra/pruebas.yaml, inventory.yaml y
el último evidencias/*/resultados.json. Cada función de chequeo recibe el libro ya cargado para poder probarse con libros alterados.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import openpyxl

import celeris_infra as ci
from gen import xlsx_pruebas as xp

GRUPO = "P4"
PRIMER_ID = "V-70"
DESCRIPCION = "XLSX de pruebas: filas = pruebas del YAML, referencias, cobertura, ensayo L, fórmulas sin errores y al día"

ERRORES_EXCEL = ("#DIV/0!", "#N/A", "#NAME?", "#NULL!", "#NUM!", "#REF!", "#VALUE!", "Err:")


# ------------------------------------------------------------------------------------------------ utilidades
def _validate():
    """Las clases de resultado viven en validate.py; se importan al ejecutar para no crear un ciclo al cargar el módulo."""
    import validate
    return validate


def filas_de_matriz(wb) -> list[dict]:
    """Filas de la hoja «Matriz» como {clave de columna: valor}."""
    ws = wb["Matriz"]
    claves = [c[0] for c in xp.COLUMNAS]
    filas = []
    for r in range(xp.FILA_ENC + 1, ws.max_row + 1):
        if ws.cell(row=r, column=xp.IDX["id"]).value in (None, ""):
            continue
        filas.append({k: ws.cell(row=r, column=i).value for i, k in enumerate(claves, start=1)} | {"_fila": r})
    return filas


def cargar_libro(x: ci.Infra):
    ruta = xp.ruta_salida(x)
    if not ruta.exists():
        return None, ruta
    return openpyxl.load_workbook(ruta), ruta


def _cadena(v) -> str:
    return "" if v is None else str(v)


def _lista(valor) -> list[str]:
    return [p.strip() for p in _cadena(valor).split(",") if p.strip()]


# ------------------------------------------------------------------------------------------------ chequeos (devuelven (nivel, mensaje, cómo corregir))
def chequeo_filas(x: ci.Infra, wb) -> list[tuple[str, str, str]]:
    r = []
    if wb.sheetnames != xp.HOJAS:
        r.append(("error", f"Hojas {wb.sheetnames} en lugar de {xp.HOJAS}", "Regenere con make matrices"))
        return r
    filas = filas_de_matriz(wb)
    ids = [f["id"] for f in filas]
    esperadas = set(x.pruebas)
    for tid in sorted(esperadas - set(ids), key=lambda s: int(s[1:])):
        r.append(("error", f"{tid} está en pruebas.yaml y no tiene fila en «Matriz»", "Regenere con make matrices"))
    for tid in sorted(set(ids) - esperadas):
        r.append(("error", f"«Matriz» tiene una fila de {tid}, que no está en pruebas.yaml", "Regenere con make matrices"))
    for tid in sorted({i for i in ids if ids.count(i) > 1}):
        r.append(("error", f"{tid} aparece más de una vez en «Matriz»", "Regenere con make matrices"))
    for f in filas:
        t = x.pruebas.get(f["id"])
        if not t:
            continue
        esperado = {
            "plantilla": t["nombre"], "esperado": t["resultado_esperado"], "comando": t["comando"], "modos": ", ".join(t["modos"]),
            "origen": xp._origen_destino(t["origen"]), "destino": xp._origen_destino(t["destino"]), "categoria": t["categoria"],
            "polaridad": xp.POLARIDAD[t["polaridad"]], "critica": "Sí" if t["critica"] else "No",
        }
        for k, v in esperado.items():
            if _cadena(f[k]) != v:
                r.append(("error", f"{f['id']}: «{k}» difiere de pruebas.yaml ({_cadena(f[k])[:50]!r} ≠ {v[:50]!r})", "Regenere con make matrices"))
        for clave in ("plantilla", "esperado", "comando", "criterio", "evidencia", "valida", "precondicion"):
            if not _cadena(f[clave]).strip():
                r.append(("error", f"{f['id']}: la columna «{clave}» está vacía", "Complete el campo en pruebas.yaml y regenere"))
        if _cadena(f["s2"]).strip():
            r.append(("advertencia", f"{f['id']}: «Resultado S2» ya tiene valor; debe quedar vacío hasta CE0313", "Déjelo vacío en el entregable de S1"))
    return r


def chequeo_referencias(x: ci.Infra, wb) -> list[tuple[str, str, str]]:
    r = []
    for f in filas_de_matriz(wb):
        for fid in re.findall(r"\bF\d+\b", _cadena(f["flujos"])):
            if fid not in x.flujos:
                r.append(("error", f"{f['id']}: cita el flujo {fid}, que no existe en el inventario", "Corrija `flujos` en pruebas.yaml"))
        for cid in _lista(f["componentes"]):
            if cid not in x.componentes:
                r.append(("error", f"{f['id']}: cita el componente {cid}, que no existe en el inventario", "Corrija `componentes` en pruebas.yaml"))
        for col, conjunto, tipo in (("od", x.objetivos, "objetivo"), ("am", x.amenazas, "amenaza"), ("det", x.detecciones, "detección"), ("rubrica", x.rubrica, "criterio de rúbrica")):
            for ref in _lista(f[col]):
                if ref not in conjunto:
                    r.append(("error", f"{f['id']}: cita {tipo} {ref}, que no existe", "Corrija pruebas.yaml"))
    return r


def chequeo_cobertura(x: ci.Infra) -> list[tuple[str, str, str]]:
    """100 % de flujos permitidos con prueba positiva y de bloqueos con prueba negativa; celdas críticas, OD, AM, DET, R3/R4 con ≥ 1 prueba."""
    r = []
    cob = x.cobertura_de_pruebas()
    exigidas = ["Flujos permitidos con prueba positiva", "Flujos bloqueados con prueba negativa", "Celdas permitidas con prueba positiva",
                "Celdas denegadas críticas con prueba negativa", "Objetivos OD con ≥ 1 prueba", "Amenazas AM con ≥ 1 prueba",
                "Detecciones DET con ≥ 1 prueba", "Criterios de rúbrica con ≥ 1 prueba", "Elementos evaluados de R3 y R4 con ≥ 1 prueba"]
    for nombre in exigidas:
        d = cob[nombre]
        if d["faltan"]:
            r.append(("error", f"{nombre}: {d['cubiertos']} de {d['total']}; faltan {', '.join(d['faltan'][:15])}{'…' if len(d['faltan']) > 15 else ''}",
                      "Agregue la prueba (T-nn) en pruebas.yaml y registre la ampliación en CAMBIOS-INVENTARIO.md"))
    todas = cob["Celdas denegadas (todas) con prueba negativa"]
    r.append(("info", f"Celdas denegadas no críticas sin prueba dedicada: {len(todas['faltan'])} de {todas['total']} (las cubre la política deny-all; ver hoja «Cobertura»)", ""))
    return r


def chequeo_ensayo(x: ci.Infra, wb, datos: dict | None) -> list[tuple[str, str, str]]:
    """Una FALLA del ensayo L lleva causa y acción; NO_APLICA, PARCIAL y la ausencia de ensayo no se presentan como PASA."""
    r = []
    resultados = {z["id"]: z["resultado"] for z in (datos or {}).get("resultados", [])}
    for f in filas_de_matriz(wb):
        real = resultados.get(f["id"], "SIN ENSAYO")
        mostrado = _cadena(f["l_res"])
        if mostrado == "PASA" and real != "PASA":
            r.append(("error", f"{f['id']}: la matriz muestra PASA en el ensayo L y resultados.json dice {real}", "Regenere con make matrices; PARCIAL y NO_APLICA no son PASA"))
        elif mostrado != real:
            r.append(("error", f"{f['id']}: la matriz muestra {mostrado} y resultados.json dice {real}", "Regenere con make matrices"))
        if real == "FALLA":
            obs = _cadena(f["obs"])
            if "Causa:" not in obs or "Acción:" not in obs or "SIN DEFINIR" in obs:
                r.append(("error", f"{f['id']}: FALLA en el ensayo L sin observación que explique la causa y la acción",
                          "Agregue `observacion_ensayo: {causa, accion}` a la prueba en pruebas.yaml y regenere"))
    if datos is None:
        r.append(("advertencia", "No hay evidencias/*/resultados.json: la matriz muestra SIN ENSAYO en todas las pruebas", "Ejecute make test-lab"))
    return r


def _soffice() -> str | None:
    for nombre in ("soffice", "libreoffice"):
        ruta = shutil.which(nombre)
        if ruta:
            return ruta
    return None


def recalcular(ruta: Path, salida: Path) -> Path | None:
    """Abre el XLSX con LibreOffice headless y lo guarda con los valores de las fórmulas calculados."""
    exe = _soffice()
    if not exe:
        return None
    perfil = Path(tempfile.mkdtemp(prefix="lo-perfil-"))
    try:
        subprocess.run([exe, f"-env:UserInstallation={perfil.as_uri()}", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(salida), str(ruta)],
                       check=True, capture_output=True, timeout=180)
    except (subprocess.SubprocessError, OSError):
        return None
    finally:
        shutil.rmtree(perfil, ignore_errors=True)
    resultado = salida / ruta.name
    return resultado if resultado.exists() else None


def chequeo_formulas(x: ci.Infra, ruta: Path, datos: dict | None) -> list[tuple[str, str, str]]:
    r = []
    wb_f = openpyxl.load_workbook(ruta)
    n_formulas = sum(1 for ws in wb_f for fila in ws.iter_rows() for c in fila if isinstance(c.value, str) and c.value.startswith("="))
    if n_formulas == 0:
        r.append(("error", "El XLSX no tiene fórmulas: los porcentajes de cobertura deben calcularse con fórmulas", "Regenere con make matrices"))
    with tempfile.TemporaryDirectory(prefix="xlsx-recalculo-") as d:
        rec = recalcular(ruta, Path(d))
        if rec is None:
            r.append(("advertencia", f"LibreOffice no está disponible o falló: no se recalcularon las {n_formulas} fórmulas", "Instale libreoffice-calc (el CI lo hace) y vuelva a ejecutar"))
            return r
        wb = openpyxl.load_workbook(rec, data_only=True)
        for ws in wb:
            for fila in ws.iter_rows():
                for c in fila:
                    if isinstance(c.value, str) and c.value.startswith(ERRORES_EXCEL):
                        r.append(("error", f"{ws.title}!{c.coordinate}: la fórmula da {c.value}", "Corrija la fórmula en infra/gen/xlsx_pruebas.py"))
        # Lo que dicen las fórmulas debe coincidir con lo que calcula la biblioteca
        cob = x.cobertura_de_pruebas()
        ws = wb["Cobertura"]
        filas = {ws.cell(row=i, column=1).value: (ws.cell(row=i, column=2).value, ws.cell(row=i, column=4).value) for i in range(5, 15)}
        pares = {
            "Flujos permitidos con prueba positiva": "Flujos permitidos con prueba positiva",
            "Flujos bloqueados con prueba negativa": "Flujos bloqueados con prueba negativa",
            "Celdas permitidas con prueba positiva": "Celdas permitidas con prueba positiva",
            "Celdas denegadas críticas con prueba negativa": "Celdas denegadas críticas con prueba negativa",
            "Celdas denegadas (todas) con prueba negativa": "Celdas denegadas (todas) con prueba negativa",
            "Criterios de rúbrica evaluables con prueba": "Criterios de rúbrica con ≥ 1 prueba",
            "Elementos evaluados de R3 y R4": "Elementos evaluados de R3 y R4 con ≥ 1 prueba",
            "Objetivos (OD)": "Objetivos OD con ≥ 1 prueba", "Amenazas (AM)": "Amenazas AM con ≥ 1 prueba", "Detecciones (DET)": "Detecciones DET con ≥ 1 prueba",
        }
        for fila, dim in pares.items():
            if fila not in filas:
                r.append(("error", f"Cobertura: falta la fila «{fila}» del resumen", "Regenere con make matrices"))
                continue
            cubiertos, total = filas[fila]
            if (cubiertos, total) != (cob[dim]["cubiertos"], cob[dim]["total"]):
                r.append(("error", f"Cobertura «{fila}»: la hoja calcula {cubiertos}/{total} y la biblioteca {cob[dim]['cubiertos']}/{cob[dim]['total']}", "Regenere con make matrices"))
        # El conteo del ensayo L de la hoja coincide con resultados.json
        resultados = [z["resultado"] for z in (datos or {}).get("resultados", [])]
        esperados = {e: resultados.count(e) for e in ("PASA", "FALLA", "PARCIAL", "NO_APLICA")}
        esperados["SIN ENSAYO"] = len(x.pruebas) - len(resultados)
        we = wb["Ensayo L"]
        for i in range(5, 10):
            estado, n = we.cell(row=i, column=1).value, we.cell(row=i, column=2).value
            if estado in esperados and n != esperados[estado]:
                r.append(("error", f"Ensayo L: la hoja cuenta {n} en {estado} y resultados.json {esperados[estado]}", "Regenere con make matrices"))
        r.append(("info", f"{n_formulas} fórmulas recalculadas con LibreOffice sin errores" if not any(h[0] == "error" for h in r) else f"{n_formulas} fórmulas recalculadas con LibreOffice", ""))
    return r


def _valores(wb) -> dict:
    return {(ws.title, c.coordinate): c.value for ws in wb for fila in ws.iter_rows() for c in fila if c.value not in (None, "")}


def chequeo_actualidad(x: ci.Infra, wb_actual) -> list[tuple[str, str, str]]:
    """El libro versionado tiene los mismos valores y fórmulas que el que se generaría hoy (se compara el contenido, no los bytes)."""
    nuevo = xp.construir(x)
    a, b = _valores(wb_actual), _valores(nuevo)
    difs = [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
    if difs:
        ej = ", ".join(f"{h}!{c}" for h, c in difs[:5])
        return [("error", f"El XLSX versionado no coincide con lo que generaría el inventario ({len(difs)} celdas; p. ej. {ej})", "Regenere con make matrices y commitee el resultado")]
    return []


# ------------------------------------------------------------------------------------------------ gancho
def _resultado(v, cid, titulo, hallazgos):
    hs = []
    for nivel, msg, fix in hallazgos:
        hs.append(v.E(msg, fix) if nivel == "error" else v.W(msg, fix) if nivel == "advertencia" else v.I(msg))
    return v.Resultado(cid, titulo, v.estado_de(hs), hs)


def run(infra):
    v = _validate()
    wb, ruta = cargar_libro(infra)
    if wb is None:
        h = [("error", f"No existe {ruta.relative_to(infra.raiz)}", "Genérelo con make matrices y versiónelo")]
        return [_resultado(v, PRIMER_ID, "XLSX de pruebas: existe y tiene una fila por prueba del YAML", h)]
    _, datos = ci.resultados_mas_recientes(infra.raiz)
    return [
        _resultado(v, "V-70", "XLSX de pruebas: hojas y una fila por prueba del YAML, con sus datos", chequeo_filas(infra, wb)),
        _resultado(v, "V-71", "XLSX de pruebas: cada prueba cita flujos, componentes, OD, AM, DET y criterios de rúbrica existentes", chequeo_referencias(infra, wb)),
        _resultado(v, "V-72", "Cobertura: 100 % de flujos permitidos con prueba positiva, de bloqueos y celdas críticas con prueba negativa; OD, AM, DET y R3/R4 con ≥ 1 prueba",
                   chequeo_cobertura(infra)),
        _resultado(v, "V-73", "Ensayo L: ninguna FALLA sin causa y acción; NO_APLICA, PARCIAL y sin ensayo nunca como PASA", chequeo_ensayo(infra, wb, datos)),
        _resultado(v, "V-74", "XLSX de pruebas: fórmulas sin errores tras recalcular con LibreOffice y coherentes con la biblioteca", chequeo_formulas(infra, ruta, datos)),
        _resultado(v, "V-75", "XLSX de pruebas: el archivo versionado está al día con pruebas.yaml, el inventario y el último ensayo", chequeo_actualidad(infra, wb)),
    ]
