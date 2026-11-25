# 1.5 Alineamiento estratégico

El alineamiento (evidencia CE0112) demuestra que cada pieza de la propuesta de TI responde a un objetivo de la universidad a través de una brecha y de un problema medidos en este informe. Se presenta de dos formas: una matriz que se lee fila por fila y una vista ArchiMate que muestra la misma cadena como un modelo.

La {{ref:t-alineamiento}} une cada objetivo estratégico con la capacidad que exige, la brecha que hoy la impide, el componente de Celeris que la cierra, el KPI que lo mide y el objetivo del proyecto. La última columna enlaza la fila con la matriz de correlación entre áreas del Marco común (00 M7), donde están los requisitos de CE02, los flujos de CE03 y las pruebas.

{{tabla:t-alineamiento}}

Ningún componente está en la matriz sin una brecha detrás, y ninguna brecha queda sin un componente. Lo que sobra en la arquitectura (por ejemplo, la réplica en AWS o el shield de caché en la nube) se retiró precisamente porque no tenía una fila aquí (00 M3.2).

La {{ref:fig-motivacion}} es la vista de motivación modelada en ArchiMate 3.2 con Archi. Va de izquierda a derecha: los drivers y su evaluación, los objetivos institucionales, los resultados del proyecto, los requisitos de CE02 que los realizan y los componentes de CE03 que realizan esos requisitos.

{{figura:fig-motivacion}}

La vista muestra que la cadena se cierra sin saltos: cada driver lleva a un objetivo por medio de una evaluación verificable, cada resultado OB-x realiza al menos un objetivo institucional, y cada requisito tiene un componente que lo realiza. El nodo de caché y la consola concentran la mayor parte de las relaciones, así que son los componentes críticos del alineamiento. El modelo se regenera desde el repositorio: si cambia un requisito o un objetivo, la vista cambia con él.
