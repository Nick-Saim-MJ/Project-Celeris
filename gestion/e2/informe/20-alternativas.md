# 2.2 Análisis de Alternativas

El análisis compara seis alternativas con criterios explícitos y ponderados. Para evitar un sesgo a favor de la solución propia, se aplican tres reglas: el costo de todas las alternativas se calcula con las mismas partidas del modelo económico; los pesos de los criterios se derivan mediante AHP y se someten a una prueba de consistencia; y se determina cuánto tendrían que cambiar los pesos para que la decisión se invirtiera.

## 2.2.1 Alternativas tecnológicas consideradas

Las alternativas incluyen la opción de no intervenir técnicamente (A0), tres soluciones de mercado o de software libre (A1, A2 y A3), la propuesta del proyecto (A4) y el aprovechamiento del equipamiento existente (A5). La {{ref:t-fichas}} describe el alcance de cada una: qué resuelve y qué deja sin resolver.

{{tabla:t-fichas}}

La {{ref:t-fichas-riesgo}} completa las fichas con los riesgos, la madurez y el costo a tres años. Las alternativas que requieren un servidor (A1 a A4) se calculan con el mismo hardware de Celeris para compararlas en igualdad de condiciones; A0 se valora como la compra de los mismos Mbps que difiere Celeris [S-40]; y A5 se registra con costo nulo como cota inferior, dado que el costo de disco y licencia del FortiGate debe levantarse con la DTI (CI-102).

{{tabla:t-fichas-riesgo}}

La {{ref:fig-tco}} compara visualmente el costo total de propiedad (TCO) a tres años de cada alternativa, distinguiendo la inversión inicial de los costos recurrentes.

{{figura:fig-tco}}

La figura evidencia que la ampliación del enlace es la alternativa más costosa, con {{dato:e2_ampliacion_tco}} en tres años, porque todo su costo es recurrente. Celeris Edge cuesta {{dato:e2_tco}}, es decir, {{dato:e2_dif_tco_a4_a1}} más que A1, A2 y A3 ({{dato:e2_tco_a1}}), diferencia que corresponde íntegramente al gateway de acceso remoto y a los respaldos en AWS. La caché del FortiGate aparece sin costo solo porque su costo real se desconoce; esta asignación favorece a la alternativa competidora y, por tanto, hace más exigente la comparación para Celeris.

## 2.2.2 Criterios de evaluación

Los seis criterios proceden de la guía CE01 v0.4 (B2.2): eficacia contra descargas repetidas, incluido el tráfico HTTPS (C1); seguridad y privacidad (C2); TCO a tres años (C3); autonomía del encargado (C4); soporte y mantenibilidad (C5); y valor académico (C6). El criterio C3 no se juzga: se calcula a partir del TCO de la {{ref:t-fichas-riesgo}} mediante una escala lineal en la que el menor costo recibe 5 y el mayor recibe 1.

Los pesos se derivan mediante el proceso analítico jerárquico de Saaty [1], [2]. La {{ref:t-ahp}} presenta la matriz de comparación por pares, los pesos obtenidos con la media geométrica de cada fila y los indicadores de consistencia.

{{tabla:t-ahp}}

La razón de consistencia es {{dato:e2_ahp_cr}}, inferior al umbral de {{dato:e2_ahp_crmax}} que Saaty establece para aceptar los juicios; el modelo de cálculo falla si este umbral se supera. Los pesos obtenidos con la media geométrica difieren de los del autovector principal en un máximo de {{dato:e2_ahp_dif}}, de modo que el método de cálculo no altera el resultado. Los juicios de cada par y su justificación se detallan en el Anexo B.

La {{ref:t-pesos}} compara los pesos AHP con los pesos de partida de la guía. Conforme a la regla del análisis, prevalecen los pesos AHP.

{{tabla:t-pesos}}

