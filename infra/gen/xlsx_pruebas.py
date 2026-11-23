"""Matriz de pruebas de conectividad planeadas (XLSX) — Entregable CE0311, criterios R3 y R4.

Se genera desde infra/pruebas.yaml (+ inventory.yaml, trazabilidad.yaml) y, para la columna «Ensayo en laboratorio emulado», desde el
evidencias/*/resultados.json más reciente. Reproducible: mismas entradas, mismos bytes. Las pruebas son PLANEADAS para S2; el ensayo del
Modo L es emulado y no es la implementación.

    python infra/genera.py xlsx-pruebas        (o: make matrices)
"""
from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import celeris_infra as ci  # noqa: E402
from celeris_infra import Infra  # noqa: E402
from gen import xlsx_comun as xc  # noqa: E402

CATEGORIAS = ["conectividad", "segmentacion", "vpn", "seguridad_web", "deteccion", "disponibilidad", "privacidad", "cifrado"]
POLARIDAD = {"positiva": "Positiva", "negativa": "Negativa", "mixta": "Mixta"}
MARCA = {"positiva": "P", "negativa": "N", "mixta": "M"}
RESULTADOS_L = ["PASA", "FALLA", "PARCIAL", "NO_APLICA", "SIN ENSAYO"]
RESULTADOS_S2 = ["PASA", "FALLA", "NO_APLICA", "PENDIENTE"]
HOJAS = ["Portada", "Matriz", "Segmentación", "Cobertura", "VPN", "Ensayo L"]
ROTULO_EMULADO = "Laboratorio emulado — no es la implementación de S2"
SUBDIR = Path("entregables") / "CE0311"

# Columnas de «Matriz» (clave, encabezado, ancho). Las dos primeras son las de la plantilla del DOCX (sección 6).
COLUMNAS = [
    ("plantilla", "Prueba de conectividad planeada", 30), ("esperado", "Resultado esperado", 36),
    ("id", "ID", 7), ("procedencia", "Procedencia", 15), ("categoria", "Categoría", 15), ("polaridad", "Polaridad", 11),
    ("critica", "Crítica", 8), ("origen", "Origen", 18), ("destino", "Destino", 22), ("flujos", "Flujos (F-nn)", 22),
    ("componentes", "Componentes", 24), ("valida", "Qué valida", 40), ("precondicion", "Precondición", 40),
    ("comando", "Comando / procedimiento", 52), ("criterio", "Criterio de aprobación", 58), ("evidencia", "Evidencia a capturar", 40),
    ("modos", "Modos", 10), ("semestre", "Semestre", 9), ("rubrica", "Criterio de rúbrica", 12), ("od", "Objetivo (OD)", 14),
    ("am", "Amenaza (AM)", 14), ("det", "Detección (DET)", 14),
    ("l_res", "Ensayo L (emulado): resultado", 14), ("l_medido", "Ensayo L: valor medido", 30), ("l_fecha", "Ensayo L: fecha", 12),
    ("l_archivo", "Ensayo L: archivo de evidencia", 38), ("s2", "Resultado S2 (CE0313)", 14), ("obs", "Observaciones", 60),
]
IDX = {k: i for i, (k, _, _) in enumerate(COLUMNAS, start=1)}
FILA_ENC = 3                      # fila del encabezado en «Matriz»

# Parámetros de D1.10 que verifica cada prueba de la hoja «VPN»: (texto, función del inventario que devuelve el valor).
def _v(x): return x.inv["vpn"]


