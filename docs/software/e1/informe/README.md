# Informe del Entregable 1 de CE02 — Requerimientos y Diseño del Sistema

Se genera con `make informe-ce02`, o con `python docs/software/e1/build_informe_ce02.py --pdf`. La salida va a
`entregables/CE02/Informe_Requerimientos_Diseno_CE02_E1_v0.4.docx` y `.pdf`. El PDF lo exporta Microsoft Word,
que también actualiza el índice.

La estructura es la plantilla oficial, título por título (`docs/fuentes/CE02/E1-plantilla-y-rubrica.md`).

| Parte | Fuente |
| --- | --- |
| Portada | `portada.yaml` + portada UPeU (`docs/infra/e1/portada-upeu.docx`) + `equipo` del Marco común |
| Resumen ejecutivo | `00-resumen.md` (las cifras `{{dato:…}}` se calculan desde el SRS) |
| Sección 0 | `05-seccion-0.md`: prefijos; supuestos y decisiones generados desde `infra/trazabilidad.yaml` |
| Sección 1 | `10-requerimientos.md`, que incluye bloques de `../srs/03…09-*.md` (la matriz 1.12.2 pasa al Anexo B) |
| Sección 2 | `20-prototipo.md` + `../prototipo/png/` |
| Sección 3 | `30-arquitectura.md`, que incluye bloques de `../arquitectura/seccion-3.md` + DS-20…DS-22 |
| Sección 4 | `40-diseno-detallado.md` + `../diagramas/png/` |
| Anexo A | `A-acta-validacion.md` (protocolo y acta en blanco: **pendiente**) |
| Anexo B | `B-trazabilidad.md`; la matriz la arma el generador |
| Anexo C | `C-diagramas.md` |
| Anexo D | `D-sustentacion.md` (guion y preguntas; registro **pendiente**) |

**Sintaxis.** Es Markdown con siete marcas propias:

- `{{figura:DS-xx|qué observar}}` (`DS-xx@0.85` reduce el ancho)
- `{{figura_prototipo:archivo|leyenda|qué observar}}`
- `{{rejilla:P-01-…|P-02-…}}` (pantallas en tres columnas)
- `{{tabla:matriz}}`, `{{tabla:supuestos}}`, `{{tabla:decisiones}}`, `{{tabla:gherkin}}` (tablas generadas)
- `{{par_uml:DS-a|DS-b|qué observar}}` (casos de uso y clases de un CU, lado a lado)
- `{{dato:clave}}` (cifras calculadas desde el SRS)
- `{{incluir:archivo|encabezado[|tabla|sin_intro]}}`: copia el bloque bajo ese encabezado y
  renumera sus referencias al SRS (1.10 → 1.5, 1.12 → Anexo B, …)

**Comprobaciones del Anexo B.** El generador falla si no cuadran:

- los requisitos del SRS y los de la tabla de componentes;
- cada componente de DS-13 y DS-22 con al menos un requisito;
- cada pantalla con al menos un requisito.

**Límite de 30 páginas.**

- El cuerpo va de la portada al final de la Sección 4. Sus páginas quedan en `paginas.json` (`paginas_cuerpo`).
- Los anexos no cuentan.

**Pendientes.** Quedan como `[COMPLETAR]`:

- el semestre de la portada;
- el acta de validación;
- el registro de la sustentación.
