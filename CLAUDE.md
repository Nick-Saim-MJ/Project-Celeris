# Reglas del proyecto Celeris — Infraestructura (CE0311, CE0331)

## Fuentes de verdad (en este orden)
1. infra/inventory.yaml, infra/pruebas.yaml, infra/trazabilidad.yaml → ÚNICA fuente de IP, VLAN, zonas,
   componentes, flujos, pruebas, OD, AM, DET y rúbrica.
2. docs/celeris/Celeris-CE03-Infraestructura.md (v0.4): D1 red, D2 centro de datos, D3 ADR, D5 laboratorio, D7 cambios.
   docs/celeris/Celeris-Arquitectura-v0.4.md: por qué de cada componente y qué va en la nube.
   docs/celeris/Celeris-00-Marco-Comun.md: alcance, actores, supuestos S-xx y contrato de IDs (M6).
3. docs/fuentes/CE03/: plantillas S1_E1 (red) y S1_E2 (centro de datos) y sus rúbricas (8 criterios cada una).

## Reglas
- Si un documento y infra/*.yaml no coinciden, manda infra/*.yaml. Si el YAML está mal, se corrige por CI-xx.
- No inventes IP, puertos, nombres ni cantidades. Si falta algo, DETENTE y regístralo en
  docs/infra/e1/CAMBIOS-INVENTARIO.md con el siguiente CI libre.
- IDs vigentes: F1–F33 (F4 reservado; F9, F11, F12, F15, F16, F17, F19, F22, F23 retirados), T01–T60
  (T12, T22, T37, T38, T39, T41, T44, T48 retirados), OD-01–OD-12, AM-01–AM-18, DET-01–DET-11, S-01–S-36,
  D-01–D-29, REQ-F-01–F-37. Un ID retirado NUNCA se reutiliza.
- Componentes vigentes (v0.4): FGT-EXT, FW01, SW-CORE01, SW-ACC, BRK01, ESX01, IPMI01, UPS01, JMP01, CTRL01,
  EDGE01, EDGE02, PORTAL01, HNY01, SIEM01, ENC01, LABCLI01, KALI01, HNY02, PCs LAB-01…LAB-10, WIFI-EST,
  VTI1, VTI2, VGW, EC2-GW, S3 celeris-backups, AWS-VPC, AWS-PUB-A, AWS-APP-A (+ EC2-DR y NAT-DR temporales).
  Retirados: DB01, OBS01, SVC01, WAF01, WEB01, IDS01, PROBE01, NAS01, EC2-SHIELD, EC2-CTRLR, NAT01.
- La consola (SPA + API + base) vive en CTRL01 (campus). En AWS solo EC2-GW (sin datos) y S3. No lo cambies.
- El Wi-Fi de estudiantes (BYOD) nunca se descifra.
- Todo supuesto se marca [S-xx]. IP públicas solo de documentación (RFC 5737). Ningún secreto en el repo.
- Regla de evidencia de la rúbrica: nada genérico; cada afirmación tiene IP, puerto, regla, figura o prueba.
- Lo emulado se rotula como emulado (CE03 D5.3). Ninguna prueba NO_APLICA o PARCIAL se reporta como PASA.
- Idioma: español claro, sin relleno.
- Antes de terminar: make validate en verde. No ejecutes `tofu apply`, no crees recursos en AWS y no hagas
  `git push` sin confirmación explícita del usuario.

## Identidad visual (diagramas y XLSX)
Okabe-Ito; el color nunca va solo (nombre de la zona en texto).
MGMT #0072B2 · SERVERS #009E73 · LAB #E69F00 · WIFI-EST #F0E442 · DMZ-SVC #D55E00 · DMZ-HONEY #CC79A7 ·
SECURITY #56B4E9 · EDGE #4D4D4D · FortiGate/tránsito #999999 · AWS: grupos AWS de draw.io.
Criticidad: Alta = borde 3 px + ALTA; Media = 2 px + MEDIA; Baja = 1 px + BAJA.
Flujos: cifrado = continua; sin cifrar con riesgo aceptado = discontinua; bloqueado = punteada + "✖ BLOQUEADO".

## Comandos
make validate · make lab-up / lab-down / test-lab · make tofu-check · make matrices · make diagrams-check ·
make informe (CE0311) · make informe-dc (CE0331) · make release-s1