PARAMETROS_VPN = {
    "T01": [("Ruta ON-PREM → AWS por el túnel activo", lambda x: f"{_v(x)['extremo_onpremise']['redes_anunciadas'][0]} → {_v(x)['extremo_aws']['redes_anunciadas'][0]}; túnel activo {_v(x)['tuneles'][0]['red_interna']}"),
            ("ASN de cada extremo (BGP)", lambda x: f"{_v(x)['extremo_onpremise']['asn']} (campus) y {_v(x)['extremo_aws']['asn']} (AWS)")],
    "T02": [("Sentido AWS → ON-PREM: solo lo que F30 permite", lambda x: f"F30: {x.flujos['F30']['protocolos'][0]['proto']}/{x.flujos['F30']['protocolos'][0]['puertos'][0]} desde EC2-GW hacia CTRL01"),
            ("Protección de F30", lambda x: x.flujos["F30"]["proteccion"]["tipo"])],
    "T03": [("Zonas no autorizadas no cruzan hacia AWS", lambda x: "flujos sobre la VPN: " + ", ".join(_v(x)["flujos_sobre_vpn"]))],
    "T04": [("Sin exposición pública del lado AWS", lambda x: f"redes de AWS: {_v(x)['extremo_aws']['redes_anunciadas'][0]}; sin ruta desde Internet")],
    "T05": [("Túneles en activo y respaldo", lambda x: ", ".join(f"{t['id']} ({t['rol']}) {t['red_interna']}" for t in _v(x)["tuneles"])),
            ("AS-path prepending del respaldo", lambda x: ", ".join(t["id"] for t in _v(x)["tuneles"] if t.get("bgp_as_path_prepending")) or "ninguno"),
            ("Temporizadores de BGP", lambda x: f"keepalive {_v(x)['bgp']['keepalive_s']} s, hold {_v(x)['bgp']['hold_s']} s"),
            ("DPD", lambda x: f"cada {_v(x)['dpd']['intervalo_s']} s, acción {_v(x)['dpd']['accion']}"),
            ("Convergencia meta", lambda x: f"≤ {_v(x)['convergencia_meta_s']} s (OD-05)")],
    "T21": [("MTU del túnel", lambda x: f"{_v(x)['mtu']} bytes"), ("MSS clamping", lambda x: f"{_v(x)['mss_clamping']} bytes")],
    "T58": [("EC2-GW solo alcanza lo que F30 y F13 permiten", lambda x: "CTRL01:443 (F30) y SIEM01:1514/1515 (F13) por la VPN"),
            ("Flujos que cruzan la VPN", lambda x: ", ".join(_v(x)["flujos_sobre_vpn"]))],
    "T26": [("Cabeceras que identifican al cliente no salen del campus (REQ-F-28, F8)", lambda x: "sin X-Forwarded-For, Via ni IP de clientes en la petición saliente (F8)"),
            ("Cifrado fase 1", lambda x: f"{_v(x)['fase1']['cifrado']}, {_v(x)['fase1']['prf']}, {_v(x)['fase1']['dh']}, vida {_v(x)['fase1']['vida_s']} s"),
            ("Cifrado fase 2", lambda x: f"{_v(x)['fase2']['cifrado']}, PFS {_v(x)['fase2']['pfs']}, vida {_v(x)['fase2']['vida_s']} s")],
    "T36": [("mTLS del nodo hacia el plano de control (F10, dentro del campus)", lambda x: x.flujos["F10"]["proteccion"]["tipo"])],
}


# ------------------------------------------------------------------------------------------------ textos
def _lista(v) -> list[str]:
    return v if isinstance(v, list) else [v]


def describir_criterio(c: dict) -> str:
    """Una línea medible por criterio de aprobación."""
    cmd = f" (`{c['comando_adicional']}`)" if c.get("comando_adicional") else ""
    nota = f" — {c['nota']}" if c.get("nota") else ""
    t = c["tipo"]
    if t == "exit_code":
        v = "distinto de 0" if c["valor"] == "distinto_de_0" else f"= {c['valor']}"
        return f"Código de salida {v}{cmd}{nota}"
    if t == "regex":
        coincide = "coincide" if c.get("debe_coincidir", True) else "no coincide"
        return f"{c['sobre']} {coincide} con /{c['patron']}/{cmd}{nota}"
    if t in ("umbral", "contador"):
        return f"{c['metrica']} {c['operador']} {c['valor']}{cmd}{nota}"
    return f"Verificación manual: {c.get('descripcion', '')}{nota}"


def _origen_destino(v) -> str:
    return ", ".join(_lista(v))


def _medido(res: dict) -> str:
    partes = []
    for k, v in (res.get("valor_medido") or {}).items():
        if isinstance(v, dict):
            v = ", ".join(f"{a}={b}" for a, b in v.items())
        partes.append(f"{k} = {v}")
    return "; ".join(partes)


def _resultado_l(res: dict | None) -> str:
    return res["resultado"] if res else "SIN ENSAYO"


def observaciones(t: dict, res: dict | None, titulos: dict[str, str]) -> str:
    """Observaciones de una prueba: ampliación, pendientes, nota de modos y todo lo que el ensayo L no dejó en PASA (causa y acción)."""
    p = []
    if t.get("ampliacion"):
        p.append(f"Ampliación {t['cambio']}: no está en D1.16.")
    if t.get("pendiente"):
        cis = ci._como_lista(t.get("cambio"))
        p.append("Pendiente (" + ", ".join(f"{c}: {titulos.get(c, '')}".rstrip(": ") for c in cis) + ").")
    if t.get("nota_modos"):
        p.append(t["nota_modos"] + ".")
    if res and res["resultado"] != "PASA":
        causa = res.get("motivo") or "; ".join(res.get("hallazgos", [])) or "sin motivo registrado"
        if res["resultado"] == "FALLA":
            obs = t.get("observacion_ensayo") or {}
            p.append(f"Ensayo L FALLA. Causa: {obs.get('causa') or causa}. Acción: {obs.get('accion') or 'SIN DEFINIR (agregue `observacion_ensayo` a la prueba)'}.")
        else:
            p.append(f"Ensayo L {res['resultado']}: {causa}.")
    elif res and res.get("hallazgos"):
        p.append("Ensayo L: " + "; ".join(res["hallazgos"]) + ".")
    return " ".join(p)


# ------------------------------------------------------------------------------------------------ hojas
def _celdas_de_matriz(x: Infra) -> list[tuple[str, str, dict]]:
    """Celdas no «no_aplica» de la matriz zona × zona, en el orden de D1.8."""
    orden = x.orden_matriz
    me = x.matriz_esperada()
    return [(o, d, me[(o, d)]) for o in orden for d in orden if (o, d) in me and me[(o, d)]["estado"] != "no_aplica"]


