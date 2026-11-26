# 3.6 Gestión Ágil

La consola del encargado es el componente con mayor incertidumbre de requisitos: el SRS la especifica, pero solo el uso con encargados reales confirmará qué valor entrega cada función. Por ello, su construcción en S2 se gestiona con Scrumban: sprints de una semana que fijan un compromiso y una revisión con el docente, como en Scrum [2], y un tablero con límites de trabajo en curso que hace visible el flujo, como en Kanban [3]. Las fechas de los sprints no son independientes del plan predictivo: los seis sprints ocupan exactamente las actividades 5.4.1–5.4.3 de la ruta crítica.

## 3.6.1 Product backlog

Las épicas del backlog corresponden a paquetes de la EDT (5.4 para la consola y 5.1 para las mejoras del nodo) y cada historia de usuario sigue el formato «Como…, quiero…, para…» [9], con los requisitos REQ-F y los casos de uso del SRS de CE02. La prioridad combina dos criterios. MoSCoW toma la prioridad del requisito principal en el SRS (M → Must, S → Should), de modo que el backlog no puede contradecir la especificación. WSJF ordena dentro de cada categoría: el costo de la demora (valor para el usuario, criticidad temporal y reducción de riesgo) dividido entre el tamaño en puntos de historia [4]. La {{ref:t-backlog}} presenta el backlog priorizado.

{{tabla:t-backlog}}

El backlog reúne {{dato:e3_hu_total}} historias, con {{dato:e3_pts_alcance}} sin contar las excluidas, de los cuales {{dato:e3_pts_must}} corresponden a historias Must. La historia de mayor WSJF es {{dato:e3_hu_primera}}, pero el orden de los sprints respeta las dependencias: el inicio de sesión con segundo factor (HU-01) ocupa el primer sprint aunque su WSJF es menor, porque habilita todas las demás. HU-17, la vista de actividad por PC, se registra como Won't porque contradice el requisito de privacidad REQ-NF-07; dejarla en el backlog documenta la decisión y evita que se reabra sin análisis. Los criterios de aceptación en formato Gherkin de cada historia figuran en el anexo B.

## 3.6.2 Sprint planning

Cada sprint dura cinco días laborables y tiene un objetivo que el docente puede verificar en la revisión. La capacidad comprometida no supera {{dato:e3_capacidad}} por sprint; la velocidad planificada es de {{dato:e3_velocidad}}, que se recalibra con la velocidad real del primer sprint. La {{ref:t-sprints}} presenta la planificación de los {{dato:e3_n_sprints}} sprints, entre el {{dato:e3_sprint1_inicio}} y el {{dato:e3_sprint6_fin}}.

{{tabla:t-sprints}}

El modelo comprueba que ninguna historia quede en un sprint anterior a otra de la que depende, que ningún sprint supere la capacidad, que toda historia Must tenga sprint y que los sprints sumen exactamente la duración de las actividades del cronograma que los contienen. Las historias que no caben en S2 ({{dato:e3_hu_fuera}}) son Should o Won't y quedan para la versión siguiente.

La {{ref:fig-kanban}} presenta el tablero al iniciar el primer sprint, con las columnas, sus límites de trabajo en curso y las tarjetas ordenadas por WSJF.

{{figura:fig-kanban}}

El tablero evidencia la regla principal del flujo: solo una historia por integrante puede estar en curso y ninguna pasa a terminada sin la revisión del otro integrante. La columna Listo contiene únicamente historias que cumplen la definición de listo, de modo que una historia ambigua no consume capacidad del sprint. La {{ref:t-dor-dod}} establece ambas definiciones y la {{ref:t-ceremonias}}, los eventos del marco.

{{tabla:t-dor-dod}}

{{tabla:t-ceremonias}}

## 3.6.3 Incrementos

Cada sprint entrega un incremento utilizable: al cierre del primero, el encargado inicia sesión con segundo factor; al del tercero, un cambio de la consola llega firmado al nodo; al del sexto, el estudiante consulta el portal de transparencia y el docente registra sus solicitudes. La {{ref:fig-burnup}} presenta el avance planificado en puntos acumulados frente al alcance.

{{figura:fig-burnup}}

El burn-up muestra que el alcance Must se completa al cierre del quinto sprint y que el sexto se dedica a historias Should, lo que deja un margen para absorber una velocidad menor a la prevista sin comprometer el piloto. Si la velocidad real del primer sprint resultara inferior, el pronóstico desplazaría historias Should, nunca Must, y el cambio se registraría en el backlog.

La {{ref:t-metricas}} define las métricas de seguimiento. El libro `Backlog_E3.xlsx` reproduce el backlog con el cálculo del WSJF, la capacidad de cada sprint y el burn-up, con una columna para registrar los puntos reales.

{{tabla:t-metricas}}
