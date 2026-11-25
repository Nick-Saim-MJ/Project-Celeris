"""Pruebas del modelo del Business Case (CE01 E2, CI-102): consistencia AHP, VAN único y Monte Carlo reproducible."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "gestion"))
sys.path.insert(0, str(RAIZ / "gestion" / "analytics"))

import business_case as bcm  # noqa: E402
import ce01_datos as cd  # noqa: E402


def test_ahp_consistente_y_pesos_suman_uno():
    a = bcm.ahp()
    assert a["cr"] < 0.10
    assert sum(a["pesos"]) == pytest.approx(1.0)
    assert a["dif_max_autovector"] < 0.02


def test_ahp_inconsistente_falla(monkeypatch):
    datos = bcm.bc()
    pares = [dict(p) for p in datos["ahp"]["pares"]]
    for p in pares:  # C1 ≫ C2, C2 ≫ C3 y a la vez C3 ≫ C1: intransitivo
        if (p["a"], p["b"]) in {("C1", "C2"), ("C2", "C3")}:
            p["v"] = 9
        if (p["a"], p["b"]) == ("C1", "C3"):
            p["v"] = 1 / 9
    monkeypatch.setattr(bcm, "bc", lambda: datos | {"ahp": datos["ahp"] | {"pares": pares}})
    with pytest.raises(bcm.ModeloError):
        bcm.ahp()


def test_van_del_modelo_igual_al_de_ce01_datos():
    assert bcm.evaluar()["van"] == pytest.approx(cd.van(), abs=0.05)


def test_montecarlo_reproducible_y_coherente_con_evaluar():
    m1, m2 = bcm.montecarlo(), bcm.montecarlo()
    assert m1["p50"] == m2["p50"] and m1["p_van_positivo"] == m2["p_van_positivo"]
    assert m1["iteraciones"] == 10000
    muestra = dict(m1["muestra_control"])
    van = muestra.pop("van")
    assert bcm.evaluar(**muestra)["van"] == pytest.approx(van, abs=0.5)
