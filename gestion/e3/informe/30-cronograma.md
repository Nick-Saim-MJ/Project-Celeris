# 3.3 Gestión del Cronograma

El cronograma se desarrolla con el método de la ruta crítica (CPM) [7] sobre el calendario del proyecto, el mismo que contiene el archivo de Microsoft Project: jornada de lunes a viernes {{dato:e3_jornada}}, con una hora de almuerzo; feriados nacionales del {{dato:e3_feriados}}; y receso entre semestres {{dato:e3_receso}}, registrados como días no laborables. El inicio de S2, el {{dato:e3_inicio_s2}}, se fija como restricción «no comenzar antes del» del hito HS2; la sustentación de S1 ({{dato:e3_fin_s1}}) y la duración de S2 ({{dato:e3_semanas_s2}}) no se imponen como restricciones, sino que se verifican contra las fechas que resultan del cálculo. Las duraciones se expresan en días laborables y las dependencias son de tipo fin a inicio (FS) o inicio a inicio (SS), con desfase cuando corresponde. El trabajo terminado conserva la fecha real del commit que lo cerró en la rama principal, y el trabajo pendiente no se programa antes de la fecha de corte.

## 3.3.1 Lista de actividades

La {{ref:t-actividades}} presenta las {{dato:e3_n_actividades}} actividades con su duración planificada, sus fechas actuales, sus predecesoras, su holgura total y su estado. Las {{dato:e3_n_hechas}} actividades terminadas indican el commit que las respalda; una holgura de cero identifica una actividad crítica.

{{tabla:t-actividades}}

La secuencia responde a la lógica del trabajo y no a la conveniencia del calendario. En S1, el levantamiento con la DTI y los encargados (2.1.2) alimenta tres entregables: la actualización del diagnóstico, la cotización del ISP para el business case y el cronometraje que requiere el modelado AS-IS / TO-BE. En S2, la construcción de la consola en sprints (5.4.1–5.4.3) y la adquisición del hardware (5.1.2) avanzan en paralelo y convergen en el despliegue del piloto (5.5.2).

La {{ref:t-recursos}} resume las horas asignadas a cada recurso. Solo las horas del equipo se valorizan; las de la DTI, los encargados y el docente se planifican como trabajo, porque su disponibilidad condiciona el cronograma, pero constituyen aporte institucional.

{{tabla:t-recursos}}

## 3.3.2 Diagrama de Gantt

El cronograma de S1 se presenta en la {{ref:fig-gantt-s1}}, con las actividades terminadas, la ruta crítica, la holgura de cada actividad pendiente y la línea base cuando difiere del pronóstico.

{{figura:fig-gantt-s1}}

El diagrama muestra que el trabajo técnico de S1 se adelantó a la línea base: los diseños de red y de centro de datos, el SRS, el prototipo y el laboratorio emulado se cerraron en la primera semana. La ruta crítica restante de S1 es {{dato:e3_rc_s1}}: depende de que la DTI y los encargados atiendan el levantamiento, por lo que el riesgo RP-01 es el que con mayor probabilidad podría desplazar la sustentación del {{dato:e3_h1}}.

La {{ref:fig-gantt-s2}} presenta el cronograma de S2, desde el inicio del semestre hasta la sustentación final.

{{figura:fig-gantt-s2}}

En S2, la ruta crítica es {{dato:e3_rc_s2}}: la consola, y no el hardware, determina la fecha del piloto. La adquisición del hardware conserva una holgura de {{dato:e3_holgura_512}}, que absorbe una parte de los plazos de compra de la universidad (RP-09). La operación del piloto, de cuatro semanas, es la actividad más larga de la ruta y la que produce la evidencia para la decisión de ampliación.

## 3.3.3 Hitos principales

La {{ref:t-hitos}} presenta los seis hitos del proyecto con su fecha en la línea base, su pronóstico actual y la condición que debe cumplirse para darlos por alcanzados. H2 y H3 son los puntos de decisión definidos en el roadmap del E1: si la DTI no aprueba el piloto o si el BHR medido no justifica la ampliación, el proyecto cierra con las lecciones aprendidas y sin comprometer inversión adicional.

{{tabla:t-hitos}}

## 3.3.4 Verificación con Microsoft Project

El modelo genera el archivo `entregables/CE01/E3/Cronograma_Celeris.xml` en formato MSPDI [8], con la jerarquía de la EDT como tareas de resumen, las dependencias con su tipo y desfase, los recursos con sus asignaciones, los costos, la línea base y el calendario con sus excepciones. Al regenerarse, el plan abre ese archivo con Microsoft Project mediante automatización COM, deja que la herramienta recalcule y compara, tarea por tarea, las fechas, la holgura total, la marca de ruta crítica y el costo con los valores de Python; si alguna difiere, la generación se detiene. La {{ref:t-msproject}} resume el resultado de la última regeneración.

{{tabla:t-msproject}}

Esta comparación elimina la dependencia de una sola herramienta: Python garantiza que el cronograma se deriva de la fuente única y Microsoft Project, que la lógica del cálculo es la estándar de la profesión.
