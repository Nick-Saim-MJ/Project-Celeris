# 4. Objetivos del diseño de centro de datos

Los cinco objetivos son medibles y orientados a capacidad y disponibilidad. La última columna dice dónde se comprueba cada uno: `V-92` y `V-94` son chequeos automáticos de `make validate` sobre `infra/centro_datos.yaml`, y OpenTofu se ejecutará en S2.

{{tabla:objetivos}}

El objetivo DC-OBJ-1 se cumple en CPU, RAM y disco. La RAM queda con {{dato:h_ram}} de holgura después de la sobrecarga de ESXi y con {{dato:m_ram}} aun reservando por completo el 20 % de crecimiento: para lograrlo, SIEM01 se dimensionó en 12 GB (CI-78, sección 9).
