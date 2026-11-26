# 4.4 Sustentación del análisis

## 4.4.1 Coherencia del modelo

Los diagramas, la simulación y las tablas salen de la misma fuente, `gestion/e4/simulacion.yaml`, de modo que una tarea que aparece en un diagrama es la misma que se simula y se tabula. El generador se detiene si un BPMN no es válido contra el esquema XSD de OMG, si un PD-xx no aparece en el diagrama y en la tabla, si su causa no es textual del Ishikawa del E1, si una automatización no tiene requisito del SRS ni prueba, o si la matriz de selección no da P1 y P2 como los procesos de mayor puntaje. Las probabilidades se leen de los supuestos y las metas de los objetivos del proyecto, no del texto.

## 4.4.2 Decisiones defendibles

- **Dos procesos y no uno.** P1 representa el volumen (la actualización masiva) y P2 la frecuencia y la autonomía del encargado; juntos cubren los problemas operativos PO-1 a PO-5 del E1.
- **Simulación propia antes que Bizagi.** La cifra del informe no depende de una herramienta de escritorio: la simulación en Python es reproducible desde el repositorio, y Bizagi la verifica con los mismos parámetros.
- **Mejora informada con su dispersión.** Cada resultado se informa con la media y los percentiles 10 y 90, y el informe declara dónde el TO-BE no alcanza la meta.
- **Sin doble conteo.** El tráfico evitado se valoriza en el E2 (BN-1); el E4 solo valoriza horas de personal.

## 4.4.3 Limitaciones

- Las duraciones de las tareas manuales y las probabilidades de las bifurcaciones son estimaciones del equipo [S-43, S-44] hasta reunir las observaciones del cronometraje.
- El volumen de material de P2 usa el mismo supuesto que una actualización masiva [S-27]; un material más liviano reduciría la descarga en ambos escenarios.
- El mapa de procesos y los pesos de la matriz de selección deben validarse con la DTI.
- La simulación trata cada ejecución por separado y no modela la competencia de varios laboratorios por el mismo técnico.

## 4.4.4 Preguntas previsibles de la sustentación

La {{ref:t-defensa-e4}} anticipa las preguntas que el jurado podría formular sobre el modelado y la respuesta que lo sustenta.

{{tabla:t-defensa-e4}}
