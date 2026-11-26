"""Pruebas del plan de gestión (CE01 E3, CI-103): CPM, coherencia alcance–cronograma–costos y backlog."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "gestion"))
sys.path.insert(0, str(RAIZ / "gestion" / "e3"))

import agil  # noqa: E402
import plan as P  # noqa: E402


@pytest.fixture(scope="module")
def m():
    return P.calcular()


def test_presupuesto_cuadra_con_linea_base(m):
    p = m["presupuesto"]
    assert sum(x["total"] for x in p["paquetes"].values()) + p["herramientas"] == pytest.approx(p["bac"])
    assert p["linea_base"] == pytest.approx(p["bac"] * 1.10)
    assert p["gestion"] == pytest.approx(p["linea_base"] * 0.05)


def test_ruta_critica_sin_holgura_y_hitos_en_fecha(m):
    filas = {f["id"]: f for f in m["filas"]}
    for aid in m["ruta_critica"]:
        assert filas[aid]["holgura"] == 0
    assert m["hitos"]["H1"]["fecha"] == "2026-12-18"
    assert m["avisos"] == []


def test_actividad_fuera_de_la_edt_falla(monkeypatch):
    datos = copy.deepcopy(P.plan())
    datos["actividades"].append({"id": "9.9.9", "paquete": "9.9", "nombre": "x", "dur": 1, "pred": ["H0"], "horas": {"Nick": 1}})
    monkeypatch.setattr(P, "plan", lambda: datos)
    with pytest.raises(P.PlanError):
        P.presupuesto()


def test_horas_distintas_del_diccionario_fallan(monkeypatch):
    datos = copy.deepcopy(P.plan())
    for a in datos["actividades"]:
        if a["id"] == "4.3.1":
            a["horas"] = {"Nick": 7}
    monkeypatch.setattr(P, "plan", lambda: datos)
    with pytest.raises(P.PlanError):
        P.presupuesto()


def test_backlog_coherente(m):
    ag = m["agil"]
    assert all(s["puntos"] <= ag["capacidad"] for s in ag["sprints"])
    assert all(h["sprint"] for h in ag["historias"] if h["moscow"] == "Must")


def test_sprint_sobre_capacidad_falla(monkeypatch, m):
    datos = copy.deepcopy(agil.agil())
    datos["capacidad_puntos"] = 5
    monkeypatch.setattr(agil, "agil", lambda: datos)
    with pytest.raises(P.PlanError):
        agil.modelo(P.programar(), P.calendario(), P.actividades(), P.PlanError)
