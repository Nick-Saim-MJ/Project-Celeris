# Autoevaluación del informe de CE0331 contra la rúbrica oficial (v1.2)

Rúbrica: `docs/fuentes/CE03/Rubrica_S1_E2_Diseno_Centro_de_Datos.xlsx` (8 criterios, puntaje = peso × nivel ÷ 4). Es una estimación del equipo, no la nota del docente. Cada afirmación remite a una sección, una figura o un chequeo de `make validate`.

Producto revisado: `Informe_Centro_Datos_v1.2.docx` y `.pdf` (31 páginas), cuatro diagramas propios (DC-0…DC-3) más FIG-5.4 de CE0311, y `Matriz_Componentes_DC_v1.2.xlsx` (56 elementos). Las versiones anteriores están en `entregables/CE0331/historial/`. Cambios de la v1.2: CI-88 resuelto (el escenario «cae ESX01» pasa a contingencia manual con la DTI y RTO objetivo de 30 min [S-35]), DC-2.png re-exportado completo (CI-89: la v1.1 lo llevaba recortado al 51 % superior) y todas las figuras en páginas horizontales al ancho útil (CI-90).

| # | Criterio (peso) | Nivel estimado | Evidencia | Qué falta para el nivel 4 |
| ---: | --- | :-: | --- | --- |
| 1 | Contexto y alcance (8 %) | **4** | Secciones 1–3: necesidades por servicio, criterio de reparto campus/nube (D-25), caché fuera de AWS (D-19), límites con responsable de cada componente y exclusiones justificadas | Nada pendiente |
| 2 | On-premise ESXi (22 %) | **4** | Sección 5 y Figuras 5.1 y 5.2: rack de 12U con ESX01 en U6–U7 (CI-79), 4 NIC, 3 datastores, vSwitch0 con teaming, vSwitch1, 9 port groups con VLAN, 11 VM con vCPU, RAM y disco; enlace de 1 GbE a SW-ACC (CI-80); V-91 y V-93. La Figura 5.2 ya se ve completa en el PDF (página 13) y en el PNG (V-108) | Nada pendiente en el diseño |
| 3 | AWS (22 %) | **4** (riesgo de 3) | Sección 6 y Figura 6.1: región con alternativa, VPC y CIDR, subredes, rutas, IGW01, VGW, endpoint de S3, EC2 con tipo justificado frente a S-33, SG, NACL, NAT temporal justificado con costo, IAM y costo mensual con precios fechados [S-12]; V-94 | Medir la latencia a us-east-1 y sa-east-1 [S-11]: hoy la región se justifica por precio, servicios y cumplimiento, no por medición |
| 4 | Integración híbrida (10 %) | **4** | Sección 7 y Figura 7.1 = FIG-5.4 de CE0311 sin cambios (V-98); mismas redes anunciadas y mismos extremos, comprobadas en V-94 | Nada pendiente |
| 5 | Dimensionamiento (12 %) | **4** (riesgo de 3) | Sección 9 y hoja «Dimensionamiento» (fórmulas visibles, recalculadas en LibreOffice): núcleos 9,75 de 12 (holgura 18,8 %), RAM 79,2 de 96 GB (holgura 31,3 % tras ESXi y 17,5 % tras reservar el 20 % de crecimiento), disco 1 206 de 1 920 GB (holgura 37,2 %); EC2-GW con margen de 50 % frente a S-33 | **CI-87:** el trunk de 1 GbE hacia SW-ACC no deja holgura frente a ≈ 1 Gbps por laboratorio; el informe lo declara como cuello de botella. Se mide con iperf3 en S2 y se pide a la DTI un enlace de 10 GbE |
| 6 | Matriz de componentes (10 %) | **4** | Sección 8 y XLSX: 56 elementos = 100 % de lo dibujado en DC-0…DC-3 y viceversa (V-105), con entorno, tipo, función, criticidad y recursos | Nada pendiente |
| 7 | Disponibilidad y continuidad (8 %) | **4** (riesgo de 3) | Sección 10 y hoja «Continuidad»: RTO y RPO de 9 servicios, redundancia, respaldo, 3-2-1-1-0 y el escenario «cae ESX01» (CT-09) con respuesta propia: como FW01 cae con el host, `DIRECT` no basta; la DTI devuelve la puerta de enlace de la VLAN 30 al FortiGate (estado previo al proyecto), los laboratorios navegan sin caché y el RTO objetivo es de 30 min (CI-88 resuelto); consola y caché se restauran desde S3 (T59). V-94 comprueba que S-34 y S-35 existen | **S-35:** los 30 min y el procedimiento los confirma la DTI, y no hay una prueba T-nn que los mida: se ensaya con la DTI en S2. **S-34:** el plazo de reposición del servidor sigue sin valor, así que consola y caché no tienen RTO total. Además, como FW01 es hoy el DNS de los laboratorios, la DTI debe entregar un resolvedor durante la contingencia |
| 8 | Calidad documental y sustentación (8 %) | **3** | Control de versiones con huella, tablas generadas desde el YAML, 14 CI registrados (13 resueltos), anexos de supuestos, rúbrica y validación emulada; las 5 figuras van en páginas horizontales al ancho útil y V-108 comprueba que ningún PNG sale recortado | Las figuras siguen siendo densas: en la página impresa el texto de las cajas es pequeño y depende del zoom del PDF o del PNG. Para el nivel 4: una figura por zona o menos texto por caja. En la sustentación, cada integrante debe defender cada cifra y el porqué de D-19, D-24 y D-25 |

**Puntaje estimado:** 8 + 22 + 22 + 10 + 12 + 10 + 8 + 6 = **98 / 100 → 19,6 sobre 20.** Si los riesgos de los criterios 3, 5 y 7 se leen como nivel 3, baja a unos 87,5 → 17,5. El cambio de la v1.2 no mueve el puntaje: CT-09 ahora tiene una respuesta y un RTO objetivo, pero ese RTO depende de un supuesto que la DTI aún no confirma.

## Qué queda abierto

- **CI-87** (trunk de 1 GbE hacia SW-ACC sin holgura): decide el equipo con la DTI. Es el único CI abierto; CI-88, CI-89 y CI-90 están resueltos.
- **S-35** (contingencia de los laboratorios si cae ESX01, con el DNS incluido) y **S-34** (plazo de reposición del servidor): sin confirmar por la DTI.
- **S-11** (latencia a AWS) y **S-33** (carga de EC2-GW): se miden en S2.

## Qué no está verificado

- Lo emulado (AWS Emulator y Modo L) está rotulado como emulado; no se presenta como implementado.
- La contingencia de CT-09 no se ha ensayado: el RTO de 30 min es un objetivo, no una medida.
- La autonomía de la UPS (15–20 min) y los precios de lista se confirman con el fabricante y en AWS Pricing Calculator.
- El PDF y el DOCX los genera Microsoft Word (COM; actualiza la tabla de contenidos); la matriz se recalcula con LibreOffice (en WSL); los diagramas se exportan con draw.io Desktop (DC-2 a escala 2,84 y el resto a 3, por el límite de ~8192 px de draw.io).
