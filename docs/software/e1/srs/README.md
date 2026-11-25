# SRS de Celeris Edge v0.4 (CE0211, Sección 1 del entregable CE02 E1)

Especificación de requisitos según ISO/IEC/IEEE 29148:2018 (§9.5, contenido del SRS). Cada archivo es una
parte de la Sección 1 del informe; se unirán al Word junto con el prototipo (Sección 2), C4 + ADR (Sección 3) y UML
(Sección 4).

| Archivo | Contenido | Cláusula 29148 |
| --- | --- | --- |
| `01-introduccion.md` | Propósito, alcance, referencias, convenciones | 9.5.2–9.5.5 |
| `02-descripcion-general.md` | Perspectiva del producto, interfaces, usuarios, restricciones, supuestos, entregas | 9.5.6–9.5.10 |
| `03-requisitos-funcionales.md` | REQ-F del nodo y de la consola | 9.5.12 |
| `04-requisitos-no-funcionales.md` | REQ-NF por característica ISO/IEC 25010:2023 | 9.5.13–9.5.14 |
| `05-reglas-restricciones.md` | REQ-RN y RS-xx | 9.5.15–9.5.16 |
| `06-casos-de-uso.md` | CU-01…CU-11, historias y criterios Gherkin | 9.5.12 (escenarios) |
| `07-datos-interfaces.md` | Interfaces externas, API de la consola y datos lógicos | 9.5.11, 9.5.14 |
| `08-verificacion-trazabilidad.md` | Método de verificación y matriz REQ ↔ OB ↔ CU ↔ P ↔ T | 9.5.17 |
| `09-huecos-cambios.md` | Huecos H-01…H-12, desviación P-11, requisitos retirados y CI-96 | Anexo |

**Reglas que sigue el texto.** Los IDs existen en `infra/trazabilidad.yaml` (REQ, D, S, OB) o en
`infra/inventory.yaml` / `infra/pruebas.yaml` (componentes, flujos, pruebas). Los CU son de CE02 C1.6 y las P-xx
de `../prototipo/pantallas.md`. Nada se presenta como hecho si no está en el código: la columna «Estado» dice
*Hecho*, *Hecho en la rama*, *Parcial* o *Pendiente*.