Las diferencias se explican por dos juicios. En primer lugar, la eficacia (C1) aumenta de {{dato:e2_peso_guia_c1}} a {{dato:e2_peso_c1}} porque, sin ella, el problema central no se resuelve. En segundo lugar, la seguridad y privacidad (C2) disminuye de {{dato:e2_peso_guia_c2}} a {{dato:e2_peso_c2}} porque una parte de ese criterio opera como restricción obligatoria para todas las alternativas (el tráfico BYOD nunca se descifra) y no como factor diferenciador; en cambio, el TCO (C3) asciende a {{dato:e2_peso_c3}}, dado que la DTI debe justificar el gasto recurrente. Estos pesos constituyen un juicio del equipo y se validarán con la DTI en una sesión de ponderación.

## 2.2.3 Matriz comparativa

La {{ref:t-justificacion}} presenta el puntaje de cada alternativa en cada criterio y lo justifica en una línea, de modo que ninguna celda de la matriz carece de sustento.

{{tabla:t-justificacion}}

La {{ref:fig-matriz}} presenta la matriz de decisión ponderada como mapa de calor: cada celda contiene el puntaje de la alternativa en el criterio y la barra lateral muestra el total ponderado con los pesos AHP.

{{figura:fig-matriz}}

La matriz sitúa a {{dato:e2_gana}} en primer lugar, con {{dato:e2_total_gana}}, y a {{dato:e2_segunda}} en segundo, con {{dato:e2_total_segunda}}; la diferencia es de {{dato:e2_margen}} puntos. Celeris Edge obtiene el puntaje máximo en seguridad y privacidad, autonomía y valor académico, y el más bajo en soporte, por depender de dos personas (RE-01). A0 obtiene el máximo en soporte, pero el mínimo en costo y valor académico, lo que confirma que ampliar el enlace no resuelve la causa de gestión.

**Sensibilidad de la decisión.** Una matriz ponderada solo es rigurosa si se conoce cuánto tendrían que cambiar los pesos para invertir el resultado. La {{ref:fig-sensibilidad}} muestra, para cada criterio, cómo varía el total de cada alternativa cuando el peso de ese criterio recorre todo su rango y los demás se reescalan en proporción.

{{figura:fig-sensibilidad}}

Celeris Edge mantiene el primer lugar en todo el rango de los criterios C1, C2, C4 y C6. Solo pierde en dos casos: si el soporte y mantenibilidad (C5) pasa de {{dato:e2_sens_peso}} a {{dato:e2_sens_cruce}}, gana {{dato:e2_sens_gana}}; y si el TCO (C3) supera la mitad del peso total, gana la caché del FortiGate, cuyo costo es una cota inferior. Ambos cambios exigirían pesos muy alejados de los juicios consistentes del AHP, por lo que la decisión es robusta. La {{ref:t-sensibilidad}} resume el peso de cruce de cada criterio.

{{tabla:t-sensibilidad}}

**Lectura de las alternativas.** El análisis admite tres lecturas complementarias:

- **A1 como plan de respaldo.** Squid con SSL-Bump es la alternativa técnica más madura y la que pasa a ganar si el soporte adquiere un peso dominante. Si se materializa RE-01, la DTI puede migrar a A1 conservando la red, la CA y el SIEM del diseño.
- **A3 y A4 como combinación válida.** WSUS o Delivery Optimization resuelven las actualizaciones de Windows sin descifrado, pero no los instaladores de otros fabricantes ni el material de la plataforma virtual. Si la DTI ya opera WSUS, Celeris puede excluir esas fuentes y concentrarse en el resto, lo que reduce el BHR atribuible al proyecto, pero no su razón de ser.
- **A5 pendiente de confirmación.** La caché del FortiGate solo puede evaluarse por completo cuando la DTI confirme el modelo instalado y su licencia. Aun con costo nulo, la alternativa exige inspección profunda sobre todo el tráfico, incluido el BYOD, lo que contradice una regla del proyecto.
