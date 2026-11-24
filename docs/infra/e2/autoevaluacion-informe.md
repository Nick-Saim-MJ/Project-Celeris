# Autoevaluación del informe de CE0331 contra la rúbrica oficial

Rúbrica: `docs/fuentes/CE03/Rubrica_S1_E2_Diseno_Centro_de_Datos.xlsx` (8 criterios, puntaje = peso × nivel ÷ 4). Es una estimación del equipo, no la nota del docente. Cada afirmación remite a una sección, una figura o un chequeo de `make validate`.

Producto revisado: `Informe_Centro_Datos_v1.0.docx` y `.pdf` (29 páginas), cuatro diagramas propios (DC-0…DC-3) más FIG-5.4 de CE0311, y `Matriz_Componentes_DC_v1.0.xlsx` (56 elementos).

| # | Criterio (peso) | Nivel estimado | Evidencia | Qué falta para el nivel 4 |
| ---: | --- | :-: | --- | --- |
| 1 | Contexto y alcance (8 %) | **4** | Secciones 1–3: necesidades por servicio, criterio de reparto campus/nube (D-25), caché fuera de AWS (D-19), límites con responsable de cada componente y exclusiones justificadas | Nada pendiente |
| 2 | On-premise ESXi (22 %) | **4** (riesgo de 3) | Sección 5 y Figuras 5.1 y 5.2: rack de 12U, ESX01 con 4 NIC y 3 datastores, vSwitch0 con teaming, vSwitch1, 9 port groups con VLAN, 11 VM con vCPU, RAM y disco; V-91 y V-93 | Cerrar CI-79 (qué dos U ocupa ESX01) y CI-80 (puerto y velocidad del enlace SW-CORE01 ↔ SW-ACC y de vmnic3): un evaluador puede leerlos como detalles menores faltantes |
| 3 | AWS (22 %) | **4** (riesgo de 3) | Sección 6 y Figura 6.1: región con alternativa, VPC y CIDR, subredes, rutas, IGW01, VGW, endpoint de S3, EC2 con tipo justificado, SG, NACL, NAT temporal justificado con costo, IAM y costo mensual; V-94 | Medir la latencia a us-east-1 y sa-east-1 [S-11] (hoy la región se justifica por precio, servicios y cumplimiento, no por medición) y cerrar CI-81 con el equipo |
| 4 | Integración híbrida (10 %) | **4** | Sección 7 y Figura 7.1 = FIG-5.4 de CE0311 sin cambios (huella comprobada por V-98); mismas redes anunciadas y mismos extremos, comprobadas en V-94 | Nada pendiente |
| 5 | Dimensionamiento (12 %) | **3** | Sección 9 y hoja «Dimensionamiento» (fórmulas visibles): núcleos 9,75 de 12 (holgura 18,8 %), RAM 84,5 de 96 GB, disco 1 206 de 1 920 GB (holgura 37,2 %); EC2-GW frente a su carga | **CI-78:** el margen de RAM tras reservar el 20 % de crecimiento es 12,0 %, por debajo del 15 % de D2.3: decidir 128 GB, reducir SIEM01 o aceptarlo. **CI-82:** la carga de EC2-GW es una propuesta sin medir: medirla con el piloto |
| 6 | Matriz de componentes (10 %) | **4** | Sección 8 y XLSX: 56 elementos = 100 % de lo dibujado en DC-0…DC-3 y viceversa (V-105), con entorno, tipo, función, criticidad y recursos; criticidad heredada sin inventar niveles | Nada pendiente |
| 7 | Disponibilidad y continuidad (8 %) | **4** (riesgo de 3) | Sección 10 y hoja «Continuidad»: RTO y RPO de 8 servicios coherentes con su criticidad (V-94), redundancia, respaldo, 3-2-1-1-0 y punto único de falla del host con mitigaciones | CI-86: no hay RTO del host (plazo de reposición del servidor). Se declara, no se inventa |
| 8 | Calidad documental y sustentación (8 %) | **3** | Control de versiones con huella de la fuente, tablas generadas desde el YAML, 10 CI registrados, anexos de supuestos, rúbrica y validación emulada | Las figuras son densas: en la página impresa el texto de las cajas es pequeño y depende del zoom del PDF o del PNG (escala 3). Para el nivel 4: simplificar DC-1 y DC-2 o una figura por zona. Y la sustentación: cada integrante debe poder defender cada cifra y el porqué de cada decisión (D-19, D-24, D-25) |

**Puntaje estimado:** 8 + 22 + 22 + 10 + 9 + 10 + 8 + 6 = **95 / 100 → 19,0 sobre 20.** Con los riesgos de los criterios 2, 3 y 7 (cada uno a nivel 3) bajaría a unos 16,4.

## Qué no está verificado

- El PDF y el DOCX se generaron con Microsoft Word (COM); la tabla de contenidos se actualizó. No hay LibreOffice en esta máquina; la matriz XLSX se recalculó con Excel (COM) y sus valores coinciden con el cálculo en Python (V-107).
- No hay draw.io Desktop instalado: los PNG y PDF de DC-0…DC-3 los exportó el respaldo de `infra/gen/exportar_dc.py` (Edge sin interfaz, con el XML de draw.io embebido). Los `.drawio` conservan los íconos de draw.io; al abrirlos se ve lo mismo que en el PNG, con íconos en lugar de glifos. Para exportar con draw.io: `python infra/gen/exportar_dc.py`.
- Los precios de t3.small y NAT Gateway (CI-83), la carga de EC2-GW (CI-82) y la autonomía de la UPS son referencias a confirmar. La latencia a AWS no se midió.
- Lo emulado (AWS Emulator y Modo L) está rotulado como emulado; no se presenta como implementado.
