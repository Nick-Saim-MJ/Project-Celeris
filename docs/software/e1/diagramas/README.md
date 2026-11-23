# Diseño detallado — diagramas UML (CE02 E1, sección 4)

Versión: v0.1. Herramienta: PlantUML 1.2026.9 + Graphviz. Fuente: documento maestro C3.3 y C4.1 a C4.7, código en `src/`
y componentes, IP y flujos de `infra/inventory.yaml`.

## Convenciones

- **«R1»** (fondo blanco): existe en el código; los nombres de tipos y métodos son los reales de `src/`.
  **«R2»** (fondo azul claro, borde azul): diseño de `celeris-control` o de los puertos del *workspace*; todavía no existe
  (hueco H-03 del prototipo). **«R3»** (gris): escalamiento. El color siempre va acompañado del estereotipo escrito.
- Cada diagrama lleva en su pie su ID (DS-nn), los requisitos, casos de uso y pantallas que cubre.
- IP, componentes y flujos salen del inventario; `render.py` rechaza cualquiera que no exista (reglas D-01 a D-08).
- Misma paleta que el prototipo y el panel (`src/panel/panel.css`): tinta #0B0B0B, acento #2A78D6, página #F9F9F7.

## Índice

| ID | Diagrama | Tipo | Versión | Rúbrica (sección 4) | Requisitos principales | CU | Pantallas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DS-01 | Modelo de dominio (C4.1) | Clases | R1 + R2 | Modelo de diseño detallado | REQ-F-02, F-06, F-16…F-18, F-24, RN-03 | CU-01, 03, 04, 07 | P-04…P-07 |
| DS-02 | Clases de diseño de `celeris-node` | Clases | R1 + puertos R2 | Diagrama de clases | REQ-F-01…F-15, F-28, NF-08, NF-13 | CU-01, 07 | P-02, P-03, P-06 |
| DS-03 | Clases de diseño de `celeris-control` | Clases | R2 | Diagrama de clases | REQ-F-16…F-20, F-24, F-25, F-30, RN-04, RN-07, RN-08 | CU-03…06, 10 | P-04, P-05, P-07, P-08 |
| DS-04 | MISS con coalescencia y HIT (C4.2) | Secuencia | R1 | Diagrama de secuencia | REQ-F-03, F-05, F-06, F-07, F-28 | CU-01 | P-02, P-03 |
| DS-05 | CONNECT y decisión por SNI | Secuencia | R1 | Diagrama de secuencia | REQ-F-02, F-10, F-11, RN-03 | CU-01, 07 | P-04, P-06 |
| DS-06 | Revalidación 304 | Secuencia | R1 | Diagrama de secuencia | REQ-F-04, F-06, F-09 | CU-01 | P-02, P-03 |
| DS-07 | Política con aprobación de cuatro ojos (C4.3) | Secuencia | R2 | Diagrama de secuencia | REQ-F-17, F-18, F-20, F-24, F-30, RN-04, RN-07, RN-08 | CU-03, 10 | P-04, P-08 |
| DS-08 | Enrolamiento de un nodo | Secuencia | R2 | Diagrama de secuencia | REQ-F-16, F-18, RN-08, NF-05 | CU-04 | P-05, P-07 |
| DS-09 | Estados de una entrada de caché (C4.4) | Estados | R1 | Diagrama de estados | REQ-F-03…F-06, F-09, RN-01, RN-02, NF-04 | CU-01 | P-02, P-03 |
| DS-10 | Estados de un nodo (C4.5) | Estados | R2 | Diagrama de estados | REQ-F-16, F-17, RN-08 | CU-04, 10 | P-05, P-07 |
| DS-11 | Estados de una versión de política | Estados | R2 | Diagrama de estados | REQ-F-17, F-20, F-24, RN-07 | CU-03, 10 | P-04, P-08 |
| DS-12 | Modelo de datos del plano de control (C4.6) | Entidad-relación | R2 | Modelo de diseño detallado | REQ-F-16…F-19, F-24, F-25, RN-07 | CU-03…06, 10 | P-02, P-04, P-05, P-07, P-08 |
| DS-13 | Componentes C3 → archivos y crates | Componentes | R1 + R2 | Modelo de diseño detallado | REQ-F-01…F-15, F-28, NF-09, NF-10 | CU-01 | P-02, P-03, P-06, P-09 |

Archivos: fuente en `src/DS-nn-*.puml` (estilo común en `src/_estilo.iuml`), imágenes en `png/` (para el informe) y
`svg/` (vectorial).

## API del plano de control (C4.7, R2)

Se mantiene la API del maestro. Transporte: operadores con OIDC desde el panel; nodos con mTLS en TCP 8443 (flujo F10,
EDGE → CTRL01 10.20.20.10). Columna «Diagrama»: dónde se ve la llamada.

