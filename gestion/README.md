# gestion/ — CE01 Gestión de TI (S1, entregables E1–E4)

Base común creada en P0. Los informes los escriben P1 (E1), P2 (E2), P3 (E3) y P4 (E4).

| Archivo | Qué hace |
| --- | --- |
| `ce01.yaml` | Fuente única de CE01: estilo (paleta UPeU), referencias a `infra/*.yaml`, lectura numérica de los S-xx, modelo económico base, criterios, alternativas, riesgos RE/RP, procesos, EDT y RACI |
| `ce01_datos.py` | Cargador: resuelve referencias, verifica cada lectura numérica contra `infra/trazabilidad.yaml`, expone `costos()`, `beneficios()`, `supuestos()`, `datos()` |
| `estilo_ce01.py` | Paleta única para matplotlib, draw.io, BPMN y XLSX (CI-100) |
| `build_informe_ce01.py` | Generador común DOCX + PDF (`--entregable E1…E4 --pdf`) con los chequeos a)–f) |
| `validate_ce01.py` | `make validate-ce01` (lo corre también `make validate`) |
| `figuras_ce01.py` | `make figuras-ce01`: llama a `gestion/eN/figuras/generar.py` de cada entregable |
| `eN/` | Lo de cada entregable (lo crea su prompt) |

## Cómo se escribe un informe (`gestion/eN/informe/NN-*.md`)

- Cada título del contenido mínimo (`docs/fuentes/CE01/contenido-minimo.yaml`) es un título del informe: `# 1.1 Contexto organizacional`.
- **Ninguna cifra a mano**: `{{dato:clave}}` (de `ce01_datos.datos()` o de `eN/datos/*.json`). El generador rechaza
  US$, %, h, min, GB, TB, Mbps, W o kWh escritos en el texto.
- **Figuras** (CI-100): registradas en `eN/figuras/figuras.yaml` (`archivo`, `titulo`, `fuente`, `horizontal`). Siempre:

  ```markdown
  Párrafo que introduce la figura y la cita: la {{ref:fig-ishikawa}} agrupa las causas…

  {{figura:fig-ishikawa}}

  Párrafo que interpreta sus resultados clave (≥ 20 palabras): qué muestra, qué se concluye y qué decide.
  ```

  Sale como «Figura 1.4. Diagrama de Ishikawa…» debajo de la figura, con «Fuente: …».
- **Tablas**: generadas con `{{tabla:id}}` (`eN/tablas.py`) o escritas a mano con una línea de título antes:

  ```markdown
  Tabla: t-fce | Factores críticos de éxito | Elaboración propia a partir de la guía CE01 B1.3
  | FCE | KPI | Meta |
  | --- | --- | --- |
  ```

  Sale como «Tabla 1.2. Factores críticos de éxito» encima y la fuente debajo. Toda tabla se cita con `{{ref:id}}`.
- Supuestos: `[S-xx]`. El anexo «Supuestos citados» y la «Autoevaluación contra la rúbrica» (`eN/autoevaluacion.yaml`)
  se generan solos.

## Identidad visual (CI-100)

Azul UPeU `#003865` y ámbar UPeU `#F8A800` (muestreados del logotipo de la portada), con tintes y grises. El color
nunca va solo: cada barra, celda o carril lleva texto. Los mapas de calor de riesgo usan rojo/ámbar/verde con el nivel
escrito. PNG de 200 dpi, Calibri, 25,7 × 13,4 cm como máximo en página horizontal (CI-90).

## Comandos (en esta PC, `mingw32-make PYTHON=python …`)

`make validate-ce01` · `make figuras-ce01` · `make informe-ce01-e1` … `make informe-ce01-e4`

## Estado

- Contenido mínimo y rúbrica cotejados con el texto literal del EPE (CI-99 resuelto): el generador exige cada título y
  cada ítem del contenido mínimo como subtítulo.
- Archi 5.12 instalado (vista de motivación del E1).
- E1 (P1) generado: informe, matrices XLSX, figuras y vista ArchiMate (`gestion/e1/README.md`). Pendiente: entrevista
  COBIT con la DTI (`actual: null`) y datos marcados [levantar con la DTI].
- E2 (P2) generado: informe, Business Case XLSX con fórmulas vivas (VAN de Excel = VAN de Python), Monte Carlo,
  AHP y figuras (`gestion/e2/README.md`, CI-102). Pendiente: sesión de pesos con la DTI, costo de A5, cotización del
  ISP y mediciones del piloto.
- Aviso abierto: la fila RACI «Prototipo de la consola y validación» no tiene aprobador (lo define P3).
