## 1.13 Huecos, desviaciones y cambios

### 1.13.1 Huecos encontrados al diseñar

Los huecos H-01 a H-03 salieron del prototipo (`../prototipo/pantallas.md`) y H-04 a H-12 de los diagramas UML
(`../diagramas/README.md`). Este SRS resuelve los que le tocan; los demás quedan con su dueño.

| ID | Vacío encontrado | Cómo se resolvió | Estado |
| --- | --- | --- | --- |
| H-01 | CU-08 (purgar, REQ-F-19) no tenía pantalla | Acción «Purgar» en cada fila de P-03, ruta `POST /v1/fuentes/{id}/purgar` y orden de purga dentro de la configuración firmada (1.7.3, 1.11.3). Criterio en `purga.feature` | Resuelto en los requisitos; la acción se dibujará en la próxima versión del prototipo |
| H-02 | Ninguna regla definía el comportamiento fuera del horario de un laboratorio | Se precisa en REQ-F-32: fuera del horario, el nodo responde 403 a ese rango, sin requerir una regla nueva. Criterio en `laboratorios.feature`. T52 actualmente solo cubre el laboratorio deshabilitado | Resuelto en los requisitos; queda pendiente ampliar T52 con el caso de horario en S2 |
| H-03 | No estaba definida la forma en que el docente registra sus solicitudes | Rol propio `docente` en la consola: entra por P-01 con segundo factor y solo crea y ve sus solicitudes (1.7.3, 1.11.4; DS-01 y DS-12 actualizados). Se eligió así porque el encargado ve quién pidió qué y la auditoría registra al autor, sin pasar por correo | Resuelto; el número de cuentas de docente queda sin cifra, como los demás roles de [S-36] |
| H-04 | La secuencia de descarga compartida mostraba «collapsed» para el cliente que espera | El código responde `hit` y ya envía la cabecera `Cache-Status` (REQ-NF-11); la secuencia se corrigió | Cerrado |
| H-08 | El puerto de administración del nodo no cumplía REQ-NF-14 (TLS) | El nodo ya cifra ese puerto (`admin_tls`) | Cerrado para el nodo; la consola, en R2 |
| H-09 | El diagrama de estados de la caché pasaba de «Vencida» a «Llenando» ante un 200 | Se corrigió según el código (DS-09): una copia vencida con validadores se revalida, y tanto el 304 como el 200 la dejan «Fresca» | Cerrado |
| H-10 | El modelo de datos carecía de `sesion`, `ca_intermedia` y `kpi_intervalo`, así como de columnas de `cambio` y `fuente` | Se agregaron al modelo de datos (DS-12) | Cerrado |
| H-11 | La API carecía de rutas para solicitudes, usuarios, rotación de CA y vista en vivo | Se agregaron a la API (Sección 4.4), junto con la purga y el perfil BYOD | Cerrado |
| H-12 | Las decisiones D-20, D-21 y D-22 no estaban en el registro común del proyecto | Se registraron (cambio CI-95) | Cerrado |

H-05, H-06 y H-07 de la v0.1 de los diagramas se cerraron antes de este SRS (`../diagramas/README.md`).

**Brecha nueva del código (sin número de hueco).** REQ-RN-11 está parcial. El nodo nunca descifra las redes de
`byod_networks`, pero acepta una configuración firmada que vacíe esa lista. Para cumplir la regla, el nodo debe
conservar WIFI-EST como BYOD aunque la configuración no la incluya. El segundo escenario de `byod.feature` lo
comprueba; se resuelve en S2.

### 1.13.2 Desviación registrada: P-11 «Actividad en vivo»

**Qué se desvía.** La tabla CE02 C2.1 tenía 10 pantallas, y la v0.2 había retirado el «registro en vivo». P-11 se
agregó el 24/11/2026 como desviación registrada. Queda pendiente de que el revisor la acepte.

**Por qué no agrega requisitos.**

