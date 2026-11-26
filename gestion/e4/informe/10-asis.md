# 4.1 Proceso Actual (AS-IS)

## 4.1.1 Identificación y caracterización de los procesos

El análisis parte de los procesos de la universidad que tocan los laboratorios de cómputo y sigue el ciclo de identificación, descubrimiento, análisis y rediseño de la gestión por procesos [4]. La {{ref:fig-mapa}} los organiza en estratégicos, misionales y de apoyo, a partir de la cadena de valor del E1 [6]; los nombres de los procesos estratégicos y de apoyo se validarán con la DTI.

{{figura:fig-mapa}}

El mapa muestra que los procesos candidatos pertenecen al apoyo de la DTI, pero que su efecto recae en el proceso misional «Enseñanza en laboratorios»: cuando una descarga no termina o un laboratorio no está listo, la clase empieza tarde. Por eso la mejora de un proceso de apoyo se mide en indicadores que percibe el docente, como las preparaciones listas al inicio de la clase.

Entre los cinco procesos de apoyo que tocan los laboratorios, la {{ref:t-seleccion}} pondera el volumen de descarga, el impacto en las clases, la frecuencia, la dependencia de TI y la factibilidad con el alcance del SRS. P2 obtiene {{dato:e4_sel_p2}} y P1 {{dato:e4_sel_p1}}; el tercero, la instalación de la imagen base, obtiene {{dato:e4_sel_tercero}} porque ocurre una vez por semestre y usa herramientas de clonación ajenas a la caché.

{{tabla:t-seleccion}}

La {{ref:t-ficha}} caracteriza los dos procesos elegidos con su objetivo, dueño, disparador, frecuencia e indicadores; la {{ref:t-sipoc}} resume sus proveedores, entradas, pasos, salidas y clientes con el formato SIPOC [5]. La frecuencia anual sale de los supuestos de ciclos por PC [S-06], laboratorios [S-26] y pedidos por semana [S-45].

{{tabla:t-ficha}}

{{tabla:t-sipoc}}

## 4.1.2 Descripción narrativa del proceso

**P1, actualización masiva de las PCs de un laboratorio.** Al iniciar un ciclo de actualización, el técnico de DTI Soporte programa la actualización y el encargado reserva una franja libre del laboratorio. Cada una de las {{dato:e4_pcs}} descarga el mismo paquete desde Internet ({{dato:e4_gb_pc}} por PC [S-27]), en competencia con las clases y los servicios del campus [S-42]. Si una clase empieza antes de que la descarga termine, el técnico la interrumpe y la reprograma para otro día con franja libre, y la parte pendiente vuelve a cruzar el enlace. Cuando la descarga termina, las PCs instalan la actualización y el técnico verifica PC por PC cuáles terminaron y relanza las que fallaron.

**P2, preparación de un laboratorio para una clase.** El docente avisa al encargado por mensaje o en persona que necesita un software o un material, a veces el mismo día de la clase. El encargado revisa el pedido; si requiere una fuente nueva o un cambio de acceso, no puede hacerlo por sí mismo y lo solicita a la DTI, que lo atiende según su carga de trabajo. Después, las {{dato:e4_pcs}} descargan el material desde Internet durante la preparación o la propia clase, y el encargado verifica PC por PC que el material esté disponible. El pedido y su resultado no quedan registrados.

## 4.1.3 Indicadores actuales

La {{ref:t-indicadores-asis}} define la línea base con su fórmula, su método de medición y el número mínimo de observaciones. El tiempo de descarga y el tráfico se calculan con supuestos registrados; el resto se estima con la simulación descrita en la sección 4.2.4 y se marca como estimado hasta reunir {{dato:e4_obs_min}} observaciones por fase con la plantilla de registro de tiempos del equipo, que separa las fases de solicitud, decisión, descarga, instalación y verificación.

{{tabla:t-indicadores-asis}}

El cálculo de la descarga de P1 es directo: {{dato:e4_gb_lab}} por el enlace con {{dato:e4_mbps_wan}} disponibles [S-26, S-27, S-42] dan {{dato:e4_wan_lab}}. El tráfico medio de P1 supera ese volumen porque {{dato:e4_p_int}} de las descargas se interrumpen [S-44] y la parte pendiente vuelve a descargarse por Internet.

## 4.1.4 Diagrama BPMN

La {{ref:fig-p1-asis}} presenta P1 en BPMN 2.0 [1], con el pool «UPeU Campus Juliaca», los carriles de los participantes, el pool colapsado «Internet / ISP» que recibe los flujos de mensaje de cada descarga y una anotación PD-xx sobre cada ineficiencia.

{{figura:fig-p1-asis}}

El diagrama hace visible el ciclo de reproceso: la compuerta «¿Terminó antes de la siguiente clase?» devuelve el flujo al técnico, a una espera de días y a una nueva descarga por Internet. La verificación PC por PC del técnico es la tarea de mayor esfuerzo, porque nada le indica qué PCs terminaron la descarga.

La {{ref:fig-p2-asis}} presenta P2 con los carriles del docente, el encargado, el técnico de la DTI y las PCs del laboratorio.

{{figura:fig-p2-asis}}

El diagrama muestra que la ruta que pasa por la DTI concentra la espera del proceso y que tanto el aviso informal como el cierre sin registro impiden medir el cumplimiento. Cuando el pedido llega el mismo día, la descarga y la verificación PC por PC no caben en el margen hasta la clase.

## 4.1.5 Problemas detectados

La {{ref:t-problemas}} vincula cada ineficiencia anotada en los diagramas con su causa en el diagrama de Ishikawa del E1 [7], su efecto sobre los problemas operativos PO-x del E1 y el indicador que la mide. Cada PD-xx aparece en el diagrama y en la tabla, y su causa se cita textualmente del Ishikawa del E1.

{{tabla:t-problemas}}

Las causas se concentran en la categoría «Método» (descarga independiente en cada estación, descargas en horario de clase, sin ventana de precarga) y en «Medición» (sin indicadores por laboratorio). Ninguna de ellas se resuelve contratando más ancho de banda: se resuelven cambiando dónde y cuándo ocurre la descarga y dando al encargado la herramienta para gestionarla.
