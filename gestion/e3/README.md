# gestion/e3/ — CE01 E3: Plan de Gestión del Proyecto (PMBOK / Agile)

Informe: `entregables/CE01/E3/Informe_CE01_E3_v0.1.docx` y `.pdf`. Anexos de trabajo en `entregables/CE01/E3/`:
`Cronograma_Celeris.xml` (MSPDI) y `.mpp`, `Presupuesto_EVM_E3.xlsx` y `Backlog_E3.xlsx`. Todo se regenera; no se edita
a mano ningún archivo de `entregables/`.

## Qué hay aquí

| Ruta | Contenido |
| --- | --- |
| `datos/plan.yaml` | Calendario (feriados, receso, fechas académicas a confirmar), recursos, parámetros de costo, hitos y actividades con paquete de la EDT, duración, predecesoras FS/SS con desfase, horas por recurso, costo fijo y fechas reales (commit) de lo terminado |
| `datos/agil.yaml` | Épicas, historias HU-01…HU-17 (REQ-F, CU, puntos, WSJF, sprint, dependencias, Gherkin), sprints, tablero Kanban, DoR, DoD, eventos y métricas |
| `datos/gobierno.yaml` | Acta (sponsor, criterios de éxito, restricciones, supuestos, firmas), compromiso de interesados, comunicaciones, umbrales de control, control de cambios, lecciones aprendidas y preguntas de la sustentación |
| `datos/plan.json` | Generado por `plan.py` (no editar) |
| `plan.py` | CPM en días laborables, línea base, presupuesto por paquete (falla si alcance, cronograma y costos no cuadran), curva S, EVM y `{{dato:e3_*}}` |
| `agil.py` | WSJF y verificación del backlog contra el SRS y el cronograma (capacidad, dependencias, MoSCoW) |
| `mspdi.py` | Escribe el XML de MS Project (resumen por la EDT, dependencias, recursos, asignaciones, costos, línea base, calendario) |
| `msproject.py` | Abre el XML con MS Project (COM), compara fechas, holgura, ruta crítica y costo con Python, y guarda el `.mpp` |
| `xlsx_e3.py` | Libros con fórmulas; los recalcula con Excel (o LibreOffice) y falla si la hoja Control no da 0 |
| `tablas.py`, `figuras/generar.py` | Tablas `{{tabla:t-…}}` y figuras (EDT, control de cambios y Kanban en draw.io; Gantt S1/S2, curva S, riesgos y burn-up en matplotlib) |
| `informe/*.md` | Texto §3.1–§3.9, referencias IEEE y anexos A (solicitud de cambio) y B (Gherkin); C (supuestos) y D (autoevaluación) se generan |
| `crear_issues.sh` | Opcional: crea las issues del backlog con `gh`. **No se ejecuta** desde make |

## Regenerar (en esta PC: `mingw32-make PYTHON=python …`)

```powershell
mingw32-make PYTHON=python informe-ce01-e3
```

```powershell
mingw32-make PYTHON=python validate-ce01
```

`informe-ce01-e3` corre `plan.py` (JSON, XML, verificación con MS Project, XLSX verificados), las figuras y el generador.
Necesita Microsoft Word (PDF), Excel o LibreOffice y draw.io Desktop. Sin MS Project, `plan.py` lo informa y sigue;
`python gestion/e3/plan.py --sin-msproject` lo omite a propósito.

## Pasos manuales

1. **MS Project.** Abrir `entregables/CE01/E3/Cronograma_Celeris.xml` (o el `.mpp`) → Proyecto > Establecer línea base
   (ya viene en el XML; se repite tras cada cambio aprobado) → vista Diagrama de Gantt con Formato > Tareas críticas →
   exportar la imagen a `gestion/e3/figuras/gantt-msproject.png`. Si existe, el Gantt de S2 del informe usa esa imagen.
2. **Calendario académico.** Cuando se publique, actualizar `calendario.academico` y `excepciones` en `datos/plan.yaml`
   y regenerar: el modelo avisa si H1 o H4 no caen en las fechas académicas.
3. **Seguimiento semanal (viernes).** Marcar lo terminado con `real: {inicio, fin, commit}`, mover `meta.fecha_estado`,
   registrar las horas reales en el issue semanal y regenerar; el corte EVM entra en la tabla y en el XLSX.
4. **Cambio de alcance.** Issue con la etiqueta `cambio-alcance` (formato del anexo A); análisis con una copia de
   `plan.yaml`; si se aprueba, CI-xx en `docs/infra/e1/CAMBIOS-INVENTARIO.md` y commit.
5. **Backlog en GitHub (opcional).** `bash gestion/e3/crear_issues.sh --dry-run` para revisar; sin `--dry-run` crea las
   issues. Solo con la aprobación del equipo.
6. **Firmas del acta.** Completar los nombres del sponsor y de la DTI en `datos/gobierno.yaml` cuando se designen.
