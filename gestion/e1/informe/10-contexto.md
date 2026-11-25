# 1.1 Contexto organizacional

La presente sección describe el entorno de los laboratorios del Campus Juliaca, la estructura que decide sobre ellos, su posición en la cadena de valor y los actores con poder o interés en el proyecto. Cada afirmación cita su fuente: un supuesto [S-xx], una sección del Marco común (00 Mx) o la marca [levantar con la DTI] para datos institucionales aún no disponibles.

## 1.1.1 Descripción del sector y entorno competitivo

La Universidad Peruana Unión es una institución privada de educación superior cuyo Campus Juliaca se ubica en el altiplano, región en la que la conectividad presenta un costo mayor y una oferta de proveedores más reducida que en la costa. Esta limitación es más visible en los laboratorios de cómputo, donde se descargan el software de cada curso y las actualizaciones. El entorno competitivo se analiza en dos dimensiones. En la externa, la universidad compite por la captación de estudiantes de ingeniería, y la calidad percibida de sus laboratorios forma parte de su propuesta de valor. En la interna, Celeris compite con otras formas de resolver el mismo problema, como la ampliación del enlace o el aprovechamiento de las funciones del FortiGate existente.

La {{ref:t-porter}} aplica el modelo de las cinco fuerzas de Porter a esta situación. La intensidad asignada a cada fuerza es una valoración del equipo del proyecto, y el hecho que la sustenta se acompaña de su fuente.

{{tabla:t-porter}}

Las dos fuerzas de intensidad alta explican la pertinencia del proyecto y la necesidad de justificarlo: el poder del proveedor de conectividad encarece el crecimiento por ancho de banda [S-03], y la amenaza de sustitutos exige comparar Celeris con alternativas más simples en el E2.

La {{ref:t-conectividad}} contrasta la oferta de conectividad del campus con una referencia de la costa. Los valores sin fuente se registran como pendientes de levantamiento.

{{tabla:t-conectividad}}

Hasta cerrar estos vacíos con el contrato vigente, el costo por Mbps adicional [S-03] sostiene el beneficio económico y se somete a sensibilidad en el E2.

## 1.1.2 Estructura organizacional

El organigrama de la {{ref:fig-organigrama}} ubica las áreas que intervienen en el proyecto. Las unidades involucradas en Celeris se presentan resaltadas y rotuladas con su rol, y las dependencias jerárquicas no confirmadas se representan con borde discontinuo.

{{figura:fig-organigrama}}

La figura evidencia que el proyecto atraviesa dos líneas de mando: la académica, a la que pertenece la Escuela Profesional en la que se encuentra el equipo autor, y la tecnológica, representada por la DTI, que aprueba y opera la infraestructura. Según la guía del curso, los encargados de laboratorio, principales usuarios de la consola, dependen del área de Soporte; sin embargo, dicha dependencia y la ubicación del oficial de datos personales se encuentran pendientes de confirmación [levantar con la DTI]. Se concluye que ninguna decisión técnica del proyecto puede avanzar sin la participación de la DTI, razón por la cual su apoyo constituye el primer factor crítico de éxito (§1.2.4).

## 1.1.3 Cadena de valor

La cadena de valor de la {{ref:fig-cadena-valor}} adapta el modelo de Porter al contexto universitario e incorpora el aspecto de interés para el diagnóstico: el grado de dependencia de cada actividad respecto de los laboratorios.

{{figura:fig-cadena-valor}}

La dependencia es alta en dos actividades: la enseñanza en laboratorios, de carácter primario, y la infraestructura de TI y soporte, de carácter de apoyo. En la primera, el problema se manifiesta como retrasos en el inicio de las clases; en la segunda, como horas técnicas consumidas en cada ciclo de actualización. Las actividades de admisión y de gestión administrativa se ven afectadas por la saturación del enlace, aunque no la originan. La {{ref:t-cadena-valor}} detalla la manifestación del problema en cada actividad.

{{tabla:t-cadena-valor}}

## 1.1.4 Mapa de stakeholders

La {{ref:fig-mendelow}} clasifica a cada stakeholder según su poder sobre el proyecto y su interés en él, conforme a la matriz de Mendelow. El color identifica la estrategia de gestión asignada, que además se consigna en texto junto a cada actor.

{{figura:fig-mendelow}}

Tres actores presentan poder e interés altos o cercanos a altos y, en consecuencia, requieren una gestión cercana: la DTI, los encargados de laboratorio y el jurado del EPE. Si bien docentes y encargados comparten la misma celda, sus estrategias difieren: los encargados operan la consola y toman decisiones sobre el contenido, mientras que los docentes requieren únicamente clases sin demoras, por lo que basta con mantenerlos informados. La {{ref:t-stakeholders}} complementa la matriz con las expectativas de cada actor.

{{tabla:t-stakeholders}}
