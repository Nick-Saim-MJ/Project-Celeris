# Sección 0: Identificadores, supuestos y decisiones

La presente sección consolida los códigos que el informe emplea para respaldar cada afirmación: el significado de
cada prefijo, los datos asumidos como supuestos y las decisiones de arquitectura adoptadas. Las demás secciones los
citan entre paréntesis, por ejemplo «(REQ-F-37, D-24)».

## 0.1 Prefijos de los identificadores

| Código | Definición | Ubicación | Ejemplo |
| --- | --- | --- | --- |
| REQ-F-xx, REQ-NF-xx, REQ-RN-xx | Requisito funcional, no funcional o regla de negocio. En una lista se abrevia tras el primero: «REQ-F-31, F-32» | 1.1–1.3 | REQ-F-37: las acciones críticas solo desde el campus |
| S-xx | Supuesto: dato no confirmado sobre el que se diseña | 0.2 | S-02: enlace a Internet de 300 Mbps |
| CU-xx | Caso de uso | 1.5 | CU-03: agregar una fuente al catálogo |
| P-xx | Pantalla del prototipo | 2.3 | P-03: catálogo de contenido |
| D-xx | Decisión de arquitectura (ADR) | 0.3 y 3.2 | D-24: acceso remoto por EC2-GW |
| DS-xx | Diagrama C4 o UML | Secciones 3 y 4, Anexo C | DS-21: contenedores |
| CE01, CE02, CE03 | Los tres cursos que integran el proyecto: gestión de TI (caso de negocio), ingeniería de software (el presente informe) e infraestructura (red y centro de datos) | — | — |
| R1, R2 | Entrega: R1 se encuentra implementado en el código del nodo; R2 se construirá en el segundo semestre (S2) | Columna «Ver.» y estereotipo de los diagramas | «R2» |
| Txx | Prueba del plan de pruebas del proyecto, compartido con el informe de infraestructura | Columna «Verifica» | T54: una aprobación desde fuera del campus devuelve 403 |
| Fxx | Flujo de red permitido por el firewall, definido en el informe de infraestructura. Se escribe sin guion, a diferencia de F-xx | Anexo B | F10: nodo → CTRL01, TCP 8443 |
| OB-x | Objetivo del proyecto, definido en el caso de negocio (CE01) | Anexo B | OB-1: ahorro de Internet |
| H-xx | Vacío identificado al contrastar requisitos, prototipo y diseño, y la forma en que se resolvió | Anexo B | H-01: ausencia de la acción «Purgar» en P-03 |

Un identificador retirado no se reutiliza; por ello, la numeración presenta saltos (por ejemplo, no existe REQ-F-16).

## 0.2 Supuestos

Un supuesto es un dato aún no confirmado que se adopta como base del diseño. Para cada uno se indica el método de
confirmación y, cuando afecta al software, la consecuencia de que resulte falso. Los valores proceden del registro
común del proyecto.

{{tabla:supuestos}}

No existen supuestos vigentes con los números S-18 ni S-20 a S-25: correspondieron a componentes de versiones
anteriores del diseño, ya retirados, y su numeración no se reutiliza.

## 0.3 Decisiones de arquitectura

El proyecto registra 29 decisiones. Las 15 de software se fundamentan en la sección 3.2 con su contexto, las
opciones evaluadas y sus consecuencias. Las 9 de infraestructura (red, firewall y zonas) se detallan en el informe de
infraestructura (CE03). Las 5 restantes correspondían a la versión anterior del diseño y ya no se aplican.

{{tabla:decisiones}}
