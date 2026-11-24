# 8. Matriz de componentes del centro de datos

La matriz consolida los {{dato:n_elementos}} elementos dibujados en las figuras 1.1, 5.1, 5.2 y 6.1, de modo que el diseño es auditable: cada caja de un diagrama tiene su fila y cada fila tiene su caja. V-105 comprueba ambos sentidos. La integración híbrida (Figura 7.1) es la de CE0311 y sus componentes están en la matriz de ese entregable. La versión completa, con «por qué existe» y «si falla» de cada fila, es el archivo `Matriz_Componentes_DC_v{{dato:version}}.xlsx`; la hoja «Componentes» reproduce esta tabla.

La criticidad de los componentes sale del inventario. La de los elementos propios del centro de datos (port groups, NIC, datastores, rack, tablas de rutas, Security Groups) es la del componente más crítico al que sirven, para no inventar un nivel: por ejemplo, PG-FW-TRUNK es Alta porque conecta a FW01, y vmnic3 es Baja porque no sirve a nadie.

{{tabla:matriz}}
