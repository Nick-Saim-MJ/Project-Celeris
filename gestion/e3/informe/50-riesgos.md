# 3.5 Gestión de Riesgos

Los riesgos del proyecto (RP) amenazan la ejecución del plan: su alcance, su cronograma o su costo. Se distinguen de los riesgos estratégicos RE-01…RE-12 del E1 y del E2, que amenazan el valor del servicio. Ambos registros se emplean en el seguimiento semanal; este plan desarrolla los RP, cuya respuesta depende del equipo.

## 3.5.1 Identificación

Los riesgos RP-01…RP-07 provienen de la guía del proyecto; RP-08, RP-09 y RP-10 se identificaron al construir este plan (CI-103): el calendario académico no publicado, los plazos de compra del hardware y la disponibilidad de los encargados para validar. Cada riesgo se formula con la estructura causa, evento y efecto, que evita confundir el riesgo con su origen o con su consecuencia. La {{ref:t-riesgos-analisis}} presenta el registro.

{{tabla:t-riesgos-analisis}}

## 3.5.2 Análisis cualitativo

La probabilidad (P) y el impacto (I) se valoran en una escala de 1 a 5, y su producto determina la severidad: ALTO desde 15, MEDIO entre 8 y 14, y BAJO hasta 7. La prioridad ordena los riesgos por severidad y, en caso de empate, por impacto. La {{ref:fig-riesgos}} ubica los diez riesgos en el mapa de calor.

{{figura:fig-riesgos}}

El mapa muestra que ningún riesgo del proyecto alcanza el nivel ALTO, pero que la mayoría se concentra en la franja MEDIA con impacto 3 o 4. Los riesgos que encabezan la prioridad son RP-01, RP-03 y RP-09, de impacto 4: el primero puede desplazar la ruta crítica de S1, el segundo comprometería la credibilidad de toda la evidencia y el tercero, la fecha del piloto. RP-04, de impacto máximo, tiene baja probabilidad porque el control preventivo ya opera en el CI.

## 3.5.3 Plan de respuesta

Cada riesgo tiene una estrategia (evitar, mitigar, transferir o aceptar), una respuesta preventiva, un plan de contingencia que se ejecuta si el riesgo se materializa, un disparador observable y un dueño. La {{ref:t-riesgos-respuesta}} presenta el plan ordenado por severidad.

{{tabla:t-riesgos-respuesta}}

Los disparadores se definieron para que cualquiera de los dos integrantes pueda reconocerlos sin interpretación: una reunión sin fecha confirmada, un validador en rojo, un SPI por debajo del umbral, una alarma de AWS Budgets o una orden de compra no emitida en la fecha indicada. La reserva de contingencia de la línea base financia la ejecución de los planes de contingencia; la estrategia de aceptar se reservó para RP-08, porque el calendario académico no depende del equipo y su efecto se absorbe recalculando el modelo.

## 3.5.4 Seguimiento

El registro se revisa cada viernes en la reunión de seguimiento, con la participación de ambos integrantes y, en S2, del docente. El director actualiza en `gestion/ce01.yaml` el estado, la probabilidad y el impacto de cada riesgo, registra los nuevos con el siguiente identificador libre y enlaza el cambio en el issue semanal; el mapa de calor se regenera con el informe. Un riesgo se cierra cuando desaparece su causa o cuando su ventana de ocurrencia ha pasado, como ocurrirá con RP-08 cuando se publique el calendario académico.
