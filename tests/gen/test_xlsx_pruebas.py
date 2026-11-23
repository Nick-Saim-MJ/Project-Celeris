"""Matriz de pruebas XLSX: estructura, reproducibilidad, cobertura y que cada chequeo V-70+ detecte la alteración que dice detectar."""
import copy
import hashlib
import json
import re

import openpyxl
import pytest

from celeris_infra import Infra
from checks import v70_xlsx_pruebas as v70
from gen import xlsx_pruebas as xp


@pytest.fixture(scope="module")
def libro(infra, tmp_path_factory):
    ruta = tmp_path_factory.mktemp("xlsx") / "m.xlsx"
    from gen import xlsx_comun as xc
    xc.guardar_reproducible(xp.construir(infra), ruta)
    return ruta, openpyxl.load_workbook(ruta)


def niveles(hallazgos, nivel="error"):
    return [m for n, m, _ in hallazgos if n == nivel]


def con_pruebas(infra, fn):
    pru = copy.deepcopy(infra.pru)
    fn({t["id"]: t for t in pru["pruebas"]}, pru)
    return Infra(infra.inv, pru, infra.traz)


# ------------------------------------------------------------------------------------------ estructura
def test_hojas_y_una_fila_por_prueba(infra, libro):
    _, wb = libro
    assert wb.sheetnames == ["Portada", "Matriz", "Segmentación", "Cobertura", "VPN", "Ensayo L"]
    filas = v70.filas_de_matriz(wb)
    assert sorted(f["id"] for f in filas) == sorted(infra.pruebas)
    assert len(filas) == len(infra.pruebas) >= 49


def test_las_dos_primeras_columnas_son_las_de_la_plantilla(libro):
    _, wb = libro
    ws = wb["Matriz"]
    assert [ws.cell(row=xp.FILA_ENC, column=c).value for c in (1, 2)] == ["Prueba de conectividad planeada", "Resultado esperado"]
    encabezados = [ws.cell(row=xp.FILA_ENC, column=c).value for c in range(1, len(xp.COLUMNAS) + 1)]
    for pedido in ("ID", "Categoría", "Origen", "Destino", "Flujos (F-nn)", "Componentes", "Qué valida", "Precondición", "Comando / procedimiento",
                   "Criterio de aprobación", "Evidencia a capturar", "Modos", "Semestre", "Criterio de rúbrica", "Objetivo (OD)", "Amenaza (AM)",
                   "Resultado S2 (CE0313)", "Observaciones"):
        assert pedido in encabezados, pedido


def test_formato_filtros_validacion_e_impresion(libro):
    _, wb = libro
    for ws in wb:
        assert ws.page_setup.orientation == "landscape" and int(ws.page_setup.paperSize) == 9, ws.title
        assert ws.sheet_properties.pageSetUpPr.fitToPage and ws.page_setup.fitToWidth == 1, ws.title
    m = wb["Matriz"]
    assert m.auto_filter.ref and m.freeze_panes == "C4"
    columnas_validadas = {rng for dv in m.data_validations.dataValidation for rng in str(dv.sqref).split()}
    cat, modos = xp.IDX["categoria"], xp.IDX["modos"]
    assert any(r.startswith(openpyxl.utils.get_column_letter(cat)) for r in columnas_validadas)
    assert any(r.startswith(openpyxl.utils.get_column_letter(modos)) for r in columnas_validadas)
    tamanos = {c.font.sz for fila in m.iter_rows(min_row=xp.FILA_ENC, max_row=m.max_row) for c in fila if c.value}
    assert tamanos == {11}


def test_el_xlsx_es_reproducible(infra, tmp_path):
    from gen import xlsx_comun as xc
    a = xc.guardar_reproducible(xp.construir(infra), tmp_path / "a.xlsx")
    b = xc.guardar_reproducible(xp.construir(infra), tmp_path / "b.xlsx")
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()


def test_segmentacion_cubre_todas_las_parejas_relevantes(infra, libro):
    _, wb = libro
    ws = wb["Segmentación"]
    filas = [ws.cell(row=r, column=3).value for r in range(4, ws.max_row + 1) if ws.cell(row=r, column=3).value]
    esperadas = [f"{o} → {d}" for (o, d), c in infra.matriz_esperada().items() if c["estado"] != "no_aplica"]
    assert sorted(filas) == sorted(esperadas)
    assert any("DENEGADO" == ws.cell(row=r, column=4).value for r in range(4, ws.max_row + 1))


def test_vpn_agrupa_las_pruebas_y_toma_los_valores_del_inventario(infra, libro):
    _, wb = libro
    texto = " ".join(str(c.value) for fila in wb["VPN"].iter_rows() for c in fila if c.value)
    for tid in ("T01", "T02", "T05", "T21", "T26"):
        assert tid in texto
    assert str(infra.inv["vpn"]["mtu"]) in texto and str(infra.inv["vpn"]["mss_clamping"]) in texto


