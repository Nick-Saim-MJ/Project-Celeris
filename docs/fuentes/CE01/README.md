# docs/fuentes/CE01 — Fuentes oficiales de CE01 Gestión de TI (S1, E1–E4)

| Archivo | Qué es |
| --- | --- |
| `E1-E4-contenido-y-rubrica.md` | Texto **literal** del EPE 2026, área B (GTI): nombre, descripción, competencias CE011–CE014, evidencias CE0111–CE0145, distribución por semestre y, para E1–E4, descripción del producto, contenido mínimo y rúbrica. Copiado de `transcripcion.md` (líneas 488–805) sin resumir (CI-99) |
| `contenido-minimo.yaml` | Generado desde el texto literal: títulos, ítems («incluye») y los cuatro descriptores de cada criterio. Lo usan `gestion/build_informe_ce01.py` (exige títulos e ítems) y `gestion/validate_ce01.py` (comprueba que todo esté tal cual en el texto literal) |

**Formato de los informes.** El EPE no fija plantilla, extensión ni formato para GTI (CE02 y CE03 sí los tienen): la
estructura de cada informe es su «Contenido mínimo requerido», título por título, y cada ítem es un subtítulo. No hay
plantilla DOCX oficial de CE01; el generador usa la portada UPeU del proyecto y referencias IEEE, como las demás áreas.

Si el texto del EPE cambia: volver a copiar el bloque B, regenerar `contenido-minimo.yaml` y correr `make validate-ce01`.