def _pruebas_ordenadas(x: Infra) -> list[dict]:
    return sorted(x.pruebas.values(), key=lambda t: int(t["id"][1:]))


def hoja_matriz(wb, x: Infra, resultados: dict, carpeta: str, titulos: dict[str, str]) -> int:
    ws = wb.create_sheet("Matriz")
    n = len(COLUMNAS)
    ws.cell(row=1, column=1, value="Matriz de pruebas de conectividad planeadas — Celeris Edge (CE0311, S1-E1)").font = xc.TITULO
    nota = ws.cell(row=2, column=1, value=f"Pruebas PLANEADAS para S2 (la columna «Resultado S2» queda vacía para CE0313). Las columnas «Ensayo L» son de un {ROTULO_EMULADO.lower()}.")
    nota.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=8)
    ws.row_dimensions[2].height = 32
    xc.escribir_encabezado(ws, FILA_ENC, [c[1] for c in COLUMNAS], [c[2] for c in COLUMNAS])
    fila = FILA_ENC + 1
    for t in _pruebas_ordenadas(x):
        res = resultados.get(t["id"])
        if t["flujos"]:
            flujos = ", ".join(t["flujos"])
        else:
            flujos = "sin F-nn: " + t.get("flujos_justificacion", "")
        v = {
            "plantilla": t["nombre"], "esperado": t["resultado_esperado"], "id": t["id"],
            "procedencia": f"Ampliación {t['cambio']}" if t.get("ampliacion") else "D1.16",
            "categoria": t["categoria"], "polaridad": POLARIDAD[t["polaridad"]], "critica": "Sí" if t["critica"] else "No",
            "origen": _origen_destino(t["origen"]), "destino": _origen_destino(t["destino"]), "flujos": flujos,
            "componentes": ", ".join(t["componentes"]), "valida": t["objetivo_que_valida"], "precondicion": t["precondicion"],
            "comando": t["comando"], "criterio": "\n".join("• " + describir_criterio(c) for c in t["criterio_aprobacion"]),
            "evidencia": "\n".join("• " + e for e in t["evidencia_a_capturar"]), "modos": ", ".join(t["modos"]), "semestre": t["semestre"],
            "rubrica": ", ".join(t["criterios_rubrica"]), "od": ", ".join(t["objetivos"]), "am": ", ".join(t["amenazas"]),
            "det": ", ".join(t.get("detecciones", [])),
            "l_res": _resultado_l(res), "l_medido": _medido(res) if res else "",
            "l_fecha": (res or {}).get("fecha", "") if res else "",
            "l_archivo": "\n".join(f"evidencias/{carpeta}/{a}" for a in res["evidencia"]) if res and res.get("evidencia") else "",
            "s2": "", "obs": observaciones(t, res, titulos),
        }
        xc.escribir_fila(ws, fila, [v[k] for k, _, _ in COLUMNAS], centrar={IDX["id"], IDX["critica"], IDX["modos"], IDX["semestre"], IDX["polaridad"], IDX["l_res"], IDX["l_fecha"], IDX["s2"]},
                         alterna=(fila % 2 == 0))
        celda = ws.cell(row=fila, column=IDX["l_res"])
        xc.celda_estado(celda, v["l_res"])
        if t["critica"]:
            ws.cell(row=fila, column=IDX["critica"]).font = xc.NEGRITA
        fila += 1
    ultima = fila - 1
    xc.configurar_hoja(ws, FILA_ENC, n, ultima, congelar=f"C{FILA_ENC + 1}")
    # Impresión: las diez primeras columnas caben legibles en A4 horizontal; las demás se leen en pantalla
    ws.print_area = f"A1:{L(IDX['destino'] + 1)}{ultima}"
    # Validación de datos: categoría, polaridad, crítica, modos y resultado de S2
    modos = sorted({", ".join(t["modos"]) for t in x.pruebas.values()} | {"L", "A", "H"})
    for col, lista in (("categoria", CATEGORIAS), ("polaridad", list(POLARIDAD.values())), ("critica", ["Sí", "No"]), ("modos", modos), ("s2", RESULTADOS_S2)):
        dv = DataValidation(type="list", formula1='"' + ",".join(lista) + '"', allow_blank=True, showErrorMessage=True,
                            errorTitle="Valor no válido", error="Elija un valor de la lista.")
        ws.add_data_validation(dv)
        dv.add(f"{L(IDX[col])}{FILA_ENC + 1}:{L(IDX[col])}{ultima}")
    return ultima