# ------------------------------------------------------------------------------------------ criterios medibles
def test_cada_criterio_de_aprobacion_es_medible(infra):
    for t in infra.pruebas.values():
        for c in t["criterio_aprobacion"]:
            texto = xp.describir_criterio(c)
            if c["tipo"] == "manual":
                continue
            assert re.search(r"[<>=≠/]|\d|código", texto), (t["id"], texto)
    for t in infra.pruebas.values():
        if t.get("ampliacion"):
            assert not any(c["tipo"] == "manual" for c in t["criterio_aprobacion"]), t["id"]
            assert t["polaridad"] in ("positiva", "negativa", "mixta")


# ------------------------------------------------------------------------------------------ cobertura
def test_cobertura_exigida_al_100(infra):
    cob = infra.cobertura_de_pruebas()
    for nombre in ("Flujos permitidos con prueba positiva", "Flujos bloqueados con prueba negativa", "Celdas denegadas críticas con prueba negativa",
                   "Celdas permitidas con prueba positiva", "Elementos evaluados de R3 y R4 con ≥ 1 prueba", "Objetivos OD con ≥ 1 prueba",
                   "Amenazas AM con ≥ 1 prueba", "Detecciones DET con ≥ 1 prueba", "Criterios de rúbrica con ≥ 1 prueba"):
        assert cob[nombre]["faltan"] == [], nombre
    assert niveles(v70.chequeo_cobertura(infra)) == []


def test_las_celdas_criticas_siguen_la_regla(infra):
    criticas = infra.celdas_denegadas_criticas()
    assert "LAB>MGMT" in criticas and "INTERNET>MGMT" in criticas and "DMZ-HONEY>INTERNET" in criticas and "WIFI-EST>MGMT" in criticas
    assert "SERVERS>LAB" not in criticas
    assert all(infra.matriz_esperada()[tuple(c.split(">"))]["estado"] == "denegado" for c in criticas)


def test_quitar_la_prueba_de_un_flujo_permitido_se_detecta(infra):
    otro = con_pruebas(infra, lambda t, _: [x.update(flujos=[f for f in x["flujos"] if f != "F20"]) for x in t.values()])
    assert any("F20" in m for m in niveles(v70.chequeo_cobertura(otro)))


def test_una_prueba_solo_negativa_no_cubre_un_flujo_permitido(infra):
    otro = con_pruebas(infra, lambda t, _: [x.update(polaridad="negativa") for x in t.values() if "F20" in x["flujos"]])
    assert any("F20" in m for m in niveles(v70.chequeo_cobertura(otro)))


def test_quitar_la_prueba_de_una_celda_critica_se_detecta(infra):
    otro = con_pruebas(infra, lambda t, _: t["T45"].update(celdas_matriz=[]))
    errores = " ".join(niveles(v70.chequeo_cobertura(otro)))
    assert "INTERNET>MGMT" in errores


def test_un_elemento_de_r4_sin_prueba_se_detecta(infra):
    traz = copy.deepcopy(infra.traz)
    traz["rubrica"]["R4"]["elementos_evaluados"][0]["pruebas"] = ["T99"]
    otro = Infra(infra.inv, infra.pru, traz)
    assert any("Elementos evaluados" in m for m in niveles(v70.chequeo_cobertura(otro)))


# ------------------------------------------------------------------------------------------ filas y referencias
def test_v70_detecta_una_fila_de_mas_o_de_menos(infra, libro):
    _, wb = libro
    sin_t10 = con_pruebas(infra, lambda t, p: p["pruebas"].remove(t["T10"]))
    assert any("T10" in m and "no está en pruebas.yaml" in m for m in niveles(v70.chequeo_filas(sin_t10, wb)))
    wb2 = openpyxl.load_workbook(libro[0])
    ws = wb2["Matriz"]
    fila = next(f["_fila"] for f in v70.filas_de_matriz(wb2) if f["id"] == "T10")
    ws.delete_rows(fila)
    assert any("T10" in m and "no tiene fila" in m for m in niveles(v70.chequeo_filas(infra, wb2)))


def test_v70_detecta_un_dato_alterado(infra, libro):
    wb = openpyxl.load_workbook(libro[0])
    ws = wb["Matriz"]
    fila = next(f["_fila"] for f in v70.filas_de_matriz(wb) if f["id"] == "T06")
    ws.cell(row=fila, column=xp.IDX["comando"]).value = "ping 1.1.1.1"
    assert any("T06" in m and "comando" in m for m in niveles(v70.chequeo_filas(infra, wb)))


