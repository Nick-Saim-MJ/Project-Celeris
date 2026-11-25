"""Cifras del Entregable 1 (CE01): el «cuánto» del problema, calculado desde los supuestos S-xx.

    python gestion/e1/calculos.py        # escribe gestion/e1/datos/e1.json e imprime el resumen

Ninguna cifra del informe E1 se escribe a mano: el Markdown usa {{dato:clave}} y las claves salen de aquí (o de
gestion/ce01_datos.datos()). Cada cálculo nombra los supuestos que usa.

Lecturas de metas de los objetivos OB-x (infra/trazabilidad.yaml → objetivos_proyecto): igual que los supuestos
(CI-97), se declara el texto exacto de la meta y se comprueba que siga ahí; si alguien cambia la meta, este script falla.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import ce01_datos as cd  # noqa: E402
from ce01_datos import num, pct, s, usd  # noqa: E402

SALIDA = AQUI / "datos" / "e1.json"

# OB-x → (valor numérico, texto exacto dentro de `meta`)
LECTURAS_OB = {
    "OB-1": (0.25, "25 %"),
    "OB-2": (0.70, "70 %"),
    "OB-4": (1.00, "100 %"),
}


def metas_ob() -> dict[str, float]:
    obs = {o["id"]: o for o in cd.objetivos()}
    out = {}
    for oid, (valor, texto) in LECTURAS_OB.items():
        if texto not in obs[oid]["meta"]:
            raise cd.DatosCE01Error(f"{oid}: la meta «{obs[oid]['meta']}» ya no contiene «{texto}»; "
                                    "actualice LECTURAS_OB en gestion/e1/calculos.py")
        out[oid] = valor
    return out


def calcular() -> dict:
    pcs_lab, labs, pcs = s("S-26.pcs_lab"), s("S-26.laboratorios"), s("S-01.pcs")
    gb_pc, ciclos, enlace = s("S-27.gb_pc"), s("S-06.ciclos_anio"), s("S-02.enlace_mbps")
    m = metas_ob()
    b = {x["id"]: x["usd"] for x in cd.beneficios()["lista"]}
    n = cd.cargar()["economia"]["horizonte_anios"]

    gb_ciclo_lab = pcs_lab * gb_pc                           # 40 × S-27
    gb_repetidos_lab = (pcs_lab - 1) * gb_pc                 # todas las copias menos la primera
    horas_lab = gb_ciclo_lab * 8 * 1000 / enlace / 3600      # GB → Gb → Mb ÷ Mbps → s → h, con TODO el enlace [S-02]
    horas_lab_meta = horas_lab * (1 - m["OB-2"])
    re_ = cd.cargar()["riesgos_estrategicos"]["lista"]
    puntajes = [r["p"] * r["i"] for r in re_]
    return {
        "pcs_lab": pcs_lab, "labs": labs, "pcs": pcs, "gb_pc": gb_pc, "ciclos": ciclos, "enlace": enlace,
        "gb_ciclo_lab": gb_ciclo_lab,
        "gb_repetidos_lab": gb_repetidos_lab,
        "gb_ciclo_total": pcs * gb_pc,
        "gb_repetidos_ciclo": gb_repetidos_lab * labs,
        "gb_repetidos_anio": gb_repetidos_lab * labs * ciclos,
        "fraccion_repetida": gb_repetidos_lab / gb_ciclo_lab,
        "horas_lab": horas_lab,
        "horas_lab_meta": horas_lab_meta,
        "horas_tecnicas_anio": pcs * ciclos * s("S-07.horas_pc_ciclo"),
        "usd_enlace_anio": b["BN-1"],
        "usd_horas_anio": b["BN-2"],
        "usd_no_actuar": (b["BN-1"] + b["BN-2"]) * n,
        "metas": m,
        "re_altos": sum(p >= 15 for p in puntajes),
        "re_medios": sum(8 <= p < 15 for p in puntajes),
        "re_bajos": sum(p < 8 for p in puntajes),
        "re_max": max(puntajes),
    }


def datos(c: dict | None = None) -> dict[str, str]:
    c = c or calcular()
    return {
        "pcs_lab": num(c["pcs_lab"]),
        "labs": num(c["labs"]),
        "pcs": num(c["pcs"]),
        "gb_pc": f"{num(c['gb_pc'])} GB",
        "enlace": f"{num(c['enlace'])} Mbps",
        "usd_mbps": usd(s("S-03.usd_mbps_mes")),
        "ciclos": num(c["ciclos"]),
        "gb_ciclo_lab": f"{num(c['gb_ciclo_lab'])} GB",
        "gb_repetidos_lab": f"{num(c['gb_repetidos_lab'])} GB",
        "gb_ciclo_total": f"{num(c['gb_ciclo_total'])} GB",
        "gb_repetidos_ciclo": f"{num(c['gb_repetidos_ciclo'])} GB",
        "gb_repetidos_anio": f"{num(c['gb_repetidos_anio'])} GB",
        "tb_repetidos_anio": f"{num(c['gb_repetidos_anio'] / 1000, 1)} TB",
        "fraccion_repetida": pct(c["fraccion_repetida"], 1),
        "horas_lab": f"{num(c['horas_lab'], 2)} h",
        "min_lab": f"{num(c['horas_lab'] * 60)} min",
        "min_lab_meta": f"{num(c['horas_lab_meta'] * 60)} min",
        "meta_ob1": pct(c["metas"]["OB-1"]),
        "meta_ob2": pct(c["metas"]["OB-2"]),
        "meta_ob4": pct(c["metas"]["OB-4"]),
        "horas_tecnicas_anio": f"{num(c['horas_tecnicas_anio'])} h",
        "usd_enlace_anio": usd(c["usd_enlace_anio"]),
        "usd_horas_anio": usd(c["usd_horas_anio"]),
        "usd_no_actuar": usd(c["usd_no_actuar"]),
        "re_altos": num(c["re_altos"]),
        "re_medios": num(c["re_medios"]),
        "re_bajos": num(c["re_bajos"]),
        "re_max": num(c["re_max"]),
    }


def main() -> int:
    d = datos()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps({"fuente": "gestion/e1/calculos.py", "datos": d}, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    for k, v in d.items():
        print(f"{k:22} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
