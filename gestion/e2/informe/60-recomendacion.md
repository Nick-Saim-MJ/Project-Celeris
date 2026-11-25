# 2.6 Recomendación y sustentación

## 2.6.1 Recomendación

Se recomienda adoptar la alternativa A4, Celeris Edge, mediante un despliegue escalonado con un punto de decisión explícito. En una primera etapa, el servicio se implementa en un único laboratorio piloto, con medición del BHR, de los tiempos de preparación y del uso de la consola. La extensión a los {{dato:labs}} laboratorios solo se aprueba si el BHR medido supera el punto de equilibrio de {{dato:e2_eq_bhr}} y se aproxima a la meta de OB-1 ({{dato:meta_ob1}}), y si la DTI confirma la cotización del ISP que sustenta el supuesto S-03.

## 2.6.2 Por qué A4 gana aunque pierde en soporte

Celeris Edge obtiene el puntaje más bajo de todas las alternativas en soporte y mantenibilidad, porque hoy depende de dos personas. La decisión se sostiene por tres razones:

1. **Es la única alternativa que ataca la causa raíz.** El E1 estableció que el problema es de gestión: nadie mide el desperdicio ni decide qué se reutiliza. Solo A4 entrega una consola al encargado y métricas por laboratorio; las demás alternativas reutilizan contenido, pero no modifican la gestión.
2. **La debilidad en soporte es mitigable, mientras que las ventajas son estructurales.** El soporte puede transferirse a la DTI mediante documentación como código; en cambio, ninguna alternativa puede adquirir la coalescencia, el descifrado selectivo con aviso previo o la exclusión del BYOD sin rediseñarse.
3. **La decisión resiste cambios importantes en los pesos.** El soporte tendría que pasar de {{dato:e2_sens_peso}} a {{dato:e2_sens_cruce}} del peso total para que A4 perdiera, y en ese caso ganaría {{dato:e2_sens_gana}}, que es el plan de respaldo del propio proyecto y comparte su red, su CA y su SIEM.

## 2.6.3 Qué decide el resultado económico

El tornado y la simulación de Monte Carlo coinciden en que el resultado depende de dos supuestos: el {{dato:e2_tornado_1}} y el {{dato:e2_tornado_2}}. Ambos determinan el beneficio BN-1, que representa la mayor parte del valor del proyecto. Los costos tienen un efecto menor: aun con la inversión y el costo de AWS en el extremo superior de sus rangos, el VAN se mantiene positivo. Por ello, la incertidumbre relevante no reside en lo que el proyecto cuesta, sino en cuánto contenido logra reutilizar y en cuánto vale cada Mbps que deja de contratarse.

La TIR de {{dato:e2_tir}} exige una advertencia expresa ante el jurado: una tasa de esa magnitud no indica un negocio extraordinario, sino una inversión reducida frente a un beneficio que todavía es un supuesto. El indicador que mejor describe el riesgo es el punto de equilibrio ({{dato:e2_eq_mbps}} diferidos), porque expresa el resultado en una magnitud que el piloto puede medir.

## 2.6.4 Qué mediría el piloto para confirmar la decisión

El piloto debe convertir en mediciones los supuestos que el tornado señala como decisivos:

- **BHR en hora punta por laboratorio** [S-04], a partir de los registros del nodo y los contadores del FortiGate (validación de S-40).
- **Cotización del Mbps adicional** [S-03], solicitada por la DTI al ISP.
- **Adopción del proxy** (CI-102): proporción de los bytes del laboratorio que pasan por la caché.
- **Minutos de descarga por laboratorio** frente a la línea base (OB-2) y tiempo para habilitar una fuente desde la consola (OB-3).
- **Horas técnicas por ciclo** [S-07], mediante el registro de la DTI.

Con estas mediciones, el modelo se recalcula sin modificar el código: basta con actualizar los supuestos en `infra/trazabilidad.yaml` y regenerar el informe.

## 2.6.5 Limitaciones

El análisis presenta las siguientes limitaciones, que se declaran conforme al Marco común (M5):

- Los beneficios y los costos se basan en supuestos no validados; ninguno se presenta como dato verificado (Anexo C).
- Los pesos AHP, los puntajes de la matriz y los escenarios de estrés de los riesgos son juicios del equipo, pendientes de validación con la DTI.
- El costo de la alternativa A5 se desconoce y se modela como cota inferior.
- El modelo no incorpora crecimiento de la demanda ni de los precios, ni valoriza el mantenimiento del software durante el periodo académico.

## 2.6.6 Preguntas previsibles de la sustentación

La {{ref:t-defensa-e2}} anticipa las preguntas previsibles de la defensa técnica e indica la respuesta sintética y la evidencia de cada una.

Tabla: t-defensa-e2 | Preguntas previsibles de la sustentación y su evidencia | Elaboración propia
| Pregunta previsible | Respuesta sintética | Evidencia |
| --- | --- | --- |
| ¿Por qué gana Celeris si es la alternativa con peor soporte? | Es la única que actúa sobre la causa de gestión; la debilidad en soporte se mitiga con la transferencia a la DTI y la decisión solo cambia con pesos alejados del AHP | §2.2.3; §2.6.2 |
| ¿De dónde salen los pesos de los criterios? | De una comparación AHP por pares con razón de consistencia aceptable; prevalecen sobre los pesos de la guía | §2.2.2; Anexo B |
| ¿No es irreal una TIR tan alta? | Refleja una inversión pequeña frente a un beneficio supuesto; por eso se presenta el punto de equilibrio y la simulación de Monte Carlo | §2.4.4; §2.4.5 |
| ¿Qué ocurre si el BHR real es bajo? | El VAN sigue siendo positivo mientras el BHR supere el punto de equilibrio; el piloto lo mide antes de extender el servicio | §2.4.4; §2.6.4 |
| ¿Por qué no usar el FortiGate existente? | Exige inspección profunda sobre todo el tráfico, incluido el BYOD, y no da control al encargado; su costo debe confirmarse con la DTI | §2.2.1; §2.2.3 |
| ¿Por qué las cifras difieren de la guía? | El repositorio prevalece sobre los documentos; la conciliación explica cada diferencia y su registro | §2.4.3; CI-98 |
| ¿Qué riesgo preocupa más desde el punto de vista económico? | La falta de aprobación de la DTI, que se mitiga con un piloto sin inversión adicional | §2.5.2; §2.5.3 |
