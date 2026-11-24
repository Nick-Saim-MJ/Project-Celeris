# 4. Objetivos del diseño de centro de datos

Los cinco objetivos son medibles y orientados a capacidad y disponibilidad. La última columna dice dónde se comprueba cada uno: `V-92` y `V-94` son chequeos automáticos de `make validate` sobre `infra/centro_datos.yaml`, y OpenTofu se ejecutará en S2.

{{tabla:objetivos}}

El objetivo DC-OBJ-1 se cumple con una salvedad que este informe declara: la holgura de RAM es {{dato:h_ram}} después de la sobrecarga de ESXi, pero queda en {{dato:m_ram}} si además se reserva por completo el 20 % de crecimiento. La diferencia se registra como CI-78 (sección 9) y la decide el equipo.