def hoja_portada(wb, x: Infra, ultima_matriz: int, carpeta: str, meta_l: dict) -> None:
    ws = wb.active
    ws.title = "Portada"
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 100
    ws.cell(row=1, column=1, value="Matriz de pruebas de conectividad planeadas").font = Font(name="Calibri", size=11, bold=True)
    ws.cell(row=2, column=1, value="Celeris Edge — CE0311 Análisis y Diseño de Red, Entregable 1 (criterios R3 y R4)")
    ver = x.pru["meta"]["version"]
    rango = f"Matriz!C{FILA_ENC + 1}:C{ultima_matriz}"
    proc = f"Matriz!D{FILA_ENC + 1}:D{ultima_matriz}"
    crit = f"Matriz!G{FILA_ENC + 1}:G{ultima_matriz}"
    filas = [
        ("Versión de la matriz", ver),
        ("Fecha de la fuente (pruebas.yaml)", x.pru["meta"]["fecha"]),
        ("Fuente de verdad", "infra/pruebas.yaml, infra/inventory.yaml e infra/trazabilidad.yaml; esta hoja no se edita a mano (make matrices)."),
        ("Alcance", "Pruebas de conectividad PLANEADAS para ejecutarse en S2 (CE0313), con su criterio de aprobación medible. Cubre la VPN (T01–T05, T21, T26), "
                    "la segmentación por zonas, la seguridad del portal, la detección y los flujos de D1.11."),
        ("Ensayo previo en laboratorio emulado", f"Las columnas «Ensayo L» y la hoja «Ensayo L» muestran el último ensayo ({carpeta}) en el laboratorio emulado "
                                                 f"(containerlab). {ROTULO_EMULADO}. PARCIAL y NO_APLICA nunca cuentan como PASA."),
        ("Total de pruebas", f"=COUNTA({rango})"),
        ("De D1.16 (T01–T28)", f'=COUNTIF({proc},"D1.16")'),
        ("Ampliaciones (T29+, CI-27)", f'=COUNTIF({proc},"Ampliación*")'),
        ("Pruebas críticas", f'=COUNTIF({crit},"Sí")'),
        ("Cobertura de flujos permitidos", "=Cobertura!E5"),
        ("Cobertura de celdas denegadas críticas", "=Cobertura!E8"),
        ("Cómo leer la hoja «Matriz»", "Las dos primeras columnas son las de la tabla de la plantilla del informe (sección 6). El resto de columnas trazan cada prueba a flujos, "
                                       "componentes, objetivos (OD), amenazas (AM), detecciones (DET) y criterios de la rúbrica. Los filtros están activos en todas las columnas."),
        ("Hojas", "Matriz · Segmentación (tabla «Origen → Destino» derivada de la matriz zona × zona) · Cobertura (flujo, celda, rúbrica, OD/AM/DET × prueba) · "
                  "VPN (parámetros de D1.10 por prueba) · Ensayo L (resultado del laboratorio emulado)."),
        ("Modo L", "Laboratorio emulado local (containerlab). No es la implementación de S2: lo emulado se rotula como emulado (Parte F4.2)."),
        ("Modo A", "AWS efímero (OpenTofu): VPC, VPN y campus simulado en AWS."),
        ("Modo H", "Híbrido real: el campus y AWS con el equipamiento de S2."),
        ("Polaridad", "Positiva: se espera tráfico permitido. Negativa: se espera una denegación. Mixta: ambas. «Prueba positiva de un flujo» = positiva o mixta que lo cita."),
        ("Crítica", "Un FALLA invalida un límite de seguridad del diseño: categoría segmentación, VPN o cifrado (CI-26)."),
        ("Valores entre < >", "<URL_SEÑUELO>, <IP_EXTERNA_DE_PRUEBA>, <USUARIO_DE_RESPALDO> y <REPOSITORIO> no están en el inventario: se definen al ejecutar la prueba (CI-27)."),
        ("Supuestos", "S-16: desfase máximo de reloj de 1 s en T33. Los umbrales de 60 s para las alertas de Wazuh son una elección de la ampliación (CI-27)."),
    ]
    for i, (a, b) in enumerate(filas, start=4):
        ca = ws.cell(row=i, column=1, value=a)
        cb = ws.cell(row=i, column=2, value=b)
        ca.font, cb.font = xc.NEGRITA, xc.FUENTE
        ca.alignment = cb.alignment = xc.AJUSTE
        ca.border = cb.border = xc.BORDE
        if isinstance(b, str) and b.startswith("=Cobertura"):
            cb.number_format = "0.0%"
            cb.alignment = Alignment(horizontal="left", vertical="top")
    ws.cell(row=4 + len(filas) + 1, column=1, value=ROTULO_EMULADO + " (las columnas de ensayo)").font = xc.NEGRITA
    xc.imprimir_a4(ws)


