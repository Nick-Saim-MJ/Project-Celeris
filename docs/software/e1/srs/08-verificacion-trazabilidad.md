## 1.12 Verificación y trazabilidad

### 1.12.1 Métodos de verificación

ISO/IEC/IEEE 29148 (§6.5) usa cuatro métodos:

- **I (inspección):** revisión de código, configuración o diseño.
- **A (análisis):** cálculo o modelo.
- **D (demostración):** se muestra funcionando ante el revisor, sin medición instrumentada.
- **P (prueba):** caso automatizado con criterio de aprobación. Son los Txx de `infra/pruebas.yaml` y los escenarios
  Gherkin de 1.10.4.

Las Txx definen origen, destino, comando y criterio. Las que corren en el laboratorio emulado (Modo L) se informan
como **emuladas** (CE03 D5.3). Ninguna se reporta como PASA si quedó NO_APLICA o PARCIAL. A la fecha, el único
resultado PASA que cita este SRS es T26 en el Modo L.

### 1.12.2 Matriz de trazabilidad

La columna OB parte de CE02 C1.7. Los valores con asterisco (\*) se agregaron en este SRS para que todo requisito
vigente quede conectado a un objetivo. La matriz completa del anexo (con componente, ADR y flujo) es CE02 C5. En S2
se generará en CI desde las etiquetas `@REQ-…` y `// req:`.

