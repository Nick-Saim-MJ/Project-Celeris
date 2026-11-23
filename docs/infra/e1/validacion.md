# Validación de la fuente única — CE0311 (Entregable 1)

> Generado por `infra/validate.py` (`make validate`). No editar a mano.

- Inventario: versión 1.1 · fecha 2026-11-22
- Contenido cargado (v0.4): **13 zonas vigentes** (3 retiradas), **31 componentes vigentes** (15 retirados; 2 temporales), **24 flujos vigentes** (23 activos, F4 reservado) y 9 retirados, **52 pruebas vigentes** y 8 retiradas, 12 objetivos OD, 18 amenazas AM, 11 detecciones DET, 7 figuras, 8 criterios de rúbrica.
- Resultado: **0 FALLA**, 2 con advertencias, 58 PASA, 1 pendientes de P2–P5.

## Chequeos

| ID | Chequeo | Resultado | Hallazgos |
| --- | --- | --- | --- |
| V-01 | Esquema JSON válido en los tres YAML | PASA | — |
| V-02 | IDs únicos | PASA | — |
| V-03 | Referencias existentes entre los tres archivos | PASA | — |
| V-04 | Cada IP dentro del CIDR de su zona (y de su subred AWS) | PASA | — |
| V-05 | Sin IP duplicadas | PASA | — |
| V-06 | Gateways .1 y coherentes con FW01; tránsito FW01 ↔ FortiGate (v0.4: 7 VLAN) | PASA | — |
| V-07 | Sin solapamientos entre 10.20.0.0/16, 10.30.0.0/16, zonas, subredes y reservas | PASA | — |
| V-08 | Convención VLAN = tercer octeto (excepción documentada: VLAN 30 → 10.20.32.0/22) | PASA | — |
| V-09 | IP públicas solo de documentación (RFC 5737) | PASA | — |
| V-10 | Hosts útiles coinciden con el CIDR | PASA | — |
| V-11 | La matriz zona × zona derivada de los flujos coincide con D1.8 | PASA | — |
| V-12 | Matriz esperada completa (celda por celda) y coherente con las acciones de los flujos | PASA | — |
| V-13 | Todo flujo permitido tiene protección en tránsito y riesgo residual | PASA | — |
| V-14 | F1–F26 de D1.11 completos (F4 reservado), ampliaciones F27+ registradas y regla de firewall con el ID del flujo | PASA | — |
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
| V-26 | Correspondencia contenidos mínimos (1–15) → secciones del DOCX cubre las 11 secciones | PASA | — |
| V-27 | Cobertura de las denegaciones de la matriz por pruebas (informativo) | PASA | 0 errores, 0 advertencias |
| V-28 | Inventario v0.4 completo: D1.12, VPC/subredes D2.5, D1.11 (F1–F33), D1.16 (T01–T60), 7 VLAN | PASA | — |
| V-29 | Pendientes (`pendiente: true`) registrados en CAMBIOS-INVENTARIO.md | PASA | 0 errores, 0 advertencias |
| V-30 | Sin secretos, llaves ni credenciales en infra/, docs/infra/, Makefile y CI | PASA | — |
| V-31 | VPN (D1.10 v0.4): ASN, /30 de túnel, NAT-T, MTU/MSS, temporizadores y flujos sobre la VPN | PASA | — |
| V-32 | Servicios base (DHCP, DNS, PAC, NTP, IPv6, DNS cifrado, Wi-Fi) consistentes con el inventario (D-28) | PASA | — |
| V-33 | Lo emulado se rotula como emulado: pruebas en Modo L solo con componentes emulados (F4.2) | PASA | — |
| V-34 | La rúbrica coincide con el XLSX oficial (nombre, peso y descriptor de nivel 4) | PASA | — |
| V-40 | El ruleset generado de fw01-sim contiene exactamente los flujos permitidos (y los bloqueos) del inventario | PASA | — |
| V-41 | swanctl, FRR y VTI generados coinciden con la sección vpn del inventario (cifrado, DPD, vidas, ASN, BGP, MTU, MSS) | PASA | — |
| V-42 | Los últimos resultados de make test-lab no tienen FALLA en pruebas críticas | PASA con advertencias | 0 errores, 2 advertencias |
| V-43 | Los artefactos generados versionados (tfvars de OpenTofu, topología de containerlab) están al día con el inventario | PASA | — |
| V-44 | Un ID retirado no se reutiliza ni aparece en flujos, pruebas, componentes, zonas, rúbrica o textos vigentes | PASA | — |
| V-45 | Ningún flujo permite descifrado con origen WIFI-EST (REQ-F-36, REQ-RN-11) | PASA | — |
| V-50 | Figuras .drawio, .png y .pdf presentes, con XML embebido y al día | PASA | Detalle y matriz componente × figura en docs/infra/e1/cobertura-figuras.md |
| V-51 | Cobertura componente × figura igual al campo `figuras` del inventario | PASA | — |
| V-52 | Todo celeris_id es un ID del contrato | PASA | — |
| V-53 | IP y CIDR rotulados existen en el inventario (y son del componente que los rotula) | PASA | — |
| V-54 | Flujos F-nn: FIG-5.5a ∪ FIG-5.5b completas y etiquetas derivadas del inventario | PASA | — |
| V-55 | Título, leyenda y panel «Qué aporta y qué pasa si falla» en cada figura | PASA | — |
| V-56 | Criticidad (borde + texto) y color de zona según CLAUDE.md | PASA | — |
| V-60 | Matriz de componentes: archivo y hojas | PASA | entregables/CE0311/Matriz_Componentes_Red_v1.1.xlsx |
| V-61 | Matriz 1 a 1 con el inventario (ID, nombre, IP, zona, criticidad, estado) | PASA | 31 filas · 31 componentes en el inventario |
| V-62 | Componentes dibujados en los .drawio = 100 % en la matriz | PASA | — |
| V-63 | Ninguna celda obligatoria vacía en la hoja Matriz | PASA | — |
| V-64 | Ningún «Por qué existe» repetido | PASA | — |
| V-65 | Las fórmulas recalculan sin errores | PASA | Microsoft Excel (COM) · 172 fórmulas · 0 errores |
| V-66 | «Por qué», «Qué aporta» y «Si falla» citan algo verificable | PASA | — |
| V-70 | XLSX de pruebas: hojas y una fila por prueba del YAML, con sus datos | PASA | — |
| V-71 | XLSX de pruebas: cada prueba cita flujos, componentes, OD, AM, DET y criterios de rúbrica existentes | PASA | — |
| V-72 | Cobertura: 100 % de flujos permitidos con prueba positiva, de bloqueos y celdas críticas con prueba negativa; OD, AM, DET y R3/R4 con ≥ 1 prueba | PASA | 0 errores, 0 advertencias |
| V-73 | Ensayo L: ninguna FALLA sin causa y acción; NO_APLICA, PARCIAL y sin ensayo nunca como PASA | PASA | — |
| V-74 | XLSX de pruebas: fórmulas sin errores tras recalcular con LibreOffice y coherentes con la biblioteca | PASA con advertencias | 0 errores, 1 advertencias |
| V-75 | XLSX de pruebas: el archivo versionado está al día con pruebas.yaml, el inventario y el último ensayo | PASA | — |
| V-80 | Informe DOCX: 11 secciones, tablas generadas del inventario, figuras y leyendas | PENDIENTE | pendiente de P5 |