- Muestra solo los agregados de 30 s que el nodo ya envía a CTRL01 por F10 (Arquitectura v0.4 §8.3).
- Se apoya en REQ-F-13, REQ-NF-13 y CU-06.
- No muestra URL, IP de equipos ni usuarios (REQ-NF-07, D-22). Por eso se descartó una vista por PC.

**Qué pide al diseño.** La tabla `kpi_intervalo` y la ruta `GET /v1/reportes/en-vivo` (H-10, H-11).

**Si el revisor no la acepta.** Se retiran P-11, la ruta y la tabla. Ninguna otra pantalla ni ningún requisito
cambia.

**No confundir con `live.rs`.** El nodo tiene hoy un registro en vivo local, que muestra qué dominios pide cada
equipo. Viene apagado y usa un seudónimo en lugar de la IP. Pertenece al panel de administración (9128) del nodo y no
a la consola. P-11 no lo usa.

### 1.13.3 Requisitos retirados

Los IDs retirados no se reutilizan (00 M6).

| ID | Requisito anterior | Motivo |
| --- | --- | --- |
| REQ-F-16 | Enrolamiento mTLS de una flota de nodos | Con dos nodos basta la configuración firmada (REQ-F-17); la flota queda como trabajo futuro |
| REQ-F-21 | Hash consistente entre nodos y *shield* | *Shield* fuera de alcance (D-19) |
| REQ-F-23 | Manifiestos firmados de *publishers* | Fuera de alcance |
| REQ-F-27 | Honey-URLs | Pasa a CE03 como detección opcional |
| REQ-F-29 | Proxy padre (*shield*) | Fuera de alcance (D-19). El código existe (`src/shield.rs`) y queda desactivado (`upstream_parent` vacío) |

### 1.13.4 Discrepancias con `infra/trazabilidad.yaml` (CI-96)

**Resuelto el 24/11/2026.** En 19 requisitos, el YAML conservaba textos de la v0.2. El validador solo comprueba que
los IDs existan, así que `make validate` no lo detectaba. Esta era la diferencia:

| Tipo | Requisitos | Ejemplo |
| --- | --- | --- |
| Cambia el significado | REQ-F-13, F-17, F-19, F-22, F-25, NF-02, NF-03, NF-10, RN-04, RN-06, RN-07 | RN-06 en el YAML habla de registros con IP real. Aquí es «un encargado solo gestiona sus laboratorios». RN-07 en el YAML exige «cuatro ojos» entre operadores; aquí, el encargado activa `cachear` y la DTI aprueba `descifrar_y_cachear` |
| Le falta una parte | REQ-F-24, NF-07, NF-12, RN-11 | NF-07 en el YAML no dice que los reportes son por laboratorio |
| Solo terminología de la v0.2 | REQ-F-02, F-10, F-14, RN-03 | «lista permitida», `intercept_domains` en lugar de fuente y modo |

Además:

- REQ-NF-11 estaba en el YAML y faltaba en CE02 C1.3. Se agregó a C1.3.
- Los cinco requisitos retirados siguen en el YAML sin marca de retiro.

**Cómo se cerró CI-96:**

1. El texto de esos 19 requisitos en el YAML se reemplazó por el de este SRS (CE02 v0.4).
2. Los cinco retirados llevan «RETIRADO (v0.3):» delante de su texto; sus IDs se conservan.
3. Se regeneró el informe CE0311 v1.4, porque su huella depende del YAML (V-80).

No cambió ningún ID, IP, flujo ni prueba.

### 1.13.5 Pendientes que no se presentan como cumplidos

- Validación con usuarios reales (Sección 2, C2.2): acta, tiempos por tarea y SUS. Sin ella, REQ-NF-12 sigue
  pendiente.
- Los escenarios Gherkin de 1.10.4 todavía no son ejecutables: `tests/features/` se crea en S2.
- Ninguna meta de desempeño (REQ-NF-01, NF-02, NF-03) se ha medido.
