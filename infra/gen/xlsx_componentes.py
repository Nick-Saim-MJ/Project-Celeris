"""Genera la Matriz de componentes de red del Entregable CE0311 (P4) desde la fuente única infra/*.yaml.

Salida: entregables/CE0311/Matriz_Componentes_Red_v<inventario_version>.xlsx con las hojas
    Portada · Matriz · Plan de direccionamiento · Cobertura · Resumen · Trazabilidad R6 · Retirados en v0.4

- La hoja Matriz trae solo lo vigente (Infra.componentes); lo retirado va a «Retirados en v0.4» con el CI que lo retiró y el
  motivo y el reemplazo de la Arquitectura v0.4 §5 (`retirado_motivo`, `retirado_cubre`, CI-74).

- Todo dato sale de `Infra` (celeris_infra). La columna «Figuras donde aparece» y la hoja Cobertura salen del informe que
  escribe infra/gen/drawio_check.py (docs/infra/e1/cobertura-figuras.json: lo que está DIBUJADO en los .drawio).
- Lo único que decide este módulo es el formato y una regla explícita para «punto único de falla» (ver `relevo_de`).
- `--verificar` abre una copia en Excel (COM, Windows) o LibreOffice headless, recalcula todas las fórmulas y registra
  en docs/infra/e1/recalculo-xlsx-componentes.json si quedó algún #REF!, #VALUE!, #NAME?, #DIV/0! o #N/A (V-65).

    python infra/gen/xlsx_componentes.py [--salida DIR] [--verificar]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from celeris_infra import RAIZ, Infra  # noqa: E402
from drawio import FIGURAS, commit_fuente  # noqa: E402

SALIDA = RAIZ / "entregables" / "CE0311"
COBERTURA_JSON = RAIZ / "docs" / "infra" / "e1" / "cobertura-figuras.json"
RECALCULO_JSON = RAIZ / "docs" / "infra" / "e1" / "recalculo-xlsx-componentes.json"
ERRORES_EXCEL = ("#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "#N/A", "#NUM!", "#NULL!")

# Estado en la matriz (H2): vigente, temporal (solo durante el simulacro T59) o existente / fuera de alcance.
ESTADO = {"diseño": "Vigente", "temporal": "Temporal", "existente": "Existente", "fuera_de_alcance": "Fuera de alcance"}
HOJA_RETIRADOS = "Retirados en v0.4"
CRITICIDADES = ["Alta", "Media", "Baja"]
# Relleno por criticidad (Okabe-Ito aclarado). El texto «Alta/Media/Baja» siempre está en la celda: el color nunca va solo.
RELLENO_CRIT = {"Alta": "F7C9A8", "Media": "FBE3B0", "Baja": "E6E6E6"}

# Columnas de la hoja Matriz: (encabezado, ancho, obligatoria). Las 5 primeras son las de la plantilla DOCX, en su orden.
COLUMNAS = [
    ("Componente", 30, True), ("IP planeada", 28, True), ("Zona", 14, True), ("Función", 30, True), ("Criticidad", 11, True),
    ("ID", 12, True), ("Tipo", 16, True), ("VLAN", 9, True), ("Estado", 14, True),
    ("Por qué existe", 55, True), ("Qué aporta al diseño", 55, True), ("Si falla: impacto y mitigación", 55, True),
    ("Dependencias", 16, True), ("Controles que aplica", 42, True), ("Flujos (F-nn)", 16, True), ("Pruebas (T-xx)", 16, True),
    ("Amenazas que mitiga (AM-xx)", 14, True), ("Objetivos (OD-xx)", 12, True), ("Decisión (D-xx) / Requisito (REQ-…)", 20, True),
    ("Figuras donde aparece", 14, True), ("Supuestos (S-xx)", 11, True), ("Observación abierta (CI-nn)", 14, False),
    ("Zonas (clave de fórmulas)", 18, False),
]
COL = {nombre: i + 1 for i, (nombre, _, _) in enumerate(COLUMNAS)}

FUENTE = Font(name="Calibri", size=11)
NEGRITA = Font(name="Calibri", size=11, bold=True)
CABECERA = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
RELLENO_CAB = PatternFill("solid", fgColor="1A1A1A")
FINO = Side(style="thin", color="BFBFBF")
BORDE = Border(left=FINO, right=FINO, top=FINO, bottom=FINO)
AJUSTE = Alignment(wrap_text=True, vertical="top")


def ordenar_ids(ids) -> list[str]:
    def clave(s):
        m = re.match(r"([A-Z-]+?)-?(\d+)", s)
        return (m.group(1), int(m.group(2))) if m else (s, 0)
    return sorted(set(ids), key=clave)


def lista(valores) -> str:
    v = [str(x) for x in valores if x]
    return ", ".join(v) if v else "—"


def ip_planeada(comp: dict) -> str:
    """Una línea por interfaz («WAN 203.0.113.10», «VLAN 20 10.20.20.1»); rango CIDR si el componente es una red."""
    lineas = []
    if comp.get("cidr"):
        lineas.append(comp["cidr"])
    for i in comp["ips"]:
        iface = i["interfaz"]
        nombre = "WAN" if iface == "wan" else (f"VLAN {iface[4:]}" if re.fullmatch(r"vlan\d+", iface) else iface)
        if i["ip"]:
            lineas.append(f"{nombre} {i['ip']}")
        else:
            lineas.append(f"{nombre}: sin IP ({i.get('nota') or 'sin dato'})")
    if not lineas:
        lineas.append("IP asignadas por AWS (1 por túnel)" if comp["tipo"] == "vpn_gateway" else "sin IP")
    return "\n".join(lineas)


def vlan_de(x: Infra, comp: dict) -> str:
    vl = []
    for z in comp["zonas"]:
        v = x.zonas[z].get("vlan")
        if v is not None and str(v) not in vl:
            vl.append(str(v))
    return ", ".join(vl) if vl else "—"


def pruebas_de(x: Infra, cid: str) -> list[str]:
    flujos = set(x.flujos_de(cid, incluir_zona=False))
    return ordenar_ids(t["id"] for t in x.pruebas.values() if cid in t.get("componentes", []) or flujos & set(t["flujos"]))


def amenazas_de(x: Infra, cid: str) -> list[str]:
    return ordenar_ids(a["id"] for a in x.amenazas.values() if cid in a["componentes"])


def relevo_de(x: Infra, comp: dict) -> list[str]:
    """Componentes que asumen la función de `comp` si falla. Regla explícita y verificable:
    - túneles: el otro túnel de vpn.tuneles (activo ↔ respaldo);
    - el resto: componentes que el texto `si_falla` nombra como relevo («conmuta a X», «réplica en X», «resuelven con X»,
      «usa X», «PAC de X»). Una mitigación de recuperación (restaurar, recrear, BRK01) no es relevo."""
    tuneles = [t["id"] for t in x.inv["vpn"]["tuneles"]]
    if comp["id"] in tuneles:
        return [t for t in tuneles if t != comp["id"]]
    texto = comp["si_falla"]
    patron = r"(?:conmuta a|réplica en|resuelven con|usa|PAC de)\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*)"
    return [c for c in dict.fromkeys(re.findall(patron, texto)) if c in x.componentes and c != comp["id"]]


def cargar_cobertura(x: Infra) -> tuple[dict[str, list[str]], str]:
    if COBERTURA_JSON.exists():
        datos = json.loads(COBERTURA_JSON.read_text(encoding="utf-8"))
        return {c: datos["componentes"].get(c, []) for c in x.componentes}, "dibujado en los .drawio (cobertura-figuras.json, P3)"
    return {c["id"]: list(c["figuras"]) for c in x.componentes.values()}, "campo `figuras` de inventory.yaml (sin informe de P3)"


def autores() -> str:
    try:
        r = subprocess.run(["git", "log", "--format=%an"], cwd=RAIZ, capture_output=True, text=True, check=True)
        return ", ".join(sorted({a.strip() for a in r.stdout.splitlines() if a.strip()}))
    except (OSError, subprocess.CalledProcessError):
        return "—"


# --------------------------------------------------------------------------------------------------
# Hojas
# --------------------------------------------------------------------------------------------------
def cabecera(ws, titulos: list[str], anchos: list[int], fila=1):
    for j, (t, a) in enumerate(zip(titulos, anchos), start=1):
        c = ws.cell(fila, j, t)
        c.font, c.fill, c.border = CABECERA, RELLENO_CAB, BORDE
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        ws.column_dimensions[get_column_letter(j)].width = a
    ws.row_dimensions[fila].height = 45


def celda(ws, f, c, valor, negrita=False):
    x = ws.cell(f, c, valor)
    x.font = NEGRITA if negrita else FUENTE
    x.alignment, x.border = AJUSTE, BORDE
    return x


def imprimir(ws, columnas_repetidas=None, ancho_paginas=1):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = ancho_paginas
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    if columnas_repetidas:
        ws.print_title_cols = columnas_repetidas
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.page_margins.top = ws.page_margins.bottom = 0.5
    ws.oddFooter.center.text = "&A · página &P de &N"


def relleno_cf(color: str) -> PatternFill:
    """Relleno para formato condicional: Excel lee bgColor en los estilos diferenciales (dxf)."""
    return PatternFill("solid", start_color=color, end_color=color, bgColor=color)


def formato_criticidad(ws, rango: str, primera: str):
    for crit, color in RELLENO_CRIT.items():
        ws.conditional_formatting.add(rango, CellIsRule(operator="equal", formula=[f'"{crit}"'],
                                                        fill=relleno_cf(color), font=Font(bold=crit == "Alta")))


def conteo_estados(x: Infra) -> str:
    n = {}
    for c in x.componentes.values():
        e = ESTADO.get(c["estado"], c["estado"])
        n[e] = n.get(e, 0) + 1
    return ", ".join(f"{v} {k.lower()}" for k, v in n.items())


def hoja_portada(wb, x: Infra, fuente_fig: str, nombre: str):
    ws = wb.active
    ws.title = "Portada"
    meta = x.inv["meta"]
    filas = [
        ("Proyecto", meta["proyecto"]),
        ("Entregable", meta["entregable"]),
        ("Documento", f"Matriz de componentes de red · {nombre}"),
        ("Versión del inventario", meta["inventario_version"]),
        ("Fecha del inventario", meta["fecha"]),
        ("Commit de la fuente (infra/*.yaml)", commit_fuente()),
        ("Autores (historial del repositorio)", autores()),
        ("Fuente de los datos", "infra/inventory.yaml, infra/pruebas.yaml, infra/trazabilidad.yaml; generado por "
                                "infra/gen/xlsx_componentes.py (no editar a mano: make matrices lo regenera)"),
        ("Figuras", f"Columna «Figuras donde aparece» y hoja Cobertura: {fuente_fig}"),
        ("Cómo leer la matriz", f"Una fila por componente vigente del inventario ({len(x.componentes)}: {conteo_estados(x)}); los "
                                f"{len(x.componentes_retirados)} retirados en la v0.4 están en la hoja «{HOJA_RETIRADOS}». "
                                "Las cinco primeras columnas son las de la plantilla "
                                "del informe (Componente, IP planeada, Zona, Función, Criticidad). Las siguientes explican por qué "
                                "existe, qué aporta y qué pasa si falla, y lo enlazan con flujos F-nn, pruebas T-xx, amenazas AM-xx, "
                                "objetivos OD-xx, decisiones D-xx, requisitos REQ-…, figuras FIG-x.x y supuestos S-xx. "
                                "Una celda con varias IP lleva una línea por interfaz."),
        ("Criticidad", "Alta: su caída corta un servicio del diseño o su recuperación (borde 3 px y etiqueta ALTA en los diagramas). "
                       "Media: degrada el servicio o la detección (2 px, MEDIA). Baja: sin impacto en el servicio (1 px, BAJA). "
                       "En esta matriz la celda lleva siempre el texto; el color es solo apoyo."),
        ("Estado", "Vigente: componente de este diseño. Temporal: solo existe durante el simulacro de recuperación (T59) y se "
                   "destruye al terminar; no se dibuja en las topologías de operación. Existente: ya está en el campus y se integra. "
                   "Fuera de alcance: existe y se documenta AS-IS, su rediseño no es parte del entregable [S-14]."),
        ("Observación abierta", "CI-nn: contradicción o vacío del documento maestro registrado en docs/infra/e1/CAMBIOS-INVENTARIO.md."),
        ("Supuestos", "Todo supuesto se marca [S-xx]; ninguno se presenta como dato. IP públicas solo de documentación (RFC 5737)."),
    ]
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 110
    t = ws.cell(1, 1, "Matriz de componentes de red — Celeris Edge (CE0311)")
    t.font = Font(name="Calibri", size=16, bold=True)
    for i, (k, v) in enumerate(filas, start=3):
        celda(ws, i, 1, k, negrita=True)
        celda(ws, i, 2, v)
    for crit, color in RELLENO_CRIT.items():
        i = len(filas) + 4 + CRITICIDADES.index(crit)
        c = celda(ws, i, 1, crit, negrita=crit == "Alta")
        c.fill = PatternFill("solid", fgColor=color)
        celda(ws, i, 2, f"Muestra del formato condicional de la columna Criticidad ({crit}).")
    imprimir(ws)
    ws.print_title_rows = None


def hoja_matriz(wb, x: Infra, cob: dict[str, list[str]]):
    ws = wb.create_sheet("Matriz")
    cabecera(ws, [c[0] for c in COLUMNAS], [c[1] for c in COLUMNAS])
    for f, comp in enumerate(x.componentes.values(), start=2):
        cid = comp["id"]
        flujos = sorted(x.flujos_de(cid, incluir_zona=False), key=lambda s: int(s[1:]))
        flujos_txt = lista(flujos) if flujos else f"— ({comp.get('flujos_justificacion') or 'sin flujos propios'})"
        cambio = comp.get("cambio")
        valores = {
            "Componente": comp["nombre"], "IP planeada": ip_planeada(comp), "Zona": ", ".join(comp["zonas"]),
            "Función": comp["funcion"], "Criticidad": comp["criticidad"], "ID": cid, "Tipo": comp["tipo"],
            "VLAN": vlan_de(x, comp), "Estado": ESTADO.get(comp["estado"], comp["estado"]),
            "Por qué existe": comp["por_que"], "Qué aporta al diseño": comp["aporta"],
            "Si falla: impacto y mitigación": comp["si_falla"], "Dependencias": lista(comp["dependencias"]),
            "Controles que aplica": comp["controles"] or "—", "Flujos (F-nn)": flujos_txt,
            "Pruebas (T-xx)": lista(pruebas_de(x, cid)), "Amenazas que mitiga (AM-xx)": lista(amenazas_de(x, cid)),
            "Objetivos (OD-xx)": lista(comp["objetivos"]),
            "Decisión (D-xx) / Requisito (REQ-…)": lista(list(comp["adr"]) + list(comp["req"])),
            "Figuras donde aparece": lista(cob.get(cid, [])), "Supuestos (S-xx)": lista(comp["supuestos"]),
            "Observación abierta (CI-nn)": lista(cambio if isinstance(cambio, list) else [cambio]) if cambio else "—",
            "Zonas (clave de fórmulas)": "," + ",".join(comp["zonas"]) + ",",
        }
        for nombre, j in COL.items():
            celda(ws, f, j, valores[nombre], negrita=nombre in ("Componente", "ID"))
    ultima = len(x.componentes) + 1
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNAS))}{ultima}"
    letra_crit, letra_est = get_column_letter(COL["Criticidad"]), get_column_letter(COL["Estado"])
    dv = DataValidation(type="list", formula1='"' + ",".join(CRITICIDADES) + '"', allow_blank=False, showErrorMessage=True,
                        errorTitle="Criticidad", error="Use Alta, Media o Baja (inventory.yaml)")
    dv.add(f"{letra_crit}2:{letra_crit}{ultima}")
    de = DataValidation(type="list", formula1='"' + ",".join(ESTADO.values()) + '"', allow_blank=False, showErrorMessage=True,
                        errorTitle="Estado", error="Use " + ", ".join(ESTADO.values()))
    de.add(f"{letra_est}2:{letra_est}{ultima}")
    ws.add_data_validation(dv)
    ws.add_data_validation(de)
    formato_criticidad(ws, f"{letra_crit}2:{letra_crit}{ultima}", f"{letra_crit}2")
    ws.conditional_formatting.add(f"{letra_est}2:{letra_est}{ultima}",
                                  CellIsRule(operator="equal", formula=['"Fuera de alcance"'], font=Font(italic=True, color="7F7F7F")))
    ws.column_dimensions[get_column_letter(COL["Zonas (clave de fórmulas)"])].hidden = True
    imprimir(ws, "A:A", ancho_paginas=4)
    return ultima


def hoja_direccionamiento(wb, x: Infra):
    ws = wb.create_sheet("Plan de direccionamiento")
    tit = ["VLAN", "Zona", "CIDR", "Gateway", "Hosts útiles", "Componentes asignados (IP)", "IP asignadas", "IP libres",
           "Confianza", "Propósito"]
    cabecera(ws, tit, [8, 14, 17, 14, 10, 48, 10, 10, 12, 50])
    ips = x.todas_las_ips()
    f = 2
    for z in x.zonas.values():
        if z.get("vlan") is None and not z.get("cidr"):
            continue
        asignadas = [(c, i, ip) for c, i, ip, zz in ips if zz == z["id"]]
        texto = "\n".join(f"{c} ({i}) {ip}" for c, i, ip in asignadas) or "—"
        vals = [z.get("vlan") if z.get("vlan") is not None else "—", z["id"], z.get("cidr") or "—",
                z.get("gateway") or "sin gateway", z.get("hosts_utiles") if z.get("hosts_utiles") is not None else "—",
                texto, len(asignadas), None, z["confianza"], z["proposito"]]
        for j, v in enumerate(vals, start=1):
            celda(ws, f, j, v, negrita=j == 2)
        ws.cell(f, 8).value = f'=IF(ISNUMBER(E{f}),E{f}-G{f},"—")'
        f += 1
    ultima = f - 1
    celda(ws, f, 1, "Total", negrita=True)
    ws.cell(f, 7).value = f"=SUM(G2:G{ultima})"
    ws.cell(f, 8).value = f"=SUM(H2:H{ultima})"
    for j in (7, 8):
        ws.cell(f, j).font, ws.cell(f, j).border = NEGRITA, BORDE
    nota = f + 2
    celda(ws, nota, 1, "Notas", negrita=True)
    celda(ws, nota, 2, "IP libres = hosts útiles − IP asignadas en el inventario (el gateway .1 de FW01 cuenta como asignada). "
                       "Reservas de crecimiento: " + "; ".join(f"{r['id']} {r['cidr']}" for r in x.inv["reservas"]))
    ws.merge_cells(start_row=nota, start_column=2, end_row=nota, end_column=10)
    ws.row_dimensions[nota].height = 45
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:J{ultima}"
    imprimir(ws)


def hoja_cobertura(wb, x: Infra, cob: dict[str, list[str]], fuente_fig: str):
    ws = wb.create_sheet("Cobertura")
    tit = ["ID", "Criticidad"] + FIGURAS + ["¿En ≥ 1 figura?", "Nº flujos", "¿≥ 1 flujo?", "Nº pruebas", "¿≥ 1 prueba?"]
    cabecera(ws, tit, [13, 11] + [9] * len(FIGURAS) + [11, 9, 10, 9, 11])
    n = len(FIGURAS)
    lf, ll = get_column_letter(3), get_column_letter(2 + n)
    c_en, c_nf, c_f, c_np, c_p = (get_column_letter(3 + n + k) for k in range(5))
    for f, comp in enumerate(x.componentes.values(), start=2):
        cid = comp["id"]
        celda(ws, f, 1, cid, negrita=True)
        celda(ws, f, 2, comp["criticidad"])
        for k, fig in enumerate(FIGURAS):
            c = celda(ws, f, 3 + k, "✔" if fig in cob.get(cid, []) else "—")
            c.alignment = Alignment(horizontal="center", vertical="top")
        celda(ws, f, 3 + n, f'=IF(COUNTIF({lf}{f}:{ll}{f},"✔")>0,"Sí","No")')
        celda(ws, f, 4 + n, len(x.flujos_de(cid, incluir_zona=False)))
        celda(ws, f, 5 + n, f'=IF({c_nf}{f}>0,"Sí","No")')
        celda(ws, f, 6 + n, len(pruebas_de(x, cid)))
        celda(ws, f, 7 + n, f'=IF({c_np}{f}>0,"Sí","No")')
    ultima = len(x.componentes) + 1
    t = ultima + 1
    celda(ws, t, 1, "Total ✔ / Sí", negrita=True)
    for k in range(n):
        L = get_column_letter(3 + k)
        celda(ws, t, 3 + k, f'=COUNTIF({L}2:{L}{ultima},"✔")', negrita=True)
    for L, j in ((c_en, 3 + n), (c_f, 5 + n), (c_p, 7 + n)):
        celda(ws, t, j, f'=COUNTIF({L}2:{L}{ultima},"Sí")', negrita=True)
    p = t + 1
    celda(ws, p, 1, "% de cobertura", negrita=True)
    for L, j in ((c_en, 3 + n), (c_f, 5 + n), (c_p, 7 + n)):
        c = celda(ws, p, j, f"={L}{t}/COUNTA($A$2:$A${ultima})", negrita=True)
        c.number_format = "0.0 %"
    r = p + 2
    celda(ws, r, 1, "Componentes", negrita=True)
    celda(ws, r, 2, f"=COUNTA(A2:A{ultima})", negrita=True)
    celda(ws, r + 1, 1, "Fuente", negrita=True)
    celda(ws, r + 1, 2, fuente_fig)
    ws.merge_cells(start_row=r + 1, start_column=2, end_row=r + 1, end_column=2 + n)
    celda(ws, r + 2, 1, "Lectura", negrita=True)
    temporales = [c["id"] for c in x.componentes.values() if c["estado"] == "temporal"]
    celda(ws, r + 2, 2, "«¿≥ 1 flujo?» = No es esperado para redes AWS y equipos sin tráfico propio: la columna Flujos de la "
                        "hoja Matriz da la justificación del inventario. Un componente vigente con «¿En ≥ 1 figura?» = No incumple R6. "
                        + (f"Excepción: {', '.join(temporales)} (estado Temporal) solo existen durante el simulacro T59 y el "
                           "inventario no los asigna a ninguna figura." if temporales else ""))
    ws.merge_cells(start_row=r + 2, start_column=2, end_row=r + 2, end_column=2 + n + 5)
    ws.row_dimensions[r + 2].height = 48
    rango_si = f"{c_en}2:{c_p}{ultima}"
    ws.conditional_formatting.add(rango_si, CellIsRule(operator="equal", formula=['"No"'],
                                                       fill=relleno_cf("FBE3B0"), font=Font(bold=True)))
    formato_criticidad(ws, f"B2:B{ultima}", "B2")
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{c_p}{ultima}"
    imprimir(ws)
    return t, p


def hoja_resumen(wb, x: Infra, ultima_matriz: int):
    ws = wb.create_sheet("Resumen")
    rz = f"Matriz!${get_column_letter(COL['Zonas (clave de fórmulas)'])}$2:${get_column_letter(COL['Zonas (clave de fórmulas)'])}${ultima_matriz}"
    rc = f"Matriz!${get_column_letter(COL['Criticidad'])}$2:${get_column_letter(COL['Criticidad'])}${ultima_matriz}"
    cabecera(ws, ["Zona", "Alta", "Media", "Baja", "Total"], [16, 10, 10, 10, 10])
    zonas = [z for z in x.zonas if any(z in c["zonas"] for c in x.componentes.values())]
    for f, z in enumerate(zonas, start=2):
        celda(ws, f, 1, z, negrita=True)
        for j, crit in enumerate(CRITICIDADES, start=2):
            celda(ws, f, j, f'=COUNTIFS({rz},"*,{z},*",{rc},"{crit}")')
        celda(ws, f, 5, f"=SUM(B{f}:D{f})", negrita=True)
    fz = len(zonas) + 2
    celda(ws, fz, 1, "Por criticidad (componentes únicos)", negrita=True)
    for j, crit in enumerate(CRITICIDADES, start=2):
        celda(ws, fz, j, f'=COUNTIFS({rc},"{crit}")', negrita=True)
    celda(ws, fz, 5, f"=SUM(B{fz}:D{fz})", negrita=True)
    multi = [c["id"] for c in x.componentes.values() if len(c["zonas"]) > 1]
    celda(ws, fz + 1, 1, f"Nota: un componente con interfaces en varias zonas ({', '.join(multi) or 'ninguno'}) cuenta en cada "
                         "una; la fila «Por criticidad» cuenta cada componente una vez.")
    ws.merge_cells(start_row=fz + 1, start_column=1, end_row=fz + 1, end_column=5)
    ws.row_dimensions[fz + 1].height = 45

    # Componentes de criticidad Alta: puntos únicos de falla y cómo se cubren
    f0 = fz + 3
    tit = ["ID", "Componente", "Zona", "¿Otro componente asume su función?", "Punto único de falla", "Si falla: impacto y mitigación"]
    anchos = [12, 30, 14, 26, 14, 80]
    for j, (t, a) in enumerate(zip(tit, anchos), start=1):
        c = ws.cell(f0, j, t)
        c.font, c.fill, c.border = CABECERA, RELLENO_CAB, BORDE
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        ws.column_dimensions[get_column_letter(j)].width = max(ws.column_dimensions[get_column_letter(j)].width or 0, a)
    f = f0 + 1
    for comp in x.componentes.values():
        if comp["criticidad"] != "Alta":
            continue
        relevo = relevo_de(x, comp)
        vals = [comp["id"], comp["nombre"], ", ".join(comp["zonas"]), ", ".join(relevo) if relevo else "Ninguno",
                "No" if relevo else "Sí", comp["si_falla"]]
        for j, v in enumerate(vals, start=1):
            celda(ws, f, j, v, negrita=j == 1)
        f += 1
    ws.conditional_formatting.add(f"E{f0 + 1}:E{f - 1}", CellIsRule(operator="equal", formula=['"Sí"'],
                                                                    fill=relleno_cf(RELLENO_CRIT["Alta"]),
                                                                    font=Font(bold=True)))
    celda(ws, f, 1, "Total", negrita=True)
    celda(ws, f, 5, f'=COUNTIF(E{f0 + 1}:E{f - 1},"Sí")', negrita=True)
    celda(ws, f + 1, 1, "Regla: «Punto único de falla» = Sí cuando ningún otro componente asume la función. Se toma del inventario: "
                        "el otro túnel de vpn.tuneles, o el componente que `si_falla` nombra como relevo (conmuta a, réplica en, "
                        "resuelven con, usa, PAC de). Restaurar, recrear o entrar por BRK01 es recuperación, no relevo.")
    ws.merge_cells(start_row=f + 1, start_column=1, end_row=f + 1, end_column=6)
    ws.row_dimensions[f + 1].height = 48
    ws.freeze_panes = "B2"
    imprimir(ws)


def hoja_r6(wb, x: Infra, t_cob: int, p_cob: int, ultima_matriz: int):
    ws = wb.create_sheet("Trazabilidad R6")
    r6 = x.rubrica["R6"]
    n = len(FIGURAS)
    c_en = get_column_letter(3 + n)
    cabecera(ws, ["Exigencia de R6 (nivel 4)", "Cómo la cumple esta matriz", "Dónde se ve", "Comprobación"], [40, 70, 40, 22])
    filas = [
        ("Matriz de componentes que cubre el 100 % de lo dibujado en las topologías",
         "Una fila por componente del inventario; los componentes de los .drawio se cruzan con la matriz (V-62) y la hoja "
         "Cobertura marca en qué figura está cada uno.", "Hojas Matriz y Cobertura; informe sección 5.6",
         f"=TEXT(Cobertura!{c_en}{p_cob},\"0.0 %\")&\" en ≥ 1 figura\""),
        ("Con IP planeada", "Columna «IP planeada» (una línea por interfaz) y hoja Plan de direccionamiento.",
         "Matriz, columna B; hoja Plan de direccionamiento",
         f"=COUNTIF(Matriz!B2:B{ultima_matriz},\"?*\")&\" de \"&COUNTA(Matriz!F2:F{ultima_matriz})&\" con IP o motivo\""),
        ("Con criticidad", "Columna «Criticidad» con validación de datos (Alta/Media/Baja) y formato que muestra el texto.",
         "Matriz, columna E; hoja Resumen",
         f"=COUNTIF(Matriz!E2:E{ultima_matriz},\"?*\")&\" de \"&COUNTA(Matriz!F2:F{ultima_matriz})"),
        ("Diagrama de flujo con protocolos y puertos completo",
         "La columna «Flujos (F-nn)» enlaza cada componente con FIG-5.5a/5.5b, donde cada F-nn lleva protocolo, puerto y protección.",
         "FIG-5.5a, FIG-5.5b; informe sección 5.5", "—"),
    ]
    f = 2
    for fila in filas:
        for j, v in enumerate(fila, start=1):
            celda(ws, f, j, v, negrita=j == 1)
        f += 1
    f += 1
    celda(ws, f, 1, f"Criterio {r6['nombre']} (peso {r6['peso']} %)", negrita=True)
    celda(ws, f, 2, r6["descriptor_nivel_4"])
    ws.merge_cells(start_row=f, start_column=2, end_row=f, end_column=4)
    ws.row_dimensions[f].height = 34
    f += 2
    celda(ws, f, 1, "Evidencias declaradas en trazabilidad.yaml", negrita=True)
    f += 1
    for ev in r6["evidencias"]:
        celda(ws, f, 1, ev["tipo"])
        celda(ws, f, 2, ev["ref"] + (f" — {ev['detalle']}" if ev.get("detalle") else ""))
        f += 1
    ws.freeze_panes = "A2"
    imprimir(ws)


def hoja_retirados(wb, x: Infra):
    ws = wb.create_sheet(HOJA_RETIRADOS)
    cabecera(ws, ["ID", "Componente", "Retirado por (CI-nn)", "Motivo (Arquitectura v0.4 §5)", "Qué cubre ahora su función",
                  "Criticidad que tenía"], [13, 40, 14, 70, 40, 12])
    f = 1
    for f, c in enumerate(x.componentes_retirados.values(), start=2):
        vals = [c["id"], c["nombre"], c["retirado_por"],
                c.get("retirado_motivo") or f"— (la §5 no da motivo; retirado por {c['retirado_por']}; ver CI-74)",
                c.get("retirado_cubre") or "—", c.get("criticidad") or "—"]
        for j, v in enumerate(vals, start=1):
            celda(ws, f, j, v, negrita=j == 1)
    nota = f + 2
    celda(ws, nota, 1, "Regla", negrita=True)
    celda(ws, nota, 2, "Un ID retirado conserva su entrada en infra/inventory.yaml con `estado: retirado` y nunca se reutiliza "
                       "(V-44); no aparece en la hoja Matriz ni en ninguna figura (V-52). Detalle de cada CI en "
                       "docs/infra/e1/CAMBIOS-INVENTARIO.md.")
    ws.merge_cells(start_row=nota, start_column=2, end_row=nota, end_column=6)
    ws.row_dimensions[nota].height = 32
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:F{max(f, 2)}"
    imprimir(ws)


# --------------------------------------------------------------------------------------------------
def generar(x: Infra, salida: Path = SALIDA) -> Path:
    salida.mkdir(parents=True, exist_ok=True)
    nombre = f"Matriz_Componentes_Red_v{x.inv['meta']['inventario_version']}.xlsx"
    cob, fuente_fig = cargar_cobertura(x)
    wb = Workbook()
    hoja_portada(wb, x, fuente_fig, nombre)
    ultima = hoja_matriz(wb, x, cob)
    hoja_direccionamiento(wb, x)
    t, p = hoja_cobertura(wb, x, cob, fuente_fig)
    hoja_resumen(wb, x, ultima)
    hoja_r6(wb, x, t, p, ultima)
    hoja_retirados(wb, x)
    wb.calculation.fullCalcOnLoad = True
    wb.properties.title = "Matriz de componentes de red — CE0311"
    wb.properties.creator = "infra/gen/xlsx_componentes.py"
    ruta = salida / nombre
    wb.save(ruta)
    return ruta


# --------------------------------------------------------------------------------------------------
# Recalcular en Excel o LibreOffice y buscar errores de fórmula (V-65)
# --------------------------------------------------------------------------------------------------
def _recalcular_excel(origen: Path, destino: Path) -> None:
    ps = (f"$ErrorActionPreference='Stop'; $x=New-Object -ComObject Excel.Application; $x.Visible=$false; $x.DisplayAlerts=$false; "
          f"try {{ $wb=$x.Workbooks.Open('{origen}'); $x.CalculateFull(); $wb.SaveAs('{destino}', 51); $wb.Close($false) }} "
          f"finally {{ $x.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($x) }}")
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not destino.exists():
        raise RuntimeError(r.stderr.strip() or "Excel no guardó la copia recalculada")


def _recalcular_libreoffice(exe: str, origen: Path, destino: Path) -> None:
    out = destino.parent / "lo"
    out.mkdir(exist_ok=True)
    r = subprocess.run([exe, "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(out), str(origen)],
                       capture_output=True, text=True, timeout=180)
    hecho = out / origen.name
    if r.returncode != 0 or not hecho.exists():
        raise RuntimeError(r.stderr.strip() or "LibreOffice no convirtió el archivo")
    shutil.move(hecho, destino)


def verificar(ruta: Path) -> dict:
    sha = hashlib.sha256(ruta.read_bytes()).hexdigest()
    resultado = {"archivo": ruta.relative_to(RAIZ).as_posix(), "sha256": sha, "motor": None, "formulas": 0, "errores": [],
                 "sin_valor": 0, "nota": ""}
    lo = shutil.which("soffice") or shutil.which("libreoffice")
    with tempfile.TemporaryDirectory() as tmp:
        origen = Path(tmp) / ruta.name
        shutil.copy(ruta, origen)
        destino = Path(tmp) / ("recalc_" + ruta.name)
        try:
            if lo:
                _recalcular_libreoffice(lo, origen, destino)
                resultado["motor"] = "LibreOffice headless"
            elif sys.platform == "win32":
                _recalcular_excel(origen, destino)
                resultado["motor"] = "Microsoft Excel (COM)"
            else:
                raise RuntimeError("no hay LibreOffice ni Excel")
        except Exception as exc:  # sin motor: se informa, no se simula
            resultado["nota"] = f"No se pudo recalcular: {exc}"
            return resultado
        formulas = load_workbook(ruta)
        valores = load_workbook(destino, data_only=True)
        for ws in formulas.worksheets:
            wv = valores[ws.title]
            for fila in ws.iter_rows():
                for c in fila:
                    if isinstance(c.value, str) and c.value.startswith("="):
                        resultado["formulas"] += 1
                        v = wv[c.coordinate].value
                        if v is None:
                            resultado["sin_valor"] += 1
                        elif isinstance(v, str) and v.strip() in ERRORES_EXCEL:
                            resultado["errores"].append(f"{ws.title}!{c.coordinate} = {v} ({c.value})")
    return resultado


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--verificar", action="store_true", help="recalcula una copia y registra errores de fórmula (V-65)")
    a = ap.parse_args(argv)
    x = Infra.cargar()
    ruta = generar(x, Path(a.salida))
    print(ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta)
    if a.verificar:
        res = verificar(ruta)
        RECALCULO_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"recálculo: {res['motor'] or 'sin motor'} · {res['formulas']} fórmulas · {len(res['errores'])} errores · "
              f"{res['sin_valor']} sin valor {res['nota']}")
        if res["errores"]:
            for e in res["errores"]:
                print("  ", e)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
