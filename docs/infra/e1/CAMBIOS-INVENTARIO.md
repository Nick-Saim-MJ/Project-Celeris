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

| ID | Tipo | Tema | Estado |
| --- | --- | --- | --- |
| CI-01 | contradicción | Versión del documento maestro (0.2 vs 0.2.1) | abierto |
| CI-02 | contradicción | «15 secciones» del documento vs 11 de la plantilla; falta la tabla de contenidos mínimos | abierto |
| CI-03 | contradicción | F3 llega a EDGE01, la matriz LAB→EDGE solo lista F1 | resuelto en CI-39 (D1.8 v0.4 lista F1 y F3) |
| CI-04 | contradicción | F2 no tiene LAB-TEST de origen, la matriz LAB-TEST→SERVERS lista F2 | resuelto en CI-39 (LAB-TEST retirada) |
| CI-05 | vacío | MGMT→Internet «443 actualizaciones» sin flujo F-nn | resuelto en CI-29 (F27) |
| CI-06 | vacío | EDGE→EDGE «peering» sin flujo ni puertos | abierto |
| CI-07 | contradicción | F13 «todos los agentes» frente a la matriz y a las reglas de zona | abierto |
| CI-08 | contradicción | T01/T21 hacen ping, pero ningún flujo ni Security Group permite ICMP | abierto |
| CI-09 | vacío | NUT (UPS01 → NAS01 → ESXi y VM) sin flujo ni puerto | abierto |
| CI-10 | vacío | PROBE01: no hay ruta de métricas hacia OBS01 | abierto |
| CI-11 | contradicción | Security Groups de D2.5 frente a F12 y F13 | abierto |
| CI-12 | vacío | SW-ACC sin IP ni modelo (levantamiento AS-IS pendiente) | abierto |
| CI-13 | vacío | Grupos AWS (VPC/subredes) sin criticidad en D1.12; IGW, rutas y S3 sin ID | abierto |
| CI-14 | contradicción | EC2-CTRLR en «app-c» (D1.12) o «app-b» (D2.5) | abierto |
| CI-15 | contradicción | Criticidad de UPS01: Media (D1.12) vs Alta (D2.7) | abierto |
| CI-16 | contradicción | T12 y T25 en Modo L, pero NAS01, ESXi e IPMI no se emulan | abierto |
| CI-17 | vacío | Detecciones DET-02, DET-05, DET-07 y DET-08 sin T-nn | resuelto con T29–T32 (CI-27) |
| CI-18 | vacío | AM-13 «Revisión de logs» no es una prueba T-nn | resuelto con T33 (CI-27) |
| CI-19 | contradicción | T24 usa 1.1.1.1 (IP pública real) contra la regla RFC 5737 | abierto |
| CI-20 | decisión de transcripción | IDs OD/AM/DET/FIG asignados por posición; FIG-5.5a/5.5b | abierto |
| CI-21 | vacío | Nombre DNS del portal y orígenes de varias pruebas no definidos | abierto |
| CI-22 | vacío | 9 flujos sin prueba T-nn propia | resuelto con T34, T36–T43 y T49 (CI-27) |
| CI-23 | decisión de transcripción | Parámetros del laboratorio y tráfico sin F-nn en los generadores (Etapa 1) | abierto |
| CI-24 | decisión de transcripción | Parámetros del laboratorio emulado (WAN, DNS de prueba, vgw-sim) y qué no se emula (Etapa 3) | abierto |
| CI-25 | vacío | IaC del Modo A (OpenTofu): DPD mínimo de AWS, reglas de salida, disco de NAT01, campus simulado (Etapa 6) | abierto |
| CI-26 | decisión de transcripción | Qué pruebas son críticas (`critica` en pruebas.yaml) y qué hace V-42 con ellas (Etapa 7) | abierto |
| CI-27 | vacío | Ampliación de la matriz de pruebas: T29–T49, polaridad y celdas críticas (P4) | abierto |
| CI-28 | decisión de transcripción | Laboratorio emulado ampliado: NAS01 con VLAN 70/71, Wazuh, shield con mTLS, PAC del binario, honey-URL y navegador (P5) | abierto |
| CI-29 | decisión de transcripción | Flujo F27: MGMT → Internet por TCP 443 para actualizaciones (resuelve CI-05) | abierto |
| CI-30 | vacío | Capas de defensa en profundidad (D1.9) y salto de la ruta por defecto hacia el ISP fuera de infra/*.yaml | abierto |
| CI-31 | contradicción | FIG-5.4: FW01 anuncia 10.20.0.0/16 por BGP, las tablas de rutas de la VPC citan 10.20.0.0/14 | abierto |
| CI-32 | texto genérico | 17 textos de componentes (por qué / aporta / si falla) sin dato verificable (V-66) | abierto |
| CI-33 | contradicción | C4.3: celeris-control (CTRL01) publica el portal en WEB01, pero no existe flujo CTRL01 → WEB01; el sitio lo despliega JMP01 por SSH (F20) | abierto |
| CI-34 | supuesto nuevo | S-20 (vigencia del token de enrolamiento) y S-21 (umbral de error del rollout), usados por el diseño detallado de CE02 | abierto |
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

## Entradas

### CI-01 — Versión del documento maestro
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** cabecera del documento (línea 3) y `CLAUDE.md`; `inventory.yaml` → `meta.documento_base`
- **Qué dice cada fuente:** la cabecera y el registro de cambios del documento llegan a la versión **0.2**; las reglas del proyecto y el encargo de P1 citan **v0.2.1**.
- **Propuesta:** confirmar si existe una v0.2.1 no subida al repositorio. Si no existe, corregir `CLAUDE.md` a 0.2; si existe, versionarla en `docs/`.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** actualizar `meta.documento_base`, quitar `pendiente`.

### CI-02 — «15 secciones» del documento vs 11 de la plantilla; tabla de contenidos mínimos inexistente
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D1 (línea 1435: «la plantilla oficial tiene 15 secciones. D1.1 a D1.15 siguen ese orden uno a uno»), D1.17 R7 (línea 1854: «15 secciones oficiales»); `trazabilidad.yaml` → `correspondencia_contenidos`
- **Qué dice cada fuente:** la plantilla DOCX (`S1_E1_Analisis_y_Diseno_de_Red.docx`) tiene **11 secciones** numeradas (1–11), con subsecciones 2.1–2.3, 3.1–3.3, 5.1–5.6 y 7.1–7.3; `CLAUDE.md` también dice 11. D1 no incluye la «tabla del inicio de D1» que correspondería a los 15 contenidos mínimos.
- **Propuesta:** tomar la plantilla (11 secciones) como contrato y la correspondencia propuesta en `trazabilidad.yaml` (D1.1→§1, D1.2→§2.1, D1.3→§2.2, D1.4→§2.3, D1.5→§3, D1.6→§4, D1.7→§5.1, D1.8→§5.2, D1.9→§5.3/7.2/7.3, D1.10→§5.4/6, D1.11→§5.5, D1.12→§5.6, D1.13→§7.1, D1.14→§8, D1.15→§9/10/11; D1.16→§6). Corregir el texto de D1 y de D1.17 (R7) a «11 secciones».
- **Decide:** equipo del proyecto
- **Efecto al resolver:** quitar `correspondencia_pendiente`; el chequeo V-26 deja de advertir.

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
- **Estado:** abierto
- **Tipo:** vacío
- **Dónde:** D1.8 matriz fila EDGE, columna EDGE (línea 1568); `matriz_esperada` EDGE→EDGE
- **Qué dice cada fuente:** «✔ peering» sin F-nn ni puerto. El tráfico entre EDGE01 y EDGE02 está dentro de la VLAN 60 (conmutado en capa 2, nota 2 de D1.8), y el hash consistente entre nodos es REQ-F-21 (R3).
- **Propuesta:** dejar la celda como «sin flujo en R1» (REQ-F-21 pendiente) o definir el puerto de peering cuando se implemente R3.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** cambiar la celda a no_aplica o agregar el flujo.

### CI-07 — F13 «todos los agentes» frente a la matriz y a las reglas de zona
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D1.11 F13 (línea 1698), D1.8 matriz columna SECURITY, D1.9 reglas de zona (líneas 1601–1607), D2.8 «≈ 15 agentes» (línea 2035); `inventory.yaml` → `flujos[F13].origen`
- **Qué dice cada fuente:** F13 dice «todos los agentes» sin lista. La matriz solo permite F13 hacia SECURITY desde SERVERS, LAB (solo HNY02), DMZ-SVC, DMZ-HONEY, EDGE, BACKUP y AWS; no desde MGMT (JMP01, ESX01) ni LAB-TEST (KALI01). D2.8 estima ≈ 15 agentes; la lista de origen transcrita suma 13. Además D1.9 dice que DMZ-SVC «no inicia hacia ninguna zona interna» y que BACKUP «solo recibe de SERVERS», pero la matriz les permite F13.
- **Propuesta:** fijar la lista de agentes: CTRL01, DB01, OBS01, SVC01, EDGE01, EDGE02, WAF01, WEB01, HNY01, HNY02, NAS01 (interfaz de respaldo), EC2-SHIELD y EC2-CTRLR (13) y decidir si JMP01 y un 14.º y 15.º agente (p. ej. JMP01 y KALI01) se suman; aclarar en D1.9 que F13 es la excepción de salida hacia SECURITY.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** ajustar `F13.origen`, la matriz y la regla de zona; quitar `pendiente`.

### CI-08 — T01 y T21 hacen ping, pero ningún flujo ni Security Group permite ICMP
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D1.16 T01 y T21 (líneas 1815, 1835), D2.5 sg-shield (línea 1993), matriz SERVERS→AWS (línea 1562); `pruebas.yaml` → T01, T21
- **Qué dice cada fuente:** T01 espera «Permitido (VPN)» al hacer `ping 10.30.10.10` desde CTRL01, y T21 usa ping con 1372 y 1400 bytes. SERVERS→AWS solo permite F12 (TCP 9128 y 9100 desde OBS01), y sg-shield solo acepta TCP 8443 y 9128. Ningún F-nn cubre ICMP ni el origen CTRL01. T21 tampoco fija el origen.
- **Propuesta:** incluir ICMP echo desde CTRL01 (y el origen de T21) hacia 10.30.10.10 como regla de diagnóstico de la VPN, con su flujo F-nn, la regla en sg-shield y en la NACL; o reemplazar el ping por una prueba TCP al 8443/9128.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar el flujo o cambiar los comandos; quitar `pendiente` en T01 y T21.

### CI-09 — NUT (UPS01 → NAS01 → ESXi y VM) sin flujo ni puerto
- **Estado:** abierto
- **Tipo:** vacío
- **Dónde:** D2.4 «Energía» (línea 1899), D1.12 UPS01 (línea 1728); `inventory.yaml` → UPS01
- **Qué dice cada fuente:** el apagado ordenado depende de NUT (UPS → NAS01 como servidor NUT → ESXi y VM), pero ni D1.11 ni la matriz tienen un flujo NUT. Las VM de SERVERS, EDGE, etc. tendrían que alcanzar NAS01 (10.20.10.30, MGMT) y la matriz solo permite MGMT→zonas (F20), no al revés. El puerto NUT no está en el documento.
- **Propuesta:** definir el flujo NUT con su puerto y la protección en tránsito; o decidir que solo ESX01 (dentro de MGMT) es cliente NUT y ESXi apaga las VM.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar el flujo (F-nn) o la nota de diseño; quitar `pendiente` de UPS01.

### CI-10 — PROBE01: no hay ruta de métricas hacia OBS01
- **Estado:** abierto
- **Tipo:** vacío
- **Dónde:** D1.12 PROBE01 (línea 1742), REQ-NF-03, D1.8 matriz SERVERS→LAB (✖), F12; `inventory.yaml` → PROBE01
- **Qué dice cada fuente:** PROBE01 (blackbox_exporter, LAB) mide la disponibilidad cada minuto, pero F12 solo scrapea EDGE, CTRL01 y EC2-SHIELD y la matriz deniega SERVERS→LAB. No se indica cómo llega la serie a OBS01 (¿scraping SERVERS→LAB, push, o PROBE01 expone por el puerto 9115?).
- **Propuesta:** agregar PROBE01 a los destinos de F12 (con la excepción en la matriz SERVERS→LAB) o definir un envío OTLP/push por F11.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** ajustar F12 o F11 y la matriz; quitar `pendiente`.

### CI-11 — Security Groups de D2.5 frente a F12 y F13
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D2.5 sección 6.4 (líneas 1991–1997), D1.11 F12, F13, D2.5 «Sin bastion»; `inventory.yaml` → EC2-CTRLR, EC2-SHIELD
- **Qué dice cada fuente:** F12 incluye TCP 9100 (node_exporter) hacia EC2-SHIELD, pero sg-shield solo acepta 8443 y 9128. sg-ctrlr limita la salida a TCP 5432 hacia 10.20.20.11, lo que impide el agente Wazuh de EC2-CTRLR hacia SIEM01 (F13, 1514/1515) y la salida de SSM por NAT01 (443).
- **Propuesta:** agregar 9100 a sg-shield, y a sg-ctrlr las salidas 1514/1515 hacia 10.20.50.10 y 443 hacia NAT01; documentarlo en D2.5.
- **Decide:** equipo del proyecto (también afecta E2)
- **Efecto al resolver:** corregir D2.5 y quitar `pendiente` de EC2-CTRLR.

### CI-12 — SW-ACC sin IP ni modelo
- **Estado:** abierto
- **Tipo:** vacío
- **Dónde:** D1.12 SW-ACC (línea 1723), D1.5 exclusiones; `inventory.yaml` → SW-ACC
- **Qué dice cada fuente:** la IP es «según levantamiento [S-14]» y la criticidad «Alta (fuera de alcance)». No hay modelo, puertos ni PoE hasta el levantamiento AS-IS con la DTI.
- **Propuesta:** dejar la IP en `null` hasta el levantamiento y registrar el resultado como CAMBIOS (resuelto) con el modelo, las IP de gestión y la lista de controles de capa 2 soportados.
- **Decide:** DTI (levantamiento) y Henyelrey (S-14)
- **Efecto al resolver:** completar IP en `ips` y `emulacion_lab`; quitar `pendiente`.

### CI-13 — Grupos AWS sin criticidad en D1.12; IGW, tablas de rutas y S3 sin ID
- **Estado:** abierto
- **Tipo:** vacío
- **Dónde:** D2.5 (líneas 1951–1997), D2.7 (VPC principal «Alta», S3 `celeris-backups` «Alta»); `inventory.yaml` → AWS-VPC, AWS-PUB-A/B, AWS-APP-A/B, AWS-DATA-A/B
- **Qué dice cada fuente:** D1.12 no lista los grupos AWS; D2.7 solo asigna criticidad a «VPC principal» (Alta). Las subredes, el Internet Gateway, las tablas rt-public/rt-private, el Gateway Endpoint de S3, los Security Groups, las NACL y el bucket S3 no tienen ID de componente.
- **Propuesta (aplicada provisionalmente):** criticidad de cada subred = la de la instancia que aloja (Media) y Baja para las reservas (pub-b, data-a, data-b). Los IDs AWS-VPC, AWS-PUB-A… son propuestos. Decidir si IGW, S3 y los SG/NACL se dibujan y se numeran en E1.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** confirmar criticidades e IDs; agregar los componentes que se dibujen; quitar `pendiente`.

### CI-14 — EC2-CTRLR en «app-c» (D1.12) o «app-b» (D2.5)
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D1.12 EC2-CTRLR «AWS app-c» (línea 1749), D2.5 tabla de subredes (app-b, línea 1960), «a y b o c, según la región» (línea 1953)
- **Qué dice cada fuente:** la IP 10.30.11.10 pertenece a app-b (10.30.11.0/24). D1.12 la ubica en «app-c», nombre que no existe en la tabla de subredes.
- **Propuesta:** usar **app-b** (la tabla de subredes manda); corregir D1.12.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** corregir D1.12; quitar el segundo `cambio` de AWS-APP-B.

### CI-15 — Criticidad de UPS01
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D1.12 UPS01 «Media» (línea 1728), D2.7 UPS01 «Alta» (línea 2014)
- **Propuesta:** la UPS protege al único servidor y al firewall: usar **Alta**. En el inventario se conservó **Media** (valor de D1.12, el documento de E1) hasta que se decida.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** unificar ambos documentos y el YAML.

### CI-16 — T12 y T25 en Modo L, pero NAS01, ESXi e IPMI no se emulan
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** F3 (línea 2361: «Modo L con T06–T20 y T22–T28»), F4.1 (topología sin NAS01, br-vlan70/71, ESXi, IPMI, BRK01); `pruebas.yaml` → T12, T25
- **Qué dice cada fuente:** T12 verifica que `10.20.70.20` (NAS01) no responde y T25 usa el puerto break-glass para alcanzar ESXi e IPMI. La topología del Modo L no tiene esos nodos, así que T12 «pasaría» sin demostrar nada y T25 no puede ejecutarse.
- **Propuesta:** T25 solo en Modo H; T12 en Modo L solo si se agrega un nodo `nas01` y `br-vlan70` sin interfaz en `fw01-sim`; de lo contrario también solo en H.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** ajustar `modos` o F4.1; quitar `pendiente`. V-33 deja de advertir.

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
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D1.16 T24 (línea 1838); regla del proyecto «IP públicas solo de documentación (RFC 5737)»; `pruebas.yaml` → T24
- **Qué dice cada fuente:** el comando sugerido usa `@1.1.1.1` (resolvedor público real).
- **Propuesta (aplicada):** `@203.0.113.53` (documentación RFC 5737); en el Modo H se sustituye por un resolvedor real al ejecutar. El resultado esperado (853 bloqueado) no depende del destino.
- **Decide:** equipo del proyecto

### CI-20 — IDs OD/AM/DET/FIG asignados por posición; FIG-5.5a y FIG-5.5b
- **Estado:** abierto
- **Tipo:** decisión de transcripción
- **Dónde:** `trazabilidad.yaml`
- **Qué dice cada fuente:** el documento maestro no define OD-xx, AM-xx ni DET-xx (usa «#» y filas) ni FIG-x.x; la plantilla DOCX solo trae figuras 1.1, 5.1–5.4 y deja 5.5 como tabla.
- **Decisión tomada:** OD-01…10 por orden de D1.6; AM-01…13 por «#» de D1.9; DET-01…09 por orden de D1.14. FIG-5.5a (flujos de usuario, portal y servicios hacia Internet: F1–F3, F5–F8, F21–F25) y FIG-5.5b (control, observabilidad, seguridad, respaldo e híbrido: F9–F20, F26) dividen el diagrama de la sección 5.5 para que cada figura sea legible.
- **Decide:** equipo del proyecto (confirmar la división de figuras)

### CI-21 — Nombre DNS del portal y orígenes de pruebas no definidos
- **Estado:** abierto
- **Tipo:** vacío
- **Dónde:** D1.16 T16–T18 («https://portal»), T04, T05, T15, T16, T17, T21, T25, T26
- **Qué dice cada fuente:** el portal se escribe `https://portal` sin FQDN, pero el certificado público por ACME (D1.9) exige un dominio público real que no está definido. Varias pruebas no indican el equipo de origen; en `pruebas.yaml` se usó el que sugiere el comando o el de la prueba vecina (CTRL01, INTERNET, EDGE01, FW01).
- **Propuesta:** definir el FQDN del portal [S-xx nuevo] y fijar el origen de cada prueba en S2.
- **Decide:** equipo del proyecto y DTI (dominio)
- **Efecto al resolver:** reemplazar `portal` en T16–T18 y quitar `pendiente`.

### CI-22 — 9 flujos sin prueba T-nn propia
- **Estado:** resuelto en CI-27 (pruebas agregadas a pruebas.yaml)
- **Tipo:** vacío
- **Dónde:** D1.16 vs D1.11: F10, F11, F15, F17, F18, F19, F20, F25, F26. F23 solo tiene la prueba negativa T19 (WEB01 no sale a Internet); la renovación ACME no tiene prueba.
- **Propuesta:** mantener `sin_prueba_justificacion` (cada una dice cómo se valida en S2) o ampliar D1.16 con T29+. Los demás flujos tienen al menos un T-nn.
- **Decide:** equipo del proyecto

### CI-23 — Parámetros del laboratorio y tráfico sin F-nn en los generadores (Etapa 1)
- **Estado:** abierto
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

### CI-24 — Parámetros del laboratorio emulado y qué no se emula (Etapa 3)
- **Estado:** abierto
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

### CI-25 — IaC del Modo A (OpenTofu): lo que el diseño no define o AWS no admite (Etapa 6)
- **Estado:** abierto
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

### CI-26 — Pruebas críticas y alcance de V-40 a V-43 (Etapa 7)
- **Estado:** abierto
- **Tipo:** decisión de transcripción
- **Dónde:** `infra/pruebas.yaml` (campo `critica`), `infra/schema/pruebas.schema.json`, `infra/validate.py` (V-40…V-43)
- **Qué no definía el diseño:** D1.16 no dice qué pruebas son críticas. Se adoptó una regla: una prueba es crítica si su categoría es `segmentacion`, `vpn` o `cifrado` (16 de 28: T01–T06, T08, T10, T12, T19–T21, T23–T24, T27–T28), es decir, si un FALLA invalida un límite de seguridad del diseño. Quedan fuera conectividad, disponibilidad, detección, seguridad web y privacidad. La regla es del equipo del proyecto, no de D1.16.
- **Qué hace V-42:** FALLA en una prueba crítica = FALLA del validador. Una crítica que aplica al modo y no está en PASA (PARCIAL, NO_APLICA, ausente), o una FALLA no crítica, = advertencia: PARCIAL y NO_APLICA no cuentan como PASA.
- **Límites de V-40 y V-41:** comprueban los artefactos generados contra el inventario (puertos, acciones, modos, algoritmos, temporizadores, ASN, MTU/MSS), no el comportamiento del firewall; eso lo mide `make test-lab`. V-40 trata como correctas las reglas «sin F-nn» de CI-23 (VPN, NAT, anti-spoofing, MSS).
- **Propuesta:** confirmar o cambiar la regla de criticidad; en particular, si T15 (WAF) y T17 (inyección) deben ser críticas.
- **Decide:** equipo del proyecto


### CI-27 — Ampliación de la matriz de pruebas: T29 a T49 (P4)
- **Estado:** abierto
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

### CI-28 — Laboratorio emulado ampliado (P5)
- **Estado:** abierto
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

### CI-29 — Flujo F27: MGMT → Internet por TCP 443 para actualizaciones (resuelve CI-05)
- **Estado:** abierto
- **Tipo:** decisión de transcripción (ampliación de D1.11)
- **Dónde:** `infra/inventory.yaml` (flujo F27 y celda MGMT → INTERNET), `infra/pruebas.yaml` (T35), `infra/validate.py` (V-14)
- **Qué decía el documento:** la matriz D1.8 permite MGMT → Internet por TCP 443 (actualizaciones), pero D1.11 no tiene ningún flujo para eso. El firewall de laboratorio, que solo abre lo que declaran los flujos, lo denegaba y T35 fallaba.
- **Qué se hizo:** se agregó F27 (JMP01 → Internet, TCP 443, TLS, registro de FW01, FIG-5.5b, OD-06) con `ampliacion: true`. D1.11 sigue siendo F1–F26; V-14 exige que todo flujo extra lleve `ampliacion` y un CI.
- **Supuesto [S-19]:** D1.8 no lista los destinos. Hasta que la DTI entregue los repositorios de actualización de ESXi, OPNsense y NAS01, F27 queda abierto a cualquier servidor TCP 443 (riesgo residual medio, anotado en el flujo).
- **Propuesta:** aceptar F27 y reemplazar el destino por la lista de repositorios cuando exista.
- **Decide:** equipo del proyecto

### CI-30 — Capas de defensa en profundidad y salto de la ruta por defecto, fuera de la fuente única (P3)
- **Estado:** abierto
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

### CI-31 — Prefijo on-premise: /16 anunciado frente a /14 en las tablas de rutas de la VPC (P3)
- **Estado:** abierto
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

### CI-32 — Textos de componentes sin dato verificable (P4, V-66)
- **Estado:** abierto
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

### CI-33 — Publicación del portal: CTRL01 → WEB01 sin flujo en el inventario (CE02 E1, sección 4)
- **Estado:** abierto
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

### CI-34 — Supuestos nuevos del diseño detallado de software: S-20 y S-21 (CE02 E1, sección 4)
- **Estado:** abierto
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