## Errores

Ninguno.


## Advertencias (contradicciones y vacíos registrados)

- **V-42** — 2026-11-23-L: la prueba crítica T23 (Fuga IPv6) está en NO_APLICA, no en PASA
- **V-42** — 2026-11-23-L: la prueba crítica T58 (EC2-GW solo alcanza CTRL01:443 y SIEM01) está en PARCIAL, no en PASA
- **V-74** — LibreOffice no está disponible o falló: no se recalcularon las 605 fórmulas

## Información

- **V-27** — 28 de 60 celdas denegadas tienen una prueba dedicada; el resto se cubre por la política deny-all (OD-06) y las reglas de denegación con registro
- **V-29** — 0 elementos pendientes en los YAML; 68 entradas CI en CAMBIOS-INVENTARIO.md; sin referencia desde los YAML: ['CI-01', 'CI-02', 'CI-03', 'CI-04', 'CI-05', 'CI-06', 'CI-07', 'CI-08', 'CI-09', 'CI-10', 'CI-11', 'CI-12', 'CI-13', 'CI-14', 'CI-15', 'CI-16', 'CI-17', 'CI-18', 'CI-19', 'CI-20', 'CI-21', 'CI-22', 'CI-23', 'CI-24', 'CI-25', 'CI-26', 'CI-27', 'CI-28', 'CI-29', 'CI-30', 'CI-31', 'CI-32', 'CI-33', 'CI-34', 'CI-35', 'CI-36', 'CI-37', 'CI-38', 'CI-39', 'CI-40', 'CI-41', 'CI-42', 'CI-43', 'CI-44', 'CI-45', 'CI-46', 'CI-47', 'CI-48', 'CI-49', 'CI-50', 'CI-51', 'CI-52', 'CI-53', 'CI-54', 'CI-55', 'CI-56', 'CI-57', 'CI-58', 'CI-59', 'CI-60', 'CI-61', 'CI-62', 'CI-63', 'CI-70', 'CI-71', 'CI-72', 'CI-73', 'CI-74']
- **V-42** — Resultados de 2026-11-23-L (commit descono): {'PASA': 34, 'FALLA': 0, 'PARCIAL': 1, 'NO_APLICA': 17}
- **V-72** — Celdas denegadas no críticas sin prueba dedicada: 32 de 60 (las cubre la política deny-all; ver hoja «Cobertura»)

## Cobertura

| Relación | Cubiertos | Total |
| --- | ---: | ---: |
| flujos con prueba | 23 | 23 |
| flujos con prueba o justificación | 23 | 23 |
| componentes con ≥ 1 flujo | 21 | 31 |
| objetivos con ≥ 1 prueba | 12 | 12 |
| amenazas con ≥ 1 prueba | 18 | 18 |
| detecciones con ≥ 1 prueba | 11 | 11 |
| celdas denegadas con ≥ 1 prueba | 28 | 60 |
| criterios de rúbrica con evidencia | 8 | 8 |

## Pendientes de P2–P5 (ganchos)

| Gancho | Qué validará | Estado |
| --- | --- | --- |
| V-80+ | Informe DOCX: 11 secciones, tablas generadas del inventario, figuras y leyendas | pendiente de P5 |
