# 1.4 Identificación del problema

Esta sección define el problema de forma estructurada, busca sus causas raíz, cuantifica su impacto con los supuestos del proyecto y justifica por qué conviene intervenir. El enunciado de referencia es el del Marco común (00 M2.1); aquí se descompone y se mide.

## 1.4.1 Definición estructurada del problema

La {{ref:t-5w2h}} aplica la plantilla 5W2H (qué, por qué, dónde, cuándo, quién, cómo y cuánto). Las cifras del «cuánto» las calcula `gestion/e1/calculos.py` a partir de los supuestos citados.

{{tabla:t-5w2h}}

**Enunciado.** En los {{dato:labs}} laboratorios del Campus Juliaca, cada PC descarga por separado los mismos archivos grandes, y en cada ciclo cruzan el enlace {{dato:gb_ciclo_lab}} por laboratorio cuando bastaría con una copia. El enlace se satura en horario de clase y nadie puede decidir qué reutilizar ni medir cuánto se pierde.

## 1.4.2 Causas raíz

El diagrama de Ishikawa de la {{ref:fig-ishikawa}} agrupa las causas en seis categorías: método, personas, tecnología, recursos, medición y entorno.

{{figura:fig-ishikawa}}

Las causas se agrupan en dos familias. Las de tecnología y recursos explican por qué la solución obvia no alcanza: casi todo viaja por HTTPS y ampliar el enlace es un gasto que se repite cada año. Las de método, personas y medición explican por qué el problema persiste: las descargas ocurren PC por PC y en clase, el encargado no tiene herramienta ni atribución, y nadie mide el desperdicio. El entorno agrava las dos familias.

El árbol de problemas de la {{ref:fig-arbol}} ordena las cuatro causas principales del Marco común debajo del problema central y los efectos encima.

{{figura:fig-arbol}}

El árbol muestra que los efectos no son solo técnicos: clases que empiezan tarde, un campus que pierde ancho de banda, presión para ampliar el enlace, horas técnicas y un desperdicio que nadie conoce. Al dar vuelta el árbol, cada causa pasa a ser un medio: una copia compartida, una precarga fuera de clase, el descifrado controlado y un encargado con herramienta. Esos medios son los componentes de la §1.5.

Los cinco porqués de la {{ref:t-5porques}} profundizan en la causa principal: la misma descarga se repite en todas las PCs del laboratorio.

{{tabla:t-5porques}}

La cadena termina en una causa de gestión, no de cableado: sin medición no hay decisión, y sin un rol con herramienta no hay quien decida. Por eso la solución combina un mecanismo técnico (caché con descifrado controlado) con una capacidad de gestión (consola del encargado y métricas por laboratorio).

## 1.4.3 Impacto estratégico

La {{ref:t-impacto}} cuantifica el impacto con los supuestos del registro común. Ninguna cifra está escrita a mano: cada fila dice cómo se calcula y qué supuestos usa.

{{tabla:t-impacto}}

El impacto toca dos objetivos institucionales. En la enseñanza, el laboratorio tarda al menos {{dato:min_lab}} en descargar un ciclo, aun usando todo el enlace, y en la práctica comparte el enlace con el resto del campus. En la gestión de recursos, crecer por ancho de banda costaría {{dato:usd_enlace_anio}} al año por los {{dato:mbps_diferidos}} que el proyecto puede diferir [S-40], más {{dato:usd_horas_anio}} en horas técnicas. Las horas de clase perdidas no tienen dato todavía y se levantan con la DTI y los docentes.

## 1.4.4 Justificación de intervención

No actuar también tiene costo: con los supuestos actuales, mantener la situación cuesta {{dato:usd_no_actuar}} en {{dato:horizonte_anios}}, sin contar las horas de clase. Ese costo se repite cada año y no deja ninguna capacidad nueva: más ancho de banda sigue trayendo cada copia una vez por PC, y el encargado sigue sin poder decidir ni medir.

La intervención propuesta es una inversión única con un costo operativo bajo, y se resume en la {{ref:t-caso-negocio}} como avance del caso de negocio (CE0113). El análisis completo, con la comparación de alternativas, Monte Carlo y tornado, es el E2. La justificación no depende de que Celeris gane esa comparación: depende de que el problema existe, se puede medir y tiene una causa de gestión que ninguna alternativa resuelve por sí sola.

{{tabla:t-caso-negocio}}
