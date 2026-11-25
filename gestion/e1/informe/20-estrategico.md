# 1.2 Análisis estratégico

El análisis estratégico conecta el problema de los laboratorios con lo que la universidad quiere lograr. Se parte de su identidad declarada, se ordenan los objetivos en un mapa estratégico y se contrasta el entorno con el FODA, el FODA cruzado y el PESTEL. Al final se fijan los factores de los que depende el éxito del proyecto.

## 1.2.1 Misión, visión y objetivos estratégicos

El texto oficial de la misión, la visión y los objetivos estratégicos sale del plan estratégico vigente de la UPeU, que el equipo todavía no tiene. No se inventa: la {{ref:t-identidad}} deja el lugar de cada texto y registra solo los objetivos que el proyecto afecta, con rótulos de trabajo (OE-a…OE-d) que se reemplazan por los códigos oficiales cuando la DTI entregue el documento.

{{tabla:t-identidad}}

El mapa estratégico de la {{ref:fig-mapa-estrategico}} ordena los objetivos del proyecto en cuatro perspectivas, adaptadas a una universidad. Las flechas indican qué objetivo hace posible a cuál: se leen de abajo (aprendizaje) hacia arriba (resultado institucional).

{{figura:fig-mapa-estrategico}}

La cadena principal empieza en «medir el desperdicio por laboratorio», pasa por «descargar una vez, servir muchas» y termina en «diferir la ampliación del enlace» (OB-1). La segunda cadena pasa por la precarga y por la autonomía del encargado para llegar a las clases sin esperas (OB-2, OB-3). La transparencia y la detección (OB-4, OB-5) sostienen la confianza en los laboratorios. Ningún objetivo queda suelto: cada uno sirve al menos a otro de la perspectiva superior.

## 1.2.2 Análisis FODA

La {{ref:t-foda}} resume el análisis interno y externo. Viene de la guía CE01 y se valida con la DTI y los encargados. Cada elemento lleva su fuente.

{{tabla:t-foda}}

El FODA no lleva a una sola respuesta. La {{ref:t-tows}} cruza sus elementos para obtener estrategias FO, FA, DO y DA, y cada estrategia apunta a una decisión de arquitectura (D-xx) o a una alternativa del business case. La estrategia DO-1 es deliberada: antes de construir, hay que usar lo que ya existe. El FortiGate y un servidor de actualizaciones del fabricante pueden resolver una parte del problema, y Celeris solo se justifica en lo que ellos no cubren.

{{tabla:t-tows}}

## 1.2.3 Análisis PESTEL

El análisis PESTEL de la {{ref:t-pestel}} solo registra factores con efecto real en el proyecto, cada uno con el hecho o la norma que lo respalda y lo que cambia en el diseño.

{{tabla:t-pestel}}

Los factores legal y tecnológico son los que más condicionan el diseño. El reglamento de la Ley 29733 obliga a avisar antes de descifrar, y de ahí sale el portal de transparencia. ECH y QUIC reducen lo que una caché puede ver, y de ahí salen el proxy explícito y el bloqueo de UDP/443 en los laboratorios (D-05, D-06). El factor económico es la base del beneficio [S-03].

## 1.2.4 Identificación de factores críticos de éxito

La {{ref:t-fce}} fija cinco factores críticos de éxito. Cada uno tiene un KPI medible, una meta, la fuente de la medición y el riesgo estratégico que lo amenaza. Las metas de BHR y de aviso previo se leen de los objetivos OB-1 y OB-4 del repositorio (CI-101).

{{tabla:t-fce}}
