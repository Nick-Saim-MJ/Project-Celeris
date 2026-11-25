# 1.1 Contexto organizacional

Esta sección describe el entorno en el que operan los laboratorios del Campus Juliaca, la estructura que decide sobre ellos, el lugar que ocupan en la cadena de valor y quiénes tienen poder o interés en el proyecto. Cada afirmación lleva su fuente: un supuesto [S-xx] del registro común, una sección del Marco común (00 Mx) o la marca [levantar con la DTI] cuando el dato es institucional y todavía no se tiene.

## 1.1.1 Descripción del sector y entorno competitivo

La universidad es una institución privada del altiplano. Ahí la conectividad es más cara y hay menos proveedores que en la costa, y los laboratorios de cómputo son donde más se nota: el software de cada curso y las actualizaciones se descargan en ellos. Para el proyecto, el «entorno competitivo» tiene dos caras. Hacia fuera, la universidad compite por estudiantes de ingeniería y la calidad visible de sus laboratorios forma parte de su oferta. Hacia dentro, Celeris compite con otras formas de resolver el mismo problema, como ampliar el enlace o usar lo que ya hace el FortiGate.

La {{ref:t-porter}} aplica las cinco fuerzas de Porter a esa situación. La intensidad es una valoración del equipo y el hecho que la sustenta tiene su fuente.

{{tabla:t-porter}}

Las dos fuerzas altas explican por qué el proyecto tiene sentido y también por qué debe justificarse. El poder del proveedor de conectividad hace caro crecer por ancho de banda [S-03]. La amenaza de sustitutos obliga a comparar Celeris con alternativas más simples antes de recomendarlo, y eso lo hace el E2.

La {{ref:t-conectividad}} compara la oferta de conectividad del campus con una referencia de la costa. No se inventa ningún precio: lo que no se sabe queda como dato por levantar.

{{tabla:t-conectividad}}

La comparación todavía tiene huecos que la DTI puede cerrar con el contrato vigente y una cotización de referencia. Hasta entonces, el costo por Mbps adicional [S-03] es el supuesto que sostiene el beneficio económico, y el E2 lo somete a análisis de sensibilidad.

## 1.1.2 Estructura organizacional

El organigrama de la {{ref:fig-organigrama}} ubica las áreas que intervienen en el proyecto. Las que toca Celeris están resaltadas y rotuladas con su rol, y las dependencias que no están confirmadas llevan borde discontinuo.

{{figura:fig-organigrama}}

La figura muestra que el proyecto atraviesa dos líneas de mando: la académica (la EP, donde está el equipo autor) y la de tecnología (la DTI, que aprueba y opera). Los encargados de laboratorio, que son los usuarios principales de la consola, cuelgan de Soporte según la guía, pero esa dependencia y la ubicación del oficial de datos personales están por confirmar [levantar con la DTI]. La conclusión práctica es que ninguna decisión técnica del proyecto avanza sin la DTI, y por eso su apoyo es el primer factor crítico de éxito (§1.2.4).

## 1.1.3 Cadena de valor

La cadena de valor de la {{ref:fig-cadena-valor}} adapta el modelo de Porter a la universidad y agrega lo que interesa al diagnóstico: cuánto depende cada actividad de los laboratorios.

{{figura:fig-cadena-valor}}

La dependencia es alta en dos puntos: la enseñanza en laboratorios (actividad primaria) y la infraestructura de TI y soporte (actividad de apoyo). En la primera el problema se ve como clases que empiezan tarde; en la segunda, como horas técnicas en cada ciclo. Admisión y gestión administrativa sufren la saturación del enlace, pero no la causan. La {{ref:t-cadena-valor}} detalla cómo se manifiesta el problema en cada actividad.

{{tabla:t-cadena-valor}}

## 1.1.4 Mapa de stakeholders

La {{ref:fig-mendelow}} ubica a cada stakeholder según su poder sobre el proyecto y su interés en él (matriz de Mendelow). El color indica la estrategia acordada, que además va escrita junto a cada nombre.

{{figura:fig-mendelow}}

Tres actores tienen poder e interés altos o casi altos y se gestionan de cerca: la DTI, los encargados de laboratorio y el jurado del EPE. Docentes y encargados ocupan la misma celda, pero su estrategia es distinta: los encargados operan la consola y deciden, mientras que los docentes solo necesitan clases sin esperas, así que basta con mantenerlos informados. La {{ref:t-stakeholders}} completa la matriz con lo que espera cada actor.

{{tabla:t-stakeholders}}
