# 2.5 Riesgos Iniciales

Los riesgos iniciales del caso de negocio son los riesgos estratégicos RE-01…RE-12 identificados en el E1 (§1.7), con los mismos identificadores que emplean CE02 y CE03. Este entregable agrega lo que el diagnóstico no podía aportar: el efecto económico de cada riesgo, calculado con el mismo modelo que produce el VAN.

## 2.5.1 Identificación de riesgos estratégicos

Se emplea la escala de 1 a 5 para la probabilidad (P) y el impacto (I) definida en el E1; el puntaje P × I determina el nivel: ALTO a partir de 15, MEDIO entre 8 y 14, y BAJO hasta 7. Para cada riesgo se define un escenario de estrés, es decir, el cambio en los parámetros del modelo que se produciría si el riesgo se materializara. Los escenarios son juicios del equipo, no supuestos medibles, y se registran con su justificación en `gestion/e2/datos/business_case.yaml` (CI-102).

La {{ref:t-riesgos-eco}} presenta los doce riesgos ordenados por su efecto en el VAN, con el escenario de estrés, el VAN resultante, la variación respecto del caso base y la estrategia de mitigación.

{{tabla:t-riesgos-eco}}

## 2.5.2 Evaluación preliminar de impacto

La {{ref:fig-riesgos-van}} ubica los riesgos en el mapa de calor de probabilidad × impacto e indica, junto a cada identificador, la variación del VAN en miles de dólares.

{{figura:fig-riesgos-van}}

El mapa revela que el nivel cualitativo y el efecto económico no siempre coinciden. El riesgo de mayor efecto económico es {{dato:e2_riesgo_peor}}, la falta de aprobación de la DTI, que se ubica en nivel MEDIO y reduciría el VAN a {{dato:e2_riesgo_peor_van}} si el servicio quedara limitado al laboratorio piloto. Los dos riesgos de nivel ALTO tienen efectos distintos: el rechazo por privacidad (RE-02) llevaría el VAN a {{dato:e2_re02_van}}, porque sin descifrado solo se reutilizaría el tráfico HTTP; en cambio, la dependencia de dos personas (RE-01) mantendría un VAN positivo de {{dato:e2_re01_van}} aun si el servicio se detuviera al cabo del primer año, dado que la inversión se recupera en ese plazo. Solo {{dato:e2_riesgos_van_neg}} de los doce escenarios de estrés producen un VAN negativo.

Los riesgos técnicos tienen efectos acotados: el aumento del costo de AWS (RE-07) reduce el VAN en {{dato:e2_re07_delta}} y la migración del hipervisor (RE-10), en {{dato:e2_re10_delta}}. El reemplazo de EC2-GW por una VPN de acceso remoto en el campus (RE-11) incluso lo aumenta en {{dato:e2_re11_delta}}, porque elimina líneas de AWS; su costo es técnico y de seguridad, no económico. El compromiso del acceso remoto (RE-12) no altera el flujo, porque EC2-GW no almacena datos y se recrea con OpenTofu, pero mantiene un impacto reputacional alto.

## 2.5.3 Estrategias de mitigación

La mitigación se concentra en los riesgos con mayor efecto económico:

- **RE-05 (aprobación de la DTI).** Piloto en un único laboratorio y demostración previa en el laboratorio emulado, sin inversión adicional hasta que la DTI apruebe la extensión. Este punto de decisión limita la pérdida a la inversión del piloto.
- **RE-02 (privacidad).** Descifrado limitado a las estaciones institucionales y a las fuentes aprobadas, aviso previo mediante el portal de transparencia (OB-4) y CA con restricciones de nombre. El tráfico BYOD nunca se descifra.
- **RE-01 (dependencia de dos personas).** Documentación como código, runbooks y transferencia formal a la DTI; A1 se mantiene como plan de respaldo con la misma red, CA y SIEM.
- **RE-03 (caída del BHR).** Medición mensual del BHR por laboratorio y priorización de fuentes HTTP; el disparador es un BHR inferior al umbral durante tres meses consecutivos, por encima del punto de equilibrio de {{dato:e2_eq_bhr}}.
