# gestion/e4/ — CE01 E4: Modelado de Procesos AS-IS / TO-BE (BPMN 2.0)

Informe: `entregables/CE01/E4/Informe_CE01_E4_v0.1.docx` y `.pdf`. Todo se regenera; no se edita a mano ningún archivo
generado. Supuestos S-42…S-45 y prefijos locales PD-xx, KPI-x y AU-x: CI-104 en `docs/infra/e1/CAMBIOS-INVENTARIO.md`.

## Qué hay aquí

| Ruta | Contenido |
| --- | --- |
| `simulacion.yaml` | Fuente única de los cuatro diagramas (P1-AS-IS, P1-TO-BE, P2-AS-IS, P2-TO-BE): nodos, carriles, flujos, mensajes, duraciones triangulares [S-43], probabilidades [S-44], PD-xx y REQ-F. Todo valor lleva su supuesto |
| `datos/procesos.yaml` | Mapa de procesos, matriz de selección, ficha y SIPOC, problemas PD-01…PD-09 (causa textual del Ishikawa del E1), automatizaciones AU-1…AU-7, indicadores KPI-1…KPI-8, cronometraje y preguntas de la defensa |
| `procesos.py` | Cálculo de la descarga, Monte Carlo (10 000 iteraciones, semilla fija), coherencia PD ↔ diagrama ↔ SRS ↔ pruebas, comparación con Bizagi y `{{dato:e4_*}}`. Escribe `datos/e4.json` y `datos/resultados.json` (no editar) |
| `bpmn.py` | Escribe `bpmn/*.bpmn` (BPMN 2.0 con `bpmndi`, pool «UPeU Campus Juliaca», pool colapsado «Internet / ISP», anotaciones PD-xx) y los valida contra el XSD de OMG |
| `instrumentos.py` | Plantilla de cronometraje `instrumentos/registro-tiempos.xlsx` (registro, resumen con fórmulas, fases) |
| `tablas.py`, `figuras/generar.py` | Tablas `{{tabla:t-…}}` y figuras (mapa en draw.io, BPMN con bpmn-js o Bizagi, barras agrupadas y dispersión en matplotlib) |
| `informe/*.md` | Texto §4.1–§4.4, referencias IEEE y anexo A (parámetros); la autoevaluación (`autoevaluacion.yaml`) se genera |
| `herramientas/xsd/` | XSD BPMN 2.0 de OMG (BPMN20, Semantic, BPMNDI, DI, DC) |
| `herramientas/render/` | `render.js`: BPMN → PNG con bpmn-js y puppeteer-core sobre el Chrome instalado (`node_modules` fuera del repositorio) |

## Regenerar (en esta PC: `mingw32-make PYTHON=python …`)

```powershell
mingw32-make PYTHON=python informe-ce01-e4
```

```powershell
mingw32-make PYTHON=python validate-ce01
```

`informe-ce01-e4` corre `procesos.py` (simulación, BPMN validados, XLSX, JSON), las figuras y el generador. Necesita
Microsoft Word (PDF), draw.io Desktop, Node 18+ y Google Chrome. El generador falla si un `.bpmn` no valida contra el
XSD, si un PD-xx falta en el diagrama o en la tabla, o si una automatización no tiene REQ-F del SRS ni prueba.

## Pasos manuales

0. **Herramientas (una vez).** `npm install` dentro de `gestion/e4/herramientas/render/`. Si Chrome no está en
   `C:/Program Files/Google/Chrome/Application/chrome.exe`, definir `CHROME_PATH` con su ruta (o Edge). Los XSD ya están en el repositorio.
1. **Abrir en Bizagi Modeler.** Archivo > Importar > BPMN 2.0 y elegir `gestion/e4/bpmn/P1-AS-IS.bpmn` (repetir con
   los otros tres). Bizagi conserva pools, carriles, compuertas y anotaciones; si reacomoda los elementos, ordenarlos
   sin cambiar nombres ni conexiones.
2. **Guardar el modelo** como `gestion/e4/bizagi/Celeris-E4.bpm` (un diagrama por proceso).
3. **Simulación nivel 1 (validación).** Vista Simulación > Validación del proceso: comprobar que todos los tokens
   llegan al fin. Si alguno queda atascado, el diagrama tiene un error: corregir `simulacion.yaml`, no el `.bpm`.
4. **Nivel 2 (tiempos).** Cargar en cada tarea y evento de temporizador la duración del anexo A (Tabla de parámetros);
   en cada compuerta, las probabilidades de la Tabla de compuertas; en el evento de inicio, el número de llegadas
   (P1: 20 ciclos al año; P2: 640 pedidos al año) y el intervalo entre ellas.
5. **Nivel 3 (recursos).** Crear los recursos Técnico DTI, Encargado de laboratorio y Docente, con el costo por hora
   del anexo A (el docente con costo 0, porque no se valoriza) y asignarlos a las tareas de su carril.
6. **Ejecutar** la simulación con las mismas iteraciones que la sección 4.2.4 (`meta.iteraciones` de `simulacion.yaml`).
7. **Exportar las imágenes** (Archivo > Exportar > Imagen PNG) como `gestion/e4/figuras/<diagrama>-bizagi.png`, por
   ejemplo `P1-AS-IS-bizagi.png`. Si existen, el informe usa esas imágenes en lugar de las de bpmn-js y su fuente
   lo indica.
8. **Exportar los resultados** de la simulación (Excel) a `gestion/e4/datos/bizagi/`.
9. **Transcribir** el tiempo medio del ciclo (h) y el costo medio (US$) de cada diagrama a
   `gestion/e4/datos/bizagi/resultados.yaml`:

   ```yaml
   P1-AS-IS: {ciclo_h: 10.8, costo: 45.0}
   P1-TO-BE: {ciclo_h: 5.5, costo: 25.4}
   ```

   `procesos.py` compara cada valor con la media de Python y avisa si difieren más de 10 %. Una diferencia así indica
   un parámetro mal cargado en Bizagi o un error del modelo: se revisa y se informa, no se ajusta a mano.
10. **Cronometraje.** Registrar al menos 30 observaciones por fase en `instrumentos/registro-tiempos.xlsx` (hoja
    Registro; una fila por observación, con hora de inicio y de fin). La hoja Resumen pasa de «Estimado [S-43]» a
    «Medido» cuando se alcanza el mínimo. Con las medidas, actualizar las duraciones triangulares de `simulacion.yaml`
    (mínimo, moda y máximo observados), registrar el cambio de S-43 con un CI-xx y regenerar.
