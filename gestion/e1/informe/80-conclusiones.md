# 1.8 Conclusiones

## 1.8.1 Conclusiones del diagnóstico

1. **El problema existe y es medible.** Cada ciclo de actualización genera {{dato:gb_ciclo_lab}} de tráfico por laboratorio, de los cuales {{dato:gb_repetidos_lab}} corresponden a copias del mismo contenido [S-26, S-27]. En términos anuales, el volumen repetido asciende a {{dato:gb_repetidos_anio}} en los {{dato:labs}} laboratorios. La línea base real se establecerá durante el piloto mediante los contadores del FortiGate y las métricas del nodo de caché.
2. **La causa raíz es de gestión y no únicamente de capacidad.** No se mide el desperdicio ni existe un rol con las herramientas y atribuciones necesarias para decidir qué contenido se reutiliza (MEA01, DSS01). La ampliación del enlace atenúa el síntoma, pero no modifica la causa.
3. **La brecha COBIT debe medirse antes de afirmarse.** El instrumento de evaluación se encuentra listo. Hasta la realización de la entrevista, las brechas se sustentan en supuestos registrados y en los datos marcados [levantar con la DTI]; ninguna se presenta como resultado de una medición.
4. **El proyecto presenta un alineamiento completo.** Cada componente responde a una brecha, a un objetivo del proyecto y a un objetivo institucional (§1.5). Los objetivos institucionales serán confirmados con el plan estratégico vigente.
5. **Las capacidades existentes tienen prioridad.** El FortiGate y un eventual servidor de actualizaciones cubren parte del problema; por ello, el E2 compara Celeris con dichas alternativas antes de emitir una recomendación.
6. **El riesgo predominante es de carácter institucional.** La dependencia respecto de dos personas, la aceptación en materia de privacidad y la relación con la DTI tienen mayor peso que los riesgos técnicos. La hoja de ruta incorpora puntos de decisión que impiden comprometer inversión adicional sin evidencia.

## 1.8.2 Preguntas previsibles de la sustentación

La {{ref:t-defensa}} anticipa las preguntas previsibles de la defensa técnica e indica, para cada una, la respuesta sintética y la sección del informe en la que se encuentra la evidencia.

Tabla: t-defensa | Preguntas previsibles de la sustentación y su evidencia | Elaboración propia
| Pregunta previsible | Respuesta sintética | Evidencia |
| --- | --- | --- |
| ¿Por qué no basta con ampliar el enlace? | La ampliación continúa transportando cada copia una vez por estación y constituye un costo recurrente; además, no aporta medición ni capacidad de decisión | §1.4.4; alternativa A0 en el E2 |
| ¿El FortiGate no cumple ya esta función? | Filtra por categorías, pero no reutiliza contenido; si su modelo dispone de caché web, corresponde a la alternativa A5, que se evalúa en primer lugar | §1.3.3; inventario §1.3.1 |
| ¿Cuál es el origen de las cifras? | Los supuestos S-xx del registro común, procesados mediante un módulo de cálculo; ninguna cifra se consigna manualmente | §1.4.3; anexo de supuestos |
| ¿Cómo se determinó el nivel de madurez? | Aún no se ha determinado: se medirá con el instrumento de entrevista sustentado en evidencia, y el informe lo identifica como pendiente | §1.3.2 |
| ¿Se descifra el tráfico de los estudiantes? | Únicamente en estaciones institucionales, solo para fuentes aprobadas y con aviso previo; los dispositivos personales (BYOD) nunca se descifran | PESTEL §1.2.3; RE-02 §1.7 |
| ¿Qué ocurre si el piloto no alcanza la meta? | La hoja de ruta incluye un punto de decisión: sin la meta de BHR de OB-1, la solución no se extiende | §1.6 |
| ¿Cómo se relaciona con CE02 y CE03? | La vista de motivación integra objetivos, requisitos de CE02 y componentes de CE03 con identificadores comunes | §1.5 |