def test_v71_detecta_un_flujo_o_componente_inexistente(infra, libro):
    wb = openpyxl.load_workbook(libro[0])
    ws = wb["Matriz"]
    fila = next(f["_fila"] for f in v70.filas_de_matriz(wb) if f["id"] == "T06")
    ws.cell(row=fila, column=xp.IDX["flujos"]).value = "F99"
    ws.cell(row=fila, column=xp.IDX["componentes"]).value = "LABCLI01, FW99"
    errores = " ".join(niveles(v70.chequeo_referencias(infra, wb)))
    assert "F99" in errores and "FW99" in errores


# ------------------------------------------------------------------------------------------ ensayo L
def libro_con_resultados(infra, tmp_path, resultados):
    raiz = tmp_path / "r"
    carpeta = raiz / "evidencias" / "2026-11-19-L"
    carpeta.mkdir(parents=True)
    datos = {"meta": {"modo": "L", "fecha": "2026-11-19", "commit": "abc1234"}, "resultados": resultados}
    (carpeta / "resultados.json").write_text(json.dumps(datos), encoding="utf-8")
    return xp.construir(infra, raiz), datos


def res(tid, estado, **kw):
    return {"id": tid, "resultado": estado, "motivo": kw.pop("motivo", ""), "valor_medido": {}, "hallazgos": [], "evidencia": [], "fecha": "2026-11-19", **kw}


def test_una_falla_sin_causa_y_accion_se_detecta(infra, tmp_path):
    wb, datos = libro_con_resultados(infra, tmp_path, [res("T07", "FALLA", motivo="falta Cache-Status")])
    assert any("T07" in m and "causa y la acción" in m for m in niveles(v70.chequeo_ensayo(infra, wb, datos)))


def test_una_falla_con_causa_y_accion_pasa(infra, tmp_path):
    otro = con_pruebas(infra, lambda t, _: t["T07"].update(observacion_ensayo={"causa": "el nodo no emite Cache-Status", "accion": "emitir la cabecera RFC 9211"}))
    wb, datos = libro_con_resultados(otro, tmp_path, [res("T07", "FALLA", motivo="falta Cache-Status")])
    assert niveles(v70.chequeo_ensayo(otro, wb, datos)) == []
    texto = [f for f in v70.filas_de_matriz(wb) if f["id"] == "T07"][0]["obs"]
    assert "Causa: el nodo no emite Cache-Status" in texto and "Acción: emitir la cabecera RFC 9211" in texto


def test_no_aplica_y_parcial_nunca_se_muestran_como_pasa(infra, tmp_path):
    wb, datos = libro_con_resultados(infra, tmp_path, [res("T08", "PARCIAL", motivo="sin navegador"), res("T25", "NO_APLICA", motivo="sin ESXi ni IPMI"), res("T06", "PASA")])
    assert niveles(v70.chequeo_ensayo(infra, wb, datos)) == []
    filas = {f["id"]: f["l_res"] for f in v70.filas_de_matriz(wb)}
    assert filas["T08"] == "PARCIAL" and filas["T25"] == "NO_APLICA" and filas["T06"] == "PASA" and filas["T01"] == "SIN ENSAYO"
    # alterar la celda a mano a PASA se detecta
    ws = wb["Matriz"]
    fila = next(f["_fila"] for f in v70.filas_de_matriz(wb) if f["id"] == "T25")
    ws.cell(row=fila, column=xp.IDX["l_res"]).value = "PASA"
    assert any("T25" in m and "PASA" in m for m in niveles(v70.chequeo_ensayo(infra, wb, datos)))


# ------------------------------------------------------------------------------------------ fórmulas y actualidad
def test_v74_recalcula_sin_errores_si_hay_libreoffice(infra, libro):
    if v70._soffice() is None:
        pytest.skip("LibreOffice no está instalado")
    ruta, _ = libro
    _, datos = __import__("celeris_infra").resultados_mas_recientes(infra.raiz)
    assert niveles(v70.chequeo_formulas(infra, ruta, datos)) == []


def test_v74_detecta_una_formula_con_error(infra, libro, tmp_path):
    if v70._soffice() is None:
        pytest.skip("LibreOffice no está instalado")
    wb = openpyxl.load_workbook(libro[0])
    wb["Cobertura"]["E5"] = "=1/0"
    roto = tmp_path / "roto.xlsx"
    wb.save(roto)
    assert any("#DIV/0!" in m for m in niveles(v70.chequeo_formulas(infra, roto, None)))


def test_v75_detecta_un_libro_desactualizado(infra, libro):
    wb = openpyxl.load_workbook(libro[0])
    assert v70.chequeo_actualidad(infra, wb) == [] or niveles(v70.chequeo_actualidad(infra, wb)) == []
    wb["Matriz"]["A5"] = "alterado a mano"
    assert niveles(v70.chequeo_actualidad(infra, wb))
