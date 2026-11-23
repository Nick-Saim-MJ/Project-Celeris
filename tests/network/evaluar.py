"""Evaluador de `criterio_aprobacion` de infra/pruebas.yaml.

Cada criterio se evalúa solo con lo que el caso de prueba midió en el laboratorio (códigos de salida, textos, medidas).
Un criterio que no se puede evaluar en el Modo L (intervención humana, Wazuh sin desplegar…) queda NO_EVALUADO con su
motivo: nunca se cuenta como cumplido. El resultado de la prueba se deriva así:

    algún criterio FALLA                             → FALLA
    todos PASA y la medición no fue vacía            → PASA
    hay PASA y NO_EVALUADO, o la medición fue vacía  → PARCIAL   (no es PASA: la parte sin evaluar queda para otro modo)
    ninguno evaluable                                → NO_APLICA
"""
from __future__ import annotations

import operator
import re
from dataclasses import dataclass, field

OPERADORES = {"<=": operator.le, ">=": operator.ge, "==": operator.eq, "!=": operator.ne, "<": operator.lt, ">": operator.gt}


@dataclass
class Medicion:
    """Lo que un caso de prueba midió. Los nombres de las claves son los del YAML (`comando_adicional`, `sobre`, `metrica`)."""
    salidas: dict[str, str] = field(default_factory=dict)      # fuente de texto → contenido
    codigos: dict[str, int] = field(default_factory=dict)      # "principal" o comando_adicional → código de salida
    medidas: dict[str, float] = field(default_factory=dict)    # métrica → valor
    no_evaluable: dict[str, str] = field(default_factory=dict) # fuente/métrica/«manual» → motivo
    vacia: str = ""                                            # si no está vacío: la medición no ejercitó lo que la prueba valida
    hallazgos: list[str] = field(default_factory=list)         # observaciones que contradicen o precisan el diseño


@dataclass
class ResultadoCriterio:
    indice: int
    descripcion: str
    estado: str            # PASA | FALLA | NO_EVALUADO
    medido: object = None
    detalle: str = ""


def describir(c: dict) -> str:
    t = c["tipo"]
    if t == "exit_code":
        base = "código de salida = 0" if c.get("valor") == 0 else "código de salida ≠ 0"
        return base + (f" ({c['comando_adicional']})" if c.get("comando_adicional") else "")
    if t == "regex":
        neg = "" if c.get("debe_coincidir", True) else "sin coincidencia con "
        return f"{neg}/{c['patron']}/ sobre {c.get('comando_adicional') or c.get('sobre', 'stdout')}"
    if t in ("umbral", "contador"):
        return f"{c['metrica']} {c['operador']} {c['valor']}"
    return c.get("descripcion", "verificación manual")


def evaluar_criterio(i: int, c: dict, m: Medicion) -> ResultadoCriterio:
    d = describir(c)
    t = c["tipo"]
    if t == "manual":
        return ResultadoCriterio(i, d, "NO_EVALUADO", detalle=m.no_evaluable.get("manual", "requiere intervención humana"))
    if t == "exit_code":
        clave = c.get("comando_adicional") or "principal"
        if clave not in m.codigos:
            return ResultadoCriterio(i, d, "NO_EVALUADO", detalle=m.no_evaluable.get(clave, f"el caso no midió «{clave}»"))
        rc = m.codigos[clave]
        ok = rc == 0 if c.get("valor") == 0 else rc != 0
        return ResultadoCriterio(i, d, "PASA" if ok else "FALLA", medido=rc, detalle=f"salida {rc}")
    if t == "regex":
        fuente = c.get("sobre", "stdout")
        clave = c.get("comando_adicional") if c.get("comando_adicional") in m.salidas else fuente
        if clave not in m.salidas:
            return ResultadoCriterio(i, d, "NO_EVALUADO", detalle=m.no_evaluable.get(clave, m.no_evaluable.get(fuente, f"sin fuente «{clave}»")))
        encontrado = re.search(c["patron"], m.salidas[clave]) is not None
        ok = encontrado == c.get("debe_coincidir", True)
        extra = re.search(c["patron"], m.salidas[clave])
        return ResultadoCriterio(i, d, "PASA" if ok else "FALLA", medido=extra.group(0)[:80] if extra else None,
                                 detalle="coincide" if encontrado else "no coincide")
    if t in ("umbral", "contador"):
        k = c["metrica"]
        if k not in m.medidas:
            return ResultadoCriterio(i, d, "NO_EVALUADO", detalle=m.no_evaluable.get(k, f"el caso no midió «{k}»"))
        v = m.medidas[k]
        ok = OPERADORES[c["operador"]](v, c["valor"])
        return ResultadoCriterio(i, d, "PASA" if ok else "FALLA", medido=v, detalle=f"{k} = {v}")
    raise ValueError(f"tipo de criterio desconocido: {t}")


def evaluar(criterios: list[dict], m: Medicion) -> tuple[str, list[ResultadoCriterio], str]:
    """(resultado, detalle por criterio, motivo)."""
    rs = [evaluar_criterio(i, c, m) for i, c in enumerate(criterios)]
    estados = {r.estado for r in rs}
    if "FALLA" in estados:
        return "FALLA", rs, "; ".join(f"{r.descripcion}: {r.detalle}" for r in rs if r.estado == "FALLA")
    if estados == {"NO_EVALUADO"}:
        return "NO_APLICA", rs, "ningún criterio es evaluable en el Modo L: " + "; ".join(sorted({r.detalle for r in rs}))
    if "NO_EVALUADO" in estados:
        return "PARCIAL", rs, "sin evaluar: " + "; ".join(f"{r.descripcion} ({r.detalle})" for r in rs if r.estado == "NO_EVALUADO")
    if m.vacia:
        return "PARCIAL", rs, f"medición vacía: {m.vacia}"
    return "PASA", rs, ""
