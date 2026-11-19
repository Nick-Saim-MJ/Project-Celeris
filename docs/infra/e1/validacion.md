# Validación de la fuente única — CE0311 (Entregable 1)

> Generado por `infra/validate.py` (`make validate`). No editar a mano.

- Inventario: versión 1.0 · fecha 2026-11-18
- Contenido cargado: **14 zonas**, **37 componentes**, **26 flujos** (F1–F26, F4 reservado), **49 pruebas** (T01–T28 de D1.16 y 21 ampliaciones), 10 objetivos OD, 13 amenazas AM, 9 detecciones DET, 7 figuras, 8 criterios de rúbrica.
- Resultado: **0 FALLA**, 4 con advertencias, 40 PASA, 3 pendientes de P2–P5.

## Chequeos

| ID | Chequeo | Resultado | Hallazgos |
| --- | --- | --- | --- |
| V-01 | Esquema JSON válido en los tres YAML | PASA | — |
| V-02 | IDs únicos | PASA | — |
| V-03 | Referencias existentes entre los tres archivos | PASA | — |
| V-04 | Cada IP dentro del CIDR de su zona (y de su subred AWS) | PASA | — |
| V-05 | Sin IP duplicadas | PASA | — |
| V-06 | Gateways .1 (salvo VLAN 70, sin gateway) y coherentes con FW01 | PASA | — |
| V-07 | Sin solapamientos entre 10.20.0.0/16, 10.30.0.0/16, zonas, subredes y reservas | PASA | — |
| V-08 | Convención VLAN = tercer octeto (excepción documentada: VLAN 30 → 10.20.32.0/22) | PASA | — |
| V-09 | IP públicas solo de documentación (RFC 5737) | PASA | — |
| V-10 | Hosts útiles coinciden con el CIDR | PASA | — |
| V-11 | La matriz zona × zona derivada de los flujos coincide con D1.8 | PASA con advertencias | 0 errores, 5 advertencias |
| V-12 | Matriz esperada completa (celda por celda) y coherente con las acciones de los flujos | PASA | — |
| V-13 | Todo flujo permitido tiene protección en tránsito y riesgo residual | PASA | — |
| V-14 | F1–F26 completos, F4 reservado y regla de firewall con el ID del flujo | PASA | — |
| V-15 | Todo flujo bloqueado tiene una prueba | PASA | — |
| V-16 | Todo flujo tiene ≥ 1 prueba o una justificación | PASA | — |
| V-17 | Componentes: por_que (1–3 frases), aporta_corto (≤ 12 palabras), aporta, si_falla, criticidad | PASA | — |
| V-18 | Componentes: ≥ 1 figura, FIG-5.1 y las figuras de sus flujos | PASA | — |
| V-19 | Componentes: ≥ 1 flujo o justificación de por qué no tienen | PASA | — |
| V-20 | Pruebas T01–T28 de D1.16 completas, ampliaciones T29+ registradas, con criterio verificable y modos válidos | PASA | — |
| V-21 | Coherencia bidireccional: pruebas ↔ amenazas, detecciones y rúbrica | PASA | — |
| V-22 | Todo objetivo OD tiene ≥ 1 prueba o indicador | PASA | — |
| V-23 | Toda amenaza AM tiene control y prueba | PASA | — |
| V-24 | Rúbrica R1–R8: pesos suman 100 y cada criterio tiene ≥ 1 evidencia | PASA | — |
| V-25 | Detecciones: ubicación existente y validación | PASA | — |
| V-26 | Correspondencia contenidos mínimos (1–15) → secciones del DOCX cubre las 11 secciones | PASA con advertencias | 0 errores, 1 advertencias |
| V-27 | Cobertura de las denegaciones de la matriz por pruebas (informativo) | PASA | 0 errores, 0 advertencias |
| V-28 | Inventario completo: D1.12, VPC/subredes D2.5, F1–F26, T01–T28, 10 VLAN | PASA | — |
| V-29 | Pendientes (`pendiente: true`) registrados en CAMBIOS-INVENTARIO.md | PASA | 0 errores, 0 advertencias |
| V-30 | Sin secretos, llaves ni credenciales en infra/, docs/infra/, Makefile y CI | PASA | — |
| V-31 | VPN (D1.10): ASN, /30 de túnel, MTU/MSS, temporizadores y flujos sobre la VPN | PASA | — |
| V-32 | Servicios base (DHCP, DNS, PAC, NTP, IPv6, DNS cifrado) consistentes con el inventario | PASA | — |
| V-33 | Lo emulado se rotula como emulado: pruebas en Modo L solo con componentes emulados (F4.2) | PASA con advertencias | 0 errores, 3 advertencias |
| V-34 | La rúbrica coincide con el XLSX oficial (nombre, peso y descriptor de nivel 4) | PASA | — |
| V-40 | El ruleset generado de fw01-sim contiene exactamente los flujos permitidos (y los bloqueos) del inventario | PASA | — |
| V-41 | swanctl, FRR y VTI generados coinciden con la sección vpn del inventario (cifrado, DPD, vidas, ASN, BGP, MTU, MSS) | PASA | — |
| V-42 | Los últimos resultados de make test-lab no tienen FALLA en pruebas críticas | PASA con advertencias | 0 errores, 7 advertencias |
| V-43 | Los artefactos generados versionados (tfvars de OpenTofu, topología de containerlab) están al día con el inventario | PASA | — |
| V-50 | Diagramas draw.io: componentes, IP, zonas, colores (Okabe-Ito), flujos F-nn y criticidad contra el inventario | PENDIENTE | pendiente de P2 |
| V-60 | XLSX de componentes: 100 % del inventario, IP, zona, criticidad, por qué, aporta y si falla | PENDIENTE | pendiente de P3 |
| V-70 | XLSX de pruebas: hojas y una fila por prueba del YAML, con sus datos | PASA | — |
| V-71 | XLSX de pruebas: cada prueba cita flujos, componentes, OD, AM, DET y criterios de rúbrica existentes | PASA | — |
| V-72 | Cobertura: 100 % de flujos permitidos con prueba positiva, de bloqueos y celdas críticas con prueba negativa; OD, AM, DET y R3/R4 con ≥ 1 prueba | PASA | 0 errores, 0 advertencias |
| V-73 | Ensayo L: ninguna FALLA sin causa y acción; NO_APLICA, PARCIAL y sin ensayo nunca como PASA | PASA | — |
| V-74 | XLSX de pruebas: fórmulas sin errores tras recalcular con LibreOffice y coherentes con la biblioteca | PASA | 0 errores, 0 advertencias |
| V-75 | XLSX de pruebas: el archivo versionado está al día con pruebas.yaml, el inventario y el último ensayo | PASA | — |
| V-80 | Informe DOCX: 11 secciones, tablas generadas del inventario, figuras y leyendas | PENDIENTE | pendiente de P5 |