def hoja_segmentacion(wb, x: Infra) -> None:
    ws = wb.create_sheet("Segmentación")
    ws.cell(row=1, column=1, value="Segmentación: «Origen → Destino» derivado de la matriz zona × zona (D1.8) y la prueba que lo verifica").font = xc.TITULO
    cols = ["Origen", "Destino", "Origen → Destino", "Resultado esperado", "Flujos (F-nn)", "Puertos permitidos", "Crítica", "Prueba(s) que lo verifican", "Cobertura", "Nota"]
    anchos = [14, 14, 26, 22, 14, 40, 9, 22, 26, 44]
    xc.escribir_encabezado(ws, 3, cols, anchos)
    criticas = x.celdas_denegadas_criticas()
    fila = 4
    for o, d, c in _celdas_de_matriz(x):
        celda = f"{o}>{d}"
        flujos = c.get("flujos", [])
        if c["estado"] == "permitido":
            esperado = "PERMITIDO"
            puertos = "; ".join(f"{f}: " + ", ".join(f"{p['proto']}/{'-'.join(map(str, p['puertos']))}" for p in x.flujos[f]["protocolos"]) for f in flujos) or "sin F-nn (CI-05/CI-06)"
            pruebas = x.pruebas_positivas_de_celda(celda, flujos)
        else:
            esperado = "DENEGADO"
            puertos = "—"
            pruebas = x.pruebas_negativas_de_celda(celda)
        es_critica = "Sí" if celda in criticas else "No"
        valores = [o, d, f"{o} → {d}", esperado, ", ".join(flujos), puertos, es_critica if esperado == "DENEGADO" else "—", ", ".join(sorted(pruebas, key=lambda s: int(s[1:]))), None, c.get("nota", "")]
        xc.escribir_fila(ws, fila, valores, centrar={7}, alterna=(fila % 2 == 0))
        ws.cell(row=fila, column=9, value=f'=IF(LEN(H{fila})>0,"Con prueba",IF(G{fila}="Sí","SIN PRUEBA — CRÍTICA","SIN PRUEBA"))')
        xc.celda_zona(ws.cell(row=fila, column=1), o)
        xc.celda_zona(ws.cell(row=fila, column=2), d)
        fila += 1
    ultima = fila - 1
    rojo = xc.relleno("D55E00")
    ws.conditional_formatting.add(f"I4:I{ultima}", FormulaRule(formula=['LEFT(I4,10)="SIN PRUEBA"'], fill=rojo, font=Font(name="Calibri", size=11, bold=True, color="FFFFFF")))
    ws.cell(row=2, column=1, value="El color de zona (Okabe-Ito) acompaña siempre al nombre de la zona. «SIN PRUEBA» en la columna Cobertura marca un hueco: no depende del color.")
    xc.configurar_hoja(ws, 3, len(cols), ultima, congelar="D4")


