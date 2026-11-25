# 1. Especificación de requisitos (SRS)

## 1.1 Propósito

Este SRS fija qué debe hacer Celeris Edge v0.4 para los laboratorios de cómputo del Campus Juliaca y cómo se
comprueba cada requisito. Lo usan tres lectores: el equipo, para construir la consola en S2 (CE022–CE024); el
docente evaluador, para revisar la completitud y la trazabilidad; y la DTI, para validar lo que toca su red.

## 1.2 Alcance del producto

**Problema (00 M2.1).** En cada laboratorio, las 40 PCs [S-26] descargan por separado los mismos archivos grandes. Si
un laboratorio entero descarga a la vez, el enlace de 300 Mbps [S-02] se satura. El FortiGate filtra sitios, pero no
evita que un mismo instalador se descargue 40 veces. Además, ningún rol del laboratorio decide qué se reutiliza.

**Producto.** Celeris Edge consta de cuatro piezas:

| Pieza | Dónde corre | Estado en el repositorio |
| --- | --- | --- |
| Nodo de caché `celeris-node` | EDGE01 10.20.60.10 y EDGE02 10.20.60.11 | **Existe** (`celeris-cache`) |
| Consola del encargado `celeris-console` (SPA + API + PostgreSQL) | CTRL01 10.20.20.10 | No existe; se especifica aquí y se construye en S2 |
| Generador del PAC | En el nodo | Hecho (`src/pac.rs`) |
| Portal de transparencia | PORTAL01 10.20.40.10 | Parcial (`notice.rs`) |

**Qué gana cada parte (00 M2.3, CE01):**

| Objetivo | Indicador | Meta |
| --- | --- | --- |
| OB-1 | BHR | ≥ 25 % [S-04] |
| OB-2 | Tiempo de descarga para dejar listo un laboratorio | −70 % |
| OB-3 | Tiempo para que el encargado habilite una fuente o un laboratorio | ≤ 5 min |
| OB-4 | PCs con el aviso entregado antes de instalar la CA | 100 % |
| OB-5 | Escenarios de abuso detectados | ≥ 90 % en S2 |

**Fuera del alcance (00 M3.2):**

- descifrar tráfico BYOD (D-27);
- rediseñar el FortiGate, el Wi-Fi o la capa de acceso [S-14, S-28, S-29];
- la red administrativa;
- el modo examen;
- el *shield* de caché en AWS (D-19);
- varias sedes.

## 1.3 Definiciones

El glosario común está en 00 M1 y el de software en CE02 C0. Este SRS usa además los términos siguientes.

| Término | Significado en este SRS |
| --- | --- |
| Fuente | Entrada del catálogo con nombre, dominios, categoría y modo (`cachear`, `descifrar_y_cachear` o `nunca`). |
| Origen de sesión | `campus` si la petición a la API llega directo desde ENC01 10.20.35.10 (F28) o JMP01 10.20.10.20; `remoto` si llega por EC2-GW 10.30.0.10 con su certificado de cliente (F29 → F30). |
| Acción crítica | Aprobar una fuente a descifrar, rotar llaves o CA, gestionar usuarios y cambiar el perfil BYOD. Solo se permite con origen `campus` (REQ-F-37). |
| Configuración firmada | Versión inmutable que compila la consola (laboratorios, fuentes, precargas y redes BYOD), firmada con ed25519 (D-11). El nodo la descarga por F10. |
| Agregado de 30 s | Conteos por laboratorio y nodo (peticiones, HIT, MISS, BYPASS, 403, bytes) que el nodo envía por F10. No lleva URL, IP de equipos ni usuarios (REQ-NF-07). |
| R1 / R2 / R3 | Entrega: R1 = prueba de concepto S1 (nodo); R2 = implementación S2 (consola, portal, agente); R3 = trabajo futuro. |

## 1.4 Referencias

| Ref. | Documento |
| --- | --- |
| [1] | ISO/IEC/IEEE 29148:2018, *Systems and software engineering — Life cycle processes — Requirements engineering*. |
| [2] | ISO/IEC 25010:2023, *Product quality model*. |
| [3] | RFC 9111 *HTTP Caching*; RFC 9211 *Cache-Status*. |
| [4] | Ley 29733 de Protección de Datos Personales y su reglamento (D.S. 016-2024-JUS). |
| [5] | `docs/celeris/Celeris-00-Marco-Comun.md` v0.4; `Celeris-Arquitectura-v0.4.md`; `Celeris-CE02-Ingenieria-Software.md` v0.4. |
| [6] | `infra/inventory.yaml`, `infra/pruebas.yaml` e `infra/trazabilidad.yaml` (IP, flujos, pruebas, decisiones, supuestos). |

## 1.5 Convenciones

**Identificadores.**

- Requisitos: REQ-F-xx (funcional), REQ-NF-xx (no funcional) y REQ-RN-xx (regla de negocio).
- Restricciones: RS-xx.
- Casos de uso CU-xx, pantallas P-xx y pruebas Txx.
- Un ID retirado no se reutiliza (00 M6).

**Prioridad (MoSCoW).** M = debe, S = debería, C = podría.

**Estado.** Viene del código y de sus ramas:

- *Hecho*: está en `main`.
- *Hecho en la rama*: falta fusionar.
- *Parcial*: está en el código, pero no cumple todo el requisito.
- *Pendiente*: no hay código.

**Supuestos.** Se marcan [S-xx] (00 M5). Un supuesto sin validar es una limitación, no un dato.

**Fuente del texto.** El texto de cada requisito es el de CE02 v0.4, porque los requisitos se definen en CE02
(00 M4.1). `infra/trazabilidad.yaml` tiene el mismo texto desde que se cerró **CI-96** (sección 1.13.4).
