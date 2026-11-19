# Validación de la fuente única — CE0311 (Entregable 1)

> Generado por `infra/validate.py` (`make validate`). No editar a mano.

- Inventario: versión 1.0 · fecha 2026-11-18
- Contenido cargado: **14 zonas**, **37 componentes**, **26 flujos** (F1–F26, F4 reservado), **28 pruebas** (T01–T28), 10 objetivos OD, 13 amenazas AM, 9 detecciones DET, 7 figuras, 8 criterios de rúbrica.
- Resultado: **0 FALLA**, 6 con advertencias, 28 PASA, 4 pendientes de P2–P5.

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
| V-16 | Todo flujo tiene ≥ 1 prueba o una justificación | PASA con advertencias | 0 errores, 1 advertencias |
| V-17 | Componentes: por_que (1–3 frases), aporta_corto (≤ 12 palabras), aporta, si_falla, criticidad | PASA | — |
| V-18 | Componentes: ≥ 1 figura, FIG-5.1 y las figuras de sus flujos | PASA | — |
| V-19 | Componentes: ≥ 1 flujo o justificación de por qué no tienen | PASA | — |
| V-20 | Pruebas T01–T28 completas, con criterio verificable y modos válidos | PASA | — |
| V-21 | Coherencia bidireccional: pruebas ↔ amenazas, detecciones y rúbrica | PASA | — |
| V-22 | Todo objetivo OD tiene ≥ 1 prueba o indicador | PASA | — |
| V-23 | Toda amenaza AM tiene control y prueba | PASA con advertencias | 0 errores, 1 advertencias |
| V-24 | Rúbrica R1–R8: pesos suman 100 y cada criterio tiene ≥ 1 evidencia | PASA | — |
| V-25 | Detecciones: ubicación existente y validación | PASA con advertencias | 0 errores, 4 advertencias |
| V-26 | Correspondencia contenidos mínimos (1–15) → secciones del DOCX cubre las 11 secciones | PASA con advertencias | 0 errores, 1 advertencias |
| V-27 | Cobertura de las denegaciones de la matriz por pruebas (informativo) | PASA | 0 errores, 0 advertencias |
| V-28 | Inventario completo: D1.12, VPC/subredes D2.5, F1–F26, T01–T28, 10 VLAN | PASA | — |
| V-29 | Pendientes (`pendiente: true`) registrados en CAMBIOS-INVENTARIO.md | PASA | 0 errores, 0 advertencias |
| V-30 | Sin secretos, llaves ni credenciales en infra/, docs/infra/, Makefile y CI | PASA | — |
| V-31 | VPN (D1.10): ASN, /30 de túnel, MTU/MSS, temporizadores y flujos sobre la VPN | PASA | — |
| V-32 | Servicios base (DHCP, DNS, PAC, NTP, IPv6, DNS cifrado) consistentes con el inventario | PASA | — |
| V-33 | Lo emulado se rotula como emulado: pruebas en Modo L solo con componentes emulados (F4.2) | PASA con advertencias | 0 errores, 3 advertencias |
| V-34 | La rúbrica coincide con el XLSX oficial (nombre, peso y descriptor de nivel 4) | PASA | — |
| V-50 | Diagramas draw.io: componentes, IP, zonas, colores (Okabe-Ito), flujos F-nn y criticidad contra el inventario | PENDIENTE | pendiente de P2 |
| V-60 | XLSX de componentes: 100 % del inventario, IP, zona, criticidad, por qué, aporta y si falla | PENDIENTE | pendiente de P3 |
| V-70 | XLSX de pruebas: T01–T28, comandos, criterios y trazabilidad contra pruebas.yaml | PENDIENTE | pendiente de P4 |
| V-80 | Informe DOCX: 11 secciones, tablas generadas del inventario, figuras y leyendas | PENDIENTE | pendiente de P5 |

## Errores

Ninguno.


## Advertencias (contradicciones y vacíos registrados)

