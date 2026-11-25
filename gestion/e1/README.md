# gestion/e1/ — CE01 E1: Diagnóstico organizacional y alineamiento estratégico

Informe: `entregables/CE01/E1/Informe_CE01_E1_v0.1.docx` y `.pdf`. Matrices: `entregables/CE01/E1/Matrices_Diagnostico_E1.xlsx`.
Todo se regenera desde este directorio; no se edita el DOCX, el PDF ni el XLSX a mano.

## Qué hay aquí

| Ruta | Contenido |
| --- | --- |
| `datos/diagnostico.yaml` | Contenido cualitativo con su fuente: Porter, organigrama, cadena de valor, stakeholders, FODA/TOWS, PESTEL, FCE, inventario, brechas, problemas, 5W2H, Ishikawa, árbol, alineamiento, ArchiMate, roadmap |
| `datos/madurez.yaml` | Instrumento COBIT 2019: seis objetivos con nivel objetivo y `actual: null` hasta la entrevista |
| `datos/e1.json` | Generado por `calculos.py` (no editar) |
| `calculos.py` | Cifras del §1.4 (GB repetidos, tiempo de descarga, costo de no actuar) desde los supuestos S-xx; metas OB-x verificadas contra `infra/trazabilidad.yaml` |
| `tablas.py` | Tablas `{{tabla:t-…}}` del informe |
| `figuras/generar.py` | Figuras: draw.io (organigrama, cadena de valor, Ishikawa, árbol, mapa estratégico), matplotlib (Mendelow, radar COBIT, brechas, impacto × frecuencia, roadmap, mapa de calor) y la vista ArchiMate |
| `archimate/generar.py` | Modelo de motivación ArchiMate 3.2 (Open Exchange XML) → Archi CLI → `.archimate` y `figuras/motivacion-archi.png` |
| `xlsx_matrices.py` | Libro de matrices con fórmulas vivas (P × I, impacto × frecuencia, nivel ALTO/MEDIO/BAJO) |
| `informe/*.md` | Texto del informe, §1.1–§1.8 y referencias IEEE |
| `instrumentos/entrevista-cobit.md` | Guía de la entrevista con la DTI (madurez COBIT y datos de contexto) |
| `autoevaluacion.yaml` | Criterio de la rúbrica → evidencia (id de figura, tabla o título) |

## Regenerar (en esta PC: `mingw32-make PYTHON=python …`)

```powershell
mingw32-make PYTHON=python figuras-ce01
```

```powershell
mingw32-make PYTHON=python informe-ce01-e1
```

```powershell
mingw32-make PYTHON=python validate-ce01
```

`figuras-ce01` necesita draw.io Desktop y Archi 5.12 instalados; `informe-ce01-e1` necesita Microsoft Word (PDF vía COM).

## Pasos manuales

1. **Vista ArchiMate (solo si falla el CLI de Archi).** `archimate/generar.py` ya importa el XML y exporta la vista por
   línea de comandos. Si falla: en Archi, *File → Import → Open Exchange XML Model…* →
   `archimate/celeris-motivacion.xml`; abrir la vista «Motivación de Celeris Edge»; *File → Export →
   View As Image…* (PNG, escala 200 %) → `figuras/motivacion-archi.png`. Guardar el modelo como
   `archimate/celeris-motivacion.archimate`.
2. **Entrevista COBIT con la DTI.** Seguir `instrumentos/entrevista-cobit.md`. Al terminar, en `datos/madurez.yaml`:
   `estado_entrevista: realizada`, `fecha_entrevista`, `entrevistados` (roles, no nombres) y `actual` de cada objetivo
   (solo el nivel con evidencia vista). Luego `make figuras-ce01` y `make informe-ce01-e1`: el radar y la brecha COBIT
   se redibujan solos, y la Tabla 1.11 muestra el nivel.
3. **Datos de contexto de la misma reunión.** Reemplazar cada `[levantar con la DTI]` de `datos/diagnostico.yaml` con
   el dato y su fuente (acta, contrato, captura). Si un dato cambia un supuesto S-xx, se corrige en
   `infra/trazabilidad.yaml` con un CI nuevo en `docs/infra/e1/CAMBIOS-INVENTARIO.md`, no en el texto.
4. **Plan estratégico de la UPeU.** Reemplazar los rótulos de trabajo OE-a…OE-d y la misión/visión marcadas
   `[confirmar con el plan estratégico]` (en `datos/diagnostico.yaml`, `identidad` y `archimate.goals`).
5. **Portada.** El semestre académico sale como `[COMPLETAR: semestre académico]` hasta que se fije en la fuente común.

## Datos marcados [levantar con la DTI]

| Dato | Sección | Qué decide |
| --- | --- | --- |
| Modelo y versión del FortiGate, licencias FortiGuard, disco y caché web | §1.3.1, §1.3.3 | Si la alternativa A5 (caché del FortiGate) es real |
| Existencia de WSUS o servidor de actualizaciones similar | §1.3.1, §1.3.3 | Alternativa A3 |
| Herramienta de imágenes y políticas de las PCs (directorio, GPO) | §1.3.1 | Cómo se reparte el PAC (D-05) |
| Sistema operativo de las PCs de laboratorio | §1.3.1 | Compatibilidad con la CA |
| Plataforma virtual de aprendizaje y mesa de ayuda | §1.3.1 | Inventario completo; fuente de tickets de PO-2 y PO-3 |
| Dependencia de los encargados y ubicación del oficial de datos personales | §1.1.2 | Organigrama y RACI (E3) |
| Contrato del ISP: ancho de banda, US$/Mbps, plazo, proveedores con fibra | §1.1.1 | S-02, S-03 |
| Horas de clase retrasadas por descargas | §1.4.3 | Impacto en la enseñanza |
| Detección de incidentes y registro de riesgos de TI actuales | §1.3.3 (BR-5, BR-7) | Brechas DSS05 y APO12 |
| Misión, visión y objetivos del plan estratégico vigente | §1.2.1 | Rótulos OE-a…OE-d |

Las decisiones de esta entrega (meta de BHR, dueños de los riesgos, tiempo de descarga, prefijos locales PO/FCE/BR/OE)
están en CI-101.
