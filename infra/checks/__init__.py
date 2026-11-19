"""Ganchos del validador (infra/validate.py) para los artefactos de P2–P5.

Cada módulo `vN0_*.py` define:
    GRUPO        "P2" … "P5": quién lo implementa
    PRIMER_ID    primer ID de chequeo del grupo ("V-50", "V-60", "V-70", "V-80")
    DESCRIPCION  qué validará
    run(infra)   -> list[validate.Resultado] | None
                 None = aún sin implementar (se informa «PENDIENTE de P#» y no falla)

Para implementarlo: devolver una lista de `Resultado` (importar desde `validate`), con IDs desde PRIMER_ID.
Reglas comunes: no leer los YAML por su cuenta (usar `infra`, de celeris_infra.Infra) y decir cómo corregir.
"""
