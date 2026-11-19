# Reglas del proyecto Celeris — CE0311 Análisis y Diseño de Red

## Fuentes de verdad (en este orden)
1. infra/inventory.yaml, infra/pruebas.yaml, infra/trazabilidad.yaml → ÚNICA fuente de IP, VLAN, zonas,
   componentes, flujos, pruebas, objetivos, amenazas y rúbrica.
2. docs/Celeris-Edge-Documento-Maestro.md (v0.2.1), Parte D1 (red), D2.4–D2.5 (hipervisor y AWS) y F (laboratorio).
3. docs/fuentes/CE03/S1_E1_Analisis_y_Diseno_de_Red.docx (plantilla: 11 secciones)
   y docs/fuentes/CE03/Rubrica_S1_E1_Diseno_de_Red.xlsx (8 criterios).

## Reglas
- No inventes IP, puertos, nombres ni cantidades. Si falta algo en infra/*.yaml, DETENTE y regístralo en
  docs/infra/e1/CAMBIOS-INVENTARIO.md. No lo "arregles" dentro de tu artefacto.
- Usa siempre los IDs del contrato: componentes (FW01…), zonas, VLAN, F1–F26, T01–T28, OD-xx, AM-xx,
  DET-xx, FIG-x.x, R1–R8, D-xx, REQ-…, S-xx.
- Todo supuesto se marca [S-xx]. Ningún supuesto se presenta como dato.
- IP públicas solo de documentación (RFC 5737). Ningún secreto, llave, token ni credencial en el repo.
- Regla de evidencia de la rúbrica: nada genérico. Cada afirmación del diseño tiene IP, puerto, regla,
  figura o prueba asociada.
- Lo emulado se rotula como emulado (Parte F4.2 del documento maestro). Nunca se presenta como implementado.
- Idioma: español. Prosa clara, sin relleno ni frases de marketing.
- Antes de terminar cualquier tarea: make validate debe pasar. Reporta lo que no pudiste validar.
- No ejecutes `tofu apply`, no crees recursos en AWS y no hagas push sin confirmación explícita del usuario.

## Identidad visual común (diagramas y XLSX)
Paleta apta para daltonismo (Okabe-Ito). El color nunca va solo: siempre con el nombre de la zona en texto.
MGMT #0072B2 · SERVERS #009E73 · LAB #E69F00 · LAB-TEST #F0E442 · DMZ-SVC #D55E00 · DMZ-HONEY #CC79A7 ·
SECURITY #56B4E9 · EDGE #4D4D4D · STORAGE #BBBBBB · BACKUP #888888 · AWS: estilo de grupos AWS de draw.io.
Criticidad: Alta = borde 3 px + etiqueta ALTA; Media = 2 px + MEDIA; Baja = 1 px + BAJA.
Flujos: cifrado = línea continua; sin cifrar con riesgo aceptado = discontinua; bloqueado = punteada + "✖ BLOQUEADO".

## Comandos
make validate        # todo: fuente única + artefactos + secretos
make lab-up / lab-down / test-lab
make matrices        # genera el XLSX de pruebas (P4); el de componentes es de P3
make diagrams-check  # valida los .drawio contra el inventario
make informe         # genera DOCX y PDF
make release-e1      # copia la versión final a entregables/CE0311/vX.Y/

## Estructura de la fuente única (E1)
- `infra/inventory.yaml`, `infra/pruebas.yaml`, `infra/trazabilidad.yaml` + `infra/schema/*.json`: los datos y su esquema.
- `infra/celeris_infra.py`: librería de carga y derivación (matriz zona × zona, coberturas). Los generadores (diagramas, XLSX,
  DOCX) la importan; no leen los YAML por su cuenta.
- `infra/validate.py` (V-01…V-43), `infra/checks/v70_xlsx_pruebas.py` (V-70…V-75: XLSX de pruebas) y `infra/checks/v50_…v80_` (ganchos para P2–P5; P4 ya está). Resultado en `docs/infra/e1/validacion.md`.
- `docs/infra/e1/CAMBIOS-INVENTARIO.md`: contradicciones y vacíos del documento maestro (CI-nn). Léelo antes de tocar un dato
  marcado `pendiente: true`.
- Dependencias: `pip install -r infra/requirements.txt` (`make deps`). En Windows sin GNU make, `python infra/validate.py` es
  equivalente a `make validate` salvo gitleaks.

## Cómo se trabaja
- Un dato que falta o se contradice se registra en CAMBIOS-INVENTARIO.md y se marca `pendiente: true` + `cambio: CI-nn` en el
  YAML; no se corrige dentro de un artefacto.
- El DOCX tiene **11 secciones** (la plantilla es el contrato, no las «15» que menciona el documento maestro; CI-02).
- El documento maestro está en v0.2 en su cabecera; la v0.2.1 de estas reglas está sin confirmar (CI-01).
- Lo emulado en el Modo L se rotula con `emulacion_lab` (F4.2) y nunca se presenta como implementado.
- Los objetivos de `make` que aún no existen fallan con «pendiente de P#»: P2 diagramas, P3 XLSX de componentes, P5 DOCX, P6 laboratorio.
