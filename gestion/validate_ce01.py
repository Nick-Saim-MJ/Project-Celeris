"""Validación de CE01 (make validate-ce01; también la corre make validate).

    python gestion/validate_ce01.py

Comprueba, sin escribir nada:
  1. La fuente única: gestion/ce01.yaml y sus referencias (gestion/ce01_datos.validar()).
  2. El contenido mínimo y la rúbrica (docs/fuentes/CE01): si ya está cotejado, que cada título y cada criterio
     aparezca tal cual en el texto literal del EPE; si no, AVISO (CI-99).
  3. Cada entregable que ya tiene texto (gestion/eN/informe/): los chequeos a)–f) del generador.
  4. Cada entregable que ya tiene DOCX en entregables/CE01/EN/: que exista su PDF.

Código de salida ≠ 0 si hay alguna FALLA. Los AVISOS no detienen make validate.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import build_informe_ce01 as bi  # noqa: E402
import ce01_datos  # noqa: E402


def _norm(t: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", t).split()).casefold()


def main() -> int:
    fallas: list[str] = []
    avisos: list[str] = []
    info: list[str] = []

    # 1. Fuente única
    fallas += [f"ce01.yaml: {e}" for e in ce01_datos.validar(avisos)]
    if not fallas:
        c = ce01_datos.costos()
        info.append(f"fuente única: {len(ce01_datos.supuestos())} supuestos verificados contra infra/trazabilidad.yaml; "
                    f"I0 {ce01_datos.usd(c['capex_total'])}, OPEX {ce01_datos.usd(c['opex_total'])}/año")

    # 2. Contenido mínimo y rúbrica
    cont = yaml.safe_load(bi.CONTENIDO.read_text(encoding="utf-8"))
    literal = bi.RAIZ / cont["meta"]["fuente_literal"]
    if not cont["meta"].get("cotejado"):
        avisos.append(f"docs/fuentes/CE01: contenido mínimo preliminar, sin cotejar con el texto literal del EPE "
                      f"({cont['meta'].get('cambio')}); los informes de CE01 no se pueden generar hasta cerrarlo")
    elif not literal.exists():
        fallas.append(f"contenido-minimo.yaml dice cotejado, pero no existe {cont['meta']['fuente_literal']}")
    else:
        texto = _norm(literal.read_text(encoding="utf-8"))
        for ent, e in cont["entregables"].items():
            for c in e["contenido_minimo"]:
                if _norm(f"{c['id']} {c['titulo']}") not in texto:
                    fallas.append(f"{ent} {c['id']}: «{c['titulo']}» no aparece tal cual en el texto literal del EPE")
                for item in c.get("incluye", []):
                    if _norm(f"- {item}") not in texto:
                        fallas.append(f"{ent} {c['id']}: el ítem «{item}» no aparece tal cual en el texto literal")
            for r in e["rubrica"]:
                if _norm(f"| {r['criterio']} | {r.get('excelente') or ''} |") not in texto:
                    fallas.append(f"{ent}: el criterio «{r['criterio']}» o su descriptor Excelente no aparecen tal cual en el texto literal")
        info.append("contenido mínimo y rúbrica de E1–E4 cotejados con el texto literal del EPE (" +
                    ", ".join(f"{k}: {len(v['contenido_minimo'])} títulos, {sum(len(c.get('incluye', [])) for c in v['contenido_minimo'])} ítems, "
                              f"{len(v['rubrica'])} criterios" for k, v in cont["entregables"].items()) + ")")

    # 3 y 4. Entregables con texto o con DOCX
    for ent in bi.ENTREGABLES:
        if (AQUI / ent.lower() / "informe").is_dir():
            try:
                f = bi.cargar_fuentes(ent)
                problemas = bi.comprobar(f, exigir_cotejado=False)
                fallas += [f"{ent}: {p}" for p in problemas]
                if not problemas:
                    info.append(f"{ent}: chequeos a)–f) en verde")
            except (bi.InformeInvalido, ce01_datos.DatosCE01Error) as e:
                fallas += [f"{ent}: {p}" for p in getattr(e, "problemas", [str(e)])]
        docx = bi.SALIDA / ent / bi.nombre_docx(ent)
        if docx.exists() and not docx.with_suffix(".pdf").exists():
            fallas.append(f"{ent}: existe {docx.name} pero no su PDF (make informe-ce01-{ent.lower()})")
    if not any((AQUI / e.lower() / "informe").is_dir() for e in bi.ENTREGABLES):
        info.append("ningún entregable de CE01 tiene texto todavía (P1–P4)")

    for x in info:
        print(f"[ OK ]     CE01  {x}")
    for x in avisos:
        print(f"[ AVISO ]  CE01  {x}")
    for x in fallas:
        print(f"[ FALLA ]  CE01  {x}")
    print(f"CE01: {len(fallas)} FALLA · {len(avisos)} avisos")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