def hoja_cobertura(wb, x: Infra) -> None:
    ws = wb.create_sheet("Cobertura")
    pruebas = _pruebas_ordenadas(x)
    ids = [t["id"] for t in pruebas]
    pol = {t["id"]: MARCA[t["polaridad"]] for t in pruebas}
    ws.cell(row=1, column=1, value="Cobertura de la matriz de pruebas (los porcentajes son fórmulas; un hueco dice «SIN PRUEBA» en texto)").font = xc.TITULO
    ws.cell(row=2, column=1, value="Marcas: P = prueba positiva, N = negativa, M = mixta (cuenta como positiva y negativa), X = la prueba cita el elemento.")
    # ---- resumen (filas 5 a 14) se escribe al final, cuando se conocen los rangos
    r0 = 18
    bloques: dict[str, tuple[int, int]] = {}      # nombre → (primera fila de datos, última)

    def encabezado(fila, extra, titulo):
        ws.cell(row=fila - 1, column=1, value=titulo).font = xc.TITULO
        cols = extra + ids + ["Positivas", "Negativas", "Estado"]
        xc.escribir_encabezado(ws, fila, cols)
        ws.row_dimensions[fila].height = 34
        return len(extra)

    def contar(fila, n_extra, positivo=True, negativo=True):
        a, b = L(n_extra + 1), L(n_extra + len(ids))
        rng = f"{a}{fila}:{b}{fila}"
        return (f'=COUNTIF({rng},"P")+COUNTIF({rng},"M")', f'=COUNTIF({rng},"N")+COUNTIF({rng},"M")', rng)

    fila = r0
    # ---------- bloque 1: flujo × prueba
    n_extra = encabezado(fila, ["Flujo", "Acción", "Propósito"], "1. Flujo × prueba (D1.11)")
    inicio = fila + 1
    fila += 1
    for f in x.flujos.values():
        if f["estado"] != "activo":
            continue
        marcas = [pol[t] if f["id"] in x.pruebas[t]["flujos"] else None for t in ids]
        xc.escribir_fila(ws, fila, [f["id"], f["accion"], f["proposito"]] + marcas + [None, None, None], centrar=set(range(4, 4 + len(ids))))
        p, n_, rng = contar(fila, n_extra)
        cp, cn, ce = L(n_extra + len(ids) + 1), L(n_extra + len(ids) + 2), L(n_extra + len(ids) + 3)
        ws[f"{cp}{fila}"], ws[f"{cn}{fila}"] = p, n_
        ws[f"{ce}{fila}"] = f'=IF(IF(B{fila}="permitir",{cp}{fila},{cn}{fila})>0,"Cubierto","SIN PRUEBA")'
        fila += 1
    bloques["flujos"] = (inicio, fila - 1)
    ce_flujo = L(n_extra + len(ids) + 3)
    fila += 3
    # ---------- bloque 2: celda zona × zona × prueba
    n_extra = encabezado(fila, ["Celda", "Resultado esperado", "Crítica"], "2. Celda zona × zona × prueba (D1.8)")
    inicio = fila + 1
    fila += 1
    criticas = x.celdas_denegadas_criticas()
    for o, d, c in _celdas_de_matriz(x):
        celda = f"{o}>{d}"
        flujos = c.get("flujos", [])
        marcas = []
        for t in ids:
            tt = x.pruebas[t]
            cita = celda in tt.get("celdas_matriz", []) or (c["estado"] == "permitido" and set(flujos) & set(tt["flujos"]))
            marcas.append(pol[t] if cita else None)
        esperado = "PERMITIDO" if c["estado"] == "permitido" else "DENEGADO"
        crit = "Sí" if celda in criticas else "No"
        xc.escribir_fila(ws, fila, [f"{o} → {d}", esperado, crit] + marcas + [None, None, None], centrar=set(range(2, 4 + len(ids))))
        p, n_, rng = contar(fila, n_extra)
        cp, cn, ce = L(n_extra + len(ids) + 1), L(n_extra + len(ids) + 2), L(n_extra + len(ids) + 3)
        ws[f"{cp}{fila}"], ws[f"{cn}{fila}"] = p, n_
        ws[f"{ce}{fila}"] = (f'=IF(IF(B{fila}="PERMITIDO",{cp}{fila},{cn}{fila})>0,"Cubierto",'
                             f'IF(C{fila}="Sí","SIN PRUEBA — CRÍTICA","SIN PRUEBA (no crítica)"))')
        fila += 1
    bloques["celdas"] = (inicio, fila - 1)
    fila += 3
    # ---------- bloques 3 y 4: rúbrica, OD, AM, DET (marca X)
    def bloque_x(titulo, clave, filas_datos, citan, estado_formula):
        nonlocal fila
        ne = encabezado(fila, ["ID", "Peso / tipo", "Descripción"], titulo)
        ini = fila + 1
        fila += 1
        for ident, aux, desc, doc in filas_datos:
            marcas = ["X" if citan(ident, t) else None for t in ids]
            xc.escribir_fila(ws, fila, [ident, aux, desc] + marcas + [None, None, None], centrar=set(range(4, 4 + len(ids))))
            a, b = L(ne + 1), L(ne + len(ids))
            cp, cn, ce = L(ne + len(ids) + 1), L(ne + len(ids) + 2), L(ne + len(ids) + 3)
            ws[f"{cp}{fila}"] = f'=COUNTIF({a}{fila}:{b}{fila},"X")'
            ws[f"{cn}{fila}"] = "—"
            ws[f"{ce}{fila}"] = ("No se evalúa con pruebas (criterio documental)" if doc else f'=IF({cp}{fila}>0,"Cubierto","SIN PRUEBA")')
            fila += 1
        bloques[clave] = (ini, fila - 1)
        fila += 3

    crit_rub = [(r, f"peso {x.rubrica[r]['peso']} %", x.rubrica[r]["nombre"], r in ci.RUBRICA_SIN_PRUEBAS) for r in sorted(x.rubrica)]
    bloque_x("3. Criterio de rúbrica × prueba", "rubrica", crit_rub, lambda r, t: r in x.pruebas[t]["criterios_rubrica"], None)
    elementos = [(e["id"], f"elemento de {e['id'][:2]}", e["elemento"], False) for r in ("R3", "R4") for e in x.rubrica[r].get("elementos_evaluados", [])]
    bloque_x("3b. Elementos evaluados de R3 y R4 × prueba (trazabilidad.yaml → rubrica.*.elementos_evaluados)", "elementos", elementos,
             lambda e, t: t in next(el["pruebas"] for r in ("R3", "R4") for el in x.rubrica[r]["elementos_evaluados"] if el["id"] == e), None)
    bloque_x("4. Objetivo (OD) × prueba", "od", [(o["id"], "objetivo", o["objetivo"], False) for o in x.objetivos.values()], lambda o, t: o in x.pruebas[t]["objetivos"], None)
    bloque_x("5. Amenaza (AM) × prueba", "am", [(a["id"], "amenaza", a["amenaza"], False) for a in x.amenazas.values()], lambda a, t: a in x.pruebas[t]["amenazas"], None)
    bloque_x("6. Detección (DET) × prueba", "det", [(d["id"], "detección", d["tecnologia"], False) for d in x.detecciones.values()], lambda d, t: d in x.pruebas[t].get("detecciones", []), None)

    # ---------- resumen con fórmulas (filas 5 a 14)
    cols = ["Dimensión", "Cubiertos", "Faltan", "Total", "Cobertura", "Meta", "Resultado"]
    xc.escribir_encabezado(ws, 4, cols)
    ne = 3
    estado_col = L(ne + len(ids) + 3)
    f1, f2 = bloques["flujos"]
    c1, c2 = bloques["celdas"]
    rf = lambda col, a, b: f"${col}${a}:${col}${b}"        # noqa: E731
    est_f, acc_f = rf(estado_col, f1, f2), rf("B", f1, f2)
    est_c, res_c, crit_c = rf(estado_col, c1, c2), rf("B", c1, c2), rf("C", c1, c2)
    cob = x.cobertura_de_pruebas()

    def est(clave):
        a, b = bloques[clave]
        return rf(estado_col, a, b)

    def faltan(nombre):
        f = cob[nombre]["faltan"]
        return ", ".join(f) if f and len(f) <= 12 else (f"{len(f)} elementos (ver bloque)" if f else "—")

    resumen = [
        ("Flujos permitidos con prueba positiva", f'=COUNTIFS({acc_f},"permitir",{est_f},"Cubierto")', f'=COUNTIF({acc_f},"permitir")', 1, "Flujos permitidos con prueba positiva"),
        ("Flujos bloqueados con prueba negativa", f'=COUNTIFS({acc_f},"bloquear",{est_f},"Cubierto")', f'=COUNTIF({acc_f},"bloquear")', 1, "Flujos bloqueados con prueba negativa"),
        ("Celdas permitidas con prueba positiva", f'=COUNTIFS({res_c},"PERMITIDO",{est_c},"Cubierto")', f'=COUNTIF({res_c},"PERMITIDO")', 1, "Celdas permitidas con prueba positiva"),
        ("Celdas denegadas críticas con prueba negativa", f'=COUNTIFS({res_c},"DENEGADO",{crit_c},"Sí",{est_c},"Cubierto")', f'=COUNTIFS({res_c},"DENEGADO",{crit_c},"Sí")', 1, "Celdas denegadas críticas con prueba negativa"),
        ("Celdas denegadas (todas) con prueba negativa", f'=COUNTIFS({res_c},"DENEGADO",{est_c},"Cubierto")', f'=COUNTIF({res_c},"DENEGADO")', None, "Celdas denegadas (todas) con prueba negativa"),
        ("Criterios de rúbrica evaluables con prueba", f'=COUNTIF({est("rubrica")},"Cubierto")', f'=COUNTIF({est("rubrica")},"Cubierto")+COUNTIF({est("rubrica")},"SIN PRUEBA")', 1, "Criterios de rúbrica con ≥ 1 prueba"),
        ("Elementos evaluados de R3 y R4", f'=COUNTIF({est("elementos")},"Cubierto")', f'=COUNTA({rf("A", *bloques["elementos"])})', 1, "Elementos evaluados de R3 y R4 con ≥ 1 prueba"),
        ("Objetivos (OD)", f'=COUNTIF({est("od")},"Cubierto")', f'=COUNTA({rf("A", *bloques["od"])})', 1, "Objetivos OD con ≥ 1 prueba"),
        ("Amenazas (AM)", f'=COUNTIF({est("am")},"Cubierto")', f'=COUNTA({rf("A", *bloques["am"])})', 1, "Amenazas AM con ≥ 1 prueba"),
        ("Detecciones (DET)", f'=COUNTIF({est("det")},"Cubierto")', f'=COUNTA({rf("A", *bloques["det"])})', 1, "Detecciones DET con ≥ 1 prueba"),
    ]
    for i, (nombre, cub, tot, meta, clave) in enumerate(resumen, start=5):
        xc.escribir_fila(ws, i, [nombre, cub, faltan(clave), tot, f'=IF(D{i}=0,"",B{i}/D{i})', meta if meta else "informativa",
                                 f'=IF(F{i}="informativa","—",IF(E{i}>=F{i},"CUMPLE","BRECHA"))'], centrar={2, 4, 5, 6, 7})
        ws[f"E{i}"].number_format = "0.0%"
        if meta:
            ws[f"F{i}"].number_format = "0%"
    ws.conditional_formatting.add("G5:G14", FormulaRule(formula=['G5="BRECHA"'], fill=xc.relleno("D55E00"), font=Font(name="Calibri", size=11, bold=True, color="FFFFFF")))
    ws.conditional_formatting.add("G5:G14", FormulaRule(formula=['G5="CUMPLE"'], fill=xc.relleno("009E73"), font=Font(name="Calibri", size=11, bold=True, color="FFFFFF")))
    # huecos resaltados en cada bloque (el texto «SIN PRUEBA» ya está en la celda)
    ult = fila
    ws.conditional_formatting.add(f"A{r0}:{L(ne + len(ids) + 3)}{ult}", FormulaRule(
        formula=[f'LEFT(${estado_col}{r0},10)="SIN PRUEBA"'], fill=xc.relleno("F4C7B0")))
    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 40
    for j in range(4, 4 + len(ids)):
        ws.column_dimensions[L(j)].width = 8
    for k, nombre in enumerate(("Positivas", "Negativas", "Estado")):
        ws.column_dimensions[L(4 + len(ids) + k)].width = 12 if k < 2 else 30
    ws.freeze_panes = "D5"
    xc.imprimir_a4(ws)


