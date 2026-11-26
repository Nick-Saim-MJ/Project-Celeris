# Registro de cambios y contradicciones del inventario — CE0311 (E1)

Este archivo es el único lugar donde se registra lo que **falta o se contradice** en el documento maestro
(`docs/Celeris-Edge-Documento-Maestro.md`, v0.2) al transcribirlo a `infra/*.yaml`.
Regla del proyecto: si falta un dato, no se inventa ni se «arregla» dentro de un artefacto; se registra aquí,
se marca `pendiente: true` + `cambio: CI-nn` en el YAML y se decide con el equipo.

El validador (`make validate`, chequeo V-29) exige que todo `pendiente: true` apunte a una entrada de este archivo
y que toda referencia `cambio: CI-nn` exista aquí. Mientras una entrada esté **abierta**, el elemento aparece como
advertencia en `docs/infra/e1/validacion.md`.

## Plantilla de entrada

```markdown
### CI-nn — Título corto
- **Estado:** abierto | resuelto (fecha, quién)
- **Tipo:** contradicción | vacío | supuesto nuevo | decisión de transcripción
- **Dónde:** sección y línea del documento maestro; ruta en el YAML
- **Qué dice cada fuente:** …
- **Propuesta:** …
- **Decide:** nombre del integrante / DTI
- **Efecto al resolver:** qué se cambia en el YAML y qué se quita (`pendiente`)
```

Para resolver una entrada: aplicar la decisión en el documento maestro **y** en el YAML, quitar `pendiente`/`cambio`,
cambiar el estado a «resuelto» y volver a ejecutar `make validate`.

## Resumen

> Cierre del 2026-11-23 (CI-57): quedan abiertos solo los CI diferidos a CE02/CE0331 (CI-34, CI-51, CI-54 y CI-56). Los demás están resueltos, aplicados u obsoletos por la v0.4.

