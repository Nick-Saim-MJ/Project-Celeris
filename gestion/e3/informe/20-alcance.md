# 3.2 Gestión del Alcance

La gestión del alcance asegura que el proyecto incluya todo el trabajo requerido, y únicamente ese trabajo [1]. Para ello se emplean tres instrumentos: la EDT orientada a entregables, su diccionario y un procedimiento de control de cambios que vincula cada solicitud con su efecto en el cronograma y en los costos.

## 3.2.1 EDT / WBS

La EDT se construyó con la regla del cien por ciento: los paquetes de un nivel suman todo el trabajo del nivel superior, y ningún trabajo queda fuera de un paquete [6]. Los nombres son sustantivos que designan entregables, no verbos, y cada paquete de nivel 2 tiene un único responsable. La {{ref:fig-edt}} presenta los tres niveles, con el costo presupuestado de cada paquete y su estado al corte.

{{figura:fig-edt}}

La figura evidencia que el área 5, Prueba de concepto, concentra la mayor parte del presupuesto ({{dato:e3_n1_5}}), porque incluye el hardware del piloto; sin ese componente, el costo del proyecto es esencialmente horas del equipo. Los paquetes de ingeniería de software e infraestructura ya figuran como terminados, mientras que los de gestión de TI y cierre se reparten entre S1 y S2, y los tres paquetes nuevos de S2 (5.4–5.6) explican el trabajo de construcción que la guía original no detallaba.

La regla del cien por ciento no es una declaración, sino una comprobación: `gestion/e3/plan.py` verifica que cada una de las {{dato:e3_n_actividades}} actividades del cronograma pertenezca a un paquete de nivel 2, que todo paquete tenga al menos una actividad con costo y que las horas de los paquetes con esfuerzo comprometido en la guía (3.2, 4.1, 4.3 y 5.2) coincidan con las de sus actividades. Si una de estas condiciones falla, el plan no se genera.

## 3.2.2 Diccionario de entregables

El diccionario de la EDT documenta cada paquete con su descripción, su criterio de aceptación, el responsable, el esfuerzo en horas del equipo, el costo y los paquetes que lo preceden en el cronograma. La {{ref:t-diccionario}} lo presenta completo; las horas y los costos provienen del modelo, no de una estimación aparte.

{{tabla:t-diccionario}}

Los criterios de aceptación son verificables por un tercero: un validador en verde, una cantidad de pantallas validadas con un SUS mínimo, una ruta crítica igual en dos herramientas o un número mínimo de observaciones cronometradas. Las predecesoras entre paquetes se derivan de las dependencias de sus actividades, de modo que el diccionario y el cronograma no pueden divergir.

## 3.2.3 Asignación de responsabilidades (RACI)

La matriz RACI de la {{ref:t-raci}} asigna, para cada bloque de trabajo, quién lo realiza (R), quién lo aprueba (A), a quién se consulta (C) y a quién se informa (I). Cada fila tiene exactamente un responsable de aprobación; el validador de CE01 lo comprueba. En el prototipo de la consola, el director aprueba lo que elabora el líder técnico (CI-103), en aplicación de la regla de revisión cruzada.

{{tabla:t-raci}}

## 3.2.4 Control de cambios

Toda modificación del alcance, del cronograma o de los costos aprobados sigue el procedimiento de la {{ref:fig-cambios}}, que adapta el control integrado de cambios del PMBOK [1] al flujo de trabajo del repositorio.

{{figura:fig-cambios}}

El procedimiento convierte cada solicitud en un issue de GitHub con la etiqueta `cambio-alcance`, de manera que la solicitud, el análisis, la decisión y el commit que la implementa quedan enlazados. El análisis de impacto no es una opinión: el director modifica una copia de `plan.yaml`, ejecuta el modelo y obtiene la diferencia en la ruta crítica, en los hitos y en el BAC antes de decidir.

La {{ref:t-cambios-pasos}} detalla cada paso y la {{ref:t-cambios-nivel}} establece quién aprueba según el impacto. El formato de la solicitud figura en el anexo A.

{{tabla:t-cambios-pasos}}

{{tabla:t-cambios-nivel}}
