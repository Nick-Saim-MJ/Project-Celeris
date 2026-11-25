## Anexo C. Diagramas complementarios

Estos diagramas completan la Sección 4. Muestran el nodo tal como está programado hoy («R1») y el detalle de las
clases de diseño, que los diagramas por caso de uso de la sección 4.1.1 usan por partes. Pasaron por el mismo
validador que los demás: todo equipo, flujo, requisito, decisión, caso de uso y pantalla que nombran existe en el
inventario del proyecto o en este informe.

{{figura:DS-03|Clases de diseño de la consola, todas «R2». Cada servicio corresponde a un componente de la vista C3 (DS-22). `AdminService` reúne las acciones que solo se permiten desde el campus (REQ-F-37).}}

{{figura:DS-02|Clases del nodo. Las marcadas «R1» ya existen en el código; los puertos «R2» (agente de configuración, precarga) se construyen en S2.}}

{{figura:DS-04|El código actual, con sus métodos reales. Dos PCs piden el mismo archivo: la primera lo descarga y la segunda espera y recibe la copia. Ambas ven la cabecera `Cache-Status` (RFC 9211, REQ-NF-11) y el hash se verifica antes de servir (REQ-F-06).}}

{{figura:DS-05|Cómo decide el nodo si descifra: primero mira la red de origen (el Wi-Fi de estudiantes nunca se descifra), luego la lista «nunca», y por último si la fuente está aprobada y el nombre del sitio (SNI) coincide.}}

{{figura:DS-06|Revalidación: el origen responde 304 («no cambió») y el nodo entrega el archivo desde su copia, sin volver a descargarlo (`Cache-Status: celeris; hit; fwd=stale; fwd-status=304`).}}

{{figura:DS-09|Los estados de una entrada de caché tal como los maneja el código actual. No hay un campo «estado»: se deducen de los datos de la entrada. Si el hash no coincide, la entrada pasa a «Corrupta» y la próxima petición vuelve a descargar (REQ-NF-04).}}

{{figura:DS-19|Un cambio de laboratorio firmado llega a los nodos por F10 en ≤ 60 s (REQ-NF-16) y los indicadores vuelven a la consola cada 30 s.}}

{{figura:DS-13|Componentes del nodo, con el archivo de código que implementa cada uno y el módulo al que pasará cuando se reorganice el código.}}
