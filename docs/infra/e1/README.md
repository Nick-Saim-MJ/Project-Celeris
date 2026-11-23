# Fuente única de la red — CE0311 (Entregable 1)

Esta carpeta documenta los archivos que sostienen el Entregable 1 (Análisis y Diseño de Red). La regla es una sola:
**el informe Word, las dos matrices XLSX, los diagramas draw.io y el laboratorio se generan o se validan contra
`infra/*.yaml`**. Si un dato no está ahí, no existe en ningún artefacto.

## Archivos

| Archivo | Qué es | Quién lo mantiene |
| --- | --- | --- |
| [`infra/inventory.yaml`](../../../infra/inventory.yaml) | Zonas, direccionamiento, componentes (D1.12 y grupos AWS de D2.5), flujos F1–F26, matriz zona × zona esperada, VPN, servicios base | Diseño de red. Todo cambio pasa por revisión del otro integrante (cuatro ojos) |
| [`infra/pruebas.yaml`](../../../infra/pruebas.yaml) | Pruebas T01–T28 con comando, criterio verificable, modos L/A/H, rúbrica, objetivos y amenazas | Seguridad / Infraestructura; las ejecuta S2 |
| [`infra/trazabilidad.yaml`](../../../infra/trazabilidad.yaml) | Objetivos OD, amenazas STRIDE AM, detecciones DET, figuras FIG, rúbrica R1–R8, correspondencia con el DOCX y catálogos de S-xx, D-xx y REQ | Quien edite el informe; la rúbrica solo cambia si cambia el XLSX oficial |
| [`infra/schema/*.schema.json`](../../../infra/schema) | JSON Schema de los tres YAML (IDs, enumeraciones, campos obligatorios) | Quien cambie la estructura de los YAML |
| [`infra/celeris_infra.py`](../../../infra/celeris_infra.py) | Librería: carga, resuelve referencias, deriva la matriz zona × zona y calcula coberturas | La usan el validador y los generadores P2–P5; no releer los YAML por otra vía |
| [`infra/validate.py`](../../../infra/validate.py) | Validador V-01…V-43 + ganchos V-50+ | Quien agregue chequeos |
| [`infra/checks/`](../../../infra/checks) | Ganchos vacíos: `v50_` diagramas (P2), `v60_` XLSX de componentes (P3), `v70_` XLSX de pruebas (P4, ya implementado: V-70…V-75), `v80_` DOCX (P5) | Cada P# implementa el suyo |
| [`validacion.md`](validacion.md) | Resultado de la última validación. Lo escribe `make validate`; no se edita a mano | Automático (el CI exige que esté al día) |
| [`CAMBIOS-INVENTARIO.md`](CAMBIOS-INVENTARIO.md) | Registro de contradicciones y vacíos del documento maestro (CI-nn) | Quien detecte el problema; lo resuelve el equipo |

## Cómo trabajar

1. `make deps` (una vez) y `make validate` antes y después de cualquier cambio.
2. Un dato que falta o que se contradice: **no se arregla en el artefacto**. Se agrega una entrada `CI-nn` en
   `CAMBIOS-INVENTARIO.md`, se marca el elemento con `pendiente: true` y `cambio: CI-nn` en el YAML y se sigue.
   El validador lo muestra como advertencia hasta que se resuelva.
3. Un supuesto nuevo se registra con un ID `S-nn` en el registro de supuestos del documento maestro (A6) y se cita como `[S-nn]`.
4. Cambios en los IDs del contrato (FW01…, F1–F26, T01–T28, OD, AM, DET, FIG, R1–R8) rompen a los generadores: requieren aviso al equipo.

## Qué valida `make validate`

- **V-01…V-10** estructura: esquema, IDs únicos, referencias entre archivos, IP dentro del CIDR de su zona, sin duplicados,
  gateways .1 (VLAN 70 sin gateway), sin solapamientos, VLAN = tercer octeto, IP públicas solo RFC 5737.
- **V-11…V-16** flujos y matriz: la matriz derivada de los flujos coincide celda por celda con D1.8; protección y riesgo
  residual por flujo; todo flujo bloqueado tiene prueba; todo flujo tiene prueba o justificación.
- **V-17…V-19** componentes: por qué existe, qué aporta, qué pasa si falla, figuras y flujos.
- **V-20…V-27** pruebas, objetivos, amenazas, detecciones y rúbrica con coherencia en ambos sentidos.
- **V-28…V-34** integridad del contrato, pendientes registrados, secretos, VPN, servicios base, Modo L (lo emulado se rotula)
  y rúbrica contra el XLSX oficial.
- **V-40…V-43** artefactos generados y resultados (Etapa 7): el ruleset de nftables tiene exactamente los flujos del inventario
  (puertos, bloqueos, F6 solo en piloto, F24 solo con ventana, política drop); swanctl, FRR y VTI coinciden con la sección `vpn`;
  los últimos `evidencias/*/resultados.json` no tienen FALLA en pruebas con `critica: true`; el tfvars de OpenTofu y la topología
  de containerlab están al día.
- **V-70…V-75** XLSX de pruebas (P4): una fila por prueba del YAML con sus datos; flujos, componentes, OD, AM, DET y rúbrica existentes; cobertura
  (100 % de flujos permitidos con prueba positiva, de bloqueos y celdas denegadas críticas con prueba negativa, OD/AM/DET y elementos de R3 y R4 con ≥ 1 prueba);
  ensayo L (una FALLA lleva causa y acción; NO_APLICA y PARCIAL nunca como PASA); fórmulas sin errores tras recalcular con LibreOffice headless; archivo al día.
- **V-50+, V-60+, V-80+** ganchos para P2, P3 y P5. Mientras no estén implementados salen como «PENDIENTE de P#».

## Qué NO es

Los YAML describen el **diseño**; nada aquí está implementado. Lo que el laboratorio emula (Modo L) lleva `emulacion_lab`
y se presenta como emulado (Parte F4.2 del documento maestro). No hay secretos: la llave precompartida de la VPN la
genera AWS y se guarda cifrada con SOPS fuera de este repositorio.
