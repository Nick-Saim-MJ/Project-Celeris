"""Pruebas del modelado de procesos (CE01 E4, CI-104): BPMN válidos, PD-xx, automatizaciones, descarga y simulación."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "gestion"))
sys.path.insert(0, str(RAIZ / "gestion" / "e4"))

import bpmn  # noqa: E402
import procesos as P  # noqa: E402


@pytest.fixture(scope="module")
def m():
    return P.calcular(2000)


def test_bpmn_validos_contra_el_xsd_y_con_sus_pd():
    sim, car = P.sim(), P.caracterizacion()
    problemas = {p["id"]: p for p in car["problemas"]}
    for pid, p in sim["procesos"].items():
        texto = bpmn.Diagrama(pid, p, sim["meta"], problemas).xml()
        assert bpmn.validar(texto, {x["id"] for x in car["problemas"] if x["diagrama"] == pid}) == []


def test_bpmn_roto_falla():
    sim, car = P.sim(), P.caracterizacion()
    texto = bpmn.Diagrama("P1-AS-IS", sim["procesos"]["P1-AS-IS"], sim["meta"], {p["id"]: p for p in car["problemas"]}).xml()
    roto = texto.replace('sourceRef="a1" ', "", 1)
    assert bpmn.validar(roto, set())


def test_descarga_calculada_con_los_supuestos():
    k = P.calculos()
    assert k["gb_lab"] == 120
    assert k["wan_lab"] == pytest.approx(120 * 8 * 1000 / 150 / 3600)       # 40 × 3 GB [S-26, S-27] a 150 Mbps [S-42]
    assert k["lan_lab"] == pytest.approx(120 * 8 / 1 / 3600)                 # por la LAN de 1 Gbps [S-14]
    assert k["p_interrupcion_tobe"] < k["p_interrupcion"]


def test_coherencia_pd_automatizaciones_srs_y_pruebas():
    assert P.verificar(P.caracterizacion(), P.sim()) == []


def test_automatizacion_sin_prueba_falla():
    car = copy.deepcopy(P.caracterizacion())
    car["automatizaciones"][0]["prueba"] = ["T99"]
    assert any("T99" in e for e in P.verificar(car, P.sim()))


def test_pd_fuera_del_diagrama_falla():
    car = copy.deepcopy(P.caracterizacion())
    car["problemas"][0]["nodo"] = "a1"
    assert P.verificar(car, P.sim())


def test_mejora_cuantificada_y_reproducible(m):
    c = m["comparativo"]
    for proc in ("P1", "P2"):
        for med in ("ocupacion_h", "horas_personal", "costo", "wan_gb"):
            assert c[proc][med]["tobe"] < c[proc][med]["asis"]
    assert c["P2"]["listo"]["tobe"] > c["P2"]["listo"]["asis"]
    assert m["kpi1"]["cumple_ob2"]
    otra = P.calcular(2000)
    assert otra["comparativo"]["P1"]["costo"]["asis"] == c["P1"]["costo"]["asis"]


def test_seleccion_elige_p1_y_p2(m):
    assert {r["id"] for r in m["seleccion"][:2]} == {"P1", "P2"}
