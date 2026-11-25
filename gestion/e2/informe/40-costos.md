# 2.4 Estimación de Costos y evaluación económica

Todas las cifras de esta sección proceden del módulo de cálculo `gestion/analytics/business_case.py`, construido con numpy-financial [20], que aplica las definiciones habituales de VAN, TIR y periodo de recuperación [6] y lee los supuestos del registro común y los datos de infraestructura del repositorio. El libro `Business_Case_E2.xlsx` reproduce el modelo con fórmulas vivas de Excel (VNA y TIR); el script verifica que el VAN de la hoja coincida con el de Python y falla si la diferencia supera un dólar.

## 2.4.1 Inversión inicial

La {{ref:t-capex}} desglosa la inversión inicial. Los switches de acceso, el FortiGate y la red Wi-Fi son infraestructura existente de la DTI y no forman parte de la inversión [S-14, S-28, S-29].

{{tabla:t-capex}}

El servidor físico concentra la mayor parte de la inversión. Su configuración se dimensionó en CE03 (D2) [19] para alojar las máquinas virtuales del diseño con margen [S-08]; la cotización real reemplazará al supuesto S-08 antes de cualquier compra.

## 2.4.2 Costos operativos

Los costos operativos corresponden a los servicios de AWS que funcionan de forma permanente y a la energía del rack. La {{ref:t-aws}} detalla las siete líneas de AWS que definen el costo mensual, con precios de lista [S-12].

{{tabla:t-aws}}

La {{ref:t-opex}} integra el costo de AWS con el de energía y separa los costos de operación de los de mantenimiento, como exige el contenido mínimo del entregable.

{{tabla:t-opex}}

AWS es la partida de operación más relevante ({{dato:e2_aws_anual}} anuales) y corresponde a la VPN, al gateway de acceso remoto EC2-GW y a los respaldos en S3; ninguna base de datos ni servicio de la consola reside en la nube. La energía suma {{dato:e2_energia}} anuales con el consumo de {{dato:consumo_w}} registrado en el inventario [S-09].

## 2.4.3 Costos de mantenimiento

El mantenimiento del hardware se estima como una fracción fija de la inversión inicial [S-41], lo que da {{dato:e2_mant}} anuales. Esta partida cubre la garantía extendida o el contrato de soporte del servidor, del switch y de la UPS, y se validará con la cotización correspondiente. El mantenimiento del software no se valoriza porque lo realiza el equipo del proyecto hasta la transferencia a la DTI; esta omisión se declara como limitación y se vincula con el riesgo RE-01.

**Costo total de propiedad.** Con una inversión de {{dato:e2_capex}} y un costo anual de {{dato:e2_opex}}, el TCO a tres años asciende a {{dato:e2_tco}} en términos nominales y a {{dato:e2_tco_va}} en valor actual al COK [S-10].

**Conciliación con la guía.** Las cifras de este informe difieren de las de la guía CE01 v0.4 porque el repositorio prevalece sobre los documentos (CI-98). La {{ref:t-conciliacion}} explica cada diferencia y el registro que la sustenta.

{{tabla:t-conciliacion}}

## 2.4.4 Flujo de caja e indicadores

La {{ref:t-flujo}} presenta el flujo de caja del caso base en el horizonte de {{dato:horizonte_anios}}, con los beneficios y los costos desagregados por partida.

{{tabla:t-flujo}}

La {{ref:fig-flujo}} representa el mismo flujo y el acumulado, lo que permite identificar el momento en que se recupera la inversión.

{{figura:fig-flujo}}

El flujo acumulado cambia de signo durante el primer año: la inversión de {{dato:e2_capex}} se recupera en {{dato:e2_payback}} y, al cierre del horizonte, el proyecto acumula un flujo neto positivo. El flujo es constante en los tres años porque el modelo no incorpora crecimiento de la demanda ni de los precios; esta simplificación es conservadora respecto del beneficio, dado que la demanda de ancho de banda tiende a crecer.

La {{ref:t-indicadores-eco}} resume los indicadores de la evaluación económica, con su método de cálculo y su lectura.

{{tabla:t-indicadores-eco}}

El VAN de {{dato:e2_van}} y la relación beneficio/costo de {{dato:e2_bc}} indican que el proyecto crea valor con los supuestos vigentes. La TIR de {{dato:e2_tir}} debe leerse con cautela: no indica un negocio extraordinario, sino una inversión pequeña frente a un beneficio supuesto. El punto de equilibrio es más informativo: el VAN es positivo siempre que la caché difiera al menos {{dato:e2_eq_mbps}}, es decir, un BHR de {{dato:e2_eq_bhr}}, muy inferior al {{dato:meta_ob1}} que fija OB-1.

## 2.4.5 Análisis de sensibilidad y simulación de Monte Carlo

Dado que el resultado depende de supuestos no validados, el modelo se somete a una simulación de Monte Carlo de {{dato:e2_mc_iter}} iteraciones con semilla fija ({{dato:e2_mc_semilla}}), de modo que el resultado es reproducible. La {{ref:t-mc-variables}} presenta las cinco variables inciertas y sus rangos.

{{tabla:t-mc-variables}}

Se emplean distribuciones triangulares porque solo se dispone de un mínimo, un máximo y un valor más probable para cada variable, sin datos históricos que permitan ajustar otra distribución [5]. La moda se sitúa en el valor del supuesto; en consecuencia, la distribución del BHR y la de la adopción son asimétricas hacia valores menores, lo que hace que la simulación sea más pesimista que el caso base.

La {{ref:fig-montecarlo}} presenta la distribución del VAN resultante, con los percentiles 5, 50 y 95.

{{figura:fig-montecarlo}}

La probabilidad de que el VAN sea positivo es de {{dato:e2_mc_p}}. El percentil 5 ({{dato:e2_mc_p5}}) se mantiene positivo, mientras que la mediana ({{dato:e2_mc_p50}}) es inferior al VAN del caso base ({{dato:e2_van}}) debido a la asimetría de las distribuciones del BHR y de la adopción. El {{dato:e2_mc_neg}} de iteraciones con VAN negativo corresponde a combinaciones simultáneas de BHR bajo, precio del Mbps bajo y adopción parcial.

La {{ref:fig-tornado}} muestra el efecto de llevar cada variable a los extremos de su rango mientras las demás permanecen en el caso base.

{{figura:fig-tornado}}

El {{dato:e2_tornado_1}} y el {{dato:e2_tornado_2}} producen el mismo recorrido del VAN ({{dato:e2_tornado_1_rango}}), porque el beneficio BN-1 es el producto de ambos y sus rangos son proporcionalmente iguales; la diferencia reside en la asimetría: con el BHR mínimo el VAN cae a {{dato:e2_tornado_1_min}}, mientras que con el precio mínimo del Mbps se mantiene en {{dato:e2_tornado_2_min}}. La {{dato:e2_tornado_3}} ocupa el tercer lugar, y los costos de AWS y la inversión tienen un efecto menor. En consecuencia, el piloto debe medir el BHR y la DTI debe obtener la cotización del ISP antes de cualquier ampliación del alcance.

La {{ref:t-escenarios}} combina los extremos de todas las variables en un escenario pesimista y otro optimista.

{{tabla:t-escenarios}}

El escenario pesimista arroja un VAN de {{dato:e2_esc_pesimista_van}}, porque supone simultáneamente el peor valor de las cinco variables; la simulación indica que esa combinación es poco probable. El escenario optimista alcanza {{dato:e2_esc_optimista_van}}. La amplitud entre ambos confirma que la decisión de inversión debe condicionarse a la medición del piloto.