| Método | Ruta | Quién llama | Efecto | Requisitos | Diagrama |
| --- | --- | --- | --- | --- | --- |
| POST | `/v1/nodes/enroll` | Nodo (token [S-20]) | CSR → certificado mTLS + CA intermedia | REQ-F-16, F-18 | DS-08 |
| GET | `/v1/nodes/{id}/bundle?since=v` | Nodo (mTLS) | Bundle firmado ed25519 | REQ-F-17, RN-08 | DS-07, DS-08 |
| POST | `/v1/policies` | Operador A | Versión en estado Propuesta | REQ-F-17, F-24 | DS-07, DS-11 |
| POST | `/v1/policies/{v}/simulate` | Operador | Reporte de impacto, sin aplicar | REQ-F-20 | DS-07 |
| POST | `/v1/policies/{v}/approve` | Operador B (≠ autor) | Firma, rollout 10 % → 100 % | REQ-RN-07, F-17 | DS-07, DS-11 |
| POST | `/v1/purges` | Operador | Purga por URL, prefijo o etiqueta | REQ-F-19 | DS-03 |
| GET | `/v1/reports/savings?from=&to=` | Operador / DTI | GB evitados, BHR, costo por GB | REQ-F-25 | DS-03, DS-12 |
| POST | `/v1/portal/publish` | Operador | Genera y firma el sitio del aviso (lo despliega JMP01, CI-33) | REQ-F-30 | DS-03, DS-07 |

Falta en el maestro: el *heartbeat* del nodo (DS-07, DS-08) no tiene ruta propia en C4.7; se propone
`POST /v1/nodes/{id}/heartbeat` (hueco H-06).

## Huecos encontrados al diseñar (para el SRS y el maestro)

Continúa la numeración de `../prototipo/pantallas.md` (H-01 a H-03).

| ID | Hueco | Propuesta |
| --- | --- | --- |
| H-04 | C4.2 muestra `Cache-Status: celeris; fwd=miss; stored` y «collapsed»; el código responde `x-celeris-cache: MISS/HIT/REVALIDATED` y el que esperó en el coalescer recibe HIT. REQ-NF-11 exige Cache-Status (RFC 9211). | Implementar Cache-Status en R2 (mantener `x-celeris-cache` mientras tanto) y corregir C4.2. DS-04 dibuja lo real. |
| H-05 | C4.3 y C3.2 hacen que CTRL01 publique el portal en WEB01, pero el inventario no tiene ese flujo; el sitio lo despliega JMP01 por SSH (F20). | Registrado como CI-33. DS-03 y DS-07 muestran la propuesta. |
| H-06 | C4.7 no tiene ruta para el *heartbeat* ni C4.6 una tabla de rollout por nodo. | `POST /v1/nodes/{id}/heartbeat` y tabla `rollout` (DS-12, marcada «nueva»). |
| H-07 | C4.6 no tiene tabla de operadores ni de tokens de enrolamiento, aunque `propuesta_por`, `aprobada_por` y CU-04 los necesitan. Relacionado con H-01. | Tablas `operador` y `enrollment_token` (DS-12, «nueva»). |
| H-08 | REQ-NF-14 exige TLS en el puerto 9128; `admin.rs` todavía sirve HTTP sin cifrar (el panel avisa cuando el token viajaría en claro). | Mantener el requisito como pendiente en el SRS; DS-13 lo indica. |
| H-09 | C4.4 lleva «Revalidando → Llenando» con 200; en el código un 200 nuevo se guarda directo (`Store::put`) y la entrada queda Fresca. | DS-09 dibuja el comportamiento real; corregir C4.4. |

## Supuestos nuevos

Pendientes de registrar en `infra/trazabilidad.yaml` (CI-34). No son datos: su valor se fija con las pruebas de S2.

| ID | Supuesto | Valor | Validación | Diagramas |
| --- | --- | --- | --- | --- |
| S-20 | Vigencia del token de enrolamiento de un solo uso, entregado fuera de banda | Por definir (corta) | Prueba de enrolamiento en S2 | DS-08, DS-10, DS-12 |
| S-21 | Umbral de errores del rollout por nodo (5xx o heartbeats perdidos) | Por definir | Línea base de métricas en S2 | DS-07, DS-10, DS-11 |

## Cómo regenerar

Requiere Java 11+ y Graphviz. Desde la raíz del repositorio:

```
python docs/software/e1/diagramas/render.py --descargar   # la primera vez: baja PlantUML y verifica su SHA-256
python docs/software/e1/diagramas/render.py               # valida IDs contra infra/*.yaml y genera png/ y svg/
python docs/software/e1/diagramas/render.py --solo-validar
```

PlantUML queda en `.tools/plantuml/` (ignorado por git). La fuente PNG usa Arial para que el resultado sea igual en
Windows y Linux.
