# 3.4 Gestión de Costos

La gestión de costos estima, presupuesta y controla el costo de ejecutar el proyecto [1]. El presupuesto se construye de abajo hacia arriba: cada actividad suma las horas del equipo multiplicadas por la tarifa [S-07] y, cuando corresponde, un costo fijo de hardware o de AWS; las actividades se agregan por paquete de la EDT, los paquetes por área y el total, más las reservas, forma la línea base.

## 3.4.1 Presupuesto detallado

La {{ref:t-presupuesto}} presenta el presupuesto de cada uno de los {{dato:e3_n_paquetes}} paquetes de la EDT, con sus horas, el costo de las horas, los costos fijos y su participación en el BAC.

{{tabla:t-presupuesto}}

La {{ref:t-costos-fijos}} justifica los tres costos fijos. El hardware del rack es la inversión inicial calculada en el E2; el costo de AWS se obtiene de los precios de `infra/centro_datos.yaml` [S-12] con {{dato:e3_aws_horas_efimero}} del laboratorio efímero durante el despliegue y {{dato:e3_aws_meses}} del acceso remoto y los respaldos durante la operación del piloto. Las herramientas no tienen costo, porque se emplean licencias libres o educativas.

{{tabla:t-costos-fijos}}

La {{ref:t-nivel1}} agrega el presupuesto por área. Las estimaciones de horas son juicio experto del equipo, contrastado con la duración real de las actividades de S1 según el historial de commits; se recalibran al cierre de cada sprint con la velocidad observada.

{{tabla:t-nivel1}}

## 3.4.2 Línea base de costos

La línea base de costos es el presupuesto aprobado, con fases temporales, contra el que se mide el desempeño [5]. Incluye la reserva de contingencia, destinada a los riesgos identificados del registro; la reserva de gestión queda fuera y solo el sponsor puede liberarla. La {{ref:t-linea-base}} detalla el cálculo.

{{tabla:t-linea-base}}

La {{ref:fig-curva-s}} distribuye el BAC en el tiempo: cada actividad aporta su costo de manera proporcional a sus días laborables en la línea base, y el resultado se acumula al cierre de cada semana.

{{figura:fig-curva-s}}

La curva S presenta tres tramos claramente diferenciados: un crecimiento moderado en S1, una meseta durante el receso entre semestres, en la que no se planifica trabajo ni gasto, y una pendiente pronunciada al inicio de S2, cuando coinciden la construcción de la consola y la compra del hardware. Ese tramo concentra el riesgo de costo del proyecto y es donde la reserva de contingencia tiene mayor probabilidad de emplearse.

## 3.4.3 Diferencia con el business case

La línea base del proyecto y la inversión del business case son magnitudes distintas que no deben sumarse ni compararse directamente. La {{ref:t-proyecto-e2}} explica la diferencia: el E2 evalúa si conviene invertir en el servicio durante su horizonte de operación; el E3 controla lo que cuesta ejecutar el proyecto hasta su cierre. La única partida común es el hardware del piloto.

{{tabla:t-proyecto-e2}}

## 3.4.4 Control presupuestal con valor ganado

El desempeño se controla con la gestión del valor ganado (EVM) [5]: el valor planificado (PV) proviene de la curva S; el valor ganado (EV) aplica la regla 0/100, que reconoce el valor de una actividad solo cuando termina; y el costo real (AC) proviene del registro de horas. El índice de desempeño del cronograma es SPI = EV / PV y el del costo, CPI = EV / AC; el umbral de alerta es {{dato:e3_umbral}}. La {{ref:t-evm}} aplica el método al avance real de S1.

{{tabla:t-evm}}

El primer corte, al {{dato:e3_semana1}}, presenta un SPI de {{dato:e3_semana1_spi}} y queda en alerta: con la regla 0/100, el trabajo en curso no suma valor hasta que se cierra. Al {{dato:e3_corte}}, el EV de {{dato:e3_ev}} supera el PV de {{dato:e3_pv}} y el SPI es de {{dato:e3_spi}}, porque las actividades técnicas se adelantaron. Este resultado no significa que el proyecto esté libre de riesgo de plazo: la ruta crítica de S1 aún depende del levantamiento con la DTI. El CPI de {{dato:e3_cpi}} no es una medición, ya que sin registro de horas el costo real se iguala al valor ganado; desde la aprobación del plan, las horas se registran en el issue semanal de seguimiento.

La {{ref:t-umbrales}} define la acción que corresponde a cada nivel de desempeño. El libro `Presupuesto_EVM_E3.xlsx` reproduce con fórmulas el presupuesto, la curva S y el EVM, y su hoja de control confirma que cada total coincide con el de Python.

{{tabla:t-umbrales}}
