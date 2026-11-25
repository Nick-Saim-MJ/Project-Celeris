# 1.8 Conclusiones

## 1.8.1 Conclusiones del diagnóstico

1. **El problema existe y se puede medir.** Cada ciclo de actualización mueve {{dato:gb_ciclo_lab}} por laboratorio, de los cuales {{dato:gb_repetidos_lab}} son copias de lo mismo [S-26, S-27]. Al año son {{dato:gb_repetidos_anio}} repetidos en los {{dato:labs}} laboratorios. La línea base real se toma en el piloto con los contadores del FortiGate y las métricas del nodo.
2. **La causa raíz es de gestión, no solo de capacidad.** Nadie mide el desperdicio ni tiene la herramienta y la atribución para decidir qué se reutiliza (MEA01, DSS01). Ampliar el enlace alivia el síntoma, pero no cambia la causa.
3. **Hay que medir antes de afirmar la brecha COBIT.** El instrumento está listo. Hasta la entrevista, las brechas se sustentan con supuestos y con los datos marcados [levantar con la DTI]; ninguna se presenta como medida.
4. **El proyecto está alineado de punta a punta.** Cada componente responde a una brecha, a un objetivo del proyecto y a un objetivo institucional (§1.5). Los objetivos institucionales se confirman con el plan estratégico vigente.
5. **Primero lo que ya existe.** El FortiGate y un posible servidor de actualizaciones cubren parte del problema. El E2 compara Celeris con esas alternativas antes de recomendarlo.
6. **El riesgo dominante es institucional.** La dependencia de dos personas, la aceptación por privacidad y la relación con la DTI pesan más que los riesgos técnicos. El roadmap tiene puertas de decisión para no invertir más sin evidencia.

## 1.8.2 Preguntas previsibles de la sustentación

La {{ref:t-defensa}} prepara la defensa técnica: para cada pregunta previsible indica la respuesta corta y dónde está la evidencia en este informe.

Tabla: t-defensa | Preguntas previsibles de la sustentación y su evidencia | Elaboración propia
| Pregunta previsible | Respuesta corta | Evidencia |
| --- | --- | --- |
| ¿Por qué no ampliar el enlace y listo? | Ampliar sigue trayendo cada copia una vez por PC y es un costo que se repite cada año; no da medición ni decisión | §1.4.4; alternativa A0 en el E2 |
| ¿El FortiGate no hace ya esto? | Filtra por categoría, pero no reutiliza; si su modelo tiene caché web, es la alternativa A5 y se evalúa primero | §1.3.3; inventario §1.3.1 |
| ¿De dónde salen las cifras? | De los supuestos S-xx del registro común, calculados por script; ninguna cifra está escrita a mano | §1.4.3; Anexo de supuestos |
| ¿Cómo saben el nivel de madurez? | Todavía no se sabe: se mide con el instrumento de entrevista y evidencia; el informe lo marca como pendiente | §1.3.2 |
| ¿Se descifra el tráfico de los estudiantes? | Solo en PCs institucionales, solo fuentes aprobadas y con aviso previo; el BYOD nunca se descifra | PESTEL §1.2.3; RE-02 §1.7 |
| ¿Qué pasa si el piloto no rinde? | El roadmap tiene una puerta de decisión: sin la meta de BHR de OB-1 no se amplía | §1.6 |
| ¿Cómo se relaciona con CE02 y CE03? | La vista de motivación une objetivos, requisitos de CE02 y componentes de CE03 con los mismos IDs | §1.5 |