| Requisito | OB | CU | Pantalla | Diagrama UML | Verificación | Método |
| --- | --- | --- | --- | --- | --- | :-: |
| REQ-F-01 | OB-1\* | CU-01 | — | DS-05 | T07 | P |
| REQ-F-02 | OB-1, OB-4 | CU-01 | P-03 | DS-05 | `intercepcion.feature` | P |
| REQ-F-03 | OB-1 | CU-01 | — | DS-04, DS-09 | Pruebas del nodo | P |
| REQ-F-04 | OB-1\* | CU-01 | — | DS-06 | Pruebas del nodo | P |
| REQ-F-05 | OB-1 | CU-01 | — | DS-04 | T55 | P |
| REQ-F-06 | OB-1 | CU-01, CU-05 | — | DS-04, DS-18 | Pruebas del nodo | P |
| REQ-F-07 | OB-1\* | CU-01 | — | DS-04 | Pruebas del nodo | P |
| REQ-F-08 | OB-1\* | CU-01 | — | DS-13 | `rangos.feature` | P |
| REQ-F-09 | OB-1\* | CU-01 | — | DS-09 | Pruebas del nodo | P |
| REQ-F-10 | OB-5 | CU-04 | P-04 | DS-05, DS-19 | T13, T52 | P |
| REQ-F-11 | OB-5 | CU-01 | — | DS-05 | T13 | P |
| REQ-F-12 | OB-4 | CU-02 | P-09 | DS-15 | T15 | P |
| REQ-F-13 | OB-1\* | CU-06 | P-02, P-11 | DS-19 | `envivo.feature` | P |
| REQ-F-14 | OB-5\* | — | — | DS-02 | T11 | P |
| REQ-F-15 | OB-5 | CU-01 | — | DS-05 | T13 | P |
| REQ-F-17 | OB-5\* | CU-04 | P-08 | DS-02, DS-19 | T51 | P |
| REQ-F-18 | OB-4\*, OB-5\* | CU-07 | P-07 | DS-05 | Revisión de certificados | I |
| REQ-F-19 | OB-3\* | CU-08 | P-03 (v0.3) | DS-17 | `purga.feature` | P |
| REQ-F-20 | OB-3 | CU-03 | P-03 | DS-15 | `catalogo.feature` | P |
| REQ-F-22 | OB-2 | CU-05 | P-05 | DS-16, DS-18 | T50 | P |
| REQ-F-24 | OB-3\*, OB-5\* | CU-10 | P-08 | DS-15, DS-19 | `auditoria.feature`, T51 | P |
| REQ-F-25 | OB-1 | CU-06 | P-02 | DS-16 | `reportes.feature` | P |
| REQ-F-26 | OB-2\* | CU-01 | — | DS-13 | T09 | P |
| REQ-F-28 | OB-4\*, OB-5 | CU-01 | — | DS-04 | T26 (PASA, Modo L, emulado) | P |
| REQ-F-30 | OB-4 | CU-02 | P-09, P-10 | DS-15 | T15, T16 | P |
| REQ-F-31 | OB-3 | CU-03, CU-07 | P-03, P-07 | DS-15, DS-17 | `catalogo.feature`, T51 | P |
| REQ-F-32 | OB-3 | CU-04 | P-04 | DS-19 | `laboratorios.feature`, T52 | P |
| REQ-F-33 | OB-3 | CU-11, CU-09 | P-01 | DS-03 | `auth.feature`, T53 | P |
| REQ-F-34 | OB-2 | CU-05 | P-05 | DS-16, DS-18 | `precarga.feature`, T50 | P |
| REQ-F-35 | OB-2 | CU-09 | P-06 | DS-16 | `solicitudes.feature` | P |
| REQ-F-36 | OB-4 | CU-01 | — | DS-05 | `byod.feature`, T56 | P |
| REQ-F-37 | OB-3, OB-5 | CU-07, CU-11 | P-01, P-07 | DS-15 | `origen.feature`, T54 | P |
| REQ-NF-01 | OB-2\* | CU-01 | — | — | k6 / oha | P |
| REQ-NF-02 | OB-2 | CU-01 | — | — | iperf3 + carga | P |
| REQ-NF-03 | OB-2\* | CU-01 | — | — | T09 | P |
| REQ-NF-04 | OB-1\* | CU-01 | — | DS-04 | kill -9 + hash | P |
| REQ-NF-05 | OB-5\* | CU-07 | P-07 | — | Revisión de diseño (D-04) | I |
| REQ-NF-06 | OB-5\* | CU-01 | — | DS-05 | testssl.sh | P |
| REQ-NF-07 | OB-4 | CU-06 | P-02, P-11 | DS-12, DS-19 | `envivo.feature`, T26 | P |
| REQ-NF-08 | OB-4\* | CU-01 | — | DS-05 | Inyección de fallos | P |
| REQ-NF-09 | OB-5\* | — | — | — | CI | A |
| REQ-NF-10 | — | — | — | — | CI | D |
| REQ-NF-11 | OB-1\* | CU-01 | — | DS-04, DS-06 | Prueba de cabeceras | P |
| REQ-NF-12 | OB-3 | CU-03…CU-06 | P-01…P-08 | — | Prueba de usabilidad (SUS) | D |
| REQ-NF-13 | OB-1\* | CU-06 | P-11 | DS-19 | Revisión de métricas | I |
| REQ-NF-14 | OB-5 | CU-11 | P-01 | DS-13 | T27 | P |
| REQ-NF-15 | OB-5\* | — | — | — | `cosign verify` | I |
| REQ-NF-16 | OB-3 | CU-03, CU-04 | P-08 | DS-19 | Integración, T51 | P |
| REQ-RN-01 | OB-4\* | CU-01 | — | DS-09 | Pruebas del nodo | P |
| REQ-RN-02 | OB-4\* | CU-01 | — | DS-09 | Pruebas del nodo | P |
| REQ-RN-03 | OB-4\* | CU-03 | P-03 | DS-05, DS-17 | `intercepcion.feature` | P |
| REQ-RN-04 | OB-5\* | CU-03 | P-03 | DS-15, DS-17 | `catalogo.feature` | P |
| REQ-RN-05 | OB-4 | CU-02 | P-09, P-10 | DS-15 | T15, T16 | D |
| REQ-RN-06 | OB-3 | CU-04 | P-04 | DS-19 | `laboratorios.feature` | P |
| REQ-RN-07 | OB-3 | CU-03, CU-07 | P-03, P-07 | DS-15, DS-17 | `catalogo.feature` | P |
| REQ-RN-08 | OB-5\* | CU-04 | — | DS-19 | T51 | P |
| REQ-RN-09 | OB-4\* | CU-03 | P-03 | DS-17 | `catalogo.feature` | P |
| REQ-RN-10 | OB-2\* | CU-05 | P-05 | DS-18 | T50 | P |
| REQ-RN-11 | OB-4 | CU-01 | — | DS-05, DS-19 | `byod.feature`, T56 | P |

REQ-NF-10 (portabilidad) no se conecta a ningún OB. Es una condición de mantenimiento del producto y no tiene
indicador en CE01; se conserva como «debería».

### 1.12.3 Cobertura

- **Requisitos vigentes:** 59, distribuidos en 32 REQ-F (F-01…F-37, excluidos los 5 retirados), 16 REQ-NF y
  11 REQ-RN.
- **Método de verificación:** 51 se verifican por prueba (Txx, Gherkin o prueba del nodo), 4 por inspección, 3 por
  demostración y 1 por análisis.
- **Caso de uso:** todos los requisitos cuentan con caso de uso, excepto REQ-F-14, NF-09, NF-10 y NF-15, que
  corresponden a operación y calidad interna y no a la interacción con un actor.
- **Pantallas:** las 11 pantallas tienen al menos un requisito asociado, y ningún requisito de la consola carece de
  pantalla.
