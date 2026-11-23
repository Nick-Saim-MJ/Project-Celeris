# 4. Objetivos del diseño de red

Cada objetivo de diseño (OD-xx) tiene un indicador que se puede medir con una prueba de la matriz planeada y responde a uno o más objetivos del proyecto (OB-x). La columna «Pruebas» indica cómo se medirá en el Semestre 2; el anexo C completa la cadena hasta las decisiones, componentes y flujos.

{{tabla:objetivos}}

Tres metas merecen una aclaración. La meta de OD-05 (≤ 60 s) es un valor **medido**, no el temporizador de BGP: en el laboratorio emulado la conmutación tardó {{dato:t05}} (T05, anexo E). OD-10 se mide en el piloto porque depende de cuántas PCs usen el PAC; la meta aplica al modo gestionado, cuando F6 (`DIRECT`) se cierra. OD-12 se cumple por construcción: el FortiGate solo publica UDP 500/4500 y TCP 80/443 hacia FW01 [S-29], y ninguna regla de FW01 lleva tráfico de Internet a CTRL01; T15 lo verifica.
