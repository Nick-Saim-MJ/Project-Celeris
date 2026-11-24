# Anexo B. Rúbrica de CE0331 y dónde se evidencia

| # | Criterio (peso) | Dónde está la evidencia |
| --- | --- | --- |
| 1 | Contexto y alcance (8 %) | Secciones 1 a 3: criterio de reparto campus/nube (D-25), caché fuera de AWS (D-19), límites y exclusiones justificadas |
| 2 | Arquitectura on-premise (22 %) | Sección 5 y Figuras 5.1 y 5.2: rack de 12U, 4 NIC, vSwitch0 con teaming, vSwitch1, port groups con su VLAN y 11 VM con vCPU, RAM y disco |
| 3 | Arquitectura AWS (22 %) | Sección 6 y Figura 6.1: región, VPC 10.30.0.0/16, subredes, rutas, IGW, VGW, endpoint de S3, EC2, SG, NACL, NAT temporal, IAM y costo |
| 4 | Integración híbrida (10 %) | Sección 7 y Figura 7.1 (FIG-5.4 de CE0311, sin cambios): mismas redes anunciadas y mismos extremos |
| 5 | Dimensionamiento (12 %) | Sección 9: núcleos, RAM y disco frente al host, EC2-GW frente a su carga, con holgura y fórmulas visibles en la matriz XLSX |
| 6 | Matriz de componentes (10 %) | Sección 8 y `Matriz_Componentes_DC_v{{dato:version}}.xlsx`: {{dato:n_elementos}} elementos, 100 % de lo dibujado, con criticidad y función |
| 7 | Disponibilidad y continuidad (8 %) | Sección 10: RTO y RPO de {{dato:n_servicios}} servicios, redundancia, respaldo 3-2-1-1-0 y punto único de falla |
| 8 | Calidad documental y sustentación (8 %) | Control de versiones y huella de la fuente; tablas generadas desde el YAML; CI registrados; cada cifra tiene su cálculo en la matriz |