- **V-11** — EDGE→EDGE: la matriz indica «permitido» sin flujos y los flujos derivan «no_aplica» — contradicción registrada (CI-06)
- **V-11** — LAB→EDGE: los flujos ['F3'] permiten LAB→EDGE pero la matriz no los lista — contradicción registrada (CI-03)
- **V-11** — LAB-TEST→EDGE: los flujos ['F3'] permiten LAB-TEST→EDGE pero la matriz no los lista — contradicción registrada (CI-03)
- **V-11** — LAB-TEST→SERVERS: la matriz lista ['F2'] pero ningún flujo los deriva — contradicción registrada (CI-04)
- **V-11** — MGMT→INTERNET: la matriz indica «permitido» sin flujos y los flujos derivan «denegado» — contradicción registrada (CI-05)
- **V-16** — 9 flujos sin prueba T-nn propia (F10, F11, F15, F17, F18, F19, F20, F25, F26): se justifican en el inventario (CI-22)
- **V-23** — AM-13: sin T-nn; se justifica «D1.9 indica «Revisión de logs», no un T-nn; se revisa el registro de d…» (CI-18)
- **V-25** — DET-02 (Suricata IDS (IDS01)): validación solo como escenario «Escaneo desde KALI01 hacia SERVERS», sin T-nn en D1.16 (CI-17)
- **V-25** — DET-05 (Canary interno (HNY02)): validación solo como escenario «Barrido de puertos desde un equipo de LAB», sin T-nn en D1.16 (CI-17)
- **V-25** — DET-07 (Honey-URLs): validación solo como escenario «Pedir la URL señuelo», sin T-nn en D1.16 (CI-17)
- **V-25** — DET-08 (CrowdSec (FW01)): validación solo como escenario «Simulación con su escenario de prueba», sin T-nn en D1.16 (CI-17)
- **V-26** — La correspondencia 1–15 → DOCX es una propuesta: el documento maestro no incluye la tabla (CI-02)
- **V-33** — T12 (Modo L): destino NAS01 no se emula en el laboratorio (F4.1/F4.2) — registrado (CI-16)
- **V-33** — T25 (Modo L): origen BRK01 no se emula en el laboratorio (F4.1/F4.2) — registrado (CI-16)
- **V-33** — T25 (Modo L): destino ESX01 no se emula en el laboratorio (F4.1/F4.2) — registrado (CI-16)

## Información

- **V-16** — F10: sin prueba T-nn en D1.16 (justificado)
- **V-16** — F11: sin prueba T-nn en D1.16 (justificado)
- **V-16** — F15: sin prueba T-nn en D1.16 (justificado)
- **V-16** — F17: sin prueba T-nn en D1.16 (justificado)
- **V-16** — F18: sin prueba T-nn en D1.16 (justificado)
- **V-16** — F19: sin prueba T-nn en D1.16 (justificado)
- **V-16** — F20: sin prueba T-nn en D1.16 (justificado)
- **V-16** — F25: sin prueba T-nn en D1.16 (justificado)
- **V-16** — F26: sin prueba T-nn en D1.16 (justificado)
- **V-27** — 8 de 92 celdas denegadas tienen una prueba dedicada; el resto se cubre por la política deny-all (OD-06) y las reglas de denegación con registro
- **V-29** — 36 elementos pendientes en los YAML; 24 entradas CI en CAMBIOS-INVENTARIO.md; sin referencia desde los YAML: ['CI-02', 'CI-22', 'CI-23', 'CI-24']

## Cobertura

| Relación | Cubiertos | Total |
| --- | ---: | ---: |
| flujos con prueba | 16 | 25 |
| flujos con prueba o justificación | 25 | 25 |
| componentes con ≥ 1 flujo | 25 | 37 |
| objetivos con ≥ 1 prueba | 10 | 10 |
| amenazas con ≥ 1 prueba | 12 | 13 |
| detecciones con ≥ 1 prueba | 5 | 9 |
| celdas denegadas con ≥ 1 prueba | 8 | 92 |
| criterios de rúbrica con evidencia | 8 | 8 |

## Pendientes de P2–P5 (ganchos)

| Gancho | Qué validará | Estado |
| --- | --- | --- |
| V-50+ | Diagramas draw.io: componentes, IP, zonas, colores (Okabe-Ito), flujos F-nn y criticidad contra el inventario | pendiente de P2 |
| V-60+ | XLSX de componentes: 100 % del inventario, IP, zona, criticidad, por qué, aporta y si falla | pendiente de P3 |
| V-70+ | XLSX de pruebas: T01–T28, comandos, criterios y trazabilidad contra pruebas.yaml | pendiente de P4 |
| V-80+ | Informe DOCX: 11 secciones, tablas generadas del inventario, figuras y leyendas | pendiente de P5 |
