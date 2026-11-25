## Anexo B. Matriz de trazabilidad de requerimientos

La matriz traza cada requisito vigente de extremo a extremo: el objetivo del proyecto que lo justifica (OB), el
caso de uso y la pantalla en que se manifiesta, el componente de software que lo implementa (C3), la decisión de
arquitectura que lo sustenta (ADR), el diagrama UML que lo detalla, la prueba que lo verifica y el elemento de
infraestructura que lo soporta (equipo y flujo de red de CE03).

**Método de construcción.** La matriz no se elabora manualmente: el programa que genera este informe la construye a
partir de la especificación de requisitos, de los ADR y de la asignación de componentes, y se detiene con error ante
cualquier inconsistencia. Los componentes corresponden a DS-13 (nodo, `node.*`) y DS-22 (consola, `console.*`). Un
asterisco (\*) en la columna OB identifica un enlace incorporado durante la redacción de los requisitos. En S2, la
matriz se generará además a partir de las etiquetas de las pruebas automatizadas y del código.

**Garantías.** En cada generación se comprueba que:

- Todo requisito vigente cuenta con componente e infraestructura.
- Todo componente de DS-13 y DS-22 figura al menos una vez.
- Las 11 pantallas figuran al menos una vez.

Un «—» en la columna ADR indica que ninguna decisión enlaza ese requisito; no obstante, este puede rastrearse
mediante su componente, su prueba y su infraestructura.

{{tabla:matriz}}

**Vacíos identificados durante el diseño y su resolución.** El contraste entre requisitos, prototipo y diseño
permitió identificar los siguientes vacíos, todos cerrados o resueltos antes de la emisión de este informe:

{{incluir:srs/09-huecos-cambios.md|### 1.13.1 Huecos encontrados al diseñar|tabla}}

## Componente e infraestructura por requisito

| Requisito | Componente | Infraestructura (CE03) |
| --- | --- | --- |
| REQ-F-01 | node.ingress | EDGE01/02 · F1 (TCP 3128) |
| REQ-F-02 | node.tls, node.policy | EDGE01/02 · F1, F8 |
| REQ-F-03 | node.cache.index, node.cache.store | EDGE01/02 |
| REQ-F-04 | node.cache.index, node.upstream | EDGE01/02 · F8 |
| REQ-F-05 | node.cache.coalesce | EDGE01/02 · F8 |
| REQ-F-06 | node.cache.store | EDGE01/02 |
| REQ-F-07 | node.policy | EDGE01/02 |
| REQ-F-08 | node.cache.range | EDGE01/02 |
| REQ-F-09 | node.cache.store | EDGE01/02 |
| REQ-F-10 | node.ingress | EDGE01/02 · F1 · rangos /26 LAB-01…LAB-10 |
| REQ-F-11 | node.security, node.ingress | EDGE01/02 · F1, F8 |
| REQ-F-12 | node.notice, console.publisher | PORTAL01 · F5, F32 |
| REQ-F-13 | node.telemetry, console.reports | EDGE01/02, CTRL01 · F10 |
| REQ-F-14 | node.security | SIEM01 · F13 |
| REQ-F-15 | node.security | EDGE01/02 · F13 |
| REQ-F-17 | node.signed, node.agent, console.publisher | EDGE01/02, CTRL01 · F10 (TCP 8443, mTLS) |
| REQ-F-18 | node.tls, console.auth | EDGE01/02 |
| REQ-F-19 | console.catalog, node.cache.store | CTRL01 · F28, F10 |
| REQ-F-20 | console.catalog | CTRL01 · F28 |
| REQ-F-22 | node.prefetch | EDGE01/02 · F8, F10 |
| REQ-F-24 | console.audit | CTRL01 · F28, F30 |
| REQ-F-25 | console.reports | CTRL01 · F10, F28 |
| REQ-F-26 | node.pac, console.publisher | EDGE01/02 · F3 (TCP 80) |
| REQ-F-28 | node.privacy | EDGE01/02 · F8 |
| REQ-F-30 | console.publisher | CTRL01, JMP01, PORTAL01 · F20, F33 |
| REQ-F-31 | console.catalog | CTRL01 · F28, F10 |
| REQ-F-32 | console.labs | CTRL01, EDGE01/02 · F28, F10 |
| REQ-F-33 | console.auth | CTRL01 · F28, F29 → F30 |
| REQ-F-34 | console.prefetch | CTRL01 · F28, F10 |
| REQ-F-35 | console.prefetch | CTRL01 · F28 |
| REQ-F-36 | node.signed, node.tls, console.publisher | WIFI-EST, EDGE01/02 · F31 |
| REQ-F-37 | console.auth | ENC01, EC2-GW, CTRL01 · F28, F30 |
| REQ-NF-01 | node.cache.index, node.cache.store | EDGE01/02 · F1 |
| REQ-NF-02 | node.cache.store, node.upstream | EDGE01/02 · F1 |
| REQ-NF-03 | node.pac | EDGE01 y EDGE02 · F3, F6 |
| REQ-NF-04 | node.cache.store | EDGE01/02 |
| REQ-NF-05 | node.tls | EDGE01/02 |
| REQ-NF-06 | node.tls, node.upstream | EDGE01/02 · F1, F8 |
| REQ-NF-07 | node.privacy, node.telemetry, console.reports | EDGE01/02, CTRL01 · F10 |
| REQ-NF-08 | node.policy, node.tls | EDGE01/02 · F1 |
| REQ-NF-09 | node.policy, node.cache.store, node.tls | Repositorio (CI) |
| REQ-NF-10 | Todo `celeris-node` | Repositorio (CI) |
| REQ-NF-11 | node.cache.index, node.security | EDGE01/02 · F1, F13 |
| REQ-NF-12 | console.spa | ENC01 · F28 |
| REQ-NF-13 | node.telemetry | EDGE01/02 · F10 |
| REQ-NF-14 | node.admin, console.router | EDGE01/02 · F20 (TCP 9128); CTRL01 · F28, F30 |
| REQ-NF-15 | Todo `celeris-node` | Repositorio (CI) |
| REQ-NF-16 | console.publisher, node.agent | CTRL01, EDGE01/02 · F10 |
| REQ-RN-01 | node.policy | EDGE01/02 |
| REQ-RN-02 | node.policy | EDGE01/02 |
| REQ-RN-03 | node.policy, console.catalog | EDGE01/02, CTRL01 |
| REQ-RN-04 | console.catalog, node.signed | CTRL01, EDGE01/02 |
| REQ-RN-05 | node.notice | PORTAL01 · F5, F32 |
| REQ-RN-06 | console.auth, console.labs | CTRL01 · F28 |
| REQ-RN-07 | console.catalog, console.auth | CTRL01 · F28 |
| REQ-RN-08 | node.signed | EDGE01/02 · F10 |
| REQ-RN-09 | console.catalog | CTRL01 |
| REQ-RN-10 | console.prefetch, node.prefetch | CTRL01, EDGE01/02 · F8 |
| REQ-RN-11 | console.publisher, node.signed, node.tls | WIFI-EST, EDGE01/02 · F31 |
