# 4.3 Análisis Comparativo

El comparativo resume, para cada dimensión, el valor del AS-IS, el del TO-BE, el porcentaje de mejora y el método con que se verificará en el piloto. La {{ref:fig-comparativo}} presenta los indicadores principales de ambos procesos en un índice en que el AS-IS vale cien.

{{figura:fig-comparativo}}

El gráfico muestra que el tráfico por el enlace es la medida que más se reduce en ambos procesos, porque cada contenido cruza el enlace una sola vez. En P1, la ocupación del laboratorio y las horas de personal se reducen menos que la descarga, porque la instalación y la verificación de la instalación no cambian; en P2, todas las medidas caen en proporción parecida, porque desaparecen la espera de la DTI y la verificación PC por PC.

## 4.3.1 Reducción de tiempos

La {{ref:t-tiempos}} compara los tiempos. La descarga para dejar listo un laboratorio, indicador de OB-2, baja de {{dato:e4_wan_lab}} a {{dato:e4_lan_lab}} ({{dato:e4_kpi1_mejora}}) y supera la meta {{dato:e4_meta_ob2}}. La guía CE01 estimaba {{dato:e4_guia_tobe}} para el TO-BE porque descargaba el primer paquete por Internet en horario de clase; con la precarga nocturna, esa parte sale del horario del laboratorio.

{{tabla:t-tiempos}}

El tiempo de ciclo de P1 en el TO-BE incluye la espera hasta la ventana nocturna, que no ocupa el laboratorio; por eso el indicador que interesa al docente es la ocupación del laboratorio, que baja de {{dato:e4_p1_ocupacion_h_asis}} a {{dato:e4_p1_ocupacion_h_tobe}}. En P2, el tiempo medio para habilitar una fuente o un acceso pasa de {{dato:e4_p2_habilitar_h_asis}} a {{dato:e4_p2_habilitar_h_tobe}}; su mediana es de {{dato:e4_p2_habilitar_p50_tobe}}, y la media la elevan los pedidos que requieren descifrar y esperan la aprobación de la DTI.

## 4.3.2 Reducción de costos

La {{ref:t-costos}} compara el costo de personal por ejecución y por año, y el tráfico anual por el enlace.

{{tabla:t-costos}}

El costo de personal de ambos procesos baja de {{dato:e4_costo_anio_asis}} a {{dato:e4_costo_anio_tobe}} al año, un ahorro de {{dato:e4_costo_anio_ahorro}}. P2 aporta la mayor parte porque se ejecuta {{dato:e4_pedidos_p2}} al año, frente a {{dato:e4_ciclos_p1}} de P1. El tráfico evitado no se suma aquí como ahorro en dinero: su valor ya está en el beneficio BN-1 del E2 (Mbps de ampliación diferidos), y sumarlo de nuevo lo contaría dos veces.

## 4.3.3 Mejora en calidad

La {{ref:t-calidad}} compara los indicadores de calidad del servicio.

{{tabla:t-calidad}}

Las preparaciones listas al inicio de la clase suben de {{dato:e4_p2_listo_asis}} a {{dato:e4_p2_listo_tobe}}, y los pedidos habilitados dentro de la meta de OB-3 ({{dato:e4_meta_ob3}}) pasan de {{dato:e4_hab_meta_asis}} a {{dato:e4_hab_meta_tobe}}. El TO-BE no alcanza la meta de {{dato:e4_meta_listo}} de preparaciones listas: cuando el pedido llega el mismo día [S-44], el margen hasta la clase puede ser menor que la entrega desde la caché más la verificación. Esta brecha no se cierra con tecnología, sino pidiendo con anticipación; la consola la hace medible y permite gestionarla con los docentes en el piloto.

## 4.3.4 Alcance y verificación de la mejora

La mejora informada es una estimación: las descargas se calculan con supuestos registrados y las tareas manuales con duraciones triangulares [S-43]. La instalación no se acelera, solo la descarga; por eso la mejora total de P1 depende de medir la fase de instalación, que hoy se estima. Cada indicador tiene su método de verificación en las tablas anteriores, y la plantilla de cronometraje permite reemplazar cada estimación por una medición sin cambiar el texto del informe: al regenerarlo, las cifras se recalculan desde `gestion/e4/simulacion.yaml`. Si los resultados de Bizagi difieren en más de un diez por ciento de los de Python, el generador lo informa para revisar los parámetros.
