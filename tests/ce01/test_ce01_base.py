"""Pruebas de la base común de CE01 (P0): fuente única, cargador y generador de informes.

Usan un entregable de juguete en un directorio temporal: cada prueba rompe una sola regla y comprueba que el
generador la detecta (chequeos a–f de gestion/build_informe_ce01.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "gestion"))

import build_informe_ce01 as bi  # noqa: E402
import ce01_datos  # noqa: E402

INTERPRETACION = ("La figura muestra que la mayor parte del tráfico repetido se concentra en las horas de clase, "
                  "lo que confirma que el problema es de coincidencia temporal y no solo de volumen total.")


def _contenido(tmp: Path, cotejado: bool = True) -> Path:
    c = yaml.safe_load(bi.CONTENIDO.read_text(encoding="utf-8"))
    c["meta"]["cotejado"] = cotejado
    p = tmp / "contenido.yaml"
    p.write_text(yaml.safe_dump(c, allow_unicode=True), encoding="utf-8")
    return p


def _png(ruta: Path):
    from PIL import Image
    ruta.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (800, 400), "#003865").save(ruta)


def _entregable(tmp: Path, **cambios) -> Path:
    """Entregable E1 válido; `cambios` reemplaza archivos (ruta relativa → texto) o los quita (→ None)."""
    base = tmp / "gestion"
    archivos = {
        "e1/informe/00-resumen.md": "# Resumen ejecutivo\n\nEl enlace se satura en horas de clase [S-02].\n",
        "e1/informe/10-cuerpo.md": "\n".join([
            "# 1.1 Contexto organizacional",
            "",
            "La {{ref:fig-trafico}} resume el tráfico de un día típico de laboratorio.",
            "",
            "{{figura:fig-trafico}}",
            "",
            INTERPRETACION,
            "",
            "# 1.2 Análisis estratégico",
            "",
            "La inversión inicial es {{dato:capex_total}} [S-08] y la {{ref:t-fce}} lista los factores críticos.",
            "",
            "Tabla: t-fce | Factores críticos de éxito | Elaboración propia",
            "| FCE | KPI |",
            "| --- | --- |",
            "| Apoyo de la DTI | Reuniones atendidas |",
            "",
            "# 1.3 Diagnóstico digital / TI",
            "",
            "Texto del diagnóstico.",
            "",
            "# 1.4 Identificación del problema",
            "",
            "Texto del problema.",
        ]) + "\n",
        "e1/figuras/figuras.yaml": yaml.safe_dump({"fig-trafico": {
            "archivo": "trafico.png", "titulo": "Tráfico de un día de laboratorio", "fuente": "Elaboración propia",
            "horizontal": True}}, allow_unicode=True),
        "e1/autoevaluacion.yaml": yaml.safe_dump([
            {"criterio": "Análisis del contexto organizacional", "evidencia": ["Contexto organizacional", "fig-trafico"]},
            {"criterio": "Identificación de brechas estratégicas", "evidencia": ["Diagnóstico digital / TI"]},
            {"criterio": "Alineamiento estratégico del proyecto", "evidencia": ["t-fce"]},
            {"criterio": "Sustentación y defensa técnica", "evidencia": ["Identificación del problema"]},
        ], allow_unicode=True),
    }
    archivos.update(cambios)
    for rel, txt in archivos.items():
        if txt is None:
            continue
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
    _png(base / "e1" / "figuras" / "trafico.png")
    return base


def _problemas(tmp: Path, cotejado: bool = True, **cambios) -> list[str]:
    f = bi.cargar_fuentes("E1", _entregable(tmp, **cambios), _contenido(tmp, cotejado))
    return bi.comprobar(f)


# ------------------------------------------------------------------ fuente única y cargador
def test_fuente_unica_coherente():
    assert ce01_datos.validar() == []


def test_valores_de_control():
    c, b = ce01_datos.costos(), ce01_datos.beneficios()
    assert c["capex_total"] == 5300                       # S-08 + S-37 + S-38 + S-39
    assert round(c["aws_mensual"], 2) == 69.58            # suma C1–C7, no «≈ 70» (CI-98)
    assert round(c["opex"][1]["usd"], 2) == 630.72        # 480 W × 8 760 h × US$ 0,15
    assert b["mbps_diferidos"] == pytest.approx(90)       # S-40 = 30 % × 300 Mbps
    assert round(ce01_datos.flujo_neto_anual()) == 7644


def test_lectura_desactualizada_falla(monkeypatch):
    original = ce01_datos._yaml

    def falso(ruta):
        d = original(ruta)
        if ruta == "infra/trazabilidad.yaml":
            d = {**d, "supuestos": {**d["supuestos"], "S-03": {**d["supuestos"]["S-03"], "valor": "US$ 10 por Mbps-mes"}}}
        return d
    ce01_datos.supuestos.cache_clear()
    monkeypatch.setattr(ce01_datos, "_yaml", falso)
    try:
        with pytest.raises(ce01_datos.DatosCE01Error, match="S-03"):
            ce01_datos.supuestos()
    finally:
        ce01_datos.supuestos.cache_clear()


def test_formato_peruano():
    assert ce01_datos.usd(1995.68) == "US$ 1 996"
    assert ce01_datos.usd(69.584, 2) == "US$ 69,58"
    assert ce01_datos.pct(0.3) == "30 %"


# ------------------------------------------------------------------ generador: caso válido
def test_entregable_valido_genera_docx(tmp_path):
    base = _entregable(tmp_path)
    ruta = bi.generar("E1", tmp_path / "salida", base_dir=base, contenido=_contenido(tmp_path))
    assert ruta.exists() and ruta.name.startswith("Informe_CE01_E1_v")
    from docx import Document
    texto = "\n".join(p.text for p in Document(str(ruta)).paragraphs)
    assert "Figura 1.1. Tráfico de un día de laboratorio" in texto
    assert "Tabla 1.1. Factores críticos de éxito" in texto
    assert "La Figura 1.1 resume" in texto
    assert "US$ 5 300" in texto
    assert "Fuente: Elaboración propia." in texto
    assert "Anexo A. Supuestos citados en el informe" in texto
    assert "Anexo B. Autoevaluación contra la rúbrica" in texto


# ------------------------------------------------------------------ generador: cada regla
def test_a_contenido_no_cotejado(tmp_path):
    assert any(p.startswith("a)") and "cotejado" in p for p in _problemas(tmp_path, cotejado=False))


def test_a_falta_titulo(tmp_path):
    cuerpo = (_entregable(tmp_path) / "e1/informe/10-cuerpo.md").read_text(encoding="utf-8")
    p = _problemas(tmp_path, **{"e1/informe/10-cuerpo.md": cuerpo.replace("# 1.3 Diagnóstico digital / TI", "# Otro")})
    assert any("1.3" in x and x.startswith("a)") for x in p)


def test_b_marca_sin_resolver(tmp_path):
    p = _problemas(tmp_path, **{"e1/informe/00-resumen.md": "# Resumen\n\nVAN de {{dato:no_existe}}.\n"})
    assert any(x.startswith("b)") and "no_existe" in x for x in p)


def test_c_figura_inexistente(tmp_path):
    p = _problemas(tmp_path, **{"e1/figuras/figuras.yaml": "{}\n"})
    assert any(x.startswith("c)") for x in p)


def test_d_cifra_a_mano(tmp_path):
    p = _problemas(tmp_path, **{"e1/informe/00-resumen.md": "# Resumen\n\nEl ahorro es de US$ 9 600 al año y 30 %.\n"})
    assert sum(x.startswith("d)") for x in p) == 2


def test_e_figura_sin_parrafo_previo_ni_interpretacion(tmp_path):
    cuerpo = (_entregable(tmp_path) / "e1/informe/10-cuerpo.md").read_text(encoding="utf-8")
    cuerpo = cuerpo.replace("La {{ref:fig-trafico}} resume el tráfico de un día típico de laboratorio.", "Texto suelto.")
    cuerpo = cuerpo.replace(INTERPRETACION, "Breve.")
    p = _problemas(tmp_path, **{"e1/informe/10-cuerpo.md": cuerpo})
    assert any("párrafo previo" in x for x in p)
    assert any("interpretación" in x for x in p)


def test_e_tabla_sin_titulo(tmp_path):
    cuerpo = (_entregable(tmp_path) / "e1/informe/10-cuerpo.md").read_text(encoding="utf-8")
    cuerpo = cuerpo.replace("Tabla: t-fce | Factores críticos de éxito | Elaboración propia\n", "")
    p = _problemas(tmp_path, **{"e1/informe/10-cuerpo.md": cuerpo})
    assert any("tabla sin título" in x for x in p)


def test_f_autoevaluacion_incompleta(tmp_path):
    p = _problemas(tmp_path, **{"e1/autoevaluacion.yaml": yaml.safe_dump(
        [{"criterio": "Análisis del contexto organizacional", "evidencia": ["Sección que no existe"]}], allow_unicode=True)})
    assert sum(x.startswith("f)") for x in p) >= 4      # 3 criterios sin evidencia + 1 evidencia inexistente


def test_estilo_paleta_unica():
    import estilo_ce01 as est
    assert est.color("azul_upeu") == "#003865"
    assert est.serie(0) == "#003865" and est.serie(1) == "#F8A800"
    assert est.nivel_riesgo(20)[1] == "ALTO" and est.nivel_riesgo(10)[1] == "MEDIO" and est.nivel_riesgo(4)[1] == "BAJO"
