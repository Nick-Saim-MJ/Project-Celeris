## Anexo C. Diagramas complementarios

Los siguientes diagramas complementan la Sección 4. Representan el nodo en su estado de implementación actual («R1»)
y el detalle de las clases de diseño, que los diagramas por caso de uso de la sección 4.1.1 emplean de forma
parcial. Fueron sometidos al mismo validador que los demás: todo equipo, flujo, requisito, decisión, caso de uso y
pantalla que mencionan existe en el inventario del proyecto o en el presente informe.

{{figura:DS-03|Clases de diseño de la consola, todas «R2». Cada servicio corresponde a un componente de la vista C3 (DS-22). `AdminService` agrupa las acciones permitidas únicamente desde el campus (REQ-F-37).}}

{{figura:DS-02|Clases del nodo. Las marcadas «R1» ya están implementadas en el código; los puertos «R2» (agente de configuración y precarga) se construirán en S2.}}

{{figura:DS-04|Comportamiento del código actual, con sus métodos reales. Dos estaciones solicitan el mismo archivo: la primera lo descarga y la segunda espera y recibe la copia. Ambas reciben la cabecera `Cache-Status` (RFC 9211, REQ-NF-11) y el hash se verifica antes de servir el contenido (REQ-F-06).}}

{{figura:DS-05|Proceso de decisión de descifrado en el nodo: se evalúa primero la red de origen (la red Wi-Fi de estudiantes nunca se descifra), a continuación la lista «nunca» y, finalmente, si la fuente está aprobada y el nombre del sitio (SNI) coincide.}}

{{figura:DS-06|Revalidación: el origen responde 304 («sin cambios») y el nodo entrega el archivo desde su copia, sin descargarlo nuevamente (`Cache-Status: celeris; hit; fwd=stale; fwd-status=304`).}}

{{figura:DS-09|Estados de una entrada de caché según su tratamiento en el código actual. No existe un campo «estado»: los estados se deducen de los datos de la entrada. Si el hash no coincide, la entrada pasa a «Corrupta» y la siguiente petición provoca una nueva descarga (REQ-NF-04).}}

{{figura:DS-19|Un cambio de laboratorio firmado llega a los nodos por F10 en ≤ 60 s (REQ-NF-16) y los indicadores retornan a la consola cada 30 s.}}

{{figura:DS-13|Componentes del nodo, con el archivo de código que implementa cada uno y el módulo al que se trasladará cuando se reorganice el código.}}