def hoja_vpn(wb, x: Infra, resultados: dict) -> None:
    ws = wb.create_sheet("VPN")
    ws.cell(row=1, column=1, value="Pruebas de la VPN híbrida (D1.10) y el parámetro que cada una verifica").font = xc.TITULO
    cols = ["Prueba", "Nombre", "Qué parámetro de D1.10 verifica", "Valor de D1.10 (inventario)", "Criterio de aprobación", "Modos", "Ensayo L (emulado)"]
    xc.escribir_encabezado(ws, 3, cols, [8, 26, 44, 56, 60, 10, 18])
    fila = 4
    for tid, params in PARAMETROS_VPN.items():
        t = x.pruebas[tid]
        res = resultados.get(tid)
        criterio = "\n".join("• " + describir_criterio(c) for c in t["criterio_aprobacion"])
        for k, (texto, valor) in enumerate(params):
            xc.escribir_fila(ws, fila, [tid, t["nombre"], texto, valor(x), criterio if k == 0 else "", ", ".join(t["modos"]), _resultado_l(res) if k == 0 else ""],
                             centrar={1, 6, 7}, alterna=(tid in ("T01", "T03", "T05", "T26", "T36", "T58")))
            if k == 0:
                xc.celda_estado(ws.cell(row=fila, column=7), _resultado_l(res))
            fila += 1
    ws.cell(row=2, column=1, value=f"{ROTULO_EMULADO}: el Modo L usa strongSwan y FRR con VTI, no OPNsense ni el VGW de AWS.")
    xc.configurar_hoja(ws, 3, len(cols), fila - 1, congelar="C4")


