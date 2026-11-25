# docs/fuentes/CE01 — Fuentes oficiales de CE01 Gestión de TI (S1, E1–E4)

| Archivo | Qué es | Estado |
| --- | --- | --- |
| `E1-E4-contenido-y-rubrica.md` | Texto **literal** del EPE, área B (GTI), para CE01 S1: descripción del producto, contenido mínimo y rúbrica de los 4 entregables y lista de evidencias CE0111–CE0135. Sin resumir. | **Pendiente (CI-99)**: el texto no estaba en el repositorio al ejecutar P0 |
| `contenido-minimo.yaml` | Los títulos del contenido mínimo y los criterios de la rúbrica en forma legible por máquina. Lo usan `gestion/build_informe_ce01.py` y `gestion/validate_ce01.py` | Preliminar (`cotejado: false`), tomado de la guía CE01 v0.4 |
| Plantilla DOCX oficial de CE01 | Si el docente entrega una, va aquí; el generador la usa en lugar de la portada UPeU de CE03 | No existe: la estructura del informe es la del contenido mínimo, título por título |

## Cómo cerrar CI-99

1. Pegar en `E1-E4-contenido-y-rubrica.md` el bloque «B. ÁREA DE GESTIÓN DE TECNOLOGÍAS DE INFORMACIÓN» de
   `transcripcion.md`, completo hasta antes de «Entregable 5».
2. En `contenido-minimo.yaml`, igualar cada `titulo` y `criterio` al texto literal, completar `excelente` y poner
   `meta.cotejado: true`.
3. `mingw32-make validate-ce01` (o `make validate-ce01`): falla si un título o un criterio del YAML no aparece tal cual
   en el texto literal.
