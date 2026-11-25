# gestion/e2/ — CE01 E2: Business Case del Proyecto

Informe: `entregables/CE01/E2/Informe_CE01_E2_v0.1.docx` y `.pdf`. Modelo con fórmulas vivas:
`entregables/CE01/E2/Business_Case_E2.xlsx`. Todo se regenera; no se edita el DOCX, el PDF ni el XLSX a mano.

## Qué hay aquí

| Ruta | Contenido |
| --- | --- |
| `datos/business_case.yaml` | Lo propio del E2 (CI-102): rangos de Monte Carlo, juicios AHP con su motivo, fichas y costo de las alternativas A0–A5, justificación de cada puntaje, escenarios de estrés RE-01…RE-12, beneficios cualitativos, indicadores de valor, árbol de objetivos, BDN y plazos SMART |
| `datos/resultados.json` | Generado por `gestion/analytics/business_case.py` (no editar) |
| `../analytics/business_case.py` | Modelo económico (VAN, TIR, payback, B/C, ROI, equilibrio), Monte Carlo (10 000 iteraciones, semilla fija), tornado, escenarios, AHP (falla si CR ≥ 0,10), TCO, matriz ponderada, sensibilidad de pesos, Pugh y efecto económico de los riesgos |
| `../analytics/business_case_xlsx.py` | Libro XLSX con fórmulas vivas; lo recalcula con Excel (o LibreOffice) y falla si el VAN de Excel difiere del de Python en más de US$ 1 |
| `tablas.py` | Tablas `{{tabla:t-…}}` del informe |
| `figuras/generar.py` | Árbol de objetivos y BDN (draw.io); TCO, matriz, sensibilidad, flujo, Monte Carlo, tornado y mapa de riesgos con ΔVAN (matplotlib) |
| `informe/*.md` | Texto del informe, §2.1–§2.6, referencias IEEE y anexos A (Pugh) y B (juicios AHP); los anexos C (supuestos) y D (autoevaluación) se generan |
| `autoevaluacion.yaml` | Criterio de la rúbrica → evidencia |

## Regenerar (en esta PC: `mingw32-make PYTHON=python …`)

```powershell
mingw32-make PYTHON=python figuras-ce01
```

```powershell
mingw32-make PYTHON=python informe-ce01-e2
```

```powershell
mingw32-make PYTHON=python validate-ce01
```

`informe-ce01-e2` corre primero el modelo (JSON + XLSX verificado), luego el generador; necesita Microsoft Word (PDF)
y Excel o LibreOffice (recálculo del XLSX). `figuras-ce01` necesita draw.io Desktop.

## Pasos manuales (actualizan el modelo sin tocar el código)

1. **Sesión de ponderación con la DTI.** Repetir las quince comparaciones del anexo B; actualizar `ahp.pares` en
   `datos/business_case.yaml`. El modelo recalcula pesos, CR, matriz y sensibilidad, y falla si el CR llega a 0,10.
2. **Costo de A5 (caché del FortiGate).** Cuando la DTI informe modelo, disco y licencia, reemplazar
   `cota_inferior: true` y las partidas de A5.
3. **Cotización del ISP [S-03].** Actualizar el supuesto en `infra/trazabilidad.yaml` (y su lectura en `gestion/ce01.yaml`).
4. **Mediciones del piloto.** BHR en hora punta [S-04, S-40], adopción del proxy (moda de `montecarlo.variables`) y
   horas técnicas por ciclo [S-07]. Con ellas se regenera el informe; el tornado indica qué supuestos deciden el VAN.