## Errores

Ninguno.


## Advertencias (contradicciones y vacíos registrados)

- **V-11** — EDGE→EDGE: la matriz indica «permitido» sin flujos y los flujos derivan «no_aplica» — contradicción registrada (CI-06)
- **V-11** — LAB→EDGE: los flujos ['F3'] permiten LAB→EDGE pero la matriz no los lista — contradicción registrada (CI-03)
- **V-11** — LAB-TEST→EDGE: los flujos ['F3'] permiten LAB-TEST→EDGE pero la matriz no los lista — contradicción registrada (CI-03)
- **V-11** — LAB-TEST→SERVERS: la matriz lista ['F2'] pero ningún flujo los deriva — contradicción registrada (CI-04)
- **V-11** — MGMT→INTERNET: la matriz indica «permitido» sin flujos y los flujos derivan «denegado» — contradicción registrada (CI-05)
- **V-26** — La correspondencia 1–15 → DOCX es una propuesta: el documento maestro no incluye la tabla (CI-02)
- **V-33** — T12 (Modo L): destino NAS01 no se emula en el laboratorio (F4.1/F4.2) — registrado (CI-16)
- **V-33** — T25 (Modo L): origen BRK01 no se emula en el laboratorio (F4.1/F4.2) — registrado (CI-16)
- **V-33** — T25 (Modo L): destino ESX01 no se emula en el laboratorio (F4.1/F4.2) — registrado (CI-16)
- **V-42** — 2026-11-19-L: la prueba crítica T08 (LAB → UDP 443) está en PARCIAL, no en PASA
- **V-42** — 2026-11-19-L: la prueba crítica T12 (STORAGE no enrutada) está en NO_APLICA, no en PASA
- **V-42** — 2026-11-19-L: la prueba crítica T23 (Fuga IPv6) está en NO_APLICA, no en PASA
- **V-42** — 2026-11-19-L: la prueba crítica T28 (Syslog cifrado) está en NO_APLICA, no en PASA
- **V-42** — 2026-11-19-L: la prueba crítica T45 (Internet → zonas internas) está en PARCIAL, no en PASA
- **V-42** — 2026-11-19-L: la prueba crítica T46 (DMZ-SVC → zonas internas) está en PARCIAL, no en PASA
- **V-42** — 2026-11-19-L: la prueba crítica T47 (DMZ-HONEY → cualquier zona) está en PARCIAL, no en PASA

## Información

- **V-27** — 36 de 92 celdas denegadas tienen una prueba dedicada; el resto se cubre por la política deny-all (OD-06) y las reglas de denegación con registro
- **V-29** — 34 elementos pendientes en los YAML; 27 entradas CI en CAMBIOS-INVENTARIO.md; sin referencia desde los YAML: ['CI-02', 'CI-17', 'CI-18', 'CI-22', 'CI-23', 'CI-24', 'CI-25', 'CI-26']
- **V-42** — Resultados de 2026-11-19-L (commit f68cb80): {'PASA': 13, 'FALLA': 0, 'PARCIAL': 12, 'NO_APLICA': 24}
- **V-72** — Celdas denegadas no críticas sin prueba dedicada: 56 de 92 (las cubre la política deny-all; ver hoja «Cobertura»)
- **V-74** — 765 fórmulas recalculadas con LibreOffice sin errores

## Cobertura

| Relación | Cubiertos | Total |
| --- | ---: | ---: |
| flujos con prueba | 25 | 25 |
| flujos con prueba o justificación | 25 | 25 |
| componentes con ≥ 1 flujo | 25 | 37 |
| objetivos con ≥ 1 prueba | 10 | 10 |
| amenazas con ≥ 1 prueba | 13 | 13 |
| detecciones con ≥ 1 prueba | 9 | 9 |
| celdas denegadas con ≥ 1 prueba | 36 | 92 |
| criterios de rúbrica con evidencia | 8 | 8 |

## Pendientes de P2–P5 (ganchos)

| Gancho | Qué validará | Estado |
| --- | --- | --- |
| V-50+ | Diagramas draw.io: componentes, IP, zonas, colores (Okabe-Ito), flujos F-nn y criticidad contra el inventario | pendiente de P2 |
| V-60+ | XLSX de componentes: 100 % del inventario, IP, zona, criticidad, por qué, aporta y si falla | pendiente de P3 |
| V-80+ | Informe DOCX: 11 secciones, tablas generadas del inventario, figuras y leyendas | pendiente de P5 |
