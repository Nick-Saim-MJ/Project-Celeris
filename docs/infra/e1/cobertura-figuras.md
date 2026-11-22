# Cobertura componente × figura (P3)

Generado por `infra/gen/drawio_check.py` desde `entregables/CE0311/diagramas/*.drawio`. No editar a mano.
Un componente cuenta como presente si tiene caja propia con `celeris_id`. Los que un bloque de FIG-1.1 agrupa
(`celeris_incluye`) se listan aparte: la vista ejecutiva no los dibuja uno por uno.

## Resultado de V-50…V-56

| ID | Chequeo | Estado | Hallazgos |
|---|---|---|---|
| V-50 | Figuras .drawio, .png y .pdf presentes, con XML embebido y al día | ADVERTENCIA | 14 |
| V-51 | Cobertura componente × figura igual al campo `figuras` del inventario | PASA | 0 |
| V-52 | Todo celeris_id es un ID del contrato | PASA | 0 |
| V-53 | IP y CIDR rotulados existen en el inventario (y son del componente que los rotula) | PASA | 0 |
| V-54 | Flujos F-nn: FIG-5.5a ∪ FIG-5.5b completas y etiquetas derivadas del inventario | PASA | 0 |
| V-55 | Título, leyenda y panel «Qué aporta y qué pasa si falla» en cada figura | PASA | 0 |
| V-56 | Criticidad (borde + texto) y color de zona según CLAUDE.md | PASA | 0 |

- **V-50** [advertencia] FIG-1.1.png es anterior a FIG-1.1.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-1.1.pdf es anterior a FIG-1.1.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.1.png es anterior a FIG-5.1.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.1.pdf es anterior a FIG-5.1.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.2.png es anterior a FIG-5.2.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.2.pdf es anterior a FIG-5.2.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.3.png es anterior a FIG-5.3.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.3.pdf es anterior a FIG-5.3.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.4.png es anterior a FIG-5.4.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.4.pdf es anterior a FIG-5.4.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.5a.png es anterior a FIG-5.5a.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.5a.pdf es anterior a FIG-5.5a.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.5b.png es anterior a FIG-5.5b.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py
- **V-50** [advertencia] FIG-5.5b.pdf es anterior a FIG-5.5b.drawio — Vuelva a exportar: python infra/gen/exportar_drawio.py

## Por figura

| Figura | Componentes | Flujos F-nn |
|---|---|---|
| FIG-1.1 | 4 | F1, F8, F13, F21 |
| FIG-5.1 | 37 | — |
| FIG-5.2 | 33 | — |
| FIG-5.3 | 26 | — |
| FIG-5.4 | 11 | — |
| FIG-5.5a | 10 | F1, F2, F3, F5, F6, F7, F8, F21, F22, F23, F24, F25 |
| FIG-5.5b | 21 | F9, F10, F11, F12, F13, F14, F15, F16, F17, F18, F19, F20, F26, F27 |

Agrupados en bloques de FIG-1.1: AWS-VPC, EC2-CTRLR, EC2-SHIELD, EDGE01, EDGE02, HNY01, IDS01, NAT01, SIEM01, VTI1, VTI2, WAF01, WEB01.

Flujos sin figura asignada (no se dibujan): F4.

## Matriz componente × figura

| Componente | Crit. | 1.1 | 5.1 | 5.2 | 5.3 | 5.4 | 5.5a | 5.5b | Total |
|---|---|---|---|---|---|---|---|---|---|
| FW01 | Alta | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | 7 |
| SW-CORE01 | Alta |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| SW-ACC | Alta |  | ✔ | ✔ | ✔ |  |  |  | 3 |
| BRK01 | Media |  | ✔ |  | ✔ |  |  |  | 2 |
| ESX01 | Alta | ✔ | ✔ | ✔ | ✔ |  |  | ✔ | 5 |
| IPMI01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| UPS01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| JMP01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| CTRL01 | Alta |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| DB01 | Alta |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| OBS01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| SVC01 | Alta |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| EDGE01 | Alta |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| EDGE02 | Alta |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| WAF01 | Alta |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| WEB01 | Alta |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| HNY01 | Media |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| SIEM01 | Alta |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| IDS01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| HNY02 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| PROBE01 | Baja |  | ✔ | ✔ | ✔ |  | ✔ |  | 4 |
| LABCLI01 | Baja |  | ✔ | ✔ | ✔ |  | ✔ |  | 4 |
| KALI01 | Baja |  | ✔ | ✔ | ✔ |  | ✔ |  | 4 |
| NAS01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| VTI1 | Alta |  | ✔ |  | ✔ | ✔ |  |  | 3 |
| VTI2 | Alta |  | ✔ |  | ✔ | ✔ |  |  | 3 |
| VGW | Alta | ✔ | ✔ |  |  | ✔ |  |  | 3 |
| EC2-SHIELD | Media |  | ✔ | ✔ |  | ✔ |  | ✔ | 4 |
| EC2-CTRLR | Media |  | ✔ | ✔ |  | ✔ |  | ✔ | 4 |
| NAT01 | Media |  | ✔ | ✔ |  | ✔ |  |  | 3 |
| AWS-VPC | Alta | ✔ | ✔ | ✔ |  | ✔ |  |  | 4 |
| AWS-PUB-A | Media |  | ✔ | ✔ |  | ✔ |  |  | 3 |
| AWS-PUB-B | Baja |  | ✔ | ✔ |  |  |  |  | 2 |
| AWS-APP-A | Media |  | ✔ | ✔ |  | ✔ |  |  | 3 |
| AWS-APP-B | Media |  | ✔ | ✔ |  | ✔ |  |  | 3 |
| AWS-DATA-A | Baja |  | ✔ | ✔ |  |  |  |  | 2 |
| AWS-DATA-B | Baja |  | ✔ | ✔ |  |  |  |  | 2 |
