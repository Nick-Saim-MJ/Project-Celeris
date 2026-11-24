# Entregable 2 — Análisis y diseño de centro de datos híbrido (CE0331)

Solo diseño: no toca `deploy/opentofu/`, `lab/` ni `src/`, no crea recursos en AWS ni ejecuta `tofu apply`.

| Pieza | Fuente | Generador | Salida |
| --- | --- | --- | --- |
| Datos | `infra/centro_datos.yaml` (+ `infra/inventory.yaml`) | — | V-90…V-94 |
| Diagramas DC-0…DC-3 | los dos YAML | `infra/gen/drawio_dc.py`, `infra/gen/exportar_dc.py` | `entregables/CE0331/diagramas/` (.drawio, .png a escala 3, .pdf); V-100…V-103 |
| Matriz y dimensionamiento | los dos YAML y `cobertura-figuras.json` | `infra/gen/xlsx_centro_datos.py --verificar` | `entregables/CE0331/Matriz_Componentes_DC_v1.0.xlsx`; V-104…V-107 |
| Informe | `docs/infra/e2/informe/*.md` y los dos YAML | `docs/infra/e2/build_informe.py --pdf` | `entregables/CE0331/Informe_Centro_Datos_v1.0.docx` y `.pdf`; V-95…V-99 |

Orden de regeneración: `make diagrams-dc`, `make diagrams-dc-check`, `make matrices-dc`, `make informe-dc` y `make validate`. Sin GNU make, los mismos comandos con `python`.

- La integración híbrida no se redibuja: el informe usa `entregables/CE0311/diagramas/FIG-5.4.png` tal cual (V-98 comprueba que no cambió).
- `exportar_dc.py` usa draw.io Desktop si está instalado; si no, un respaldo con Edge o Chrome sin interfaz que dibuja los stencils como glifos (ver `exportacion.json`). El `.drawio` conserva los íconos de draw.io.
- El PDF del informe lo exporta Word (COM) o LibreOffice; la matriz se recalcula con LibreOffice o, si no está, con Excel (COM).
- Contradicciones y vacíos: CI-77…CI-88 en `docs/infra/e1/CAMBIOS-INVENTARIO.md`.
- `autoevaluacion-informe.md`: nivel estimado por criterio y qué falta para el nivel 4.
