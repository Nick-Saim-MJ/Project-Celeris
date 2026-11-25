# 1.2 Análisis estratégico

El análisis estratégico vincula el problema de los laboratorios con los propósitos institucionales de la universidad. Para ello, se parte de su identidad declarada, se organizan los objetivos en un mapa estratégico y se contrasta el entorno mediante el análisis FODA, el FODA cruzado y el análisis PESTEL. Finalmente, se establecen los factores de los que depende el éxito del proyecto.

## 1.2.1 Misión, visión y objetivos estratégicos

El texto oficial de la misión, la visión y los objetivos estratégicos procede del plan estratégico vigente de la UPeU, documento que aún no ha sido facilitado al equipo. Con el fin de no consignar información no verificada, la {{ref:t-identidad}} reserva el espacio de cada texto y registra únicamente los objetivos que el proyecto afecta, identificados con rótulos de trabajo (OE-a…OE-d) que serán reemplazados por los códigos oficiales una vez que la DTI proporcione el documento.

{{tabla:t-identidad}}

El mapa estratégico de la {{ref:fig-mapa-estrategico}} organiza los objetivos del proyecto en cuatro perspectivas adaptadas al ámbito universitario; las flechas indican relaciones de habilitación y se leen de abajo hacia arriba.

{{figura:fig-mapa-estrategico}}

La cadena principal parte de la medición del desperdicio, continúa con la descarga única servida a todas las estaciones y culmina en el diferimiento de la ampliación del enlace (OB-1). La segunda cadena, mediante la precarga y la autonomía del encargado, conduce a clases sin demoras (OB-2, OB-3), mientras que la transparencia y la detección (OB-4, OB-5) sostienen la confianza en los laboratorios. Ningún objetivo queda aislado.

## 1.2.2 Análisis FODA

La {{ref:t-foda}} sintetiza el análisis interno y externo. Su contenido procede de la guía del curso CE01 y se validará con la DTI y con los encargados de laboratorio. Cada elemento se acompaña de su fuente.

{{tabla:t-foda}}

El análisis FODA, por sí solo, no conduce a una respuesta única. Por ello, la {{ref:t-tows}} cruza sus elementos para formular estrategias FO, FA, DO y DA, cada una vinculada a una decisión de arquitectura (D-xx) o a una alternativa del caso de negocio. La estrategia DO-1 responde a un criterio deliberado: antes de construir una solución nueva, deben aprovecharse las capacidades existentes. El FortiGate y un servidor de actualizaciones del fabricante podrían resolver parte del problema, de modo que Celeris solo se justifica en aquello que dichas herramientas no cubren.

{{tabla:t-tows}}

## 1.2.3 Análisis PESTEL

El análisis PESTEL de la {{ref:t-pestel}} registra exclusivamente los factores con efecto demostrable sobre el proyecto, cada uno con el hecho o la norma que lo respalda y su consecuencia en el diseño.

{{tabla:t-pestel}}

Los factores legal y tecnológico son los que más condicionan el diseño. El reglamento de la Ley 29733 exige informar a los usuarios antes de descifrar tráfico, obligación de la que deriva el portal de transparencia. Por su parte, ECH y QUIC reducen la visibilidad del tráfico para una caché, lo que fundamenta el uso de proxy explícito y el bloqueo de UDP/443 en los laboratorios (D-05, D-06). El factor económico constituye la base del beneficio esperado [S-03].

## 1.2.4 Identificación de factores críticos de éxito

La {{ref:t-fce}} establece cinco factores críticos de éxito. Cada uno cuenta con un indicador clave (KPI) medible, una meta, la fuente de medición y el riesgo estratégico que lo amenaza. Las metas de tasa de acierto de caché (BHR) y de aviso previo se toman de los objetivos OB-1 y OB-4 del registro del proyecto (CI-101).

{{tabla:t-fce}}