| ID | Tipo | Tema | Estado |
| --- | --- | --- | --- |
| CI-01 | contradicción | Versión del documento maestro (0.2 vs 0.2.1) | resuelto (aplicado) |
| CI-02 | contradicción | «15 secciones» del documento vs 11 de la plantilla; falta la tabla de contenidos mínimos | resuelto (aplicado) |
| CI-03 | contradicción | F3 llega a EDGE01, la matriz LAB→EDGE solo lista F1 | resuelto en CI-39 (D1.8 v0.4 lista F1 y F3) |
| CI-04 | contradicción | F2 no tiene LAB-TEST de origen, la matriz LAB-TEST→SERVERS lista F2 | resuelto en CI-39 (LAB-TEST retirada) |
| CI-05 | vacío | MGMT→Internet «443 actualizaciones» sin flujo F-nn | resuelto en CI-29 (F27) |
| CI-06 | vacío | EDGE→EDGE «peering» sin flujo ni puertos | resuelto |
| CI-07 | contradicción | F13 «todos los agentes» frente a la matriz y a las reglas de zona | resuelto |
| CI-08 | contradicción | T01/T21 hacen ping, pero ningún flujo ni Security Group permite ICMP | resuelto (CI-58) |
| CI-09 | vacío | NUT (UPS01 → NAS01 → ESXi y VM) sin flujo ni puerto | resuelto (obsoleto por v0.4, ver CI-35…43) |
| CI-10 | vacío | PROBE01: no hay ruta de métricas hacia OBS01 | resuelto (obsoleto por v0.4, ver CI-35…43) |
| CI-11 | contradicción | Security Groups de D2.5 frente a F12 y F13 | resuelto (obsoleto por v0.4, ver CI-35…43) |
| CI-12 | vacío | SW-ACC sin IP ni modelo (levantamiento AS-IS pendiente) | resuelto |
| CI-13 | vacío | Grupos AWS (VPC/subredes) sin criticidad en D1.12; IGW, rutas y S3 sin ID | resuelto |
| CI-14 | contradicción | EC2-CTRLR en «app-c» (D1.12) o «app-b» (D2.5) | resuelto (obsoleto por v0.4, ver CI-35…43) |
| CI-15 | contradicción | Criticidad de UPS01: Media (D1.12) vs Alta (D2.7) | resuelto (CI-61) |
| CI-16 | contradicción | T12 y T25 en Modo L, pero NAS01, ESXi e IPMI no se emulan | resuelto (obsoleto por v0.4, ver CI-35…43) |
| CI-17 | vacío | Detecciones DET-02, DET-05, DET-07 y DET-08 sin T-nn | resuelto con T29–T32 (CI-27) |
| CI-18 | vacío | AM-13 «Revisión de logs» no es una prueba T-nn | resuelto con T33 (CI-27) |
| CI-19 | contradicción | T24 usa 1.1.1.1 (IP pública real) contra la regla RFC 5737 | resuelto |
| CI-20 | decisión de transcripción | IDs OD/AM/DET/FIG asignados por posición; FIG-5.5a/5.5b | resuelto (aplicado) |
| CI-21 | vacío | Nombre DNS del portal y orígenes de varias pruebas no definidos | resuelto (CI-59) |
| CI-22 | vacío | 9 flujos sin prueba T-nn propia | resuelto con T34, T36–T43 y T49 (CI-27) |
| CI-23 | decisión de transcripción | Parámetros del laboratorio y tráfico sin F-nn en los generadores (Etapa 1) | resuelto (aplicado) |
| CI-24 | decisión de transcripción | Parámetros del laboratorio emulado (WAN, DNS de prueba, vgw-sim) y qué no se emula (Etapa 3) | resuelto (aplicado) |
| CI-25 | vacío | IaC del Modo A (OpenTofu): DPD mínimo de AWS, reglas de salida, disco de NAT01, campus simulado (Etapa 6) | resuelto (obsoleto por v0.4, ver CI-35…43) |
| CI-26 | decisión de transcripción | Qué pruebas son críticas (`critica` en pruebas.yaml) y qué hace V-42 con ellas (Etapa 7) | resuelto (aplicado) |
| CI-27 | vacío | Ampliación de la matriz de pruebas: T29–T49, polaridad y celdas críticas (P4) | resuelto (aplicado) |
| CI-28 | decisión de transcripción | Laboratorio emulado ampliado: NAS01 con VLAN 70/71, Wazuh, shield con mTLS, PAC del binario, honey-URL y navegador (P5) | resuelto (aplicado) |
| CI-29 | decisión de transcripción | Flujo F27: MGMT → Internet por TCP 443 para actualizaciones (resuelve CI-05) | resuelto (aplicado) |
| CI-30 | vacío | Capas de defensa en profundidad (D1.9) y salto de la ruta por defecto hacia el ISP fuera de infra/*.yaml | resuelto (aplicado) |
| CI-31 | contradicción | FIG-5.4: FW01 anuncia 10.20.0.0/16 por BGP, las tablas de rutas de la VPC citan 10.20.0.0/14 | resuelto (aplicado) |
| CI-32 | texto genérico | 17 textos de componentes (por qué / aporta / si falla) sin dato verificable (V-66) | resuelto (aplicado) |
| CI-33 | contradicción | C4.3: celeris-control (CTRL01) publica el portal en WEB01, pero no existe flujo CTRL01 → WEB01; el sitio lo despliega JMP01 por SSH (F20) | resuelto (obsoleto por v0.4, ver CI-35…43) |
| CI-34 | supuesto nuevo | S-20 (vigencia del token de enrolamiento) y S-21 (umbral de error del rollout), usados por el diseño detallado de CE02 | diferido (CE02/CE0331) |
| CI-35 | decisión de transcripción | v0.4 (D7 CI-30): consola (SPA + API + PostgreSQL) en CTRL01; se retiran DB01 y F15 | resuelto (2026-11-22, I1) |
| CI-36 | decisión de transcripción | v0.4 (D7 CI-31): EC2-GW, F29, F30, sg-gw; se retiran EC2-SHIELD, EC2-CTRLR, NAT01, F9, F16 y las subredes pub-b, app-b, data-a, data-b | resuelto (2026-11-22, I1) |
| CI-37 | decisión de transcripción | v0.4 (D7 CI-32): FW01 detrás del FortiGate (FGT-EXT), tránsito 10.20.0.0/29, NAT-T; WAN de FW01 = 10.20.0.2 | resuelto (2026-11-22, I1) |
| CI-38 | decisión de transcripción | v0.4 (D7 CI-33): zona WIFI-EST (172.16.0.0/16, provisional), F31, F32, T56, T57 | resuelto (2026-11-22, I1) |
| CI-39 | decisión de transcripción | v0.4 (D7 CI-34): simplificación: se retiran SVC01, OBS01, IDS01, PROBE01, NAS01, WAF01, WEB01, ESX01 vmk1, VLAN 31, 70 y 71, F11, F12, F17, F19 y F22; PORTAL01; DNS y NTP en FW01 | resuelto (2026-11-22, I1) |
| CI-40 | decisión de transcripción | v0.4 (D7 CI-35): ENC01 y F28; LABCLI01 y KALI01 a 10.20.35.0/24; rangos /26 de laboratorio | resuelto (2026-11-22, I1) |
| CI-41 | decisión de transcripción | v0.4 (D7 CI-36): pruebas retiradas T12, T22, T37, T38, T39, T41, T44, T48; nuevas T50–T60; destinos de T01, T02, T20, T21, T29, T42, T46 | resuelto (2026-11-22, I1) |
| CI-42 | supuesto nuevo | v0.4 (D7 CI-37): supuestos S-26…S-30 | resuelto (2026-11-22, I1) |
| CI-43 | decisión de transcripción | v0.4 (D7 CI-38): trazabilidad OD-04, OD-08, OD-11, OD-12, AM-14…AM-18, DET-02, DET-10, DET-11 | resuelto (2026-11-22, I1) |
| CI-44 | contradicción | F20 (D1.11 v0.4: TCP 22 y 443) frente a la administración del nodo en 9128 y el dashboard de Wazuh | resuelto (2026-11-22: F20 agrega TCP 9128) |
| CI-45 | vacío | La matriz D1.8 v0.4 no tiene columna WIFI-EST | resuelto (2026-11-22: se acepta «denegado») |
| CI-46 | vacío | nacl-private de D2.5: «puertos de servicio» sin definir | resuelto (2026-11-22: TCP 443 desde pub-a y efímeros) |
| CI-47 | contradicción | F2 «zonas internas» frente a DMZ-HONEY («solo envía al SIEM», D1.9) | resuelto (2026-11-22: F2 excluye DMZ-HONEY) |
| CI-48 | decisión de transcripción | Laboratorio emulado v0.4 (I2): parámetros que el inventario no fija (WAN y IP públicas, labcli02/03, byod01, gw-sim) y equivalencias distintas de D5.3 | resuelto (aplicado) |
| CI-49 | contradicción | F24 (señuelo) exige que el FortiGate publique TCP 22 y 23, pero D1.8 y S-29 limitan su NAT 1:1 a UDP 500/4500 y TCP 80/443 | resuelto (CI-60) |
| CI-50 | vacío | F23 y D1.9 («Salida: solo ACME y Wazuh»): FW01 permite TCP 443 a cualquier destino; el diseño no dice cómo se limita el destino | resuelto (2026-11-23: opción A, ver CI-52) |
| CI-52 | decisión de diseño | Opción A de CI-50: F23 retirado; ACME corre en FW01 y entrega el certificado a PORTAL01 por SFTP (F33); PORTAL01 no sale a la WAN | resuelto (2026-11-23) |
| CI-53 | decisión de transcripción | Demo de OpenTofu solo contra el AWS Emulator (I3-DEMO): `var.emulador = true` por defecto, credenciales ficticias, ruta estática en lugar de la propagación del VGW, módulos aws-vpc, aws-vpn, aws-gw y aws-backup | resuelto (2026-11-23) |
| CI-54 | vacío | EC2-GW: D2.5 y CE02 no definen su AMI ni su software de arranque (Caddy + Coraza, certificado de cliente, agente Wazuh); el módulo crea la instancia sin `user_data` | diferido (CE02/CE0331) |
| CI-55 | decisión de transcripción | El AWS Emulator no implementa EnableVgwRoutePropagation ni ModifyVpnTunnelOptions y no registra la Debian 13: diferencias con AWS real que el módulo absorbe | resuelto (2026-11-23) |
| CI-56 | vacío | Política del bucket de respaldos: D2.5 dice «solo acepta la IP pública del campus» sin decir si la regla alcanza a todos los principales o solo a la credencial de respaldo | diferido (CE02/CE0331) |
| CI-51 | vacío | Memoria para servir objetos grandes: 20 clientes de un instalador de 100 MB agotan `max_buffered_bytes` (512 MiB); D2.4 no lo dimensiona | diferido (CE02/CE0331) |
| CI-57 | decisión de transcripción | Cierre del registro: triage de los CI abiertos (2026-11-23) | resuelto (2026-11-23) |
| CI-58 | decisión de transcripción | T01 y T21 por TCP hacia CTRL01:443 (resuelve CI-08) | resuelto (2026-11-23) |
| CI-59 | supuesto nuevo | S-32: nombre del portal (resuelve CI-21) | resuelto (2026-11-23) |
| CI-60 | decisión de transcripción | Pedido a la DTI: TCP 22 y 23 hacia HNY01 durante la ventana del señuelo (resuelve CI-49) | resuelto (2026-11-23) |
| CI-61 | decisión de transcripción | UPS01 es Alta; NUT intrazona de MGMT (resuelve CI-15 y CI-09) | resuelto (2026-11-23) |
| CI-62 | decisión de transcripción | T25 solo en el Modo H (resuelve CI-16) | resuelto (2026-11-23) |
| CI-63 | decisión de transcripción | Capas de defensa en profundidad (D1.9) en la fuente única (resuelve la parte 1 de CI-30) | resuelto (2026-11-23) |
| CI-70 | vacío | FGT-EXT sin FIG-5.3 ni FIG-5.4; WIFI-EST sin FIG-5.3 (H1) | resuelto (2026-11-23) |
| CI-71 | contradicción | `muestra` de FIG-5.5a/b con los flujos de la v0.2 (H1) | resuelto (2026-11-23) |
| CI-72 | contradicción | Confianza de la zona AWS: «Media» en el YAML, «Baja, expuesta» en D1.9 (H1) | resuelto (2026-11-23) |
| CI-73 | vacío | «Por qué existe» de HNY01, SIEM01 y VGW más pobre que la Arquitectura v0.4 §4 (H2) | resuelto (2026-11-23) |
| CI-74 | vacío | Los componentes retirados no tienen motivo ni reemplazo en el YAML; la §5 no da motivo para las subredes AWS-PUB-B, AWS-APP-B, AWS-DATA-A y AWS-DATA-B (H2) | resuelto (2026-11-23) |
| CI-75 | vacío | Los OD-xx no citan la necesidad ni el objetivo del proyecto (OB-x) que atienden; el anexo C del informe lo necesita (H3) | resuelto (2026-11-23) |
| CI-76 | contradicción | El supuesto S-18 (usuario SFTP de NAS01, prueba T39) describe piezas retiradas en v0.4 y aparecía como vigente en el anexo D | resuelto (2026-11-23) |

## Entradas

### CI-01 — Versión del documento maestro
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** contradicción
- **Dónde:** cabecera del documento (línea 3) y `CLAUDE.md`; `inventory.yaml` → `meta.documento_base`
- **Qué dice cada fuente:** la cabecera y el registro de cambios del documento llegan a la versión **0.2**; las reglas del proyecto y el encargo de P1 citan **v0.2.1**.
- **Propuesta:** confirmar si existe una v0.2.1 no subida al repositorio. Si no existe, corregir `CLAUDE.md` a 0.2; si existe, versionarla en `docs/`.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** actualizar `meta.documento_base`, quitar `pendiente`.
- **Resolución:** No existe una v0.2.1: el documento llega a 0.2 y es la base histórica. `inventory.yaml → meta.documento_base` sin `pendiente`; el diseño vigente es `documentos_v04` (CE03 v0.4) y `CLAUDE.md` cita la v0.4.

### CI-02 — «15 secciones» del documento vs 11 de la plantilla; tabla de contenidos mínimos inexistente
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** contradicción
- **Dónde:** D1 (línea 1435: «la plantilla oficial tiene 15 secciones. D1.1 a D1.15 siguen ese orden uno a uno»), D1.17 R7 (línea 1854: «15 secciones oficiales»); `trazabilidad.yaml` → `correspondencia_contenidos`
- **Qué dice cada fuente:** la plantilla DOCX (`S1_E1_Analisis_y_Diseno_de_Red.docx`) tiene **11 secciones** numeradas (1–11), con subsecciones 2.1–2.3, 3.1–3.3, 5.1–5.6 y 7.1–7.3; `CLAUDE.md` también dice 11. D1 no incluye la «tabla del inicio de D1» que correspondería a los 15 contenidos mínimos.
- **Propuesta:** tomar la plantilla (11 secciones) como contrato y la correspondencia propuesta en `trazabilidad.yaml` (D1.1→§1, D1.2→§2.1, D1.3→§2.2, D1.4→§2.3, D1.5→§3, D1.6→§4, D1.7→§5.1, D1.8→§5.2, D1.9→§5.3/7.2/7.3, D1.10→§5.4/6, D1.11→§5.5, D1.12→§5.6, D1.13→§7.1, D1.14→§8, D1.15→§9/10/11; D1.16→§6). Corregir el texto de D1 y de D1.17 (R7) a «11 secciones».
- **Decide:** equipo del proyecto
- **Efecto al resolver:** quitar `correspondencia_pendiente`; el chequeo V-26 deja de advertir.
- **Resolución:** La plantilla (11 secciones) es el contrato: `trazabilidad.yaml → correspondencia_contenidos` sin `correspondencia_pendiente` (V-26 sin advertencia) y D1 de `docs/celeris/Celeris-CE03-Infraestructura.md` dice «11 secciones».

### CI-03 — F3 llega a EDGE01, pero la matriz LAB→EDGE solo lista F1
- **Estado:** resuelto en CI-39 (2026-11-22, I1): D1.8 v0.4 lista F1 y F3 en LAB → EDGE y F3 ya no incluye LAB-TEST
- **Tipo:** contradicción
- **Dónde:** D1.11 F3 (línea 1688), D1.8 matriz (filas LAB y LAB-TEST, columna EDGE, líneas 1563–1564), D1.9 «EDGE: solo recibe 3128 desde LAB» (línea 1602); `inventory.yaml` → `flujos[F3]`, `matriz_esperada` LAB→EDGE y LAB-TEST→EDGE
- **Qué dice cada fuente:** F3 (PAC, TCP 80) tiene como destino `pac.celeris.internal` = SVC01 **y EDGE01**, y D1.12 dice que EDGE01 sirve una copia del PAC. La matriz solo permite F1 (TCP 3128) de LAB y LAB-TEST hacia EDGE, y la regla de la zona EDGE dice que solo recibe 3128.
- **Propuesta:** agregar F3 a las celdas LAB→EDGE y LAB-TEST→EDGE y ajustar la regla de EDGE a «recibe 3128 y 80 (PAC) desde LAB». Es la opción que mantiene el PAC disponible cuando cae SVC01 (T22, OD-04).
- **Decide:** equipo del proyecto
- **Efecto al resolver:** corregir las dos celdas (o quitar EDGE01 del destino de F3); quitar `pendiente` de F3 y de las celdas. V-11 deja de advertir.

### CI-04 — F2 no incluye LAB-TEST de origen, pero la matriz lo lista
- **Estado:** resuelto en CI-39 (2026-11-22, I1): la zona LAB-TEST se retira en la v0.4
- **Tipo:** contradicción
- **Dónde:** D1.11 F2 (línea 1687), D1.8 matriz fila LAB-TEST, columna SERVERS (línea 1564); `inventory.yaml` → `flujos[F2].origen`, `matriz_esperada` LAB-TEST→SERVERS
- **Qué dice cada fuente:** el origen de F2 es «LAB, SECURITY, EDGE»; la matriz da `F2, F3` en LAB-TEST→SERVERS. Sin DNS, KALI01 y los equipos de LAB-TEST no resuelven nombres.
- **Propuesta:** agregar LAB-TEST al origen de F2.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar `LAB-TEST` a `F2.origen`; quitar `pendiente` de F2 y de la celda.

### CI-05 — MGMT→Internet «443 actualizaciones» sin flujo F-nn
- **Estado:** resuelto en CI-29 (F27)
- **Tipo:** vacío
- **Dónde:** D1.8 matriz fila MGMT, columna Internet (línea 1561); `matriz_esperada` MGMT→INTERNET
- **Qué dice cada fuente:** la celda dice «✔ 443 actualizaciones», sin ID de flujo. D1.11 no tiene un flujo MGMT→Internet, y el objetivo OD-07 exige que el 100 % de los flujos de D1.11 tengan protección documentada. D1.9 dice «Solo JMP01 inicia conexiones» en MGMT.
- **Propuesta:** definir el flujo (origen: ESX01 vmk0 y JMP01; destino: repositorios de actualización; TCP 443; TLS). El ID F4 está reservado; un ID nuevo (F27) rompe el contrato F1–F26, así que decide el equipo si usa F4 o amplía el rango.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar el flujo, citarlo en la celda y en las pruebas; quitar `pendiente`.

### CI-06 — EDGE→EDGE «peering» sin flujo ni puertos
- **Estado:** resuelto (2026-11-23)
- **Tipo:** vacío
- **Dónde:** D1.8 matriz fila EDGE, columna EDGE (línea 1568); `matriz_esperada` EDGE→EDGE
- **Qué dice cada fuente:** «✔ peering» sin F-nn ni puerto. El tráfico entre EDGE01 y EDGE02 está dentro de la VLAN 60 (conmutado en capa 2, nota 2 de D1.8), y el hash consistente entre nodos es REQ-F-21 (R3).
- **Propuesta:** dejar la celda como «sin flujo en R1» (REQ-F-21 pendiente) o definir el puerto de peering cuando se implemente R3.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** cambiar la celda a no_aplica o agregar el flujo.
- **Resolución:** En R1 no hay flujo EDGE ↔ EDGE: el tráfico entre EDGE01 y EDGE02 va dentro de la VLAN 60 (capa 2) y la celda EDGE → EDGE de `matriz_esperada` es `no_aplica`. El hash consistente entre nodos es REQ-F-21 (R3). T44 está retirada (CI-41); se quitó su `pendiente`.

### CI-07 — F13 «todos los agentes» frente a la matriz y a las reglas de zona
- **Estado:** resuelto (2026-11-23)
- **Tipo:** contradicción
- **Dónde:** D1.11 F13 (línea 1698), D1.8 matriz columna SECURITY, D1.9 reglas de zona (líneas 1601–1607), D2.8 «≈ 15 agentes» (línea 2035); `inventory.yaml` → `flujos[F13].origen`
- **Qué dice cada fuente:** F13 dice «todos los agentes» sin lista. La matriz solo permite F13 hacia SECURITY desde SERVERS, LAB (solo HNY02), DMZ-SVC, DMZ-HONEY, EDGE, BACKUP y AWS; no desde MGMT (JMP01, ESX01) ni LAB-TEST (KALI01). D2.8 estima ≈ 15 agentes; la lista de origen transcrita suma 13. Además D1.9 dice que DMZ-SVC «no inicia hacia ninguna zona interna» y que BACKUP «solo recibe de SERVERS», pero la matriz les permite F13.
- **Propuesta:** fijar la lista de agentes: CTRL01, DB01, OBS01, SVC01, EDGE01, EDGE02, WAF01, WEB01, HNY01, HNY02, NAS01 (interfaz de respaldo), EC2-SHIELD y EC2-CTRLR (13) y decidir si JMP01 y un 14.º y 15.º agente (p. ej. JMP01 y KALI01) se suman; aclarar en D1.9 que F13 es la excepción de salida hacia SECURITY.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** ajustar `F13.origen`, la matriz y la regla de zona; quitar `pendiente`.
- **Resolución:** La lista de agentes de F13 es la de `inventory.yaml` v0.4: CTRL01, EDGE01, EDGE02, PORTAL01, HNY01, HNY02 y EC2-GW. Es la que enrola el Modo L (`AGENTES` de `infra/gen/lab.py`: los mismos, con EC2-GW como `gw-sim`). F13 sin `pendiente`.

### CI-08 — T01 y T21 hacen ping, pero ningún flujo ni Security Group permite ICMP
- **Estado:** resuelto (2026-11-23, ver CI-58)
- **Tipo:** contradicción
- **Dónde:** D1.16 T01 y T21 (líneas 1815, 1835), D2.5 sg-shield (línea 1993), matriz SERVERS→AWS (línea 1562); `pruebas.yaml` → T01, T21
- **Qué dice cada fuente:** T01 espera «Permitido (VPN)» al hacer `ping 10.30.10.10` desde CTRL01, y T21 usa ping con 1372 y 1400 bytes. SERVERS→AWS solo permite F12 (TCP 9128 y 9100 desde OBS01), y sg-shield solo acepta TCP 8443 y 9128. Ningún F-nn cubre ICMP ni el origen CTRL01. T21 tampoco fija el origen.
- **Propuesta:** incluir ICMP echo desde CTRL01 (y el origen de T21) hacia 10.30.10.10 como regla de diagnóstico de la VPN, con su flujo F-nn, la regla en sg-shield y en la NACL; o reemplazar el ping por una prueba TCP al 8443/9128.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar el flujo o cambiar los comandos; quitar `pendiente` en T01 y T21.
- **Resolución:** T01 y T21 pasan de `ping` a pruebas TCP hacia CTRL01:443 por F30; no se agrega ningún flujo ICMP ni regla de Security Group. Detalle en CI-58.

### CI-09 — NUT (UPS01 → NAS01 → ESXi y VM) sin flujo ni puerto
- **Estado:** resuelto (2026-11-23, obsoleto por v0.4: CI-35…43)
- **Tipo:** vacío
- **Dónde:** D2.4 «Energía» (línea 1899), D1.12 UPS01 (línea 1728); `inventory.yaml` → UPS01
- **Qué dice cada fuente:** el apagado ordenado depende de NUT (UPS → NAS01 como servidor NUT → ESXi y VM), pero ni D1.11 ni la matriz tienen un flujo NUT. Las VM de SERVERS, EDGE, etc. tendrían que alcanzar NAS01 (10.20.10.30, MGMT) y la matriz solo permite MGMT→zonas (F20), no al revés. El puerto NUT no está en el documento.
- **Propuesta:** definir el flujo NUT con su puerto y la protección en tránsito; o decidir que solo ESX01 (dentro de MGMT) es cliente NUT y ESXi apaga las VM.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar el flujo (F-nn) o la nota de diseño; quitar `pendiente` de UPS01.
- **Resolución:** NUT queda en JMP01 y es intrazona de MGMT: UPS01 (10.20.10.40) → JMP01 (10.20.10.20), que apaga por SSH las VM y luego ESXi (F20). No cruza FW01 y no necesita F-nn. NAS01 se retiró (CI-39). Ver también CI-61.

### CI-10 — PROBE01: no hay ruta de métricas hacia OBS01
- **Estado:** resuelto (2026-11-23, obsoleto por v0.4: CI-35…43)
- **Tipo:** vacío
- **Dónde:** D1.12 PROBE01 (línea 1742), REQ-NF-03, D1.8 matriz SERVERS→LAB (✖), F12; `inventory.yaml` → PROBE01
- **Qué dice cada fuente:** PROBE01 (blackbox_exporter, LAB) mide la disponibilidad cada minuto, pero F12 solo scrapea EDGE, CTRL01 y EC2-SHIELD y la matriz deniega SERVERS→LAB. No se indica cómo llega la serie a OBS01 (¿scraping SERVERS→LAB, push, o PROBE01 expone por el puerto 9115?).
- **Propuesta:** agregar PROBE01 a los destinos de F12 (con la excepción en la matriz SERVERS→LAB) o definir un envío OTLP/push por F11.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** ajustar F12 o F11 y la matriz; quitar `pendiente`.
- **Resolución:** PROBE01 y OBS01 se retiraron (CI-39): ya no hay ruta de métricas que definir.

### CI-11 — Security Groups de D2.5 frente a F12 y F13
- **Estado:** resuelto (2026-11-23, obsoleto por v0.4: CI-35…43)
- **Tipo:** contradicción
- **Dónde:** D2.5 sección 6.4 (líneas 1991–1997), D1.11 F12, F13, D2.5 «Sin bastion»; `inventory.yaml` → EC2-CTRLR, EC2-SHIELD
- **Qué dice cada fuente:** F12 incluye TCP 9100 (node_exporter) hacia EC2-SHIELD, pero sg-shield solo acepta 8443 y 9128. sg-ctrlr limita la salida a TCP 5432 hacia 10.20.20.11, lo que impide el agente Wazuh de EC2-CTRLR hacia SIEM01 (F13, 1514/1515) y la salida de SSM por NAT01 (443).
- **Propuesta:** agregar 9100 a sg-shield, y a sg-ctrlr las salidas 1514/1515 hacia 10.20.50.10 y 443 hacia NAT01; documentarlo en D2.5.
- **Decide:** equipo del proyecto (también afecta E2)
- **Efecto al resolver:** corregir D2.5 y quitar `pendiente` de EC2-CTRLR.
- **Resolución:** F12 se retiró (CI-39) y EC2-SHIELD y EC2-CTRLR también (CI-36). El Security Group vigente es `sg-gw` (F29, F30, F13).

### CI-12 — SW-ACC sin IP ni modelo
- **Estado:** resuelto (2026-11-23)
- **Tipo:** vacío
- **Dónde:** D1.12 SW-ACC (línea 1723), D1.5 exclusiones; `inventory.yaml` → SW-ACC
- **Qué dice cada fuente:** la IP es «según levantamiento [S-14]» y la criticidad «Alta (fuera de alcance)». No hay modelo, puertos ni PoE hasta el levantamiento AS-IS con la DTI.
- **Propuesta:** dejar la IP en `null` hasta el levantamiento y registrar el resultado como CAMBIOS (resuelto) con el modelo, las IP de gestión y la lista de controles de capa 2 soportados.
- **Decide:** DTI (levantamiento) y Henyelrey (S-14)
- **Efecto al resolver:** completar IP en `ips` y `emulacion_lab`; quitar `pendiente`.
- **Resolución:** SW-ACC es existente y fuera de alcance, con IP `null` hasta el levantamiento AS-IS [S-14]. `pendiente` quitado en `inventory.yaml`.

### CI-13 — Grupos AWS sin criticidad en D1.12; IGW, tablas de rutas y S3 sin ID
- **Estado:** resuelto (2026-11-23)
- **Tipo:** vacío
- **Dónde:** D2.5 (líneas 1951–1997), D2.7 (VPC principal «Alta», S3 `celeris-backups` «Alta»); `inventory.yaml` → AWS-VPC, AWS-PUB-A/B, AWS-APP-A/B, AWS-DATA-A/B
- **Qué dice cada fuente:** D1.12 no lista los grupos AWS; D2.7 solo asigna criticidad a «VPC principal» (Alta). Las subredes, el Internet Gateway, las tablas rt-public/rt-private, el Gateway Endpoint de S3, los Security Groups, las NACL y el bucket S3 no tienen ID de componente.
- **Propuesta (aplicada provisionalmente):** criticidad de cada subred = la de la instancia que aloja (Media) y Baja para las reservas (pub-b, data-a, data-b). Los IDs AWS-VPC, AWS-PUB-A… son propuestos. Decidir si IGW, S3 y los SG/NACL se dibujan y se numeran en E1.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** confirmar criticidades e IDs; agregar los componentes que se dibujen; quitar `pendiente`.
- **Resolución:** El Internet Gateway y las tablas de rutas se dibujan dentro de AWS-VPC y no tienen ID propio (texto en `aporta` de AWS-VPC). Las criticidades de las subredes siguen la regla provisional (la de la instancia que alojan). `pendiente` quitado de las subredes.

### CI-14 — EC2-CTRLR en «app-c» (D1.12) o «app-b» (D2.5)
- **Estado:** resuelto (2026-11-23, obsoleto por v0.4: CI-35…43)
- **Tipo:** contradicción
- **Dónde:** D1.12 EC2-CTRLR «AWS app-c» (línea 1749), D2.5 tabla de subredes (app-b, línea 1960), «a y b o c, según la región» (línea 1953)
- **Qué dice cada fuente:** la IP 10.30.11.10 pertenece a app-b (10.30.11.0/24). D1.12 la ubica en «app-c», nombre que no existe en la tabla de subredes.
- **Propuesta:** usar **app-b** (la tabla de subredes manda); corregir D1.12.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** corregir D1.12; quitar el segundo `cambio` de AWS-APP-B.
- **Resolución:** EC2-CTRLR y la subred app-b se retiraron (CI-36).

### CI-15 — Criticidad de UPS01
- **Estado:** resuelto (2026-11-23, ver CI-61)
- **Tipo:** contradicción
- **Dónde:** D1.12 UPS01 «Media» (línea 1728), D2.7 UPS01 «Alta» (línea 2014)
- **Propuesta:** la UPS protege al único servidor y al firewall: usar **Alta**. En el inventario se conservó **Media** (valor de D1.12, el documento de E1) hasta que se decida.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** unificar ambos documentos y el YAML.
- **Resolución:** UPS01 es **Alta** (D2.7): protege al único servidor y al firewall. `inventory.yaml` y la fila de UPS01 en D1.12 de `docs/celeris/` quedan en Alta.

### CI-16 — T12 y T25 en Modo L, pero NAS01, ESXi e IPMI no se emulan
- **Estado:** resuelto (2026-11-23, obsoleto por v0.4: CI-35…43)
- **Tipo:** contradicción
- **Dónde:** F3 (línea 2361: «Modo L con T06–T20 y T22–T28»), F4.1 (topología sin NAS01, br-vlan70/71, ESXi, IPMI, BRK01); `pruebas.yaml` → T12, T25
- **Qué dice cada fuente:** T12 verifica que `10.20.70.20` (NAS01) no responde y T25 usa el puerto break-glass para alcanzar ESXi e IPMI. La topología del Modo L no tiene esos nodos, así que T12 «pasaría» sin demostrar nada y T25 no puede ejecutarse.
- **Propuesta:** T25 solo en Modo H; T12 en Modo L solo si se agrega un nodo `nas01` y `br-vlan70` sin interfaz en `fw01-sim`; de lo contrario también solo en H.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** ajustar `modos` o F4.1; quitar `pendiente`. V-33 deja de advertir.
- **Resolución:** NAS01 se retiró (CI-39) y T12 también (CI-41). T25 pasa a ejecutarse solo en el Modo H (CI-62).

### CI-17 — Detecciones DET-02, DET-05, DET-07 y DET-08 sin T-nn
- **Estado:** resuelto en CI-27 (pruebas agregadas a pruebas.yaml)
- **Tipo:** vacío
- **Dónde:** D1.14 (líneas 1778–1788) vs D1.16; `trazabilidad.yaml` → `detecciones`
- **Qué dice cada fuente:** la columna «Validación en S2» de D1.14 describe escenarios (escaneo desde KALI01, barrido desde LAB, honey-URL, escenario de prueba de CrowdSec), pero D1.16 no tiene pruebas T-nn para ellos. OD-09 exige ≥ 90 % de escenarios detectados.
- **Propuesta:** ampliar la matriz con T29+ (por ejemplo, T29 escaneo KALI01→SERVERS, T30 barrido en LAB, T31 honey-URL, T32 CrowdSec) o aceptar el escenario como validación sin T-nn. Ampliar T-nn rompe el contrato T01–T28.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar las pruebas o quitar `pendiente`.

### CI-18 — AM-13 «Revisión de logs»
- **Estado:** resuelto en CI-27 (pruebas agregadas a pruebas.yaml)
- **Tipo:** vacío
- **Dónde:** D1.9 STRIDE fila 13 (línea 1649)
- **Propuesta:** definir la revisión como procedimiento de S2 (muestreo de denegaciones de FW01 y verificación de NTS) o asignar un T-nn.
- **Decide:** equipo del proyecto

### CI-19 — T24 usa 1.1.1.1
- **Estado:** resuelto (2026-11-23)
- **Tipo:** contradicción
- **Dónde:** D1.16 T24 (línea 1838); regla del proyecto «IP públicas solo de documentación (RFC 5737)»; `pruebas.yaml` → T24
- **Qué dice cada fuente:** el comando sugerido usa `@1.1.1.1` (resolvedor público real).
- **Propuesta (aplicada):** `@203.0.113.53` (documentación RFC 5737); en el Modo H se sustituye por un resolvedor real al ejecutar. El resultado esperado (853 bloqueado) no depende del destino.
- **Decide:** equipo del proyecto
- **Resolución:** T24 usa `@203.0.113.53` (RFC 5737); en el Modo H se sustituye por un resolvedor real al ejecutar. `pendiente` quitado.

### CI-20 — IDs OD/AM/DET/FIG asignados por posición; FIG-5.5a y FIG-5.5b
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** decisión de transcripción
- **Dónde:** `trazabilidad.yaml`
- **Qué dice cada fuente:** el documento maestro no define OD-xx, AM-xx ni DET-xx (usa «#» y filas) ni FIG-x.x; la plantilla DOCX solo trae figuras 1.1, 5.1–5.4 y deja 5.5 como tabla.
- **Decisión tomada:** OD-01…10 por orden de D1.6; AM-01…13 por «#» de D1.9; DET-01…09 por orden de D1.14. FIG-5.5a (flujos de usuario, portal y servicios hacia Internet: F1–F3, F5–F8, F21–F25) y FIG-5.5b (control, observabilidad, seguridad, respaldo e híbrido: F9–F20, F26) dividen el diagrama de la sección 5.5 para que cada figura sea legible.
- **Decide:** equipo del proyecto (confirmar la división de figuras)
- **Resolución:** OD, AM y DET por posición y FIG-5.5a/5.5b quedan como están en `trazabilidad.yaml` (sin `pendiente`). La lista de flujos que muestra cada figura se actualiza al regenerar los diagramas (I4).

### CI-21 — Nombre DNS del portal y orígenes de pruebas no definidos
- **Estado:** resuelto (2026-11-23, ver CI-59)
- **Tipo:** vacío
- **Dónde:** D1.16 T16–T18 («https://portal»), T04, T05, T15, T16, T17, T21, T25, T26
- **Qué dice cada fuente:** el portal se escribe `https://portal` sin FQDN, pero el certificado público por ACME (D1.9) exige un dominio público real que no está definido. Varias pruebas no indican el equipo de origen; en `pruebas.yaml` se usó el que sugiere el comando o el de la prueba vecina (CTRL01, INTERNET, EDGE01, FW01).
- **Propuesta:** definir el FQDN del portal [S-xx nuevo] y fijar el origen de cada prueba en S2.
- **Decide:** equipo del proyecto y DTI (dominio)
- **Efecto al resolver:** reemplazar `portal` en T16–T18 y quitar `pendiente`.
- **Resolución:** El FQDN del portal es el supuesto nuevo **S-32**; T16, T17 y T18 usan el nombre de trabajo `portal.celeris.internal`. Detalle en CI-59.

### CI-22 — 9 flujos sin prueba T-nn propia
- **Estado:** resuelto en CI-27 (pruebas agregadas a pruebas.yaml)
- **Tipo:** vacío
- **Dónde:** D1.16 vs D1.11: F10, F11, F15, F17, F18, F19, F20, F25, F26. F23 solo tiene la prueba negativa T19 (WEB01 no sale a Internet); la renovación ACME no tiene prueba.
- **Propuesta:** mantener `sin_prueba_justificacion` (cada una dice cómo se valida en S2) o ampliar D1.16 con T29+. Los demás flujos tienen al menos un T-nn.
- **Decide:** equipo del proyecto

### CI-23 — Parámetros del laboratorio y tráfico sin F-nn en los generadores (Etapa 1)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** decisión de transcripción
- **Dónde:** `infra/gen/nftables.py`, `infra/gen/vpn.py`, `infra/gen/pac.py`
- **Qué falta en el inventario y cómo se resolvió (todo es del laboratorio emulado, nada cambia el diseño):**
  1. **IP públicas de los dos extremos AWS.** D1.10 dice «2 IP asignadas por AWS». Los generadores las reciben por parámetro (`--aws-peer`, ×2); los tests usan 198.51.100.21 y .22 (RFC 5737). La IP WAN de `fw01-sim` en el laboratorio (F4.1: red 198.51.100.0/24) se fija en la Etapa 3.
  2. **Direcciones de host de los /30 de túnel.** D1.8 solo da 169.254.10.0/30 y 169.254.11.0/30. Convención adoptada, la de AWS: primer host = extremo AWS, segundo = campus.
  3. **AS-path prepending del túnel 2.** El inventario dice `bgp_as_path_prepending: true` sin cantidad. Se usa una repetición del ASN (el mínimo que invierte la preferencia).
  4. **Nombre de las interfaces de túnel, clave VTI y marca.** `vti1`/`vti2` (ID del componente en minúsculas); la clave del VTI y la marca de strongSwan son el número de túnel. Se usan VTI (como dice D1.10) y no interfaces XFRM porque el kernel de WSL2 no las trae.
  5. **Tráfico que no es un flujo F-nn de D1.11 pero el firewall necesita:** IKEv2 (UDP 500/4500), ESP y BGP (TCP 179) de la VPN; NAT de salida; anti-spoofing de WAN (D1.13); MSS clamping (D1.10). Se generan en reglas rotuladas «sin F-nn» y el validador (V-40) las distingue de los flujos.
  6. **F20 hacia FW01.** F20 usa los mismos puertos para todos los destinos («hosts listados»); la regla de entrada a FW01 hereda 22, 443, 3000, 5601 y 9128 aunque la GUI solo necesita 443. Conviene fijar el puerto por destino en D1.11.
  7. **REQ-F-26.** `infra/gen/pac.py` genera el `wpad.dat` desde el inventario (lab y entrega), pero el binario `celeris-cache` (src/) aún no genera PAC: el requisito de producto sigue pendiente en el código.
- **Propuesta:** aceptar las convenciones 2–4 como definitivas para el laboratorio; fijar 1 en la Etapa 3; revisar 5 y 6 al corregir D1.11.
- **Decide:** equipo del proyecto
- **Resolución:** Convenciones y reglas «sin F-nn» en `infra/gen/nftables.py`, `infra/gen/vpn.py` e `infra/gen/pac.py` (V-40 las distingue). Los parámetros de la v0.4 están en CI-37 y CI-48.

### CI-24 — Parámetros del laboratorio emulado y qué no se emula (Etapa 3)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** decisión de transcripción
- **Dónde:** `infra/gen/lab.py` (`PARAMETROS_LAB`), `lab/celeris.clab.yml`
- **Parámetros que el inventario no fija y el laboratorio necesita (solo Modo L, nada cambia el diseño):**
  1. WAN del laboratorio 198.51.100.0/24 (F4.1): `fw01-sim` 198.51.100.10 (mismo último octeto que 203.0.113.10), `ext01` 198.51.100.100, extremos AWS de `vgw-sim` 198.51.100.21 y .22.
  2. `vgw-sim` se coloca en la subred app-a con 10.30.10.1 (la VPC real no tiene ese equipo; es el router de EC2-SHIELD en la emulación).
  3. Nombres DNS de prueba: `portal.celeris.internal` (portal, WAF01), `listado.example.com` (dominio listado de T07, interceptado por el nodo) y `example.com` (T14, T19, T22, T24). Los tres se resuelven a WAF01 o a `ext01` con Unbound. Relacionado con CI-21 (el FQDN real del portal sigue sin definirse).
  4. Red de gestión de containerlab (172.20.20.0/24): es infraestructura del laboratorio, no del diseño; no se usa en ninguna prueba.
- **No se emula en el Modo L (rotulado en `emulacion_lab` y en ensayo-laboratorio.md):** ESX01, SW-CORE01, SW-ACC, IPMI01, UPS01, BRK01, NAS01 y las VLAN 70 y 71 (F4.1 no las incluye; CI-16), CTRL01, DB01, PROBE01, EC2-CTRLR y NAT01. SIEM01 (Wazuh) queda como perfil opcional sin implementar en esta etapa.
- **Equivalencias distintas de F4.2:** el WAF es nginx + ModSecurity v3 + OWASP CRS (F4.2: Caddy + Coraza); HNY01 es Cowrie oficial (SSH, puerto 2222); OpenCanary y el puerto 23 de F24 no se emulan; HNY02 es un canario propio en Python (puertos 22, 80, 445 y 3389); EDGE01/02 y shield01 usan el binario de la imagen OCI sobre la imagen base de laboratorio (la imagen mínima no trae shell para configurar la red); EC2-SHIELD solo responde conexiones de prueba hasta que exista REQ-F-29.
- **Hallazgos del montaje (contradicen o precisan el diseño):**
  - El kernel de WSL2 no soporta interfaces XFRM, solo VTI: coincide con D1.10 («interfaces VTI»), por eso el generador usa VTI.
  - strongSwan necesita desactivar los plugins `kernel-libipsec`, `forecast` y `bypass-lan` para que el IKE salga por la WAN y el BGP entre al túnel: sin eso el diseño de D1.10 no funciona con VTI.
  - Con FRR hace falta `maximum-paths 1` para cumplir «un solo túnel a la vez» de D1.10; por defecto FRR reparte entre los dos (ECMP).
  - La ruta 10.20.0.0/16 debe existir (aquí, a `Null0`) para que BGP anuncie el agregado: D1.10 dice «Redes anunciadas 10.20.0.0/16» y no dice cómo se origina.
- **Propuesta:** dar por buenos los parámetros 1–4 para el laboratorio; incluir en el informe la nota sobre `maximum-paths` y el origen del agregado BGP en D1.10.
- **Decide:** equipo del proyecto
- **Resolución:** Parámetros del laboratorio en `infra/gen/lab.py` (`PARAMETROS_LAB`) y `lab/celeris.clab.yml`; lo que no se emula está en `emulacion_lab` de cada componente. Los de la v0.4 están en CI-48.

### CI-25 — IaC del Modo A (OpenTofu): lo que el diseño no define o AWS no admite (Etapa 6)
- **Estado:** resuelto (2026-11-23, obsoleto por v0.4: CI-35…43)
- **Tipo:** vacío y contradicción
- **Dónde:** `infra/inventory.yaml` (sección `aws`, campo `instancia` de EC2-SHIELD, EC2-CTRLR y NAT01), `infra/gen/tofu.py`, `deploy/opentofu/`
- **Qué falta o choca y cómo se transcribió (nada se cambió en el diseño):**
  1. **DPD.** D1.10 pide un DPD de 10 s. AWS no admite un `dpd_timeout_seconds` menor de 30. El módulo `aws-vpn` usa 30 s (`DPD_MINIMO_AWS_S` en `tofu.py`); strongSwan en cgw-sim conserva los 10 s del inventario. La detección de caída de un túnel desde el lado AWS es entonces tres veces más lenta que lo escrito en D1.10.
  2. **Reglas de salida.** D2.5 define las reglas de entrada de los Security Groups y de las NACL, no las de salida. Se transcribe «todo permitido» en ambos (`egress: todo`). Si el diseño quiere salida restringida, hay que escribirla en D2.5.
  3. **`sg-ctrlr` sin salida a F13 ni a SSM.** Por CI-11 se copió la regla de D2.5 tal cual (salida solo TCP 5432 hacia DB01, F16). Con esa regla EC2-CTRLR no alcanza el endpoint de Session Manager ni al plano de control de CTRL01 (F13). Se refleja el documento; la corrección es de D2.5.
  4. **`nacl-public`.** NAT01 necesita recibir tráfico de las subredes privadas; se añadió «permitir todo desde 10.30.0.0/16» a la entrada de `nacl-public`, que D2.5 no lista. Las denegaciones de 22 y 3389 se evalúan antes.
  5. **Disco de NAT01.** F5.2 da un rango; se tomó el extremo inferior (8 GB) como `disco_gb_gp3`. Los tipos y discos de EC2-SHIELD (t3.medium, 200 GB) y EC2-CTRLR (t3.small, 60 GB) y sus equivalentes de laboratorio (t3.small y t3.micro) vienen de D2.5, 6.3.
  6. **Campus simulado.** La subred WAN de `cgw-sim` (10.20.0.0/24) y su IP privada (la décima de la subred) son parámetros del laboratorio, no de D1.8. La VPC 10.20.0.0/16, la subred de `labcli-sim` (zona LAB) y la IP 10.20.32.50 sí son del inventario.
  7. **Nombres de Security Group.** AWS prohíbe que empiecen por `sg-`: el nombre real es `celeris-sg-…`; el ID del diseño se conserva en la etiqueta `Name`.
  8. **Presupuesto (RE-07).** El inventario fija el umbral de alarma (80 %) pero no el tope en USD. Es la variable `presupuesto_usd` (sin valor por defecto: sin ella no se crea el presupuesto). El tope es un supuesto sin [S-xx] asignado.
  9. **AMI.** Se resuelve la Debian 13 oficial por su parámetro público de SSM (`/aws/service/debian/release/13/latest/amd64`); la elección de Debian 13 es un supuesto de la IaC, sin [S-xx] asignado.
- **Sin verificar (no se ejecutó `tofu apply` ni `tofu plan` contra AWS):**
  - **NAT-T con interfaces XFRM.** En el Modo A `cgw-sim` queda detrás de una IP elástica (NAT 1:1). Por eso su configuración usa interfaces XFRM con `if_id` y no VTI como D1.10 y el Modo L (el kernel de WSL2 no trae XFRM, el de EC2 sí). El comportamiento es el mismo en teoría; no se comprobó con una VPN real.
  - **AWS Academy.** No se sabe si el laboratorio permite crear un VGW y una conexión VPN con BGP. La IaC admite `perfil_de_instancia_existente` para no crear roles de IAM.
  - **Modo A' (sin VGW)** no está implementado.
  - AWS Emulator no está instalado: la única verificación de planificación es `tofu validate` y un plan estructural con credenciales falsas en una copia temporal (78 recursos, sin llamadas a AWS), cuya salida no es evidencia de despliegue.
- **Secretos.** Las llaves precompartidas de los túneles las genera AWS (`tunnelN_preshared_key`) y quedan en el estado de OpenTofu y en el `user_data` de cgw-sim. El estado es local, está en `.gitignore` y no debe versionarse; es un riesgo aceptado solo para el laboratorio efímero.
- **Propuesta:** completar D2.5 con las reglas de salida (2 y 3), corregir D1.10 o documentar el DPD de 30 s (1), fijar el tope de RE-07 (8) y decidir si se verifica en AWS Academy antes de la demostración.
- **Decide:** equipo del proyecto
- **Resolución:** La IaC de la v0.2 (EC2-SHIELD, EC2-CTRLR, NAT01, Budgets) se reemplazó por la demo de la v0.4 (CI-53 y CI-55).

### CI-26 — Pruebas críticas y alcance de V-40 a V-43 (Etapa 7)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** decisión de transcripción
- **Dónde:** `infra/pruebas.yaml` (campo `critica`), `infra/schema/pruebas.schema.json`, `infra/validate.py` (V-40…V-43)
- **Qué no definía el diseño:** D1.16 no dice qué pruebas son críticas. Se adoptó una regla: una prueba es crítica si su categoría es `segmentacion`, `vpn` o `cifrado` (16 de 28: T01–T06, T08, T10, T12, T19–T21, T23–T24, T27–T28), es decir, si un FALLA invalida un límite de seguridad del diseño. Quedan fuera conectividad, disponibilidad, detección, seguridad web y privacidad. La regla es del equipo del proyecto, no de D1.16.
- **Qué hace V-42:** FALLA en una prueba crítica = FALLA del validador. Una crítica que aplica al modo y no está en PASA (PARCIAL, NO_APLICA, ausente), o una FALLA no crítica, = advertencia: PARCIAL y NO_APLICA no cuentan como PASA.
- **Límites de V-40 y V-41:** comprueban los artefactos generados contra el inventario (puertos, acciones, modos, algoritmos, temporizadores, ASN, MTU/MSS), no el comportamiento del firewall; eso lo mide `make test-lab`. V-40 trata como correctas las reglas «sin F-nn» de CI-23 (VPN, NAT, anti-spoofing, MSS).
- **Propuesta:** confirmar o cambiar la regla de criticidad; en particular, si T15 (WAF) y T17 (inyección) deben ser críticas.
- **Decide:** equipo del proyecto
- **Resolución:** Campo `critica` en `infra/pruebas.yaml` y V-42 en `infra/validate.py`. FALLA en una prueba crítica es FALLA del validador; PARCIAL y NO_APLICA nunca cuentan como PASA.

### CI-27 — Ampliación de la matriz de pruebas: T29 a T49 (P4)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** vacío (resuelve CI-17, CI-18 y CI-22; la regla de celdas críticas es una decisión de transcripción)
- **Dónde:** `infra/pruebas.yaml` (T29–T49, `polaridad`, `ampliacion`), `infra/trazabilidad.yaml` (`elementos_evaluados` de R3 y R4), `infra/celeris_infra.py` (`cobertura_de_pruebas`), V-70+ en `infra/checks/v70_xlsx_pruebas.py`
- **Qué faltaba:** D1.16 define T01–T28 y deja sin prueba positiva 10 flujos permitidos (F10, F11, F15, F17, F18, F19, F20, F23, F25, F26), 4 detecciones (DET-02, DET-05, DET-07, DET-08), la amenaza AM-13 y casi todas las celdas denegadas críticas de la matriz zona × zona. Se agregaron 21 pruebas que no sustituyen a ninguna de D1.16 y llevan `ampliacion: true`:
  - **Detección y rastro (cierra CI-17 y CI-18):** T29 escaneo lateral (DET-02), T30 canary interno (DET-05), T31 honey-URL (DET-07), T32 CrowdSec (DET-08), T33 rastro de las denegaciones (AM-13).
  - **Flujos permitidos sin prueba (cierra CI-22):** T34 administración desde JMP01 (F20), T36 mTLS del nodo (F10), T37 OTLP (F11), T38 base de datos (F15), T39 respaldo en NAS01 (F17), T40 respaldo en S3 (F18), T41 NFS (F19), T42 NTS (F25), T43 reglas de seguridad (F26), T49 ACME (F23).
  - **Celdas permitidas sin F-nn:** T35 MGMT → Internet (CI-05), T44 peering entre nodos de borde (CI-06).
  - **Celdas denegadas críticas:** T45 Internet → zonas internas, T46 DMZ-SVC → zonas internas, T47 DMZ-HONEY → cualquier zona, T48 cualquier zona → STORAGE.
- **Regla de «celda denegada crítica»** (la del encargo, aplicada por `celdas_denegadas_criticas()`): Internet → interna o AWS, LAB → MGMT, DMZ-SVC → interna o AWS, DMZ-HONEY → cualquiera y cualquiera → STORAGE. «Interna» = MGMT, SERVERS, LAB, LAB-TEST, SECURITY, EDGE, STORAGE y BACKUP. Son 35 celdas y las 35 tienen prueba negativa. Las otras 56 celdas denegadas (por ejemplo, SERVERS → LAB-TEST) no son críticas y siguen sin prueba dedicada: las cubre la política deny-all y se miden en la hoja «Cobertura».
- **Polaridad.** Cada prueba lleva `polaridad`: positiva (se espera tráfico permitido), negativa (se espera denegación) o mixta. «Prueba positiva de un flujo» = positiva o mixta que lo cita.
- **Modos.** T29, T30, T31, T35, T39, T44–T47 y T49 son de los modos L y H y tienen caso en el laboratorio emulado (`tests/network/casos.py`; CI-28 explica qué se agregó al laboratorio); T48 es de A y H; el resto (T32–T34, T36–T38, T40–T43) es del Modo H porque el laboratorio no tiene CrowdSec, NTS, ESXi, S3, PostgreSQL ni el plano de control: el ensayo las muestra como NO_APLICA, nunca como PASA. T44 queda PARCIAL (el puerto del peering no está definido, CI-06) y T35 FALLA por el hallazgo de CI-05 (ver CI-28).
- **Valores que el diseño no fija y las pruebas necesitan (no son del inventario):**
  1. T31: la ruta de la honey-URL (REQ-F-27 está pendiente); T31 queda `pendiente: true`.
  2. T32: la IP externa de pruebas; la pone el equipo al ejecutar.
  3. T39: usuario y repositorio de restic en NAS01.
  4. T49: el endpoint ACME; se usa el directorio de Let's Encrypt como ejemplo.
  5. T33: el desfase de reloj máximo entre FW01 y SIEM01 (menos de 1 s) es el supuesto [S-16].
  6. Los umbrales «alerta de Wazuh de nivel ≥ 10 en menos de 60 s» siguen D1.14 (nivel ≥ 10) y el criterio de T18; los 60 s son una elección de esta ampliación, no un dato de D1.
  7. T29: la firma que debe aparecer en IDS01 se pide por patrón (`scan` o `escaneo`) y por el origen KALI01: en S2 será una firma ET SCAN de ET Open; en el Modo L es la regla local sid 9000001. No se comprobó contra la versión de reglas de S2.
- **Contradicción hallada:** la matriz D1.8 dice que LAB-TEST → SERVERS está permitido por F2, pero F2 no incluye a LAB-TEST (CI-04). T29 escanea OBS01, que ningún flujo alcanza desde LAB-TEST, y no cuenta esa celda. SVC01 no sirve de destino: F3 abre su puerto 80 a LAB-TEST y un primer ensayo lo mostró abierto.
- **Hallazgos del ensayo en el laboratorio emulado:**
  - DET-05: un canario de aplicación (HNY02) solo registra conexiones completas. Un barrido SYN (`nmap -sS`) no lo activa y IDS01 no captura la VLAN 30 (D1.14, nota sobre la captura). T30 usa `-sT`; un barrido SYN dentro de LAB queda sin detección. Conviene decidirlo en D1.14.
  - T22 era intermitente por el tiempo de espera del caso, no por el diseño; con SVC01 caído el cliente espera el tiempo de espera del resolvedor (2 s) antes de usar FW01.
- **R1 y R7** no tienen pruebas: son criterios documentales (contexto y alcance; calidad documental y trazabilidad). La cobertura de rúbrica por pruebas se mide sobre R2–R6 y R8.
- **Propuesta:** aceptar T29–T49 como ampliación de D1.16 (o descartar las que el equipo considere fuera de alcance), confirmar la regla de celdas críticas y resolver los valores 1 a 4.
- **Decide:** equipo del proyecto
- **Resolución:** Pruebas T29…T60 en `infra/pruebas.yaml` (T37, T38, T39, T41, T44 y T48 retiradas por CI-41). T31 usa la ruta señuelo de S-17 y ya no está `pendiente`.

### CI-28 — Laboratorio emulado ampliado (P5)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** decisión de transcripción (cierra parte de CI-16 y CI-24)
- **Dónde:** `infra/gen/lab.py`, `lab/`, `siem/wazuh/local_rules.xml`, `tests/network/casos.py`, `src/` (REQ-F-26, REQ-F-27 y REQ-F-29)
- **Qué se agregó al laboratorio (todo emulado, F4.2):**
  1. **NAS01** con sus tres interfaces (STORAGE, BACKUP y MGMT) y los puentes `br-vlan70` y `br-vlan71`. STORAGE no tiene interfaz en FW01 (D1.4: sin gateway); BACKUP sí (10.20.71.1). NAS01 no reenvía entre interfaces. Es sshd + restic y un puerto 2049 que no es NFS: no es un NAS. ESX01, IPMI01, SW-CORE01, UPS01 y BRK01 siguen sin emularse, por lo que T25 queda NO_APLICA en el Modo L y T41 en el Modo H.
  2. **SIEM01** como Wazuh manager 4.9.2 (imagen fijada por digest) y agentes en OBS01, SVC01, WAF01, WEB01, HNY01, HNY02, IDS01, EDGE01, EDGE02 y NAS01, que se enrolan por F13 (1515 y 1514): el laboratorio valida esas reglas de FW01. Las alertas de las pruebas son las reales del manager. Las reglas locales 100300–100304 del laboratorio están en `siem/wazuh/local_rules.xml`; el criterio de D1.14 es nivel ≥ 10.
  3. **Syslog por TLS (F14).** SIEM01 recibe en 6514 con TLS (receptor `socat`) y lo pasa al syslog TCP de bucle local de Wazuh; no escucha UDP 514. FW01 no es OPNsense: el evento de T28 lo envía `socat` desde `fw01-sim`; lo que se prueba es el receptor de SIEM01.
  4. **Shield con mTLS (REQ-F-29, F9).** EDGE01 y EDGE02 envían los MISS a `shield01` (10.30.10.10:8443) por la VPN con certificado de cliente de una CA de nodos. `vgw-sim` hace NAT de la VPC hacia «Internet» (hace el papel de NAT01).
  5. **PAC generado por el binario (REQ-F-26).** EDGE01 ejecuta `celeris-cache pac` al arrancar y nginx sirve el resultado; SVC01 sigue sirviendo el PAC de `infra/gen/pac.py`.
  6. **Honey-URL (REQ-F-27).** Ruta señuelo de laboratorio `/admin-backup.zip` [S-17].
  7. **Navegador real automatizado.** Chromium sin pantalla en LABCLI01 para T08, T09 y T22; los criterios manuales de esas tres pruebas pasaron a medibles (`automatizable: true`). Usa `--ignore-certificate-errors` porque la CA del nodo no está en su almacén.
  8. **Restic y ACME de laboratorio.** Usuario y carpeta de restic [S-18]; directorio ACME de laboratorio en `ext01` (no es Let's Encrypt).
- **No se agregó:** NTS (T42), actualización de reglas (T43), OTLP (T37), PostgreSQL (T38), S3 (T40), ESXi/NFS real (T41), mTLS del plano de control (T36) y RA guard (T23). Siguen en el Modo H.
- **Hallazgo — T35 (CI-05):** la matriz D1.8 permitía MGMT → Internet por TCP 443 sin ningún flujo F-nn, y FW01 lo denegaba: T35 fallaba en el Modo L por esa causa. Se resolvió con el flujo F27 (CI-29).
  9. **CrowdSec (T32).** CrowdSec y su bouncer de nftables, reales y del repositorio oficial del fabricante, corren en `fw01-sim` en modo local (sin la nube de CrowdSec). La decisión de bloqueo se agrega con `cscli decisions add` (la «simulación con su escenario de prueba» de D1.14); el aviso a Wazuh lo envía `socat` por el syslog TLS de F14. Versión instalada en el ensayo: CrowdSec 1.8.2. Como el contenedor no tiene systemd, los paquetes se extraen sin ejecutar sus scripts de instalación; el script de arranque crea las credenciales de la API local, un índice vacío del hub y la clave del bouncer (generadas al arrancar, fuera del repositorio). No hay parsers ni escenarios del hub: la detección real de abusos exige logs de SSH o del WAF y queda en el Modo H.
  - **Hallazgo — T32:** una recarga de reglas de FW01 con `flush ruleset` borra la tabla `crowdsec` del bouncer y deja de bloquear. T32 reinicia el bouncer antes de medir. En OPNsense real habrá que comprobar que un `reload` de reglas no tenga el mismo efecto (se ejecuta en el Modo H).
- **Hallazgo — F13 e IDS01:** F13 no lista a IDS01 ni a FW01 como origen, pero DET-02 exige que sus alertas lleguen a Wazuh. En el laboratorio IDS01 y SIEM01 están en la misma VLAN y no cruzan FW01.
- **Entorno (no es del diseño).** Con Docker Desktop y su integración de WSL, `/var/run/docker.sock` pasa a ser el de Docker Desktop y containerlab no funciona. `lab/docker-nativo.sh` (root, una vez) agrega un socket al `dockerd` de la distribución y `lab/docker-env.sh` lo usa solo cuando detecta Docker Desktop. La red de gestión de containerlab pasó a 172.30.250.0/24 porque 172.20.20.0/24 chocaba con otras redes de Docker.
- **Decide:** equipo del proyecto
- **Resolución:** Laboratorio ampliado en `infra/gen/lab.py`, `lab/`, `siem/wazuh/local_rules.xml` y `tests/network/casos.py`; lo retirado en la v0.4 (NAS01, IDS01, WAF01, WEB01…) quedó fuera por CI-39.

### CI-29 — Flujo F27: MGMT → Internet por TCP 443 para actualizaciones (resuelve CI-05)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** decisión de transcripción (ampliación de D1.11)
- **Dónde:** `infra/inventory.yaml` (flujo F27 y celda MGMT → INTERNET), `infra/pruebas.yaml` (T35), `infra/validate.py` (V-14)
- **Qué decía el documento:** la matriz D1.8 permite MGMT → Internet por TCP 443 (actualizaciones), pero D1.11 no tiene ningún flujo para eso. El firewall de laboratorio, que solo abre lo que declaran los flujos, lo denegaba y T35 fallaba.
- **Qué se hizo:** se agregó F27 (JMP01 → Internet, TCP 443, TLS, registro de FW01, FIG-5.5b, OD-06) con `ampliacion: true`. D1.11 sigue siendo F1–F26; V-14 exige que todo flujo extra lleve `ampliacion` y un CI.
- **Supuesto [S-19]:** D1.8 no lista los destinos. Hasta que la DTI entregue los repositorios de actualización de ESXi, OPNsense y NAS01, F27 queda abierto a cualquier servidor TCP 443 (riesgo residual medio, anotado en el flujo).
- **Propuesta:** aceptar F27 y reemplazar el destino por la lista de repositorios cuando exista.
- **Decide:** equipo del proyecto
- **Resolución:** F27 (JMP01 → Internet, TCP 443) en `infra/inventory.yaml`, con T35 y el supuesto S-19.

### CI-30 — Capas de defensa en profundidad y salto de la ruta por defecto, fuera de la fuente única (P3)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** vacío
- **Dónde:** FIG-5.3 (franja «Defensa en profundidad») y FIG-5.2 (nota «Ruteo»); `infra/gen/drawio.py` (`CAPAS_D19`)
- **Qué falta:**
  1. La tabla de nueve capas de D1.9 (perímetro, zona, capa 2, host, aplicación, datos en tránsito, detección, respuesta,
     recuperación) no está en `infra/*.yaml`. FIG-5.3 la necesita; se transcribió en `CAPAS_D19` con la marca CI-30 en la
     figura, sin IP ni puertos nuevos.
  2. La ruta por defecto 0.0.0.0/0 de FW01 sale por la WAN 203.0.113.10, pero el salto siguiente del ISP no está definido.
     FIG-5.2 lo rotula «salto del ISP no definido: CI-30»; no se inventó una IP.
- **Propuesta:** añadir a `trazabilidad.yaml` una lista `defensa_profundidad` (capa, controles, componentes) y a
  `inventory.yaml` el campo `vpn`/`ruteo.salto_isp` (IP de documentación RFC 5737 hasta tener el dato de la DTI [S-xx]).
  Al hacerlo, `drawio.py` debe leerlos de `Infra` y borrar `CAPAS_D19`.
- **Decide:** equipo del proyecto (capas) y DTI (salto del ISP)
- **Resolución:** (1) Las capas de D1.9 v0.4 están en `trazabilidad.yaml → defensa_profundidad` (CI-63). (2) El salto de la ruta por defecto ya está definido: FW01 sale por la red de tránsito hacia FGT-EXT 10.20.0.1 (CI-37). `infra/gen/drawio.py` conserva `CAPAS_D19` (v0.2) y la nota «salto del ISP» hasta regenerar los diagramas (I4), que deben leer el YAML.

### CI-31 — Prefijo on-premise: /16 anunciado frente a /14 en las tablas de rutas de la VPC (P3)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** contradicción
- **Dónde:** `inventory.yaml` → `vpn.extremo_onpremise.redes_anunciadas` (10.20.0.0/16) y `redes_anunciadas_futuro`
  (10.20.0.0/14) frente al `aporta` de AWS-PUB-A y AWS-APP-A (rt-public y rt-private: «10.20.0.0/14 → VGW»). Se ve en FIG-5.4.
- **Qué dice cada fuente:** FW01 anuncia hoy por BGP solo el /16; el `por_que` de VGW dice que «aprende 10.20.0.0/14» y
  las tablas de la VPC lo citan como ruta propagada. El /14 es la reserva `CAMPUS-RESUMEN` (agrega las sedes), que según
  `redes_anunciadas_futuro` se anunciará más adelante. No rompe el ruteo actual (el /16 está dentro del /14), pero el texto
  describe como presente una ruta que hoy no se anuncia.
- **Propuesta:** que VGW, AWS-PUB-A y AWS-APP-A digan «10.20.0.0/16 (10.20.0.0/14 cuando se anuncie el resumen)», o anunciar ya el /14.
  Al resolverlo, quitar la observación de FIG-5.4 (`fig_5_4` en `infra/gen/drawio.py`).
- **Decide:** equipo del proyecto
- **Resolución:** `inventory.yaml` anuncia 10.20.0.0/16 (VGW, AWS-PUB-A y AWS-APP-A); el /14 queda solo en `redes_anunciadas_futuro`. La «Observación CI-31» de FIG-5.4 está en `infra/gen/drawio.py` y se quita al regenerar los diagramas (I4).

### CI-32 — Textos de componentes sin dato verificable (P4, V-66)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** texto genérico
- **Dónde:** `infra/inventory.yaml` → `componentes[].por_que | aporta | si_falla`. Lo detecta V-66 (advertencia): el texto no cita
  ningún ID, flujo, zona, IP, puerto ni cifra. La matriz XLSX copia el texto del inventario tal cual; no se corrige en el artefacto.
- **Propuesta** (solo con datos que ya están en `infra/*.yaml`; aplicar en el YAML por PR revisado por el responsable de P0):

| Componente | Campo | Texto propuesto |
|---|---|---|
| CTRL01 | por_que | Enrola EDGE01 y EDGE02 por TCP 8443 (F10), distribuye bundles firmados y emite las CA intermedias por nodo; sin él los nodos conservan su última configuración firmada. |
| OBS01 | si_falla | Se pierden las trazas OTLP (F11, TCP 4317/4318) y el scraping de métricas (F12, TCP 9128/9100), no el servicio. Mitigación: los registros de acceso de Celeris y SIEM01 (F13) siguen disponibles. |
| HNY01 | si_falla | Se pierde la detección de fuerza bruta por señuelo SSH/Telnet (F24, DET-04); DMZ-SVC y el resto de la red no se afectan porque HNY01 vive en la VLAN 41 (D-16). |
| PROBE01 | si_falla | Se pierde la medición de disponibilidad de REQ-NF-03 (≥ 99,5 %) desde la VLAN 30, no el servicio. |
| KALI01 | si_falla | No hay generador de ataques para las pruebas desde la VLAN 31 (LAB-TEST); la red de producción no se afecta. |
| EC2-CTRLR | por_que | Mantiene una réplica en espera de PostgreSQL (F16: el standby se conecta a DB01 por TCP 5432, TLS en IPsec) y la API del plano de control, con RPO 15 min, para continuidad si se pierde el servidor del campus. |
| AWS-PUB-A | si_falla | NAT01 queda sin subred: AWS-APP-A y AWS-APP-B pierden la salida a Internet (rt-private 0.0.0.0/0 → NAT01) y SSM. |
| AWS-PUB-B | por_que | Reserva 10.30.1.0/24 en la AZ b para un segundo NAT si se quiere salida redundante (hoy NAT01 solo está en AWS-PUB-A). |
| AWS-PUB-B | aporta | Sin recursos en esta fase; deja reservado el /24 de la AZ b para no renumerar la VPC 10.30.0.0/16. |
| AWS-PUB-B | si_falla | Sin impacto: no aloja recursos y ningún flujo F-nn la usa. |
| AWS-APP-B | aporta | Subred privada 10.30.11.0/24 (AZ b) de EC2-CTRLR, con las mismas rutas que AWS-APP-A (rt-private: 0.0.0.0/0 → NAT01, prefijo del campus → VGW; ver CI-25). |
| AWS-DATA-A | por_que | Reserva 10.30.20.0/24 (AZ a) para una base de datos gestionada si el plano de control crece más allá de DB01 + EC2-CTRLR. |
| AWS-DATA-A | aporta | Sin recursos en esta fase; reserva el rango para no renumerar la VPC 10.30.0.0/16. |
| AWS-DATA-A | si_falla | Sin impacto: no aloja recursos y ningún flujo F-nn la usa. |
| AWS-DATA-B | por_que | Reserva 10.30.21.0/24 (AZ b) para la segunda zona de disponibilidad de esa base gestionada (alta disponibilidad). |
| AWS-DATA-B | aporta | Sin recursos en esta fase; reserva el rango para no renumerar la VPC 10.30.0.0/16. |
| AWS-DATA-B | si_falla | Sin impacto: no aloja recursos y ningún flujo F-nn la usa. |

- **Efecto al resolver:** V-66 pasa sin advertencias; `make matrices` regenera la matriz con los textos nuevos.
- **Decide:** responsable de P0 (dueño de `infra/inventory.yaml`) y equipo del proyecto
- **Resolución:** Los textos de `por_que`, `aporta` y `si_falla` de `inventory.yaml` de los componentes vigentes citan ID, IP, flujo, zona, prueba o cifra (la heurística de V-66, que corre con la matriz de componentes en I5, no encuentra ninguno sin dato). Se reescribieron los 9 que no lo hacían: FGT-EXT (2), PORTAL01 (2), HNY01, KALI01, WIFI-EST, AWS-APP-A y EC2-DR; los demás componentes de la tabla propuesta se retiraron en la v0.4.

### CI-33 — Publicación del portal: CTRL01 → WEB01 sin flujo en el inventario (CE02 E1, sección 4)
- **Estado:** resuelto (2026-11-23, obsoleto por v0.4: CI-35…43)
- **Tipo:** contradicción
- **Dónde:** documento maestro C3.1 («CE publica política vigente → PT»), C3.2 (`celeris-control`: «generación del portal»;
  diagrama «C publica sitio firmado → PT») y C4.3 (`CP->>PT: publicar aviso v42 firmado`); C4.7 `POST /v1/portal/publish`.
  En `infra/inventory.yaml`: WEB01 solo atiende TCP 8080 desde WAF01 (F22) y su `aporta` no menciona a CTRL01; JMP01
  (10.20.10.20) «despliega el sitio de WEB01 por SSH» dentro de F20 (TCP 22).
- **Qué dice cada fuente:** el maestro da por hecho que CTRL01 empuja el sitio firmado al portal; el inventario no tiene
  ningún flujo CTRL01 → WEB01 (ni CTRL01 → DMZ-SVC) y asigna el despliegue a JMP01.
- **Propuesta:** mantener el inventario (menor superficie: SERVERS no abre conexiones hacia DMZ-SVC). `celeris-control`
  genera y firma el sitio estático (REQ-F-30) y lo deja como artefacto; JMP01 lo descarga y lo despliega en WEB01 por SSH
  (F20) tras verificar la firma. Alternativa: agregar un flujo F-nn CTRL01 → WEB01 TCP 22 con su regla, prueba y riesgo.
  Los diagramas de CE02 (DS-03, DS-07 en `docs/software/e1/diagramas/`) muestran la propuesta y citan esta entrada.
- **Decide:** responsable de P0 (dueño de `infra/inventory.yaml`) y equipo de software (CE02)
- **Efecto al resolver:** si se adopta la propuesta, corregir C3.1, C3.2 y C4.3 del maestro; si se adopta la alternativa,
  agregar el flujo a `infra/inventory.yaml` (y su T-nn) y quitar la nota de los diagramas.
- **Resolución:** WEB01 se retiró (CI-39). La consola genera el sitio estático del portal y FW01 lo entrega a PORTAL01; el certificado, por SFTP (F33, CI-52).

### CI-34 — Supuestos nuevos del diseño detallado de software: S-20 y S-21 (CE02 E1, sección 4)
- **Estado:** diferido (2026-11-23, CE02/CE0331)
- **Tipo:** supuesto nuevo
- **Dónde:** documento maestro C4.3 («error < umbral», sin valor) y C4.5 («CSR aprobado», sin decir cómo se autentica el
  primer contacto del nodo); `infra/trazabilidad.yaml` → `supuestos` llega hasta S-19 tras integrar.
- **Qué dice cada fuente:** el maestro usa un umbral de errores para ampliar o revertir el rollout y un enrolamiento con mTLS,
  pero no fija el valor del umbral ni el mecanismo de arranque de confianza del nodo.
- **Propuesta:** registrar en `supuestos` de `infra/trazabilidad.yaml`:
  - S-20 — El nodo se enrola con un token de un solo uso, de vigencia corta, entregado fuera de banda; valor de la vigencia
    por definir con la prueba de enrolamiento de S2. Responsable: equipo de software.
  - S-21 — Umbral de errores del rollout por nodo (porcentaje de respuestas 5xx o de heartbeats perdidos); valor por
    definir con la línea base de métricas de S2. Responsable: equipo de software.
  Mientras tanto, los diagramas DS-07, DS-08, DS-10, DS-11 y DS-12 los citan como [S-20] y [S-21] y
  `docs/software/e1/diagramas/README.md` los lista en «Supuestos nuevos».
- **Decide:** equipo del proyecto
- **Nota de integración (v0.4):** en CE02 se llamaban S-16 y S-17; esos números los usan otros supuestos de `infra/trazabilidad.yaml` (matriz de pruebas), así que se renumeraron a S-20 y S-21.
- **Efecto al resolver:** agregar S-20 y S-21 a `infra/trazabilidad.yaml` y quitarlos de la tabla del README.

## Entradas de la v0.4 (I1)

> **Numeración.** CE03 D7 registra estos cambios como CI-30…CI-38, pero la integración de ramas (I0) ya ocupó CI-30…CI-34. Aquí llevan
> CI-35…CI-43 (D7 + 5, en el mismo orden). Los documentos de `docs/celeris/` y el Marco común (M6: «CI-01…CI-38») usan la numeración de D7;
> la equivalencia está en cada título. Lo retirado conserva su ID con `estado: retirado` y `retirado_por` y nunca se reutiliza (V-44).
- **Resolución:** S-20 y S-21 son supuestos del diseño detallado de software: los registra CE02 en su entrega. No cambian el inventario de red.

### CI-35 — Consola (SPA + API + PostgreSQL) en CTRL01; se retiran DB01 y F15 (D7 CI-30)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** decisión de transcripción
- **Contexto:** En la v0.2 la base del plano de control vivía en DB01 (F15) y se replicaba a AWS (F16).
- **Cambio:** CTRL01 aloja SPA + API + PostgreSQL local por socket (sin puerto en la red), 2 vCPU, 8 GB, 100 GB. DB01 y F15 pasan a `retirado`.
- **Motivo:** Una base pequeña no justifica otra VM; la consola completa en el campus evita que el nodo dependa de Internet y deja la llave de firma y los datos dentro (Arquitectura §1.1 y §5).
- **ADR:** D-25
- **Archivos afectados:** `infra/inventory.yaml` (CTRL01, DB01, F15), `infra/pruebas.yaml`, `infra/trazabilidad.yaml`
- **Decide:** equipo del proyecto

### CI-36 — EC2-GW (10.30.0.10), F29, F30 y sg-gw; se retiran EC2-SHIELD, EC2-CTRLR, NAT01, F9, F16 y las subredes pub-b, app-b, data-a y data-b (D7 CI-31)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** decisión de transcripción
- **Contexto:** La v0.2 tenía un shield de caché y una réplica de la consola en AWS, con NAT permanente.
- **Cambio:** Nuevos EC2-GW (t3.micro, pub-a), S3 `celeris-backups` (Object Lock 30 días), EC2-DR y NAT-DR (estado `temporal`, simulacro T59), F29 (Internet → EC2-GW:443) y F30 (EC2-GW → CTRL01:443 por IPsec con mTLS), sg-gw y sg-dr. Quedan en AWS solo la VPC, pub-a y app-a. Las tablas de rutas citan 10.20.0.0/16 (D2.5), con lo que los textos de VGW y de las subredes ya no describen el /14 que observaba CI-31.
- **Motivo:** Un segundo nivel de caché en AWS no ahorra enlace del campus (D-19); la continuidad por respaldo en S3 basta para un RTO de 2 h; el panel remoto entra por AWS sin publicar ningún puerto del campus (D-24).
- **ADR:** D-24, D-19
- **Archivos afectados:** `infra/inventory.yaml` (componentes AWS, F9, F16, F29, F30, bloque `aws`, `vpn`), `infra/pruebas.yaml` (T01–T05, T21, T26, T58, T59)
- **Decide:** equipo del proyecto

### CI-37 — FW01 detrás del FortiGate: FGT-EXT, tránsito 10.20.0.0/29 y NAT-T (D7 CI-32)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** decisión de transcripción
- **Contexto:** La v0.2 daba a FW01 la IP pública 203.0.113.10 en su WAN.
- **Cambio:** Nuevo componente FGT-EXT (existente, fuera de alcance; público 203.0.113.10 y tránsito 10.20.0.1) y nueva zona TRANSITO (10.20.0.0/29). La WAN de FW01 pasa a 10.20.0.2. `vpn` agrega `nat_t: true`, `ip_publica_en: FGT-EXT` e `identidad_ike` (la IP pública). El FortiGate hace NAT 1:1 hacia 10.20.0.2 solo para UDP 500/4500 y TCP 80/443 y excluye a EDGE01/02 de su inspección SSL [S-29].
- **Motivo:** Respeta lo que la DTI ya opera: FortiGuard sigue filtrando la salida de los nodos; depende de cambios mínimos en el FortiGate (RE-11).
- **ADR:** D-26
- **Archivos afectados:** `infra/inventory.yaml` (zonas, FGT-EXT, FW01, `vpn`), `infra/trazabilidad.yaml` (S-29)
- **Decide:** equipo del proyecto

### CI-38 — Zona WIFI-EST (172.16.0.0/16, provisional), F31, F32, T56 y T57 (D7 CI-33)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** decisión de transcripción
- **Contexto:** El diseño no incluía el Wi-Fi de estudiantes (BYOD).
- **Cambio:** Nueva zona externa WIFI-EST (`supuesto: S-28`, color #F0E442) y componente-grupo WIFI-EST. F31 (WIFI-EST → EDGE01/02, TCP 3128 y 80, siempre passthrough) y F32 (→ PORTAL01:443). V-07 admite su red fuera de 10.20.0.0/16 y V-45 exige que ningún flujo con origen WIFI-EST permita descifrado (REQ-F-36).
- **Motivo:** Privacidad: los equipos personales nunca se descifran y no alcanzan servidores ni laboratorios; el ahorro en BYOD es bajo y se declara.
- **ADR:** D-27
- **Archivos afectados:** `infra/inventory.yaml`, `infra/pruebas.yaml` (T56, T57), `infra/validate.py` (V-07, V-45)
- **Decide:** equipo del proyecto

### CI-39 — Simplificación: se retiran SVC01, OBS01, IDS01, PROBE01, NAS01, WAF01, WEB01, ESX01 vmk1, VLAN 31, 70 y 71, F11, F12, F17, F19 y F22 (D7 CI-34)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** decisión de transcripción
- **Contexto:** La v0.2 tenía 10 VLAN y 17 VM en la fase F1.
- **Cambio:** Quedan 7 VLAN (10, 20, 30, 40, 41, 50, 60). WAF01 + WEB01 pasan a PORTAL01 (10.20.40.10). DNS y NTP en FW01 (F2 con destino FW01; F25 con origen FW01); el PAC lo sirven EDGE01 y EDGE02. LAB-TEST, STORAGE y BACKUP pasan a `retirado`. DET-02 pasa a Suricata de FW01. OD-04 cambia de meta. El UPS apaga por NUT desde JMP01 (CI-09 sigue abierto: el flujo NUT no tiene puerto).
- **Motivo:** 7 VM menos en la fase F1 (34 → 23 vCPU) sin perder criterios de la rúbrica: siguen habiendo IDS/IPS (Suricata en FW01), honeypot (HNY01, HNY02) y un servicio publicado detrás de un WAF.
- **ADR:** D-28
- **Archivos afectados:** `infra/inventory.yaml`, `infra/pruebas.yaml`, `infra/trazabilidad.yaml`; resuelve CI-03 y CI-04
- **Decide:** equipo del proyecto

### CI-40 — ENC01 (10.20.35.10) y F28; LABCLI01 y KALI01 al rango de infraestructura; rangos /26 de laboratorio (D7 CI-35)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** decisión de transcripción
- **Contexto:** Los laboratorios no tenían rangos propios y KALI01 vivía en la VLAN 31.
- **Cambio:** ENC01 10.20.35.10 (F28 → CTRL01:443), LABCLI01 → 10.20.35.50, KALI01 → 10.20.35.60 (zona LAB), HNY02 en 10.20.35.250. Nuevo bloque `rangos_lab`: LAB-01…LAB-10 (/26 desde 10.20.32.0), reserva 10.20.34.128/25 e infraestructura 10.20.35.0/24, con `habilitado`. Componente-grupo PCS-LAB.
- **Motivo:** El encargado habilita accesos por laboratorio sin rediseñar la capa de acceso (REQ-F-10, F-32, OD-11); ENC01 queda fuera de MGMT para no recibir acceso de administración.
- **ADR:** D-23
- **Archivos afectados:** `infra/inventory.yaml` (`rangos_lab`, ENC01, PCS-LAB, LABCLI01, KALI01), `infra/pruebas.yaml` (T52)
- **Decide:** equipo del proyecto

### CI-41 — Pruebas: se retiran T12, T22, T37, T38, T39, T41, T44 y T48; se agregan T50–T60; cambian de destino T01, T02, T20, T21, T29, T42 y T46 (D7 CI-36)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** decisión de transcripción
- **Contexto:** Varias pruebas apuntaban a piezas retiradas (STORAGE, SVC01, OTLP, base en red, NAS, NFS, peering).
- **Cambio:** Las ocho pruebas quedan con `estado: retirado` y `retirado_por`. T50–T60 llevan `ampliacion: true`. T26 (privacidad) pasa a medir F8 (la petición saliente al origen) y deja de ser prueba de la VPN. T27 pasa a cubrir F20, F28 y F30. T56 es crítica por decisión del equipo (2026-11-22): un FALLA descifraría un equipo personal (REQ-F-36); es la única excepción a la regla de criticidad de CI-26. Los IDs no se reutilizan.
- **Motivo:** Cobertura de las funciones nuevas (precarga, firma de configuración, acceso por laboratorio, panel remoto, BYOD, simulacro de recuperación, WPAD).
- **ADR:** —
- **Archivos afectados:** `infra/pruebas.yaml`, `infra/trazabilidad.yaml` (rúbrica R2–R8)
- **Decide:** equipo del proyecto

### CI-42 — Supuestos S-26…S-30 (D7 CI-37)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** supuesto nuevo
- **Contexto:** Marco común M5: los S-16…S-19 y S-25 ya tenían uso en el repositorio.
- **Cambio:** S-26 (10 laboratorios × 40 PCs), S-27 (3 GB por PC), S-28 (Wi-Fi de la DTI), S-29 (FortiGate) y S-30 (IAM de solo escritura para respaldos). Los S-20 y S-21 de CE02 (token de enrolamiento y umbral del rollout) siguen sin registrarse en `trazabilidad.yaml` (CI-34).
- **Motivo:** Todo supuesto se declara [S-xx]; los que no se validan se declaran como limitación en el informe.
- **ADR:** —
- **Archivos afectados:** `infra/trazabilidad.yaml` (`supuestos`)
- **Decide:** equipo del proyecto

### CI-43 — Trazabilidad: OD-11, OD-12, AM-14…AM-18, DET-10, DET-11; OD-04, OD-08 y DET-02 ajustados; AM-01, AM-02 y AM-11 con pruebas nuevas (D7 CI-38)
- **Estado:** resuelto (2026-11-22, I1)
- **Tipo:** decisión de transcripción
- **Contexto:** La trazabilidad describía la v0.2.
- **Cambio:** OD-11 (acceso por laboratorio, 10 de 10) y OD-12 (0 puertos del campus alcanzan CTRL01 desde Internet). AM-01 → T13, T52; AM-02 → T60; AM-11 → T06, T34, T57; AM-14…AM-18 nuevas. DET-10 (auditoría de la consola) y DET-11 (Coraza de EC2-GW). Se agregan D-24…D-28 y los requisitos REQ-F-31…37, REQ-NF-16 y REQ-RN-09…11 del contrato de IDs (Marco M6). OD-08 incluye ahora la calificación TLS de EC2-GW (D1.6 v0.4), cambio que D7 no lista. Las evidencias de la rúbrica se derivan de `criterios_rubrica` (V-21).
- **Motivo:** Mantener la trazabilidad bidireccional entre pruebas, amenazas, detecciones y rúbrica.
- **ADR:** D-23…D-28
- **Archivos afectados:** `infra/trazabilidad.yaml`, `infra/pruebas.yaml`
- **Decide:** equipo del proyecto

### CI-44 — F20: D1.11 v0.4 lista solo TCP 22 y 443, pero el nodo se administra por 9128
- **Estado:** resuelto (2026-11-22, decisión del equipo: F20 agrega TCP 9128 (administración del nodo))
- **Tipo:** contradicción
- **Contexto:** CE03 D1.11 y la Arquitectura §7 dan F20 = TCP 22, 443. El repositorio usaba 22, 443, 3000, 5601 y 9128; T27 verifica el puerto 9128 (REQ-NF-14) y `e2e/` usa 9128. El dashboard de Wazuh escucha en 5601 si no se pone detrás de 443.
- **Cambio:** F20 transcribe solo TCP 22 y 443 (D1.11 v0.4) y queda `pendiente: true`. T27 describe la sesión a 9128 y lo marca en su precondición.
- **Motivo:** No se elige en silencio: con 22/443 el firewall del laboratorio no abre 9128 desde JMP01 y la administración del nodo por su puerto actual no tendría flujo.
- **ADR:** —
- **Archivos afectados:** `infra/inventory.yaml` (F20), `infra/pruebas.yaml` (T27)
- **Decide:** equipo del proyecto
- **Propuesta:** agregar 9128 (administración del nodo, REQ-NF-14) a F20 o mover la administración al 443; confirmar si el dashboard de Wazuh va por 443 o 5601.
- **Efecto al resolver:** corregir `protocolos` y `regla_fw` de F20 y quitar `pendiente`.

### CI-45 — La matriz D1.8 v0.4 no tiene columna WIFI-EST
- **Estado:** resuelto (2026-11-22, decisión del equipo: se acepta «denegado» para la columna WIFI-EST)
- **Tipo:** vacío
- **Contexto:** D1.8 y la Arquitectura §6.3 incluyen WIFI-EST solo como fila (origen); ninguna celda dice qué pasa hacia el Wi-Fi.
- **Cambio:** Para que V-12 pueda comprobar una matriz completa, `matriz_esperada` agrega la columna WIFI-EST con «denegado» (FW01 no enruta hacia el Wi-Fi) y «no_aplica» desde Internet; todas esas celdas llevan `pendiente: true`.
- **Motivo:** No hay flujo F-nn hacia WIFI-EST; el retorno de F31 y F32 lo cubre el firewall con estado.
- **ADR:** —
- **Archivos afectados:** `infra/inventory.yaml` (`matriz_esperada`)
- **Decide:** equipo del proyecto
- **Propuesta:** agregar la columna a D1.8 con ✖ en todas las filas salvo Internet (—).
- **Efecto al resolver:** quitar `pendiente` de las celdas.

### CI-46 — nacl-private (D2.5): «puertos de servicio» sin definir
- **Estado:** resuelto (2026-11-22, decisión del equipo: nacl-private: entrada TCP 443 desde pub-a y efímeros de retorno; salida TCP 443 y efímeros; sin SSH)
- **Tipo:** vacío
- **Contexto:** D2.5: «Permitir 10.20.0.0/16 y 10.30.0.0/16 en puertos de servicio y retorno efímero; denegar el resto». Con app-a vacía en operación normal, no hay servicio que abrir.
- **Cambio:** El bloque `aws.nacl` conserva las reglas con `puertos: servicio` y `pendiente: true`; no se inventa un puerto.
- **Motivo:** La IaC (I3) necesita puertos concretos para el simulacro T59 (HTTPS hacia S3 y retorno efímero).
- **ADR:** —
- **Archivos afectados:** `infra/inventory.yaml` (`aws.nacl`)
- **Decide:** equipo del proyecto
- **Propuesta:** fijar la lista (por ejemplo TCP 443) en D2.5 para el simulacro.
- **Efecto al resolver:** reemplazar `puertos: servicio` en nacl-private y quitar `pendiente`.

### CI-47 — F2 «zonas internas» incluye DMZ-HONEY, que D1.9 limita a enviar al SIEM
- **Estado:** resuelto (2026-11-22, decisión del equipo: F2 excluye DMZ-HONEY)
- **Tipo:** contradicción
- **Contexto:** D1.11 y la Arquitectura §7: F2 = «Zonas internas → FW01». D1.9: DMZ-HONEY «Solo envía al SIEM» y el honeypot no tiene salida.
- **Cambio:** F2 lista todas las zonas internas (MGMT, SERVERS, LAB, DMZ-SVC, DMZ-HONEY, SECURITY, EDGE) como origen y FW01 como destino; no cambia la matriz zona × zona.
- **Motivo:** Transcripción literal de «zonas internas»; el DNS de HNY01 contradice «sin salida».
- **ADR:** —
- **Archivos afectados:** `infra/inventory.yaml` (F2)
- **Decide:** equipo del proyecto
- **Propuesta:** quitar DMZ-HONEY del origen de F2.
- **Efecto al resolver:** corregir `origen` y `regla_fw` de F2 y quitar `pendiente`.

### CI-48 — Laboratorio emulado v0.4: parámetros del laboratorio y equivalencias (I2)
- **Estado:** resuelto (2026-11-23, aplicado)
- **Tipo:** decisión de transcripción
- **Dónde:** `infra/gen/lab.py` (`PARAMETROS_LAB`, `NODOS`, `CLIENTES_LAB`), `lab/celeris.clab.yml`
- **Parámetros que el inventario no fija y el laboratorio necesita (solo Modo L, nada cambia el diseño):**
  1. IP pública del FortiGate en el laboratorio: `198.51.100.10` sustituye a 203.0.113.10 (F4.1); `ext01` 198.51.100.100; `origin-sim` 198.51.100.110; IP pública de EC2-GW 198.51.100.30; extremos AWS 198.51.100.21 y .22.
  2. `vgw-sim` toma 10.30.0.1 dentro de pub-a (junto a EC2-GW 10.30.0.10); la VPC real no tiene ese equipo.
  3. Wi-Fi: `fgt-sim` 172.16.0.1 y `byod01` 172.16.0.50 dentro de 172.16.0.0/16 [S-28].
  4. PC de prueba: `labcli02` 10.20.32.2 (LAB-01, control positivo de T52) y `labcli03` 10.20.32.130 (LAB-03, el laboratorio que T52 deshabilita). LABCLI01 sigue en 10.20.35.50 (rango de infraestructura).
  5. Nombres de prueba: `descargas.example.com` (origin-sim, T55) y `panel.celeris.internal` (EC2-GW).
- **Equivalencias distintas de D5.3:** `gw-sim` y `portal01` son nginx + ModSecurity + OWASP CRS, no Caddy + Coraza (la imagen base no los trae). `fgt-sim` no emula FortiGuard ni la inspección SSL, de modo que la exclusión de EDGE01/02 [S-29] no se puede probar en el Modo L. No hay sincronización NTS hacia arriba.
- **Propuesta:** dar por buenos los parámetros 1–5 para el laboratorio; construir una imagen con Caddy + Coraza si el equipo quiere «mismo producto» en gw-sim.
- **Decide:** equipo del proyecto
- **Resolución:** Parámetros del laboratorio v0.4 en `infra/gen/lab.py` (`PARAMETROS_LAB`, `NODOS`, `CLIENTES_LAB`) y `lab/celeris.clab.yml`; equivalencias de D5.3 en `emulacion_lab` de cada componente.

### CI-49 — F24: el señuelo necesita que el FortiGate publique TCP 22 y 23
- **Estado:** resuelto (2026-11-23, ver CI-60)
- **Tipo:** contradicción
- **Dónde:** CE03 D1.8 («Posición frente al FortiGate»), D1.11 (F24), S-29; `infra/inventory.yaml` (F24); T11
- **Qué dice cada fuente:** D1.8 y S-29: el FortiGate hace NAT 1:1 hacia FW01 «solo» para UDP 500/4500 y TCP 80/443. D1.11 F24: Internet → HNY01 por TCP 22 (→ 2222) y 23, con autorización de la DTI y una ventana.
- **Qué se hizo:** en el Modo L, T11 abre en `fgt-sim` una cadena `ventana` con TCP 22 y 23 mientras dura la prueba y la vacía después. F24 queda `pendiente: true`.
- **Propuesta:** decir en D1.8 y en el pedido a la DTI que la ventana del señuelo incluye un cambio temporal en el FortiGate (22 y 23 hacia 10.20.0.2), o publicar el honeypot por otros puertos.
- **Decide:** equipo del proyecto y DTI
- **Resolución:** El pedido a la DTI (S-29) incluye TCP 22 y 23 hacia HNY01; si la DTI lo niega, HNY01 solo ve tráfico interno. Registrado en D1.8 y en S-29. Detalle en CI-60.

### CI-50 — F23: la salida del portal no está limitada a los endpoints ACME
- **Estado:** resuelto (2026-11-23, opción A; ver CI-52)
- **Tipo:** vacío
- **Dónde:** CE03 D1.9 (DMZ-SVC, «Salida: solo ACME y el agente Wazuh»), D1.11 (F23), T19; `infra/inventory.yaml` (F23)
- **Qué dice cada fuente:** F23 es PORTAL01 → Internet TCP 443 «solo hacia los endpoints ACME», pero el flujo se transcribe por zona y puerto: FW01 permite 443 hacia cualquier destino. T19 («Salida del portal: curl https://example.com, Denegado») no se cumple con esa regla.
- **Qué se hizo:** T19 mide el hallazgo (control positivo: el endpoint ACME de laboratorio; prueba: otro destino) y F23 queda `pendiente: true`.
- **Propuesta:** limitar el destino con un alias de FW01 por FQDN (los endpoints de la CA elegida) o con una lista de IP del FortiGate; sin eso, T19 falla por diseño.
- **Decide:** equipo del proyecto
- **Resolución:** se elige la opción A: el portal no sale a la WAN. F23 se retira (CI-52) y T19 pasa a «PORTAL01 no establece conexiones hacia la WAN». `pendiente` queda en `false`: se quita de F23.

### CI-51 — Memoria para servir un objeto grande a muchos clientes a la vez
- **Estado:** diferido (2026-11-23, CE02/CE0331)
- **Tipo:** vacío
- **Dónde:** CE03 D2.4 (EDGE01: 8 GB de RAM), D2.8 (dimensionamiento), `max_buffered_bytes` del nodo, T55
- **Qué se midió:** con el valor por defecto (512 MiB), 20 clientes simultáneos de un objeto de 100 MB obtuvieron 5 HIT y 15 pasaron por el origen (sobre presupuesto): el nodo reserva el tamaño del objeto por cada cliente servido desde memoria. Con 3 GiB, T55 da 1 descarga en el origen y 19 HIT.
- **Qué se hizo:** el laboratorio fija `max_buffered_bytes = 3 GiB`, `max_object_bytes = 200 MiB` y `coalesce_wait_secs = 30` en los nodos EDGE (CI-48); no cambia el diseño.
- **Propuesta:** dimensionar la RAM de EDGE01/02 para N clientes × el instalador más grande (S-27: 3 GB por PC en una actualización masiva) o servir los objetos grandes desde disco sin reservar memoria por cliente. Es trabajo de CE02.
- **Decide:** equipo de software (CE02) y equipo del proyecto
- **Resolución:** Dimensionar la RAM de EDGE01/02 o servir objetos grandes desde disco es trabajo de CE02 (S2); el laboratorio usa `max_buffered_bytes` = 3 GiB.

### CI-52 — F23 retirado; F33 (FW01 → PORTAL01, SFTP) entrega el certificado del portal
- **Estado:** resuelto (2026-11-23)
- **Tipo:** decisión de diseño (resuelve CI-50, opción A)
- **Dónde:** CE03 D1.8 (matriz: DMZ-SVC → Internet), D1.9 (DMZ-SVC, «Salida»), D1.11 (F23, F33), D1.16 (T19, T49); `infra/inventory.yaml` (F23, F33, PORTAL01, FW01, `matriz_esperada`); `infra/pruebas.yaml` (T19, T49, T46); `infra/trazabilidad.yaml` (D-29, S-31)
- **Qué cambia:**
  - **F23** (PORTAL01 → Internet, TCP 443) pasa a `estado: retirado` (`retirado_por: CI-52`); su ID no se reutiliza.
  - **F33** nuevo: FW01 → PORTAL01, TCP 22, «despliegue del certificado del portal por SFTP (ACME en FW01)». Control: llave dedicada y usuario chroot en la carpeta del certificado. Nace en FW01 (local al firewall, como F14), por eso no figura en la matriz zona × zona.
  - **Matriz D1.8:** DMZ-SVC → Internet pasa de ✔ F23 a ✖; se agrega la nota de F33 (FW01 → DMZ-SVC).
  - **T19** = «PORTAL01 no establece conexiones hacia la WAN (TCP/UDP)»; criterio: 0 conexiones establecidas en los contadores de FW01; sigue crítica. En el Modo H agrega un paso: la renovación ACME desde FW01 llega a PORTAL01 por F33.
  - **T49** = entrega del certificado por F33: en el Modo L solo se comprueba que F33 abre (no hay Internet, no se emula ACME).
  - **D-29** (decisión) y **S-31** (el FortiGate deja a FW01 llegar a la CA por 443 y 80; supuesto a confirmar con la DTI).
- **Efecto sobre el laboratorio:** `fw01-sim` genera la regla de F33 y ninguna regla permite a PORTAL01 salir a la WAN; `portal01` abre TCP 22 como emulación del SFTP (solo el puerto; sin ACME ni chroot real, CI-48).
- **Decide:** equipo del proyecto

### CI-53 — Demo de OpenTofu solo contra el AWS Emulator
- **Estado:** resuelto (2026-11-23, indicado en el prompt I3-DEMO)
- **Tipo:** decisión de transcripción
- **Dónde:** `deploy/opentofu/` (envs/demo y módulos aws-vpc, aws-vpn, aws-gw, aws-backup); `infra/gen/tofu.py`; CE03 D2.5 y D5.4
- **Qué se hizo:**
  - **AWS emulado: plano de control, sin tráfico.** El proveedor apunta al AWS Emulator oficial (`github.com/aws/aws-emulator`) en Docker, en `https://127.0.0.1:9297`, con credenciales ficticias y `skip_credentials_validation`, `skip_requesting_account_id`, `skip_metadata_api_check` y `skip_region_validation`. Nada va contra una cuenta real.
  - `var.emulador` vale `true` por defecto: sin `-var emulador=false` nadie toca una cuenta real. El camino `false` (AWS real) no se probó.
  - El generador (`infra/gen/tofu.py`) pasa a la v0.4: VPC con pub-a y app-a, sg-gw, nacl-public y nacl-private, EC2-GW, S3 celeris-backups y la VPN con NAT-T. Quedan fuera EC2-DR, NAT-DR y sg-dr (temporales, solo del simulacro T59) y EC2-SHIELD, EC2-CTRLR y NAT01 (retirados). El módulo aws-shield se elimina; `onprem-sim` (campus simulado del Modo A real) queda sin usar en esta demo.
  - Quedan fuera, por indicación: runbook de cuenta real, simulacro T59 y AWS Budgets.
  - El estado de OpenTofu se guarda fuera del repositorio (`~/.aws-emulator-lab/demo.tfstate`): contiene las llaves de la VPN.
- **Descargas hechas para esto:** el Dockerfile oficial baja el RPM de `downloads.aws.com` (imagen de 2,1 GB, no publicada por AWS); `awscli` v1 desde PyPI (para `aws ec2/s3 describe`); el proveedor `hashicorp/aws` 5.100 con `tofu init`.
- **Decide:** equipo del proyecto

### CI-54 — EC2-GW sin AMI ni software definidos
- **Estado:** diferido (2026-11-23, CE02/CE0331)
- **Tipo:** vacío
- **Dónde:** CE03 D2.5 (EC2-GW); `deploy/opentofu/modules/aws-gw`
- **Qué dice cada fuente:** D2.5 fija IP 10.30.0.10, subred pub-a, t3.micro, disco de 8 GB, sg-gw y perfil sin permisos sobre S3. El software («Caddy + Coraza, mTLS hacia CTRL01, agente Wazuh») es de CE02 y no hay receta de arranque. En la v0.2, la Debian 13 salía del parámetro público de SSM.
- **Qué se hizo:** el módulo crea la instancia, la IP elástica y el rol con solo Session Manager, sin `user_data`. Con el emulador usa una imagen de Amazon Linux 2023 que él registra; con AWS real, la Debian 13 por SSM (sin probar).
- **Propuesta:** CE02 entrega la receta de EC2-GW (paquete o imagen y certificado de cliente) y se agrega como `user_data` en el Modo A real.
- **Decide:** equipo de software (CE02)
- **Resolución:** La receta de EC2-GW (paquete o imagen, certificado de cliente) la entrega CE02; el módulo `aws-gw` crea la instancia sin `user_data`.

### CI-55 — Diferencias del AWS Emulator con AWS real
- **Estado:** resuelto (2026-11-23): documentadas y absorbidas
- **Tipo:** decisión de transcripción
- **Dónde:** `deploy/opentofu/modules/aws-vpn`, `envs/demo/main.tf`
- **Qué se midió:**
  - `EnableVgwRoutePropagation` devuelve `NotImplemented`. **Diferencia con AWS real:** con `var.emulador = true` se crea una ruta estática a 10.20.0.0/16 (la sede, `SEDE-JULIACA`) hacia el VGW en `rt-public` y `rt-private`. La ruta estática no sigue al BGP: no desaparece si cae el túnel. En AWS real se usa la propagación.
  - `ModifyVpnTunnelOptions` devuelve `NotImplemented` y el emulador devuelve valores por defecto de integridad de fase 2 y de margen de rekey que el proveedor quiere corregir. Como D1.10 usa AES-GCM (AEAD), esos campos no son de diseño y el recurso los ignora con `lifecycle.ignore_changes`.
  - El emulador no registra la Debian 13 ni tiene los parámetros de SSM: se usa una imagen de Amazon Linux 2023 suya.
  - Crea la instancia pero no la ejecuta ni abre túneles: no hay tráfico (T01, T02, T05 y T21 siguen siendo de los Modos A y H).
  - No evalúa políticas de IAM ni de bucket: la política con condición de IP se crea pero no se hace cumplir.
  - Un nombre de Security Group no puede empezar con `sg-` (tampoco en AWS): el módulo lo prefija con el nombre de la VPC.
- **Decide:** equipo del proyecto

### CI-56 — Alcance de «solo acepta la IP pública del campus»
- **Estado:** diferido (2026-11-23, CE02/CE0331)
- **Tipo:** vacío
- **Dónde:** CE03 D2.5 (S3 celeris-backups), S-30; `deploy/opentofu/modules/aws-backup`
- **Qué dice cada fuente:** el inventario dice «Solo acepta la IP pública del campus; credencial aparte con solo s3:PutObject y condición de IP de origen». No dice si la restricción de IP alcanza a todos los principales (lo que dejaría fuera a quien administra el bucket desde otra red) o solo a la credencial de respaldo.
- **Qué se hizo:** la política IAM del usuario `celeris-respaldo` permite solo `s3:PutObject` con `aws:SourceIp` = 203.0.113.10/32 (la IP del FortiGate, S-29), y la política del bucket niega cualquier acción de ese usuario fuera de esa IP. No se niega a los demás principales. En AWS Academy puede no existir el usuario [S-30]: `var.crear_credencial_respaldo = false`.
- **Propuesta:** confirmar con el equipo si se endurece (denegar a todos salvo un rol de administración) y probarlo en el Modo A real: el emulador no evalúa políticas.
- **Decide:** equipo del proyecto
- **Resolución:** Endurecer la política del bucket de respaldos y probarla exige AWS real (el emulador no evalúa políticas): es de CE0331 en el Modo A.

### CI-57 — Cierre del registro: triage de los CI abiertos (2026-11-23)
- **Estado:** resuelto (2026-11-23)
- **Tipo:** decisión de transcripción
- **Qué cambia:** Cierra como obsoletos por la v0.4 CI-09, CI-10, CI-11, CI-14, CI-16, CI-25 y CI-33; resuelve CI-06, CI-07, CI-08, CI-12, CI-13, CI-15, CI-19, CI-21 y CI-49; da por aplicados CI-01, CI-02, CI-20, CI-23, CI-24, CI-26…CI-32 y CI-48; difiere CI-34, CI-51, CI-54 y CI-56 (CE02/CE0331). Los cambios de datos están en CI-58…CI-63.
- **Dónde:** `docs/infra/e1/CAMBIOS-INVENTARIO.md`; se quitan los `pendiente` resueltos de `inventory.yaml`, `pruebas.yaml` y `trazabilidad.yaml`
- **Decide:** equipo del proyecto

### CI-58 — T01 y T21 por TCP hacia CTRL01:443 (resuelve CI-08)
- **Estado:** resuelto (2026-11-23)
- **Tipo:** decisión de transcripción
- **Qué cambia:** T01 («VPN: TCP entre AWS y el campus») pasa de `ping -c 4 10.30.0.10` a `nc -zv -w 5 10.20.20.10 443` desde EC2-GW (F30, TCP 443 por la VPN). T21 («MTU del túnel») pasa de `ping -M do` con 1372 y 1400 bytes a una descarga TCP de CTRL01:443 con `ss -ti` que debe mostrar un MSS ≤ 1360 (MTU 1400, MSS clamping 1360). No se agrega ningún flujo ICMP ni regla de Security Group. Siguen en los modos A y H y como críticas; T01 y T21 citan F30 y T01 ya no cubre la celda SERVERS → AWS.
- **Dónde:** `infra/pruebas.yaml` (T01, T21); `entregables/CE0311/Matriz_Pruebas_Conectividad_v1.2.xlsx`; D1.16 de `docs/celeris/`
- **Decide:** equipo del proyecto

### CI-59 — S-32: nombre del portal (resuelve CI-21)
- **Estado:** resuelto (2026-11-23)
- **Tipo:** supuesto nuevo
- **Qué cambia:** El FQDN público del portal lo entrega la DTI y el certificado de la CA lo emite FW01 por ACME (F33). Hasta tenerlo, el diseño y las pruebas usan el nombre de trabajo `portal.celeris.internal` (el del Modo L) y el Modo H lo sustituye por el real al ejecutar. T16, T17 y T18 dejan de escribir `https://portal`.
- **Dónde:** `infra/trazabilidad.yaml` (S-32); `infra/pruebas.yaml` (T16, T17, T18); `docs/celeris/Celeris-00-Marco-Comun.md` (tabla de supuestos)
- **Decide:** equipo del proyecto

### CI-60 — Pedido a la DTI: TCP 22 y 23 hacia HNY01 durante la ventana del señuelo (resuelve CI-49)
- **Estado:** resuelto (2026-11-23)
- **Tipo:** decisión de transcripción
- **Qué cambia:** El pedido a la DTI (S-29) incluye, además del NAT 1:1 de UDP 500/4500 y TCP 80/443, un cambio temporal en el FortiGate: TCP 22 y 23 hacia 10.20.0.2 durante la ventana autorizada de F24. Si la DTI lo niega, HNY01 solo ve tráfico interno (DET-04 queda con el tráfico de la propia red). F24 queda sin `pendiente` y mantiene su condición: solo con autorización escrita y una ventana definida.
- **Dónde:** `infra/inventory.yaml` (F24); `infra/trazabilidad.yaml` (S-29); D1.8 de `docs/celeris/Celeris-CE03-Infraestructura.md` («Posición frente al FortiGate»)
- **Decide:** equipo del proyecto

### CI-61 — UPS01 es Alta; NUT intrazona de MGMT (resuelve CI-15 y CI-09)
- **Estado:** resuelto (2026-11-23)
- **Tipo:** decisión de transcripción
- **Qué cambia:** D1.12 decía Media y D2.7 decía Alta: se unifica en **Alta**. El flujo NUT no necesita F-nn: UPS01 → JMP01 es intrazona de MGMT y JMP01 apaga las VM por SSH (F20).
- **Dónde:** `infra/inventory.yaml` (UPS01: `criticidad`, `flujos_justificacion`); D1.12 de `docs/celeris/`. Los diagramas y la matriz de componentes se regeneran en I4 e I5 (V-56, V-60)
- **Decide:** equipo del proyecto

### CI-62 — T25 solo en el Modo H (resuelve CI-16)
- **Estado:** resuelto (2026-11-23)
- **Tipo:** decisión de transcripción
- **Qué cambia:** T25 (break-glass) usa BRK01, ESX01 e IPMI01, que el laboratorio no emula (F4.1, F4.2). Se quita L de `modos`: ya no aparece como NO_APLICA en el ensayo del Modo L y V-33 deja de advertir. La prueba sigue siendo del Modo H.
- **Dónde:** `infra/pruebas.yaml` (T25); `tests/network/casos.py` (`NO_APLICA_L`)
- **Decide:** equipo del proyecto

### CI-63 — Capas de defensa en profundidad (D1.9) en la fuente única (resuelve la parte 1 de CI-30)
- **Estado:** resuelto (2026-11-23)
- **Tipo:** decisión de transcripción
- **Qué cambia:** `trazabilidad.yaml → defensa_profundidad` transcribe las 11 capas de la tabla de D1.9 v0.4 (capa, controles, detalle). La lista de `drawio.py` (`CAPAS_D19`) era de la v0.2 y trae controles retirados (NAS01, IDS01): al regenerar la figura 5.3 (I4) se debe leer del YAML y borrar la constante.
- **Dónde:** `infra/trazabilidad.yaml`, `infra/schema/trazabilidad.schema.json`
- **Decide:** equipo del proyecto

## Entradas de los diagramas v0.4 (H1, rango CI-70…CI-89)

### CI-70 — FGT-EXT y WIFI-EST faltan en el campo `figuras` de FIG-5.3 y FIG-5.4
- **Estado:** resuelto (2026-11-23, Henyelrey; lo revisa Nick en el PR de `v04/diagramas-red`)
- **Tipo:** vacío
- **Dónde:** `infra/inventory.yaml` → FGT-EXT y WIFI-EST (`figuras`); D1.8 («Posición frente al FortiGate», D-26), D1.9 (defensa en profundidad y zonas) y D1.10 (NAT-T) de `docs/celeris/Celeris-CE03-Infraestructura.md`
- **Qué dice cada fuente:** D1.9 pone «FortiGate existente con FortiGuard» como primera capa de la defensa en profundidad y lista WIFI-EST entre las zonas por nivel de confianza; D1.10 ubica el extremo de la VPN en FW01 detrás del FortiGate (NAT 1:1 y NAT-T UDP 4500). El YAML dejaba a FGT-EXT solo en FIG-1.1, 5.1 y 5.2, y a WIFI-EST sin FIG-5.3, por lo que V-51 no permitía dibujarlos donde la figura los pide (en las figuras, el recuadro de la zona WIFI-EST cuenta como el componente del mismo ID).
- **Decisión aplicada:** FGT-EXT → `[FIG-1.1, FIG-5.1, FIG-5.2, FIG-5.3, FIG-5.4]`; WIFI-EST → `[FIG-1.1, FIG-5.1, FIG-5.2, FIG-5.3, FIG-5.5a]`. No cambia ninguna IP, flujo ni componente.
- **Efecto:** la matriz de componentes (H2) toma la cobertura de `docs/infra/e1/cobertura-figuras.json`.
- **Decide:** equipo del proyecto

### CI-71 — `muestra` de FIG-5.5a y FIG-5.5b con los flujos de la v0.2
- **Estado:** resuelto (2026-11-23, Henyelrey)
- **Tipo:** contradicción
- **Dónde:** `infra/trazabilidad.yaml` → `figuras` (FIG-5.5a, FIG-5.5b, campo `muestra`)
- **Qué dice cada fuente:** el campo `figura` de cada flujo del inventario asigna F1–F3, F5–F8, F21, F24, F25, F31 y F32 a FIG-5.5a, y F10, F13, F14, F18, F20, F26–F30 y F33 a FIG-5.5b. El texto `muestra` seguía citando «F1–F3, F5–F8, F21–F25» y «F9–F20, F26», que incluyen flujos retirados (F9, F11, F12, F15–F17, F19, F22, F23).
- **Decisión aplicada:** se reescribe `muestra` con las listas del campo `figura`. Manda el campo `figura`; el texto es descriptivo (lo usará el informe, H3).
- **Decide:** equipo del proyecto

### CI-72 — Confianza de la zona AWS: «Media» en el YAML, «Baja, expuesta» en D1.9
- **Estado:** resuelto (2026-11-23)
- **Tipo:** contradicción
- **Dónde:** `infra/inventory.yaml` → zona AWS (`confianza`, marcada con `cambio: CI-72`); D1.9 «Zonas y su nivel de confianza» («AWS (EC2-GW) — Baja, expuesta»)
- **Qué dice cada fuente:** el YAML da a la zona AWS la confianza «Media». La tabla de D1.9 v0.4 da «Baja, expuesta» a AWS (EC2-GW), igual que a DMZ-SVC, porque EC2-GW recibe F29 desde Internet.
- **Propuesta:** «Baja» con `confianza_nota: expuesta` (como DMZ-SVC), porque EC2-GW es lo único del diseño expuesto a Internet además del portal. Mientras tanto, la FIG-5.3 dibuja el valor del YAML (Media) y ordena las zonas con él.
- **Decide:** equipo del proyecto (Nick y Henyelrey)
- **Decisión aplicada:** `confianza: Baja` y `confianza_nota: expuesta` en la zona AWS; se quitó `cambio: CI-72`. Que EC2-GW no guarde datos no vuelve más confiable a su zona: solo reduce el impacto si la comprometen. FIG-5.3 y el informe se regeneraron con el valor nuevo; ninguna regla cambia.

## Entradas de la matriz de componentes v1.1 (H2, rango CI-70…CI-89)

### CI-73 — «Por qué existe» de HNY01, SIEM01 y VGW más pobre que la Arquitectura §4
- **Estado:** resuelto (2026-11-23)
- **Tipo:** vacío
- **Dónde:** `infra/inventory.yaml` → `por_que` de HNY01, SIEM01 y VGW (marcados con `cambio: CI-73`); `docs/celeris/Celeris-Arquitectura-v0.4.md` §4.1 y §4.2
- **Qué dice cada fuente:** la §4 da una razón de existir que el YAML no recogía. HNY01: «lo exige la rúbrica (criterio 5 en S1, criterio 4 en S2). Cuesta 1 vCPU». SIEM01: las alertas incluyen IP del campus, «por eso queda en el campus». VGW: «transporta F30 y F13; lo exige la rúbrica de conectividad híbrida».
- **Decisión aplicada:** se agrega esa razón al `por_que` de cada uno, sin quitar lo que ya tenía. Los demás componentes vigentes concuerdan con la §4 (el YAML es igual o más detallado). La matriz se regenera; no se edita a mano.
- **Decide:** equipo del proyecto

### CI-74 — Motivo y reemplazo de los componentes retirados
- **Estado:** resuelto (2026-11-23)
- **Tipo:** vacío
- **Dónde:** `infra/inventory.yaml` → componentes con `estado: retirado`; campos nuevos `retirado_motivo` y `retirado_cubre` (opcionales en `infra/schema/inventory.schema.json`); Arquitectura v0.4 §5
- **Qué dice cada fuente:** el YAML solo guardaba `retirado_por` (CI-35, CI-36 o CI-39). La hoja «Retirados en v0.4» de la matriz pide el motivo. La §5 da el motivo y lo que cubre la función de DB01, OBS01, SVC01, WAF01, WEB01, IDS01, PROBE01, NAS01, EC2-SHIELD, EC2-CTRLR y NAT01. Para las subredes AWS-PUB-B, AWS-APP-B, AWS-DATA-A y AWS-DATA-B la §5 no da motivo; la §10.2 solo deja pub-a, app-a y la reserva 10.30.128.0/17.
- **Decisión aplicada:** `retirado_motivo` y `retirado_cubre` con el texto de la §5 en los 11 componentes que la §5 nombra. Las 4 subredes quedan sin motivo; la matriz lo muestra como «la §5 no da motivo (CI-74)».
- **Decisión del equipo (2026-11-23):** el motivo de AWS-PUB-B, AWS-APP-B, AWS-DATA-A y AWS-DATA-B es D-28: ya no hay réplica ni componentes multi-AZ (se retiraron EC2-CTRLR y EC2-SHIELD), así que no tienen nada que alojar. Se agregó `retirado_motivo` y `retirado_cubre` a las cuatro subredes. Nota: el texto de D-28 en CE03 habla de los servicios de apoyo; el retiro de EC2-CTRLR y EC2-SHIELD figura como CI-36.
- **Decide:** equipo del proyecto (Nick y Henyelrey)

## Entradas del informe CE0311 (H3, rango CI-70…CI-89)

### CI-75 — Objetivos del proyecto (OB-x) en la trazabilidad
- **Estado:** resuelto (2026-11-23)
- **Tipo:** vacío
- **Dónde:** `infra/trazabilidad.yaml` → lista nueva `objetivos_proyecto` y campo `objetivo_proyecto` en cada OD-xx (opcionales en `infra/schema/trazabilidad.schema.json`); CE03 D1.6 (columna «Objetivo del proyecto»); 00 Marco común M2.3
- **Qué dice cada fuente:** D1.6 asigna a cada OD-xx uno o más objetivos del proyecto (OB-1…OB-5) y M2.3 da la necesidad, el indicador y la meta de cada OB. El YAML no tenía ni lo uno ni lo otro, y el anexo C del informe (necesidad → OD → D-xx → componente → F → T) no se podía generar desde la fuente única.
- **Decisión aplicada:** se copian las cinco filas de M2.3 en `objetivos_proyecto` y la asignación de D1.6 en `objetivo_proyecto`. OD-05 queda con lista vacía, como en D1.6 («—»).
- **Decide:** equipo del proyecto

### CI-76 — Supuesto S-18 sobre piezas retiradas
- **Estado:** resuelto (2026-11-23)
- **Tipo:** contradicción
- **Dónde:** `infra/trazabilidad.yaml` → `supuestos.S-18`; `infra/inventory.yaml` → NAS01 (`estado: retirado`); `infra/pruebas.yaml` → T39 (retirada)
- **Qué dice cada fuente:** S-18 fija el usuario SFTP y la carpeta restic de NAS01 para la prueba T39. La arquitectura v0.4 (§5) retira NAS01 («el respaldo va a S3») y T39 ya no es vigente, pero S-18 seguía sin marca y la validación V-83 del informe lo detectó como ID retirado citado como vigente.
- **Decisión aplicada:** S-18 conserva su ID (para que las referencias históricas no cambien de sentido) y se marca `estado: retirado` con `retirado_motivo`. El anexo D del informe lista solo los supuestos vigentes y nombra los retirados en una nota.
- **Decide:** equipo del proyecto


## Entradas del Entregable 2 — centro de datos híbrido (CE0331, desde CI-77)

`infra/centro_datos.yaml` transcribe CE03 D2.3–D2.9 y Arquitectura §10–§11. Lo que falta o se contradice se registra aquí; el YAML cita el CI en el campo `ci`.

### CI-77 — Consumo eléctrico de ESX01: 400 W (D2.4) o 480 W (inventario)
- **Estado:** resuelto (2026-11-23, por la regla del proyecto: manda el inventario)
- **Tipo:** contradicción
- **Dónde:** CE03 D2.4 «Energía» (≈ 400 W); `infra/inventory.yaml` → UPS01.`por_que` («autonomía de 15–20 min a ≈ 480 W»)
- **Decisión aplicada:** se usa 480 W en `centro_datos.yaml` → `energia.consumo_w`; V-93 comprueba que coincide con el inventario. La autonomía de 15–20 min sigue «a confirmar con el fabricante».
- **Decide:** equipo del proyecto (confirmar con la ficha del servidor y de la UPS)

### CI-78 — Holgura de RAM: ≥ 15 % (D2.3) frente a 12,0 % tras el crecimiento (D2.8)
- **Estado:** resuelto (2026-11-23, decisión del equipo: SIEM01 a 12 GB)
- **Tipo:** contradicción
- **Dónde:** CE03 D2.3 («100 % cubierto con ≥ 15 % de holgura»); D2.8 y Arquitectura §10.1; `infra/inventory.yaml` → SIEM01.`vm.ram_gb`; `infra/centro_datos.yaml`
- **Qué decían las fuentes:** con SIEM01 en 16 GB, 64 GB × 1,1 × 1,2 = 84,5 GB sobre 96 GB dejaban 12,0 % de margen.
- **Decisión aplicada:** SIEM01 pasa de 16 a 12 GB: Wazuh todo en uno admite hasta 25 agentes con 8 GiB y el diseño tiene ≈ 8 agentes. Las VM suman 52 GB en F1 y 60 GB en F2; 60 × 1,1 × 1,2 = 79,2 GB, así que quedan 16,8 GB libres (17,5 % del host) y la holgura tras la sobrecarga de ESXi es 31,3 %. Se actualizaron el inventario, `centro_datos.yaml`, CE03 D2.4 y D2.8 y la Arquitectura §10.1.
- **Decide:** equipo del proyecto (Nick)

### CI-79 — Rack: ESX01 ocupa 2U pero D2.4 le asigna el rango U6–9 (4U)
- **Estado:** resuelto (2026-11-23, decisión del equipo: ESX01 en U6–U7)
- **Tipo:** vacío
- **Dónde:** CE03 D2.4 «Rack de 12U»; `infra/centro_datos.yaml` → `rack.ocupacion`
- **Decisión aplicada:** ESX01 (2U) ocupa U6–U7. Quedan libres U8–U9 y U4–U5, sin uso asignado. V-93 comprueba que las U libres son las que no ocupa ningún equipo. DC-1 rotula las U reales; el alto de las filas no es a escala.
- **Decide:** equipo del proyecto

### CI-80 — Enlace SW-CORE01 ↔ SW-ACC sin velocidad ni puerto
- **Estado:** resuelto (2026-11-23, decisión del equipo: 1 GbE por SW-ACC [S-14]); deja abierto CI-88
- **Tipo:** vacío
- **Dónde:** CE03 D2.4; `infra/centro_datos.yaml` → `host.enlace_acceso`
- **Decisión aplicada:** el enlace es un trunk 802.1Q de 1 GbE, la velocidad del SW-ACC existente [S-14]. La cuarta NIC (vmnic3) queda libre y sin enlace; no se le asigna velocidad.
- **Decide:** equipo del proyecto con la DTI (levantamiento AS-IS)

### CI-81 — Región de producción: «us-east-1 elegida» (D2.5) o «sa-east-1 candidata» (inventario, S-11)
- **Estado:** resuelto (2026-11-23, por la regla del proyecto: manda el inventario)
- **Tipo:** contradicción
- **Dónde:** CE03 D2.5 («us-east-1 … Elegida (laboratorio y producción)»); `infra/inventory.yaml` → `aws.region` (laboratorio us-east-1, producción_candidata sa-east-1); S-11
- **Decisión aplicada:** el informe presenta us-east-1 como región del laboratorio y del costo de referencia [S-12], y sa-east-1 como candidata de producción a confirmar con `mtr` desde Juliaca [S-11]. La región es una variable (`var.region`).
- **Decide:** equipo del proyecto (Nick) al medir la latencia

### CI-82 — Carga de EC2-GW sin cifras
- **Estado:** resuelto (2026-11-23, decisión del equipo: supuesto S-33)
- **Tipo:** vacío (supuesto nuevo)
- **Dónde:** CE03 D2.8 («EC2-GW solo atiende sesiones del panel (pocos usuarios)»); `infra/trazabilidad.yaml` → `supuestos.S-33`; `infra/centro_datos.yaml` → `aws.instancias[EC2-GW].carga_diseno`
- **Decisión aplicada:** S-33 fija la carga esperada derivada de S-26 (10 laboratorios, una sesión por laboratorio): 10 sesiones simultáneas, 5 solicitudes por segundo, 0,10 vCPU de media y 512 MiB. Frente a un t3.micro (línea base de 0,20 vCPU, 1 GiB) el margen es 50 % en CPU y 50 % en RAM. V-94 comprueba que las sesiones son las del número de laboratorios. Se mide con el piloto en S2; si la media supera la línea base se pasa a t3.small.
- **Decide:** equipo del proyecto (Nick)

### CI-83 — Precios de lista fuera de D2.5 (t3.small, NAT Gateway)
- **Estado:** resuelto (2026-11-23, decisión del equipo: precios de lista con fecha y región [S-12])
- **Tipo:** supuesto nuevo
- **Dónde:** `infra/centro_datos.yaml` → `aws.costo_mensual` (`region_precios`, `fecha_precios`, `nota_precios`), `aws.nat.alternativas`
- **Decisión aplicada:** todos los precios son de lista de AWS, de us-east-1 y de noviembre de 2026 [S-12]: US$ 0,0208/h para t3.small y US$ 0,045/h para el NAT Gateway. La matriz y el informe lo rotulan; no entran en el costo mensual de 24×7. Se confirman en AWS Pricing Calculator.
- **Decide:** Nick (S-12)

### CI-84 — S-08 en `trazabilidad.yaml` es de la v0.3
- **Estado:** resuelto (2026-11-23, decisión del equipo: corregir a la v0.4 y regenerar CE0311 como v1.2)
- **Tipo:** contradicción
- **Dónde:** `infra/trazabilidad.yaml` → `supuestos.S-08` (decía «Servidor físico disponible o a adquirir», US$ 4 500); Marco común S-08 (12 núcleos, 96 GB, 2 × 1,92 TB + 2 × 1 TB NVMe, US$ 3 800); Arquitectura §10.1 («hay que recalcular S-08»)
- **Decisión aplicada:** S-08 queda como en el Marco común y la v0.4: «Servidor físico (12 núcleos, 96 GB, 2 × 1,92 TB + 2 × 1 TB NVMe)», US$ 3 800 si se compra, validación «Cotización». Como cambia la huella de la fuente, el informe, las figuras y las matrices de CE0311 se regeneraron como v1.2 (`meta.inventario_version`); las v1.1 pasaron a `entregables/CE0311/historial/`.
- **Decide:** equipo del proyecto

### CI-85 — `inventory.yaml` no referencia a `centro_datos.yaml`
- **Estado:** resuelto (2026-11-23)
- **Tipo:** decisión de transcripción
- **Dónde:** encargo del Entregable 2 («referenciado desde inventory.yaml»); `huella_fuente()` de `docs/infra/e1/build_informe.py`
- **Qué dice cada fuente:** el informe de CE0311, cerrado en main, guarda la huella SHA-256 de `inventory.yaml`, `pruebas.yaml` y `trazabilidad.yaml`; V-80 y V-89 fallan si cambian. Escribir una referencia en `inventory.yaml` obligaría a regenerar y volver a entregar CE0311.
- **Decisión aplicada:** la referencia va en sentido contrario: `centro_datos.yaml` → `meta.inventario` y todo ID se valida contra el inventario (V-90, V-91). El inventario no se toca.
- **Decide:** equipo del proyecto

### CI-86 — Plazo de reposición del servidor físico
- **Estado:** resuelto (2026-11-23, decisión del equipo: escenario «cae ESX01» y supuesto S-34)
- **Tipo:** vacío
- **Dónde:** CE03 D2.9 (no había fila para ESX01); D2.2 excluye la alta disponibilidad entre hosts; `infra/centro_datos.yaml` → servicio CT-09 y `continuidad.punto_unico_de_falla`
- **Decisión aplicada (ajustada por CI-88: `DIRECT` no basta, falta la contingencia manual con la DTI):** el escenario «cae ESX01» es: los laboratorios pasan a `DIRECT` por el PAC (navegación sin caché); la consola y la caché se recuperan al reponer el host restaurando desde S3 (T59). El plazo de reposición del servidor es el supuesto S-34, por confirmar con la DTI; se agregó CT-09 a la tabla de RTO/RPO sin RTO numérico hasta que S-34 tenga valor. CE03 D2.9 y Arquitectura §11 llevan la fila nueva. La EC2 temporal EC2-DR sigue siendo el medio del simulacro T59, no un destino de recuperación en producción.
- **Decide:** equipo del proyecto; la DTI confirma S-34

### CI-87 — El trunk de 1 GbE hacia SW-ACC no deja holgura frente a D2.8
- **Estado:** abierto
- **Tipo:** contradicción (consecuencia de CI-80)
- **Dónde:** CE03 D2.8 (≈ 1 Gbps desde la caché hacia un laboratorio, REQ-NF-02 ≥ 900 Mbps); `infra/centro_datos.yaml` → `host.enlace_acceso`, `dimensionamiento.red`
- **Qué dicen las fuentes:** el host tiene 2 × 10 GbE y la caché sirve ≈ 1 Gbps a un laboratorio, pero el enlace SW-CORE01 ↔ SW-ACC (1 GbE por SW-ACC [S-14]) iguala ese objetivo: holgura 0 % y un solo laboratorio a la vez; varios laboratorios comparten 1 Gbps.
- **Decisión aplicada:** el informe y la matriz lo declaran como cuello de botella («sin holgura») y no lo ocultan; no se cambia la velocidad del SW-ACC, que es de la DTI.
- **Propuesta:** medir con iperf3 en S2 (LAB → EDGE con y sin IPS) y pedir a la DTI un enlace SFP+ de 10 GbE entre SW-CORE01 y SW-ACC si los laboratorios descargan a la vez.
- **Decide:** equipo del proyecto con la DTI

### CI-88 — `DIRECT` con ESX01 caído depende de FW01, que es una VM de ESX01
- **Estado:** resuelto (2026-11-24, decisión del equipo: contingencia manual y RTO objetivo de 30 min [S-35])
- **Tipo:** contradicción (consecuencia de CI-86)
- **Dónde:** `infra/inventory.yaml` → FW01 (`si_falla`: se pierde el ruteo entre VLAN y la salida a Internet; punto único de falla AM-12; puerta de enlace de la VLAN 30 en 10.20.32.1); D-17 (todo tráfico entre zonas pasa por FW01); CT-09
- **Qué dicen las fuentes:** la decisión de CI-86 dice que, si cae ESX01, los laboratorios siguen en `DIRECT` por el PAC. Pero `DIRECT` solo evita los nodos de caché; el tráfico de los laboratorios sigue saliendo por FW01 hacia el FortiGate, y FW01 corre en ESX01.
- **Decisión aplicada:** CT-09 cambia. FW01 cae con el host, así que `DIRECT` no basta. Contingencia manual: la DTI devuelve la puerta de enlace de la VLAN 30 al FortiGate (estado previo al proyecto) y los laboratorios navegan sin caché (`DIRECT` por el PAC). RTO objetivo de 30 min [S-35, a confirmar con la DTI]. La consola y la caché siguen recuperándose al reponer el host restaurando desde S3 (T59), con el plazo de S-34. Durante la contingencia los laboratorios quedan sin IPS ni reglas de FW01 y sin acceso a las otras VLAN. Actualizados: informe §10 y resumen, hoja «Continuidad», autoevaluación, CE03 D2.9 y Arquitectura §11 (la misma fila), Marco común (S-35), `centro_datos.yaml` (CT-09) y V-94.
- **Pendiente con la DTI:** FW01 es hoy el DNS de los laboratorios (Unbound en la interfaz .1 de cada VLAN, D-28), así que la contingencia también necesita un resolvedor que entregue la DTI; quedó dentro de S-35. El procedimiento no tiene una prueba T-nn en `pruebas.yaml` (no se creó una para no alterar CE0311): se ensaya y cronometra con la DTI en S2.
- **Decide:** equipo del proyecto; la DTI confirma S-35

### CI-89 — DC-2.png salía recortado: draw.io Desktop deja en blanco lo que pasa de ~8192 px
- **Estado:** resuelto (2026-11-24)
- **Tipo:** defecto de exportación
- **Dónde:** `entregables/CE0331/diagramas/DC-2.png` (y el informe v1.1, que la incrusta); `infra/gen/exportar_drawio.py`; V-108
- **Qué pasaba:** DC-2 mide 2830 × 1100 y a escala 3 el PNG era de 8437 × 3277 px; draw.io solo dibujó el 51 % superior, sin avisar, y faltaban 14 de los 30 `celeris_id` (PG-SEC, SIEM01, PG-EDGE, EDGE01, EDGE02, PG-FW-TRUNK, FW01, vSwitch1…). El .drawio y el PDF estaban completos y V-50 y V-100 no miraban los píxeles, así que nada falló.
- **Decisión aplicada:** `escala_png()` calcula la escala de cada figura (3 si cabe; si no, la mayor con ancho y alto ≤ 8000 px y área ≤ 2^25 × 0,95): DC-2 sale a 2,84 y las otras 10 figuras siguen en 3. V-108 revisa los 11 PNG de CE0311 y CE0331: misma proporción que el dibujo y que el PDF, contenido en ≥ 90 % del alto y todo `celeris_id` dibujado. Las 7 figuras de CE0311 no estaban recortadas. DC-0…DC-3 se re-exportaron con draw.io Desktop y el ancho declarado de la página de DC-2 pasó de 2400 a 2840.
- **Decide:** equipo del proyecto

### CI-90 — Figuras de los informes: sección horizontal y ancho útil
- **Estado:** resuelto (2026-11-24)
- **Tipo:** decisión de maquetación
- **Dónde:** `docs/infra/e1/build_informe.py` y `docs/infra/e2/build_informe.py` (`figura()`, `_es_apaisado()`)
- **Qué pasaba:** FIG-1.1 y DC-0 iban en páginas verticales, y las demás tenían un tope de alto de 12,2 y 12,6 cm que las dejaba más angostas que el ancho útil de la página apaisada (25,7 cm).
- **Decisión aplicada:** toda figura va en una sección apaisada y mide el ancho útil de la página (25,7 cm); el alto se limita a 13,4 cm (`ALTO_FIGURA_CM`) para que la figura, su leyenda y «Qué observar» quepan en la misma página. CE0311 se regeneró como v1.3 y CE0331 como v1.2.
- **Decide:** equipo del proyecto

### CI-91 — Los informes no nombraban a la universidad ni a la DTI como quien opera la red
- **Estado:** resuelto (2026-11-24)
- **Tipo:** decisión de redacción
- **Dónde:** `docs/infra/e1/informe/01-resumen.md` y `02-organizacion.md`; `docs/infra/e2/informe/01-resumen.md` y `02-organizacion.md`
- **Qué pasaba:** los textos decían «una universidad» y «el Campus Juliaca» sin nombrar a la Universidad Peruana Unión, y la DTI aparecía sin decir que es el área que opera la red.
- **Decisión aplicada:** §1 y §2 de ambos informes dicen «Universidad Peruana Unión (UPeU), Campus Juliaca» y «la Dirección de Tecnologías de la Información (DTI) es el área de la UPeU que opera la red». Ningún dato técnico cambia.
- **Decide:** equipo del proyecto

### CI-92 — La tabla de necesidades de CE0311 §2.1 solo contaba equipos, no personas
- **Estado:** resuelto (2026-11-24, supuesto nuevo S-36)
- **Tipo:** supuesto nuevo
- **Dónde:** `docs/infra/e1/informe/02-organizacion.md` (tabla de necesidades); `infra/trazabilidad.yaml` → S-36
- **Qué pasaba:** la tabla listaba PCs, Wi-Fi y enlaces, pero no las personas que usan o administran el servicio.
- **Decisión aplicada:** fila «Usuarios (personas, no equipos)»: hasta 400 estudiantes y docentes simultáneos en laboratorio (una persona por PC, de S-26) y 10 encargados (uno por laboratorio). Los administradores de la DTI, el auditor y los usuarios BYOD no tienen cifra en ninguna fuente: se declaran «sin cifra definida» en S-36 y se levantan con la DTI antes de S2. No se inventó ninguna cantidad.
- **Decide:** equipo del proyecto; la DTI aporta las cifras pendientes de S-36

### CI-93 — CE0311 §5.1 no nombraba las zonas MGMT, DMZ-SVC y DMZ-HONEY en la topología general
- **Estado:** resuelto (2026-11-24)
- **Tipo:** decisión de redacción
- **Dónde:** `docs/infra/e1/informe/05-topologias.md` (§5.1)
- **Decisión aplicada:** una frase ubica MGMT (VLAN 10, solo desde JMP01), DMZ-SVC (VLAN 40, PORTAL01, F21) y DMZ-HONEY (VLAN 41, HNY01, F24 en la ventana autorizada) dentro de la topología general. Los datos salen de `infra/inventory.yaml`; DMZ-SVC y DMZ-HONEY no tienen ningún flujo hacia MGMT ni SERVERS.
- **Decide:** equipo del proyecto

### CI-94 — Referencias de ambos informes sin formato IEEE y sin citas en el texto
- **Estado:** resuelto (2026-11-24)
- **Tipo:** defecto de formato
- **Dónde:** `docs/infra/e1/informe/11-referencias.md`, `docs/infra/e2/informe/12-referencias.md`; `build_informe.py` (E1, bloque `ref`); V-80 y V-95
- **Qué pasaba:** las referencias iban con viñetas, sin la fecha de acceso de las fuentes en línea, agrupaban dos URL en una misma entrada y ningún `[n]` se citaba en el cuerpo. En CE0311, RFC 8915 (NTS) no tenía respaldo en el diseño, que sirve NTP desde FW01 sin NTS.
- **Decisión aplicada:** lista numerada `[n]` con sangría francesa y numeración por orden de primera cita (IEEE). Cada fuente en línea termina en «[En línea]. Disponible en: URL. [Accedido: 24-nov-2026].»; las entradas con dos URL se separaron (OWASP CRS y Coraza; restic y pgBackRest). Cada `[n]` del cuerpo está en la lista y cada referencia está citada: CE0311 queda en 20 entradas (se quitó RFC 8915 y se separaron OWASP CRS y Coraza) y CE0331 en 18 (se separaron restic y pgBackRest). V-80 y V-95 comprueban el formato.
- **Decide:** equipo del proyecto

### CI-95 — D-20, D-21 y D-22 están en CE02 C3.4 pero no en `infra/trazabilidad.yaml`
- **Estado:** resuelto (2026-11-24)
- **Tipo:** faltante en la fuente de verdad
- **Dónde:** `infra/trazabilidad.yaml` → `decisiones`; `docs/celeris/Celeris-CE02-Ingenieria-Software.md` C3.4 y C5; `docs/software/e1/diagramas/` (DS-01, DS-12)
- **Qué pasa:** CE02 C3.4 define D-20 (catálogo con tres modos y aprobación DTI solo para descifrar), D-21 (precarga en el nodo) y D-22 (ahorro por laboratorio, nunca por persona), y C5 cita D-20…D-22. El YAML salta de D-19 a D-23. El validador de diagramas (`render.py`, D-05) los rechaza.
- **Decisión aplicada:** D-20, D-21 y D-22 se agregaron a `infra/trazabilidad.yaml → decisiones` con el texto de CE02 C3.4 (sin cambiar su contenido). Los diagramas UML vuelven a citarlas: D-20 en DS-17, D-21 en DS-16 y DS-18, D-22 en DS-01 y DS-12.
- **Decide:** equipo del proyecto

### CI-96 — Textos de requisitos de la v0.2 en `infra/trazabilidad.yaml`
- **Estado:** resuelto (2026-11-24, aprobado por el equipo)
- **Tipo:** discrepancia entre la fuente de verdad y CE02
- **Dónde:** `infra/trazabilidad.yaml` → `requisitos`; `docs/celeris/Celeris-CE02-Ingenieria-Software.md` C1.2 a C1.4; `docs/software/e1/srs/` (§1.13.4)
- **Qué pasa:** 19 requisitos del YAML conservan textos de la v0.2.
  - En 11 cambia el significado: REQ-F-13, F-17, F-19, F-22, F-25, NF-02, NF-03, NF-10, RN-04, RN-06 y RN-07. Por ejemplo:
    - RN-06 trata en el YAML de registros con IP real; en CE02, de los laboratorios asignados.
    - RN-07 exige en el YAML «cuatro ojos»; en CE02, aprobación de la DTI solo para descifrar.
    - NF-02 pide en el YAML 5 000 conexiones; en CE02, 40 PCs a ≥ 900 Mbps. Ese último valor es el que usa `infra/centro_datos.yaml`.
  - En 4 falta una parte: REQ-F-24, NF-07, NF-12 y RN-11.
  - En 4 solo cambia la terminología: REQ-F-02, F-10, F-14 y RN-03.
  - Los requisitos retirados F-16, F-21, F-23, F-27 y F-29 siguen sin marca de retiro.
  - REQ-NF-11 faltaba en CE02 C1.3. Se agregó a CE02 el 2026-11-24.
  - El validador solo comprueba que los IDs existan, por eso `make validate` no lo detecta.
- **Decisión aplicada:**
  - Los requisitos se definen en CE02 (00 M4.1). Por eso se igualan los textos del YAML a CE02 v0.4 y al SRS.
  - Se antepone «RETIRADO (v0.3):» a los cinco retirados, sin borrar sus IDs.
  - Se regeneró CE0311 v1.4 (47 páginas), porque su huella depende del YAML (V-80).
  - No cambia ningún ID, IP, flujo ni prueba.
- **Decide:** equipo del proyecto

### CI-97 — Costos y derivaciones del business case de CE01 sin supuesto registrado
- **Estado:** resuelto (2026-11-24)
- **Tipo:** supuesto nuevo
- **Dónde:** `docs/celeris/Celeris-CE01-Gestion-TI.md` v0.4 B2.3–B2.4; `infra/trazabilidad.yaml` → `supuestos`; `gestion/ce01.yaml`
- **Qué pasaba:** la guía CE01 suma a la inversión inicial un switch núcleo L2 con 10 GbE (US$ 600), una UPS de 1,5 kVA (US$ 700) y cableado (US$ 200) sin supuesto que los respalde; usa «100 Mbps de ampliación diferidos» sin derivarlos y «mantenimiento = 10 % del hardware» sin decir de qué base.
- **Decisión aplicada:**
  - S-37 switch (US$ 600), S-38 UPS (US$ 700) y S-39 cableado (US$ 200), cada uno a validar con cotización.
  - S-40 «Mbps diferidos» queda como fórmula sin cifra propia: BHR [S-04] × enlace [S-02]. Con los valores actuales da 90 Mbps, no 100; el número lo calcula `gestion/ce01_datos.py`.
  - S-41 mantenimiento = 10 % de la inversión inicial en hardware (S-08 + S-37 + S-38 + S-39), no solo del servidor.
  - `gestion/ce01.yaml` no copia los valores de los supuestos: declara una «lectura numérica» por supuesto (valor y el texto exacto donde aparece) y `gestion/ce01_datos.py` falla si ese texto ya no está en `infra/trazabilidad.yaml`. Así, si un supuesto cambia, CE01 no sigue usando la cifra vieja.
  - La huella de CE0311 incluye `infra/trazabilidad.yaml` (V-80): se regeneró el informe CE0311 v1.4 y su anexo de supuestos lista S-37…S-41.
- **Decide:** equipo del proyecto

### CI-98 — Cifras desactualizadas de la guía CE01 v0.4 frente al repositorio
- **Estado:** resuelto (2026-11-24); la corrección va en los informes de CE01, no en la guía
- **Tipo:** contradicción
- **Dónde:** `docs/celeris/Celeris-CE01-Gestion-TI.md` v0.4 B2.4–B2.5; `infra/centro_datos.yaml` → `energia.consumo_w` y `aws.costo_mensual.lineas`
- **Qué dice cada fuente:**
  - Energía: la guía usa 400 W (US$ 526/año); el repositorio, 480 W (CI-77), que dan ≈ US$ 631/año con S-09.
  - AWS: la guía usa «≈ US$ 70/mes» (US$ 840/año); la suma de las líneas C1–C7 da US$ 69,58/mes (US$ 834,98/año).
  - Mbps diferidos: la guía usa 100; la derivación de S-40 da 90 (30 % × 300 Mbps).
  - RAM: el documento de prompts de CE01 atribuía a la guía «56 GB de RAM en F1»; la guía v0.4 no cita esa cifra (solo el host de 96 GB), así que no hay discrepancia. F1 suma 52 GB en `centro_datos.yaml` (CI-78).
- **Decisión aplicada:** manda el repositorio. Los informes de CE01 leen consumo, AWS y supuestos a través de `gestion/ce01_datos.py` y nunca de la guía; el E2 incluye una nota de conciliación con la guía (VAN, flujo y payback de la guía quedan como referencia histórica). La guía no se edita a mano.
- **Decide:** equipo del proyecto

### CI-99 — Texto literal del EPE para CE01 S1 ausente del repositorio
- **Estado:** resuelto (2026-11-25)
- **Tipo:** vacío
- **Dónde:** `docs/fuentes/CE01/E1-E4-contenido-y-rubrica.md`; `docs/fuentes/CE01/contenido-minimo.yaml`
- **Qué pasaba:** P0 se ejecutó sin el bloque «B. ÁREA DE GESTIÓN DE TECNOLOGÍAS DE INFORMACIÓN» de `transcripcion.md`; el contenido mínimo quedó preliminar, con los títulos de la guía CE01 v0.4, y el generador no podía armar informes.
- **Decisión aplicada:**
  - El bloque B se copió literal (líneas 488–805 de `transcripcion.md`, hasta antes de «Entregable 5»), comprobado línea a línea contra la fuente; el encabezado del archivo guarda la huella SHA-256 de la fuente.
  - `contenido-minimo.yaml` se regeneró desde ese texto: E1 4 títulos y 16 ítems, E2 5 y 14, E3 6 y 17, E4 3 y 11; la rúbrica con sus cuatro descriptores (4, 4, 7 y 4 criterios). `cotejado: true`.
  - Varios títulos de la guía no eran los del EPE: «Justificación» → «Justificación del Proyecto», «Beneficios» → «Evaluación de Beneficios», «Costos» → «Estimación de Costos», «Alcance/Cronograma/Costos/Riesgos» → «Gestión del …», «AS-IS/TO-BE» → «Proceso Actual (AS-IS)» / «Proceso Propuesto (TO-BE)». En la rúbrica, el último criterio de todos los entregables es «Sustentación y defensa técnica».
  - El generador exige ahora, además de cada título, cada ítem del contenido mínimo como subtítulo (lo que va entre paréntesis, como «(opcional según complejidad)» o «(si aplica)», no se exige). `validate-ce01` comprueba que títulos, ítems y descriptores estén tal cual en el texto literal.
  - El EPE no fija plantilla, extensión ni formato para GTI (a diferencia de CE02 y CE03): la estructura es el contenido mínimo. No hay plantilla DOCX oficial de CE01: se usa la portada UPeU del proyecto. Evidencias según el índice del EPE: E1 CE0111–CE0115, E2 CE0113, E3 CE0121–CE0125, E4 CE0131–CE0135.
- **Decide:** Henyelrey

### CI-100 — Identidad visual y numeración de figuras y tablas de CE01
- **Estado:** resuelto (2026-11-24, pedido del equipo antes de P0)
- **Tipo:** decisión de diseño
- **Dónde:** `gestion/ce01.yaml` → `estilo`; `gestion/estilo_ce01.py`; `gestion/build_informe_ce01.py`
- **Decisión aplicada:**
  - Una sola paleta para todas las figuras de CE01 (BPMN, EDT, draw.io, gráficos de Python y XLSX): los colores institucionales de la UPeU, muestreados del logotipo de la portada (`docs/infra/e1/portada-upeu.docx`): azul #003865 y ámbar #F8A800, con tintes del azul, un tinte del ámbar y grises neutros. No hay manual de marca en el repositorio; si la universidad entrega uno, se ajusta solo `gestion/ce01.yaml`. CE03 sigue con Okabe-Ito (CLAUDE.md). El color nunca va solo: cada barra, celda o carril lleva su texto. Única excepción semántica: los mapas de calor de riesgo usan rojo, ámbar y verde con el nivel escrito (ALTO/MEDIO/BAJO).
  - Tablas y figuras se numeran por entregable al estilo IEEE: «Tabla 1.3. …» encima de la tabla y «Figura 1.1. …» debajo de la figura, con la fuente debajo («Fuente: elaboración propia…»). El texto las cita con `{{ref:id}}`.
  - Ninguna figura sin un párrafo previo que la introduzca (y la cite) y un párrafo posterior que interprete sus resultados clave; ninguna tabla sin título ni cita. El generador falla si no se cumple.
  - Figuras: PNG de 200 dpi, Calibri (Arial si no está), ancho útil 25,7 cm y alto máximo 13,4 cm en sección horizontal (CI-90), 17 cm en vertical.
- **Decide:** equipo del proyecto

### CI-101 — Diagnóstico E1 de CE01: meta de BHR del FCE, dueños de RE-xx e identificadores locales
- **Estado:** resuelto (2026-11-25, P1)
- **Tipo:** contradicción | vacío
- **Dónde:** guía CE01 v0.4 B1.3 (factores críticos de éxito) y B1.8 (riesgos estratégicos); `gestion/ce01.yaml` → `riesgos_estrategicos`; `gestion/e1/`
- **Qué dice cada fuente:**
  - La guía pone «BHR ≥ 20 %» como factor crítico de éxito, pero el objetivo OB-1 de `infra/trazabilidad.yaml` fija «BHR ≥ 25 % [S-04]».
  - El prompt P1 pide la matriz de riesgos estratégicos con dueño, pero B1.8 no asigna dueño a RE-01…RE-12.
  - El E1 necesita rotular los problemas operativos y los factores críticos de éxito, y el contrato de IDs (00 M6) no tiene prefijo para ellos.
- **Decisión aplicada:**
  - El FCE de BHR usa la meta de OB-1 (manda el repositorio); el informe la lee de `infra/trazabilidad.yaml`, no la escribe.
  - Cada RE-xx tiene `dueno` en `gestion/ce01.yaml`, asignado según el reparto de M9 (CE01 y red: Henyelrey; CE02, centro de datos, laboratorio y AWS: Nick; RE-01: ambos). Es una propuesta del equipo que se confirma en P3 junto con la RACI.
  - Tiempo de descarga de un laboratorio (OB-2): 00 M2.3 da «≈ 1,8 h (ilustrativo)» sin derivarlo. El E1 lo calcula con los supuestos (40 PCs × 3 GB [S-26, S-27] con todo el enlace de 300 Mbps [S-02]) y lo presenta como cota inferior (≈ 0,89 h); el 1,8 h equivale a usar la mitad del enlace. La línea base real se mide en el E4.
  - Prefijos locales del E1, sin uso fuera de CE01: PO-1…PO-5 (problemas operativos asociados a TI), FCE-1…FCE-5 (factores críticos de éxito), BR-1…BR-7 (brechas) y OE-a…OE-d (rótulos de trabajo de los objetivos estratégicos institucionales, hasta tener los códigos oficiales del plan estratégico). No son IDs del contrato M6 y no se reutilizan con otro significado.
- **Decide:** equipo del proyecto

### CI-102 — Business Case E2 de CE01: rangos de Monte Carlo, juicios AHP, costo de las alternativas y escenarios de estrés
- **Estado:** resuelto (2026-11-25, P2)
- **Tipo:** vacío | decisión de diseño
- **Dónde:** guía CE01 v0.4 B2.2–B2.5; prompt P2; `gestion/e2/datos/business_case.yaml`; `gestion/analytics/business_case.py`; `gestion/ce01.yaml` → `referencias.supuestos.S-05`
- **Qué faltaba:**
  - La guía y el prompt piden Monte Carlo con distribuciones triangulares, pero no fijan los rangos de todas las variables ni la moda de la adopción del proxy.
  - Ni la guía ni el repositorio tienen los juicios por pares para derivar los pesos con AHP, ni el costo de cada alternativa con las mismas partidas.
  - B1.8 no traduce los riesgos RE-01…RE-12 en cambios de parámetros del modelo.
  - Los indicadores de valor necesitan el tráfico mensual de laboratorios (S-05) como número; `ce01.yaml` solo tenía su texto.
- **Decisión aplicada:**
  - Monte Carlo: 10 000 iteraciones, semilla 20261125, triangular (mín, moda, máx) con la moda en el valor del supuesto: BHR 10–40 % [S-04], costo por Mbps-mes US$ 4–12 [S-03], adopción 60–100 % con moda 100 % (sin dato: el caso base supone que todo el tráfico del laboratorio pasa por la caché), factor AWS 0,70–1,30 [S-12] y factor de inversión 0,85–1,15 [S-08]. La adopción es un parámetro del modelo, no un supuesto S-xx; se mide en el piloto.
  - AHP: quince juicios del equipo con la escala de Saaty, cada uno con su motivo (anexo B del informe); CR = 0,014 < 0,10. El modelo falla si un cambio de juicios lleva el CR al umbral. Los pesos AHP prevalecen sobre los de partida de B2.2 y se validan con la DTI en una sesión de ponderación.
  - El criterio C3 no se juzga: se calcula del TCO a tres años con escala lineal (menor costo = 5, mayor = 1).
  - Costo de las alternativas con las partidas del modelo: A1, A2 y A3 con el mismo hardware que A4 (servidor, switch, UPS y cableado), sin EC2-GW ni S3; A0 como la compra de los mismos Mbps que difiere Celeris [S-40] al costo de S-03; A5 con costo nulo como cota inferior hasta que la DTI informe disco y licencia del FortiGate.
  - Escenarios de estrés por riesgo (juicio del equipo): RE-01 servicio solo el primer año; RE-02 BHR 10 %; RE-03 BHR 15 %; RE-04 beneficio BN-1 al 75 % el primer año; RE-05 un solo laboratorio y BN-2 al 10 %; RE-06 sin BN-2; RE-07 AWS × 1,30; RE-08 adopción 90 %; RE-09 beneficio del primer año al 50 %; RE-10 inversión × 1,15; RE-11 sin EC2-GW (VPN en el campus); RE-12 sin efecto en el flujo (reputacional).
  - S-05 recibe el número `tb_mes: 19,4` (el mismo valor que ya decía su texto); no cambia el supuesto.
- **Decide:** equipo del proyecto (juicios a validar con la DTI)

### CI-103 — Plan de gestión E3 de CE01: actividades, estimaciones, fechas académicas, RACI, EDT de S2 y riesgos nuevos
- **Estado:** resuelto (2026-11-25, P3)
- **Tipo:** vacío | decisión de diseño
- **Dónde:** guía CE01 v0.4 B3.1–B3.7; prompt P3; `gestion/e3/datos/{plan,agil,gobierno}.yaml`; `gestion/ce01.yaml` → `edt`, `raci`, `riesgos_proyecto`
- **Qué faltaba:**
  - La guía da la EDT de S1 (B3.3) y un extracto del diccionario, pero no las actividades, duraciones, dependencias ni horas, ni los paquetes de construcción, piloto y ampliación de S2.
  - Las fechas académicas (cierre de S1, inicio y duración de S2) no están publicadas; 00 M9 solo fija semanas relativas.
  - La fila RACI «Prototipo de la consola y validación» no tenía responsable de aprobación (A).
  - B3.5 da un presupuesto agregado (10 semanas × 12 h) que no cubre S2 ni sale de actividades.
  - No hay registro de horas reales del equipo en S1.
- **Decisión aplicada:**
  - Actividades (nivel 3), duraciones en días laborables, dependencias FS/SS y horas por recurso: estimación del equipo en `gestion/e3/datos/plan.yaml`; lo terminado en `main` va al 100 % con la fecha del commit que lo cierra. Se respetan los esfuerzos de B3.3 (3.2 = 20 h, 4.1 = 40 h, 4.3 = 6 h, 5.2 = 16 h); `plan.py` falla si no coinciden.
  - EDT: nuevos paquetes 5.4 Consola del encargado, 5.5 Piloto en un laboratorio y 5.6 Ampliación a los laboratorios; cada paquete de nivel 2 recibe descripción, criterio de aceptación y responsable.
  - Fechas académicas marcadas «[confirmar con el calendario académico]» (no son supuestos S-xx, para no tocar `infra/trazabilidad.yaml`): fin de S1 18 dic 2026 (semana 4 de 00 M9), receso 21 dic 2026–26 feb 2027, inicio de S2 1 mar 2027 (roadmap del E1), 16 semanas. Se gestionan con el riesgo RP-08 y el modelo recalcula el cronograma.
  - RACI: en «Prototipo de la consola y validación» aprueba el director (A = Henyelrey) y realiza el líder técnico (R = Nick), por la regla de revisión cruzada.
  - Costos: solo se valorizan las horas del equipo (S-07); DTI, encargados y docente se planifican sin costo. AWS del proyecto: 20 h del Modo A más el simulacro durante el despliegue y 2 meses de C1–C7 durante el piloto. Hardware = CAPEX del E2. Contingencia 10 % del BAC dentro de la línea base; reserva de gestión 5 % de la línea base fuera de ella.
  - EVM con regla 0/100; AC = EV mientras no haya registro de horas (el CPI se declara no medido).
  - Riesgos nuevos: RP-08 calendario académico, RP-09 compra del hardware, RP-10 disponibilidad de los encargados; RP-01…RP-07 reciben causa, efecto, estrategia, contingencia, disparador y estado.
  - Backlog de la consola: HU-01…HU-17 (prefijo local de CE01, no del contrato M6) con REQ-F y CU del SRS; puntos de historia y componentes del WSJF son estimación del equipo.
  - Las fechas del roadmap del E1 se mantienen como horizontes; el E3 las precisa en H1–H4.
- **Decide:** equipo del proyecto (fechas a confirmar con el calendario académico; RACI y presupuesto a aprobar por el sponsor)

### CI-104 — Modelado AS-IS / TO-BE E4 de CE01: parámetros de la simulación, supuestos nuevos y prefijos locales
- **Estado:** resuelto (2026-11-26, P4)
- **Tipo:** vacío | supuesto nuevo | decisión de diseño
- **Dónde:** guía CE01 v0.4 B4.1–B4.6; prompt P4; `infra/trazabilidad.yaml` → `supuestos`; `gestion/ce01.yaml` → `referencias.supuestos`; `gestion/e4/{simulacion.yaml,datos/procesos.yaml}`
- **Qué faltaba:**
  - La guía calcula la descarga de P1 con «150 Mbps disponibles» sin supuesto que lo respalde (CI-101 ya notaba que equivale a la mitad del enlace).
  - Ni la guía ni el repositorio tienen duraciones de las tareas manuales, probabilidades de las bifurcaciones (interrupciones, pedidos del mismo día, cambios que requieren a la DTI) ni frecuencia de P2, que la simulación necesita.
  - El E4 necesita rotular los problemas del proceso y sus indicadores, y el contrato de IDs (00 M6) no tiene prefijo para ellos.
  - La guía (B4.3) estima ≈ 18 min para el TO-BE descargando el primer paquete por Internet de día; la prueba T50 fija la precarga en ventana horaria con un límite de 50 Mbps.
- **Decisión aplicada:**
  - Supuestos nuevos: S-42 ancho de banda disponible para una descarga masiva en horario de laboratorio (150 Mbps, la mitad de S-02); S-43 duraciones triangulares de las tareas manuales, cuyos valores viven en `gestion/e4/simulacion.yaml`; S-44 probabilidades de las bifurcaciones; S-45 frecuencia de P2 (2 pedidos por laboratorio por semana lectiva, 32 semanas). Todos se validan con el cronometraje (≥ 30 observaciones por fase, `gestion/e4/instrumentos/registro-tiempos.xlsx`) o con los registros del piloto. `gestion/ce01.yaml` declara su lectura numérica, como en CI-97.
  - La entrega por la LAN usa 1 GbE de `infra/centro_datos.yaml` → `host.enlace_acceso` [S-14]; el límite de la precarga se lee de T50. Con la precarga nocturna, la descarga de día es solo la de la LAN (≈ 16 min); el ≈ 18 min de la guía queda como referencia y el informe lo concilia.
  - La probabilidad de interrupción del TO-BE no es un supuesto aparte: se deriva de S-44 escalada por la duración de la entrega (LAN frente a Internet).
  - Solo se valorizan las horas del técnico y del encargado (S-07); el tiempo del docente se informa sin valorizar. El tráfico evitado no se valoriza en el E4 porque ya está en BN-1 del E2.
  - El ahorro de personal de P1 que estima el E4 (≈ 0,10 h por PC y ciclo) es menor que S-07 (0,25 h), porque la verificación de la instalación sigue siendo manual (REQ-NF-07 impide mostrar el estado por PC); el E4 agrega el ahorro de P2, que el E2 no valoriza. Ambos se exportan a `gestion/e4/datos/resultados.json`; el E2 conserva S-07 hasta que se midan.
  - Prefijos locales del E4, sin uso fuera de CE01: PD-01…PD-09 (problemas del proceso), KPI-1…KPI-8 (indicadores del proceso), AU-1…AU-7 (automatizaciones) y C3…C5 (procesos candidatos no elegidos). No son IDs del contrato M6.
  - El mapa de procesos y los pesos de la matriz de selección son juicio del equipo, a validar con la DTI.
  - Herramientas: XSD BPMN 2.0 de OMG (`gestion/e4/herramientas/xsd/`) y render con bpmn-js + puppeteer-core sobre el Chrome instalado (`gestion/e4/herramientas/render/`, `node_modules` fuera del repositorio).
  - La huella de CE0311 incluye `infra/trazabilidad.yaml` (V-80): se regeneró el informe CE0311.
- **Decide:** equipo del proyecto (supuestos a validar con la DTI y el cronometraje)
