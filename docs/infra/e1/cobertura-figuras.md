# Cobertura componente × figura (P3)

Generado por `infra/gen/drawio_check.py` desde `entregables/CE0311/diagramas/*.drawio`. No editar a mano.
Un componente cuenta como presente si tiene caja propia con `celeris_id`. Los que un bloque de FIG-1.1 agrupa
(`celeris_incluye`) se listan aparte: la vista ejecutiva no los dibuja uno por uno.

## Resultado de V-50…V-56

| ID | Chequeo | Estado | Hallazgos |
|---|---|---|---|
| V-50 | Figuras .drawio, .png y .pdf presentes, con XML embebido y al día | PASA | 0 |
| V-51 | Cobertura componente × figura igual al campo `figuras` del inventario | FALLA | 30 |
| V-52 | Todo celeris_id es un ID del contrato | FALLA | 93 |
| V-53 | IP y CIDR rotulados existen en el inventario (y son del componente que los rotula) | FALLA | 16 |
| V-54 | Flujos F-nn: FIG-5.5a ∪ FIG-5.5b completas y etiquetas derivadas del inventario | FALLA | 20 |
| V-55 | Título, leyenda y panel «Qué aporta y qué pasa si falla» en cada figura | PASA | 0 |
| V-56 | Criticidad (borde + texto) y color de zona según CLAUDE.md | FALLA | 3 |

