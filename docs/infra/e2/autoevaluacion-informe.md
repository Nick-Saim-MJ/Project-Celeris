# Autoevaluación del informe de CE0331 contra la rúbrica oficial (v1.1)

Rúbrica: `docs/fuentes/CE03/Rubrica_S1_E2_Diseno_Centro_de_Datos.xlsx` (8 criterios, puntaje = peso × nivel ÷ 4). Es una estimación del equipo, no la nota del docente. Cada afirmación remite a una sección, una figura o un chequeo de `make validate`.

Producto revisado: `Informe_Centro_Datos_v1.1.docx` y `.pdf` (31 páginas), cuatro diagramas propios (DC-0…DC-3) más FIG-5.4 de CE0311, y `Matriz_Componentes_DC_v1.1.xlsx` (56 elementos). La v1.0 está en `entregables/CE0331/historial/`. Cambios de la v1.1: SIEM01 a 12 GB (CI-78), S-33 y S-34, ESX01 en U6–U7, trunk de 1 GbE a SW-ACC, escenario «cae ESX01» (CT-09) y S-08 corregido (CI-84, CE0311 v1.2).

| # | Criterio (peso) | Nivel estimado | Evidencia | Qué falta para el nivel 4 |
| ---: | --- | :-: | --- | --- |
| 1 | Contexto y alcance (8 %) | **4** | Secciones 1–3: necesidades por servicio, criterio de reparto campus/nube (D-25), caché fuera de AWS (D-19), límites con responsable de cada componente y exclusiones justificadas | Nada pendiente |
| 2 | On-premise ESXi (22 %) | **4** | Sección 5 y Figuras 5.1 y 5.2: rack de 12U con ESX01 en U6–U7 (CI-79), 4 NIC, 3 datastores, vSwitch0 con teaming, vSwitch1, 9 port groups con VLAN, 11 VM con vCPU, RAM y disco; enlace de 1 GbE a SW-ACC (CI-80); V-91 y V-93 | Nada pendiente en el diseño |
| 3 | AWS (22 %) | **4** (riesgo de 3) | Sección 6 y Figura 6.1: región con alternativa, VPC y CIDR, subredes, rutas, IGW01, VGW, endpoint de S3, EC2 con tipo justificado frente a S-33, SG, NACL, NAT temporal justificado con costo, IAM y costo mensual con precios fechados [S-12]; V-94 | Medir la latencia a us-east-1 y sa-east-1 [S-11]: hoy la región se justifica por precio, servicios y cumplimiento, no por medición |
| 4 | Integración híbrida (10 %) | **4** | Sección 7 y Figura 7.1 = FIG-5.4 de CE0311 sin cambios (V-98); mismas redes anunciadas y mismos extremos, comprobadas en V-94 | Nada pendiente |
| 5 | Dimensionamiento (12 %) | **4** (riesgo de 3) | Sección 9 y hoja «Dimensionamiento» (fórmulas visibles, recalculadas en LibreOffice): núcleos 9,75 de 12 (holgura 18,8 %), RAM 79,2 de 96 GB (holgura 31,3 % tras ESXi y 17,5 % tras reservar el 20 % de crecimiento), disco 1 206 de 1 920 GB (holgura 37,2 %); EC2-GW con margen de 50 % frente a S-33 | **CI-87:** el trunk de 1 GbE hacia SW-ACC no deja holgura frente a ≈ 1 Gbps por laboratorio; el informe lo declara como cuello de botella. Se mide con iperf3 en S2 y se pide a la DTI un enlace de 10 GbE |
| 6 | Matriz de componentes (10 %) | **4** | Sección 8 y XLSX: 56 elementos = 100 % de lo dibujado en DC-0…DC-3 y viceversa (V-105), con entorno, tipo, función, criticidad y recursos | Nada pendiente |
| 7 | Disponibilidad y continuidad (8 %) | **4** (riesgo de 3) | Sección 10 y hoja «Continuidad»: RTO y RPO de 9 servicios, redundancia, respaldo, 3-2-1-1-0 y el escenario «cae ESX01» (CT-09) | **S-34:** el plazo de reposición del servidor espera valor de la DTI, así que CT-09 no tiene RTO numérico. **CI-88:** `DIRECT` con ESX01 caído depende de FW01, que corre en ESX01; falta que la DTI confirme una salida alternativa para los laboratorios |
| 8 | Calidad documental y sustentación (8 %) | **3** | Control de versiones con huella, tablas generadas desde el YAML, 12 CI registrados (10 resueltos), anexos de supuestos, rúbrica y validación emulada; figuras exportadas con draw.io Desktop | Las figuras son densas: en la página impresa el texto de las cajas es pequeño y depende del zoom del PDF o del PNG. Para el nivel 4: una figura por zona o menos texto por caja. En la sustentación, cada integrante debe defender cada cifra y el porqué de D-19, D-24 y D-25 |

**Puntaje estimado:** 8 + 22 + 22 + 10 + 12 + 10 + 8 + 6 = **98 / 100 → 19,6 sobre 20.** Si los riesgos de los criterios 3, 5 y 7 se leen como nivel 3, baja a unos 87,5 → 17,5.

## Qué queda abierto

- **CI-87** (trunk de 1 GbE hacia SW-ACC sin holgura) y **CI-88** (`DIRECT` con ESX01 caído depende de FW01): decide el equipo con la DTI.
- **S-34** (plazo de reposición del servidor) sin valor, por confirmar con la DTI; **S-11** (latencia a AWS) y **S-33** (carga de EC2-GW) se miden en S2.

## Qué no está verificado

- Lo emulado (AWS Emulator y Modo L) está rotulado como emulado; no se presenta como implementado.
- La autonomía de la UPS (15–20 min) y los precios de lista se confirman con el fabricante y en AWS Pricing Calculator.
- El PDF y el DOCX los genera Microsoft Word (COM; actualiza la tabla de contenidos); la matriz se recalcula con LibreOffice (en WSL); los diagramas se exportan con draw.io Desktop.
