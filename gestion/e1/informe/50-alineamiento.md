# 1.5 Alineamiento estratégico

El alineamiento estratégico (evidencia CE0112) demuestra que cada elemento de la propuesta de TI responde a un objetivo institucional por medio de una brecha y de un problema cuantificados en este informe. Se presenta en dos formas complementarias: una matriz de lectura por filas y una vista ArchiMate que representa la misma cadena como modelo de arquitectura.

La {{ref:t-alineamiento}} relaciona cada objetivo estratégico con la capacidad que exige, la brecha que actualmente la impide, el componente de Celeris que la cierra, el indicador que la mide y el objetivo del proyecto correspondiente. La última columna vincula cada fila con la matriz de correlación entre áreas del Marco común (00 M7), en la que se registran los requisitos de CE02, los flujos de CE03 y las pruebas asociadas.

{{tabla:t-alineamiento}}

Ningún componente figura en la matriz sin una brecha que lo justifique, y ninguna brecha queda sin un componente que la atienda. Los elementos que no cumplían esta condición, como la réplica en AWS o la caché intermedia en la nube, fueron retirados de la arquitectura precisamente por carecer de una fila en esta matriz (00 M3.2).

La {{ref:fig-motivacion}} presenta la vista de motivación en ArchiMate 3.2, elaborada con Archi. Se lee de izquierda a derecha: drivers, evaluaciones, objetivos institucionales, resultados del proyecto, requisitos de CE02 y componentes de CE03.

{{figura:fig-motivacion}}

La vista demuestra que la cadena se cierra sin discontinuidades: cada driver conduce a un objetivo mediante una evaluación verificable, cada resultado OB-x contribuye a un objetivo institucional y cada requisito tiene un componente que lo implementa. El nodo de caché y la consola concentran la mayoría de las relaciones y constituyen, por ello, los componentes críticos del alineamiento.
