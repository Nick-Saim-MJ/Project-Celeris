# 1.3 Diagnóstico digital / TI

El diagnóstico de tecnologías de información responde a cuatro preguntas: qué sistemas operan actualmente en torno a los laboratorios, qué grado de madurez presentan los procesos de TI involucrados en el proyecto, qué brechas existen entre la situación actual y la requerida, y qué problemas operativos se derivan de dichas brechas.

## 1.3.1 Inventario de sistemas de información existentes

La {{ref:t-inventario}} presenta los sistemas relacionados con los laboratorios, con su responsable, versión, soporte, dependencia de Internet y criticidad. La última columna indica el grado de certeza de cada dato: un supuesto del registro común o un dato pendiente de levantamiento con la DTI.

{{tabla:t-inventario}}

Tres datos de este inventario condicionan decisiones del proyecto. El primero es el modelo del FortiGate y la disponibilidad de caché web, que determina la viabilidad de la alternativa A5. El segundo es la existencia de un servidor de actualizaciones (WSUS o equivalente), que cubriría las actualizaciones de Windows (alternativa A3). El tercero es la herramienta de gestión de imágenes y políticas de las estaciones, mediante la cual se distribuye el archivo PAC (D-05). Los tres datos se incluyen en la guía de entrevista con la DTI.

## 1.3.2 Nivel de madurez digital (COBIT 2019)

La madurez se evalúa mediante la escala de capacidad de COBIT 2019 (0 a 5) en los seis objetivos de gobierno y gestión que el proyecto involucra. El nivel actual no se presume: se determinará mediante una entrevista estructurada sustentada en evidencia, cuyo instrumento se encuentra en el repositorio del proyecto (`gestion/e1/instrumentos/entrevista-cobit.md`). La {{ref:t-cobit}} presenta, para cada objetivo, la pregunta guía, la evidencia que se solicitará y el nivel requerido al cierre del piloto.

{{tabla:t-cobit}}

La {{ref:fig-radar-cobit}} representa el nivel objetivo de cada proceso. El nivel actual se incorporará como segunda serie una vez registrados los resultados de la entrevista; hasta entonces, la figura lo identifica como pendiente.

{{figura:fig-radar-cobit}}

La figura muestra un perfil objetivo prácticamente uniforme en el nivel definido (3), lo que implica procesos documentados, con responsable asignado y sujetos a medición. La excepción es APO12, para el cual resulta suficiente un registro de riesgos gestionado (2). La brecha relevante no reside en la forma del polígono, sino en la distancia que revele la entrevista; por esta razón, el criterio de identificación de brechas con evidencia objetiva depende de dicha medición.

## 1.3.3 Brechas tecnológicas

El análisis de brechas de la {{ref:t-brechas}} relaciona cada situación actual con el estado deseado, la acción que la cierra, el componente de Celeris que la ejecuta y el objetivo del proyecto al que contribuye. La columna COBIT vincula cada brecha con el proceso que la entrevista evaluará.

{{tabla:t-brechas}}

La {{ref:fig-brechas}} cuantifica las brechas que ya pueden calcularse con los supuestos y las metas del registro del proyecto, y mantiene visible la brecha COBIT pendiente de medición.

{{figura:fig-brechas}}

La brecha de mayor magnitud es la de volumen: actualmente atraviesan el enlace {{dato:gb_ciclo_lab}} por laboratorio y ciclo, cuando sería suficiente transferir una sola copia de {{dato:gb_pc}}. La brecha de tiempo se reduce de {{dato:min_lab}} a {{dato:min_lab_meta}} con la meta de OB-2, y la de transparencia pasa de ninguna estación informada a la totalidad. Las tres cifras constituyen cotas derivadas de supuestos y serán reemplazadas por mediciones durante el piloto.

El análisis con enfoque de pensamiento lateral exige reconocer las capacidades que ya funcionan. La {{ref:t-ya-resuelto}} registra las necesidades que la infraestructura actual ya atiende y que Celeris no debe duplicar.

{{tabla:t-ya-resuelto}}

## 1.3.4 Problemas operativos asociados a TI

La {{ref:t-problemas}} presenta los cinco problemas operativos que el diagnóstico asocia a TI, con su impacto y frecuencia según la valoración del equipo, y la evidencia que permitirá confirmarlos.

{{tabla:t-problemas}}

La {{ref:fig-impacto-frecuencia}} ubica dichos problemas en una matriz de impacto × frecuencia con los mismos umbrales empleados en la matriz de riesgos.

{{figura:fig-impacto-frecuencia}}

Dos problemas se sitúan en la zona alta: la saturación del enlace durante las clases (PO-1), por su impacto, y la ausencia de medición del desperdicio (PO-5), por su frecuencia permanente. Los tres restantes se ubican en la zona media y se derivan de los dos primeros. Si el desperdicio se midiera, la saturación tendría un responsable y una vía de solución; por ello, el análisis de causa raíz del §1.4 se orienta hacia la medición y la toma de decisiones, y no únicamente hacia la capacidad del enlace.
