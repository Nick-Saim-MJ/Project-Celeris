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
| CI-03 | contradicción | F3 llega a EDGE01, la matriz LAB→EDGE solo lista F1 | abierto |
| CI-04 | contradicción | F2 no tiene LAB-TEST de origen, la matriz LAB-TEST→SERVERS lista F2 | abierto |
| CI-05 | vacío | MGMT→Internet «443 actualizaciones» sin flujo F-nn | abierto |
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
| CI-17 | vacío | Detecciones DET-02, DET-05, DET-07 y DET-08 sin T-nn | abierto |
| CI-18 | vacío | AM-13 «Revisión de logs» no es una prueba T-nn | abierto |
| CI-19 | contradicción | T24 usa 1.1.1.1 (IP pública real) contra la regla RFC 5737 | abierto |
| CI-20 | decisión de transcripción | IDs OD/AM/DET/FIG asignados por posición; FIG-5.5a/5.5b | abierto |
| CI-21 | vacío | Nombre DNS del portal y orígenes de varias pruebas no definidos | abierto |
| CI-22 | vacío | 9 flujos sin prueba T-nn propia | abierto |
| CI-23 | decisión de transcripción | Parámetros del laboratorio y tráfico sin F-nn en los generadores (Etapa 1) | abierto |
| CI-24 | decisión de transcripción | Parámetros del laboratorio emulado (WAN, DNS de prueba, vgw-sim) y qué no se emula (Etapa 3) | abierto |

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
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D1.11 F3 (línea 1688), D1.8 matriz (filas LAB y LAB-TEST, columna EDGE, líneas 1563–1564), D1.9 «EDGE: solo recibe 3128 desde LAB» (línea 1602); `inventory.yaml` → `flujos[F3]`, `matriz_esperada` LAB→EDGE y LAB-TEST→EDGE
- **Qué dice cada fuente:** F3 (PAC, TCP 80) tiene como destino `pac.celeris.internal` = SVC01 **y EDGE01**, y D1.12 dice que EDGE01 sirve una copia del PAC. La matriz solo permite F1 (TCP 3128) de LAB y LAB-TEST hacia EDGE, y la regla de la zona EDGE dice que solo recibe 3128.
- **Propuesta:** agregar F3 a las celdas LAB→EDGE y LAB-TEST→EDGE y ajustar la regla de EDGE a «recibe 3128 y 80 (PAC) desde LAB». Es la opción que mantiene el PAC disponible cuando cae SVC01 (T22, OD-04).
- **Decide:** equipo del proyecto
- **Efecto al resolver:** corregir las dos celdas (o quitar EDGE01 del destino de F3); quitar `pendiente` de F3 y de las celdas. V-11 deja de advertir.

### CI-04 — F2 no incluye LAB-TEST de origen, pero la matriz lo lista
- **Estado:** abierto
- **Tipo:** contradicción
- **Dónde:** D1.11 F2 (línea 1687), D1.8 matriz fila LAB-TEST, columna SERVERS (línea 1564); `inventory.yaml` → `flujos[F2].origen`, `matriz_esperada` LAB-TEST→SERVERS
- **Qué dice cada fuente:** el origen de F2 es «LAB, SECURITY, EDGE»; la matriz da `F2, F3` en LAB-TEST→SERVERS. Sin DNS, KALI01 y los equipos de LAB-TEST no resuelven nombres.
- **Propuesta:** agregar LAB-TEST al origen de F2.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar `LAB-TEST` a `F2.origen`; quitar `pendiente` de F2 y de la celda.

### CI-05 — MGMT→Internet «443 actualizaciones» sin flujo F-nn
- **Estado:** abierto
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
- **Estado:** abierto
- **Tipo:** vacío
- **Dónde:** D1.14 (líneas 1778–1788) vs D1.16; `trazabilidad.yaml` → `detecciones`
- **Qué dice cada fuente:** la columna «Validación en S2» de D1.14 describe escenarios (escaneo desde KALI01, barrido desde LAB, honey-URL, escenario de prueba de CrowdSec), pero D1.16 no tiene pruebas T-nn para ellos. OD-09 exige ≥ 90 % de escenarios detectados.
- **Propuesta:** ampliar la matriz con T29+ (por ejemplo, T29 escaneo KALI01→SERVERS, T30 barrido en LAB, T31 honey-URL, T32 CrowdSec) o aceptar el escenario como validación sin T-nn. Ampliar T-nn rompe el contrato T01–T28.
- **Decide:** equipo del proyecto
- **Efecto al resolver:** agregar las pruebas o quitar `pendiente`.

### CI-18 — AM-13 «Revisión de logs»
- **Estado:** abierto
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
- **Estado:** abierto
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