def hoja_ensayo(wb, x: Infra, resultados: dict, carpeta: str, meta: dict) -> None:
    ws = wb.create_sheet("Ensayo L")
    ws.cell(row=1, column=1, value=f"Ensayo en laboratorio emulado — {ROTULO_EMULADO}").font = xc.TITULO
    ws.cell(row=2, column=1, value=(f"Fuente: evidencias/{carpeta}/resultados.json (commit {str(meta.get('commit', '—'))[:7]}). {meta.get('aviso', '')} "
                                    "SIN ENSAYO = la prueba no está en resultados.json."))
    ws.cell(row=2, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:H2")
    ws.row_dimensions[2].height = 48
    # resumen (fórmulas) en las filas 4 a 9; la tabla empieza en la fila 12
    cols = ["ID", "Prueba", "Modos", "Crítica", "Resultado en L", "Valor medido", "Motivo o hallazgo", "Fecha", "Evidencia"]
    anchos = [16, 34, 10, 9, 16, 44, 70, 12, 44]
    xc.escribir_encabezado(ws, 12, cols, anchos)
    fila = 13
    for t in _pruebas_ordenadas(x):
        res = resultados.get(t["id"])
        motivo = ""
        if res:
            motivo = res.get("motivo") or ""
            if res.get("hallazgos"):
                motivo = (motivo + " | " if motivo else "") + "; ".join(res["hallazgos"])
        xc.escribir_fila(ws, fila, [t["id"], t["nombre"], ", ".join(t["modos"]), "Sí" if t["critica"] else "No", _resultado_l(res), _medido(res) if res else "", motivo,
                                    (res or {}).get("fecha", ""), "\n".join(f"evidencias/{carpeta}/{a}" for a in (res or {}).get("evidencia", []))],
                         centrar={1, 3, 4, 5, 8}, alterna=(fila % 2 == 0))
        xc.celda_estado(ws.cell(row=fila, column=5), _resultado_l(res))
        fila += 1
    ultima = fila - 1
    rng = f"$E$13:$E${ultima}"
    xc.escribir_encabezado(ws, 4, ["Resultado en L", "Pruebas", "Cuenta como PASA"])
    for i, estado in enumerate(RESULTADOS_L, start=5):
        xc.escribir_fila(ws, i, [estado, f'=COUNTIF({rng},"{estado}")', "Sí" if estado == "PASA" else "No"], centrar={2, 3})
        xc.celda_estado(ws.cell(row=i, column=1), estado)
    xc.escribir_fila(ws, 10, ["Total", f"=SUM(B5:B9)", ""], centrar={2})
    ws.cell(row=10, column=1).font = xc.NEGRITA
    xc.configurar_hoja(ws, 12, len(cols), ultima, congelar="C13")


# ------------------------------------------------------------------------------------------------ libro
def construir(x: Infra, raiz: Path | None = None) -> Workbook:
    raiz = raiz or x.raiz
    carpeta, datos = ci.resultados_mas_recientes(raiz)
    resultados = {r["id"]: {**r, "fecha": r.get("fecha") or datos["meta"].get("fecha", "")} for r in datos["resultados"]} if datos else {}
    meta = datos["meta"] if datos else {}
    nombre_carpeta = carpeta.name if carpeta else "—"
    titulos = ci.titulos_de_cambios()
    wb = Workbook()
    ultima = hoja_matriz(wb, x, resultados, nombre_carpeta, titulos)
    hoja_portada(wb, x, ultima, nombre_carpeta, meta)
    hoja_segmentacion(wb, x)
    hoja_cobertura(wb, x)
    hoja_vpn(wb, x, resultados)
    hoja_ensayo(wb, x, resultados, nombre_carpeta, meta)
    wb._sheets = [wb[n] for n in HOJAS]
    xc.propiedades(wb, "Matriz de pruebas de conectividad planeadas — Celeris Edge", x.pru["meta"]["fecha"])
    return wb


def ruta_salida(x: Infra, raiz: Path | None = None) -> Path:
    return (raiz or x.raiz) / SUBDIR / f"Matriz_Pruebas_Conectividad_v{x.pru['meta']['version']}.xlsx"


def main(x: Infra, raiz: Path | None = None) -> Path:
    ruta = ruta_salida(x, raiz)
    xc.guardar_reproducible(construir(x, raiz), ruta)
    return ruta