- **V-51** [error] FGT-EXT falta en FIG-1.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] FGT-EXT falta en FIG-5.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] FGT-EXT falta en FIG-5.2 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PORTAL01 falta en FIG-5.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PORTAL01 falta en FIG-5.2 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PORTAL01 falta en FIG-5.3 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PORTAL01 falta en FIG-5.5a (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PORTAL01 falta en FIG-5.5b (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] ENC01 falta en FIG-5.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] ENC01 falta en FIG-5.2 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] ENC01 falta en FIG-5.3 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] ENC01 falta en FIG-5.5b (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PCS-LAB falta en FIG-1.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PCS-LAB falta en FIG-5.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PCS-LAB falta en FIG-5.2 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PCS-LAB falta en FIG-5.3 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] PCS-LAB falta en FIG-5.5a (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] WIFI-EST falta en FIG-1.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] WIFI-EST falta en FIG-5.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] WIFI-EST falta en FIG-5.2 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] WIFI-EST falta en FIG-5.5a (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] EC2-GW falta en FIG-1.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] EC2-GW falta en FIG-5.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] EC2-GW falta en FIG-5.2 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] EC2-GW falta en FIG-5.3 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] EC2-GW falta en FIG-5.4 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] EC2-GW falta en FIG-5.5b (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] S3 falta en FIG-1.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] S3 falta en FIG-5.1 (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-51** [error] S3 falta en FIG-5.5b (campo `figuras`) — Añádalo a la disposición de la figura en drawio.py
- **V-52** [error] FIG-5.1: dibuja el ID retirado «WAF01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «WEB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «IDS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «PROBE01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «LAB-TEST» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «DB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «OBS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «SVC01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «BACKUP» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «NAS01:respaldo» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «NAS01:gestion» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «STORAGE» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «NAS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: celeris_id desconocido «ESX01:vmk1» — Use solo IDs de infra/*.yaml
- **V-52** [error] FIG-5.1: dibuja el ID retirado «NAT01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «AWS-PUB-B» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «EC2-SHIELD» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «AWS-APP-B» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «EC2-CTRLR» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «AWS-DATA-A» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.1: dibuja el ID retirado «AWS-DATA-B» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «NAS01:gestion» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «DB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «OBS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «SVC01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «PROBE01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «LAB-TEST» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «WAF01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «WEB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «IDS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «STORAGE» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: celeris_id desconocido «ESX01:vmk1» — Use solo IDs de infra/*.yaml
- **V-52** [error] FIG-5.2: dibuja el ID retirado «NAS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «BACKUP» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «NAS01:respaldo» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «NAT01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «EC2-SHIELD» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «AWS-DATA-A» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «AWS-PUB-B» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «AWS-APP-B» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «EC2-CTRLR» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.2: dibuja el ID retirado «AWS-DATA-B» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «WAF01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «WEB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «PROBE01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «LAB-TEST» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «DB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «OBS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «SVC01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «IDS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «BACKUP» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «NAS01:respaldo» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «STORAGE» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: dibuja el ID retirado «NAS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.3: celeris_id desconocido «ESX01:vmk1» — Use solo IDs de infra/*.yaml
- **V-52** [error] FIG-5.3: dibuja el ID retirado «NAS01:gestion» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.4: dibuja el ID retirado «NAT01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.4: dibuja el ID retirado «EC2-SHIELD» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.4: dibuja el ID retirado «AWS-APP-B» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.4: dibuja el ID retirado «EC2-CTRLR» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «WAF01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «WEB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «PROBE01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «LAB-TEST» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «SVC01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «BACKUP» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «STORAGE» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «F22» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5a: dibuja el ID retirado «F23» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «WAF01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «WEB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «LAB-TEST» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «DB01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «OBS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «SVC01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «IDS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «BACKUP» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «NAS01:respaldo» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «STORAGE» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «NAS01» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: celeris_id desconocido «ESX01:vmk1» — Use solo IDs de infra/*.yaml
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «NAS01:gestion» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «EC2-SHIELD» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «EC2-CTRLR» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F9» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F11» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F12» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F12» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F12» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F15» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F16» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F17» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-52** [error] FIG-5.5b: dibuja el ID retirado «F19» (v0.4); pendiente de I4: regenerar los diagramas — Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)
- **V-53** [error] FIG-1.1: la caja de FW01 rotula 203.0.113.10, que no es de FW01
- **V-53** [error] FIG-1.1: «10.20.70.10» en ESX01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.1: la caja de FW01 rotula 203.0.113.10, que no es de FW01
- **V-53** [error] FIG-5.1: «10.20.32.50» en LABCLI01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.1: «10.20.31.60» en KALI01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.2: la caja de FW01 rotula 203.0.113.10, que no es de FW01
- **V-53** [error] FIG-5.2: «10.20.32.50» en LABCLI01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.2: «10.20.31.60» en KALI01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.3: la caja de FW01 rotula 203.0.113.10, que no es de FW01
- **V-53** [error] FIG-5.3: «10.20.32.50» en LABCLI01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.3: «10.20.31.60» en KALI01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.4: la caja de FW01 rotula 203.0.113.10, que no es de FW01
- **V-53** [error] FIG-5.5a: la caja de FW01 rotula 203.0.113.10, que no es de FW01
- **V-53** [error] FIG-5.5a: «10.20.32.50» en LABCLI01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.5a: «10.20.31.60» en KALI01 no está en infra/inventory.yaml — Corrija el generador o registre el CI-nn
- **V-53** [error] FIG-5.5b: la caja de FW01 rotula 203.0.113.10, que no es de FW01
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5b: F20 con etiqueta «F20 · TCP/22,443,3000,5601,9128 · SSH»; se espera «F20 · TCP/22,443,9128 · SSH»
- **V-54** [error] FIG-5.5a: falta F31
- **V-54** [error] FIG-5.5a: falta F32
- **V-54** [error] FIG-5.5b: falta F28
- **V-54** [error] FIG-5.5b: falta F29
- **V-54** [error] FIG-5.5b: falta F30
- **V-54** [error] FIG-5.5b: falta F33
- **V-56** [error] FIG-5.1: AWS-APP-A con criticidad Media; inventario: Baja
- **V-56** [error] FIG-5.2: AWS-APP-A con criticidad Media; inventario: Baja
- **V-56** [error] FIG-5.4: AWS-APP-A con criticidad Media; inventario: Baja

## Por figura

| Figura | Componentes | Flujos F-nn |
|---|---|---|
| FIG-1.1 | 4 | F1, F8, F13, F21 |
| FIG-5.1 | 22 | — |
| FIG-5.2 | 18 | — |
| FIG-5.3 | 18 | — |
| FIG-5.4 | 7 | — |
| FIG-5.5a | 6 | F1, F2, F3, F5, F6, F7, F8, F21, F24, F25 |
| FIG-5.5b | 12 | F10, F13, F14, F18, F20, F26, F27 |

Agrupados en bloques de FIG-1.1: AWS-VPC, EDGE01, EDGE02, HNY01, SIEM01, VTI1, VTI2.

Flujos sin figura asignada (no se dibujan): F4.

## Matriz componente × figura

| Componente | Crit. | 1.1 | 5.1 | 5.2 | 5.3 | 5.4 | 5.5a | 5.5b | Total |
|---|---|---|---|---|---|---|---|---|---|
| FGT-EXT | Alta |  |  |  |  |  |  |  | 0 |
| FW01 | Alta | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | 7 |
| SW-CORE01 | Alta |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| SW-ACC | Alta |  | ✔ | ✔ | ✔ |  |  |  | 3 |
| BRK01 | Media |  | ✔ |  | ✔ |  |  |  | 2 |
| ESX01 | Alta | ✔ | ✔ | ✔ | ✔ |  |  | ✔ | 5 |
| IPMI01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| UPS01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| JMP01 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| CTRL01 | Alta |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| EDGE01 | Alta |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| EDGE02 | Alta |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| PORTAL01 | Alta |  |  |  |  |  |  |  | 0 |
| HNY01 | Media |  | ✔ | ✔ | ✔ |  | ✔ | ✔ | 5 |
| SIEM01 | Alta |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| HNY02 | Media |  | ✔ | ✔ | ✔ |  |  | ✔ | 4 |
| ENC01 | Media |  |  |  |  |  |  |  | 0 |
| LABCLI01 | Baja |  | ✔ | ✔ | ✔ |  | ✔ |  | 4 |
| KALI01 | Baja |  | ✔ | ✔ | ✔ |  | ✔ |  | 4 |
| PCS-LAB | Alta |  |  |  |  |  |  |  | 0 |
| WIFI-EST | Media |  |  |  |  |  |  |  | 0 |
| VTI1 | Alta |  | ✔ |  | ✔ | ✔ |  |  | 3 |
| VTI2 | Alta |  | ✔ |  | ✔ | ✔ |  |  | 3 |
| VGW | Alta | ✔ | ✔ |  |  | ✔ |  |  | 3 |
| AWS-VPC | Alta | ✔ | ✔ | ✔ |  | ✔ |  |  | 4 |
| AWS-PUB-A | Media |  | ✔ | ✔ |  | ✔ |  |  | 3 |
| AWS-APP-A | Baja |  | ✔ | ✔ |  | ✔ |  |  | 3 |
| EC2-GW | Media |  |  |  |  |  |  |  | 0 |
| S3 | Alta |  |  |  |  |  |  |  | 0 |
| EC2-DR | Baja |  |  |  |  |  |  |  | 0 |
| NAT-DR | Baja |  |  |  |  |  |  |  | 0 |
