# 1.4 Identificación del problema

La presente sección define el problema de manera estructurada, identifica sus causas raíz, cuantifica su impacto con los supuestos del proyecto y fundamenta la conveniencia de intervenir. El enunciado de referencia es el establecido en el Marco común (00 M2.1), que aquí se descompone y se cuantifica.

## 1.4.1 Definición estructurada del problema

La {{ref:t-5w2h}} aplica la técnica 5W2H (qué, por qué, dónde, cuándo, quién, cómo y cuánto). Las cifras correspondientes a la dimensión «cuánto» se obtienen mediante el módulo de cálculo del proyecto (`gestion/e1/calculos.py`) a partir de los supuestos citados.

{{tabla:t-5w2h}}

**Enunciado del problema.** En los {{dato:labs}} laboratorios del Campus Juliaca, cada estación descarga de forma independiente los mismos archivos de gran tamaño, de modo que en cada ciclo atraviesan el enlace {{dato:gb_ciclo_lab}} por laboratorio cuando bastaría con una única copia. Como consecuencia, el enlace se satura en horario de clase, sin que exista un rol facultado para decidir qué contenido reutilizar ni un mecanismo para medir el volumen desperdiciado.

## 1.4.2 Causas raíz

El diagrama de Ishikawa de la {{ref:fig-ishikawa}} agrupa las causas identificadas en seis categorías: método, personas, tecnología, recursos, medición y entorno.

{{figura:fig-ishikawa}}

Las causas se organizan en dos grupos. Las de tecnología y recursos explican por qué la solución inmediata resulta insuficiente: la mayor parte del tráfico viaja cifrado mediante HTTPS y la ampliación del enlace constituye un gasto recurrente. Las de método, personas y medición explican la persistencia del problema: las descargas se realizan estación por estación y durante las clases, el encargado carece de herramientas y de atribuciones, y el desperdicio no se mide. Los factores del entorno agravan ambos grupos.

El árbol de problemas de la {{ref:fig-arbol}} ubica las cuatro causas principales identificadas en el Marco común por debajo del problema central, y sus efectos por encima.

{{figura:fig-arbol}}

El árbol evidencia que los efectos trascienden el ámbito técnico: retrasos en el inicio de las clases, pérdida de ancho de banda para el resto del campus, presión para ampliar el enlace, consumo de horas técnicas y un desperdicio que no se cuantifica. Al transformar el árbol de problemas en árbol de objetivos, cada causa se convierte en un medio: una copia compartida, una precarga fuera del horario de clase, un descifrado controlado y un encargado con herramientas de gestión. Estos medios corresponden a los componentes analizados en la §1.5.

El análisis de los cinco porqués de la {{ref:t-5porques}} profundiza en la causa principal: la repetición de la misma descarga en todas las estaciones del laboratorio.

{{tabla:t-5porques}}

La cadena de porqués concluye en una causa de gestión y no de infraestructura física: sin medición no es posible tomar decisiones, y sin un rol dotado de herramientas no existe un responsable que las tome. En consecuencia, la solución propuesta combina un mecanismo técnico (caché con descifrado controlado) con una capacidad de gestión (consola del encargado y métricas por laboratorio).

## 1.4.3 Impacto estratégico

La {{ref:t-impacto}} cuantifica el impacto a partir de los supuestos del registro común. Ninguna cifra se consigna manualmente: cada fila indica el método de cálculo y los supuestos empleados.

{{tabla:t-impacto}}

El impacto alcanza dos objetivos institucionales. En el ámbito de la enseñanza, un laboratorio requiere al menos {{dato:min_lab}} para descargar un ciclo aun disponiendo de la totalidad del enlace, que en la práctica comparte con el resto del campus. En el ámbito de la gestión de recursos, el crecimiento basado en ancho de banda costaría {{dato:usd_enlace_anio}} anuales por los {{dato:mbps_diferidos}} que el proyecto permitiría diferir [S-40], a lo que se suman {{dato:usd_horas_anio}} en horas técnicas. Las horas de clase perdidas aún no cuentan con un dato verificado y se levantarán con la DTI y los docentes.

## 1.4.4 Justificación de intervención

La inacción también tiene un costo: con los supuestos vigentes, mantener la situación actual representa {{dato:usd_no_actuar}} en {{dato:horizonte_anios}}, sin considerar las horas de clase perdidas. Dicho costo es recurrente y no genera capacidades nuevas, puesto que un mayor ancho de banda continuaría transportando cada copia una vez por estación, y el encargado seguiría sin posibilidad de decidir ni de medir.

La intervención propuesta consiste en una inversión única con un costo operativo reducido, cuyo resumen se presenta en la {{ref:t-caso-negocio}} como avance del caso de negocio (CE0113). El análisis completo, que incluye la comparación de alternativas, la simulación de Monte Carlo y el análisis de tornado, se desarrolla en el E2. La justificación de la intervención no depende del resultado de dicha comparación, sino de tres hechos: el problema existe, es medible y obedece a una causa de gestión que ninguna alternativa resuelve por sí sola.

{{tabla:t-caso-negocio}}
