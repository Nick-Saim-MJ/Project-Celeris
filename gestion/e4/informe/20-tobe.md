# 4.2 Proceso Propuesto (TO-BE)

## 4.2.1 Rediseño del flujo

El rediseño conserva los dueños de cada proceso y agrega un carril nuevo, «Celeris (consola + nodo)», con las tareas que pasan a ser automáticas (tareas de servicio). El principio es uno solo: el contenido cruza el enlace a Internet una vez, de noche, y las PCs lo reciben desde la caché por la LAN de {{dato:e4_lan}} [S-14]. La {{ref:fig-p1-tobe}} presenta P1 rediseñado.

{{figura:fig-p1-tobe}}

En P1, el encargado programa la precarga en la consola; el nodo descarga una sola vez en la ventana nocturna con el límite que verifica la prueba T50 ({{dato:e4_mbps_precarga}}, {{dato:e4_wan_precarga}} por paquete), y de día las PCs reciben la actualización desde la caché en {{dato:e4_lan_lab}}. Como la entrega dura menos, la probabilidad de que una clase la interrumpa baja de {{dato:e4_p_int}} a {{dato:e4_p_int_tobe}}, y la parte pendiente sale de la caché, no del enlace.

La {{ref:fig-p2-tobe}} presenta P2 rediseñado.

{{figura:fig-p2-tobe}}

En P2, el docente registra el pedido en la consola y el encargado agrega la fuente al catálogo o habilita el laboratorio sin pedirlo a la DTI; la DTI solo interviene cuando la fuente requiere descifrar, y aprueba en la misma consola. El nodo aplica la configuración firmada, precarga el material y registra la auditoría y el ahorro, de modo que el proceso deja un registro que hoy no existe.

La {{ref:t-eliminadas}} lista las tareas del AS-IS que desaparecen o se sustituyen y el motivo de cada cambio.

{{tabla:t-eliminadas}}

## 4.2.2 Automatizaciones propuestas

La {{ref:t-automatizaciones}} detalla cada automatización con la tarea del AS-IS que reemplaza, la tecnología que la realiza, el requisito del SRS de CE02 que la especifica y la prueba que la verifica (infra/pruebas.yaml o un escenario BDD del SRS). Cada PD-xx queda eliminado por al menos una automatización; el generador falla si falta el requisito o la prueba.

{{tabla:t-automatizaciones}}

Las automatizaciones no inventan funciones nuevas: todas están en el alcance del SRS, de modo que el TO-BE es construible con la consola planificada en el E3. La precarga (AU-1, AU-2) ataca el volumen y el horario de la descarga; el catálogo y el acceso por laboratorio (AU-5) atacan la dependencia de la DTI; el registro de pedidos y la auditoría (AU-4, AU-7) hacen medible el proceso.

## 4.2.3 Nuevos indicadores

La {{ref:t-indicadores-tobe}} define los indicadores del TO-BE con su meta, su fórmula, la fuente automática del dato (consola, auditoría o contadores del FortiGate) y su frecuencia. Las metas de KPI-1 a KPI-3 son las de los objetivos del proyecto OB-1 a OB-3; la de KPI-4, la de la guía CE01; las demás parten del valor simulado y se recalibran con el piloto.

{{tabla:t-indicadores-tobe}}

## 4.2.4 Mejora estimada en eficiencia

La mejora se estima con una simulación de Monte Carlo [2] sobre los mismos diagramas BPMN. Cada iteración recorre el diagrama desde el evento de inicio, muestrea la duración de cada tarea (triangular [S-43] o la fórmula de descarga con supuestos registrados) y elige la salida de cada compuerta con su probabilidad [S-44]; se ejecutan {{dato:e4_iteraciones}} iteraciones por escenario con la semilla {{dato:e4_semilla}}. El costo de personal valoriza las horas del técnico y del encargado a {{dato:e4_tarifa}} [S-07]; el tiempo del docente se informa, pero no se valoriza. Los parámetros completos están en el anexo A, en el formato que se carga en Bizagi Modeler [3] para repetir la simulación.

La {{ref:t-mejora}} informa la media y los percentiles 10 y 90 de cada medida en los cuatro escenarios.

{{tabla:t-mejora}}

La {{ref:fig-dispersion}} muestra la distribución del costo de personal por ciclo en los cuatro escenarios.

{{figura:fig-dispersion}}

La dispersión del AS-IS es mayor porque incluye el reproceso: en P1, las descargas interrumpidas suman horas de reprogramación y una nueva descarga; en P2, la espera de la DTI varía de horas a días. En el TO-BE, el percentil 90 del costo queda por debajo de la media del AS-IS en ambos procesos, de modo que la mejora no depende del caso favorable.

El ahorro de personal de P1 tiene un límite explícito: la consola confirma las descargas del laboratorio en conjunto, pero no el estado de cada PC, porque el requisito REQ-NF-07 prohíbe registrar las IP de los equipos; la verificación de la instalación sigue siendo manual. Por eso el modelo estima un ahorro de {{dato:e4_ahorro_h_pc}} por PC y ciclo, menor que las {{dato:e4_horas_pc_e2}} que supone el E2 [S-07]. La {{ref:t-e2}} compara ambos valores y agrega el ahorro de P2, que el E2 no valoriza.

{{tabla:t-e2}}

Los valores del E4 se exportan a `gestion/e4/datos/resultados.json` para que el E2 los use en lugar de S-07 cuando se midan; mientras tanto, el E2 conserva su supuesto. Con los valores actuales, el beneficio de P1 sería menor que el estimado en el E2, pero el de P2 lo compensa con holgura.
