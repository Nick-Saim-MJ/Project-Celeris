# Diseño detallado — diagramas UML (CE02 E1, sección 4)

Versión: **v0.2** (24/11/2026), alineada con la **arquitectura v0.4** y con `docs/celeris/Celeris-CE02-Ingenieria-Software.md`
§C3.3 y §C4. Herramienta: PlantUML 1.2026.9 + Graphviz. Fuentes: CE02 C4.1–C4.9, el código del nodo en `src/`, el
prototipo v0.2 (`../prototipo/pantallas.md`) y los componentes, IP y flujos de `infra/inventory.yaml`.

## Convenciones

- **«R1»** (fondo blanco): existe en el código del nodo; los nombres de tipos y métodos son los reales de `src/`.
  **«R2»** (fondo azul claro, borde azul): diseño de `celeris-console` o de partes nuevas del nodo (agente de
  configuración, precarga, BYOD); se construye en S2. El color siempre va con el estereotipo escrito.
- Cada diagrama lleva en su pie su ID (DS-nn) y los requisitos, casos de uso y pantallas que cubre.
- IP, componentes y flujos salen del inventario; `render.py` rechaza cualquiera que no exista (reglas D-01 a D-08).
  Los rangos /26 de los laboratorios se nombran sin IP (el validador solo admite direcciones de host del inventario).
- Datos de ejemplo iguales a los del prototipo (LAB-03, SOL-12, fuente «Instaladores de JetBrains», configuración v43 → v44).

## Índice

Cubre lo que pide la rúbrica de CE02 (C7): dominio, tres o más secuencias, tres diagramas de estados, modelo de datos y API.

| ID | Diagrama | Tipo | Versión | CE02 | Requisitos principales | CU | Pantallas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DS-14 | Casos de uso | Casos de uso | R1 + R2 | C1.6 | REQ-F-31…F-37, RN-05, RN-07 | CU-01…CU-11 | P-01…P-11 |
| DS-01 | Modelo de dominio | Clases | R1 + R2 | C4.1 | REQ-F-17, F-18, F-24, F-31…F-37, NF-07, RN-06…RN-11 | CU-03…CU-07, CU-09…CU-11 | P-02…P-08, P-11 |
| DS-02 | Clases de diseño de `celeris-node` | Clases | R1 + puertos R2 | C3.3 | REQ-F-01…F-11, F-13…F-15, F-17, F-28 | CU-01, CU-06 | P-02, P-11 |
| DS-03 | Clases de diseño de `celeris-console` | Clases | R2 | C3.3 | REQ-F-17, F-20, F-24…F-26, F-30…F-37 | CU-03…CU-07, CU-09…CU-11 | P-01…P-08, P-11 |
| DS-15 | Fuente que requiere descifrado: creación, 403 desde remoto y aprobación desde el campus | Secuencia | R2 | C4.2 | REQ-F-20, F-31, F-37, RN-04, RN-05, RN-07, RN-08 | CU-03, CU-07, CU-11 | P-03, P-07, P-08, P-09 |
| DS-16 | Precarga nocturna desde una solicitud y HIT en la clase | Secuencia | R2 | C4.3 | REQ-F-22, F-34, F-35, RN-10, NF-07 | CU-05, CU-06, CU-09 | P-02, P-05, P-06, P-11 |
| DS-04 | MISS con coalescencia y HIT | Secuencia | R1 | C4.4 | REQ-F-03, F-05, F-06, F-07, F-28 | CU-01 | P-02, P-05, P-11 |
| DS-19 | Cambio de laboratorio firmado hasta los nodos y KPI de vuelta (F10) | Secuencia | R2 | C3.2, C4.9 | REQ-F-10, F-13, F-17, F-32, NF-16, RN-08, RN-11 | CU-04, CU-06 | P-04, P-08, P-11 |
| DS-05 | CONNECT y decisión de descifrado por SNI (con BYOD en R2) | Secuencia | R1 + R2 | C3.3 | REQ-F-02, F-10, F-11, F-36, RN-03, RN-11 | CU-01, CU-03 | P-03, P-04, P-09 |
| DS-06 | Revalidación 304 | Secuencia | R1 | — | REQ-F-04, F-06, F-09 | CU-01 | P-02, P-11 |
| DS-17 | Estados de una fuente del catálogo | Estados | R2 | C4.5 | REQ-F-31, F-37, RN-03, RN-04, RN-07, RN-09 | CU-03, CU-07, CU-08 | P-03, P-07, P-09 |
| DS-18 | Estados de una precarga | Estados | R2 | C4.6 | REQ-F-22, F-34, F-35, RN-10 | CU-05, CU-09 | P-02, P-05, P-06 |
| DS-09 | Estados de una entrada de caché | Estados | R1 | C4.7 | REQ-F-03…F-06, F-09, RN-01, RN-02 | CU-01 | P-02, P-05, P-11 |
| DS-12 | Modelo de datos de la consola | Entidad-relación | R2 | C4.8 | REQ-F-17, F-24, F-25, F-31…F-35, F-37, NF-07 | CU-03…CU-07, CU-09…CU-11 | P-01…P-08, P-11 |
| DS-13 | Componentes C3 del nodo → archivos y crates | Componentes | R1 + R2 | C3.3 | REQ-F-01…F-15, F-17, F-26, F-28 | CU-01, CU-04, CU-06 | P-02, P-04, P-09, P-11 |

Archivos: fuente en `src/DS-nn-*.puml` (estilo común en `src/_estilo.iuml`), imágenes en `png/` (para el informe) y
`svg/` (vectorial).

### Retirados en la v0.2 (no se reutilizan sus IDs)

| ID | Diagrama v0.1 | Motivo |
| --- | --- | --- |
| DS-07 | Política con aprobación de cuatro ojos | La v0.4 reemplaza la regla entre operadores por REQ-RN-07 (el encargado propone, la DTI aprueba solo lo que se descifra): DS-15 |
| DS-08 | Enrolamiento de un nodo | REQ-F-16 retirado (C1.8): con dos nodos basta la configuración firmada (DS-19) |
| DS-10 | Estados de un nodo (enrolamiento, rollout) | Ídem; además citaba DB01 y EC2-CTRLR, retirados |
| DS-11 | Estados de una versión de política | La versión de configuración es inmutable y no tiene flujo de propuesta y aprobación propio; los estados relevantes son los de la fuente (DS-17) y la precarga (DS-18) |

Además se rehicieron DS-01, DS-03 y DS-12, que usaban `celeris-control`, Tenant/Site, operadores, Cedar y DB01.

## API de la consola (CE02 C4.9, R2)

Transporte: la SPA llega por TLS 443, desde el campus (ENC01 por F28, JMP01 por F20) o de forma remota (EC2-GW por F30,
con certificado de cliente); los nodos, por F10 (TCP 8443, mTLS, EDGE → CTRL01 10.20.20.10). La columna «Origen» aplica
REQ-F-37: **solo campus** significa que una llamada que llega por EC2-GW recibe 403 y queda en la auditoría.

| Método | Ruta | Uso | Rol | Origen | Requisitos | Diagrama · Pantalla |
| --- | --- | --- | --- | --- | --- | --- |
| POST | `/v1/sesion` | Login con contraseña y TOTP; la sesión guarda su origen | Todos | campus o remoto | REQ-F-33, F-37 | DS-03 · P-01 |
| GET/POST/PATCH | `/v1/fuentes` | Catálogo | Encargado | campus o remoto | REQ-F-31, RN-07, RN-09 | DS-15 · P-03 |
| POST | `/v1/fuentes/{id}/simular` | ¿Se descifraría? ¿Se guardaría? ¿La CA lo cubre? | Encargado | campus o remoto | REQ-F-20, RN-04 | DS-15 · P-03 |
| POST | `/v1/fuentes/{id}/aprobar` | Aprobar o rechazar una fuente a descifrar | Admin | **solo campus** | REQ-RN-07, F-37 | DS-15 · P-07 |
| POST | `/v1/ca/{nodo}/rotacion` *(nueva)* | Proponer y aprobar la rotación de una CA intermedia | Admin | **solo campus** para aprobar | REQ-F-18, F-37 | DS-01 · P-07 |
| GET/PATCH | `/v1/laboratorios/{id}` | Habilitar y horario (el rango /26 es de solo lectura) | Encargado asignado | campus o remoto | REQ-F-32, RN-06 | DS-19 · P-04 |
| GET/POST/PATCH | `/v1/precargas` | Programar, editar y ver avance | Encargado | campus o remoto | REQ-F-34, RN-10 | DS-16 · P-05 |
| GET/POST | `/v1/solicitudes` *(nueva)* | Pedidos de los docentes y conversión en precarga | Docente, encargado | campus o remoto | REQ-F-35 | DS-16 · P-06 |
| GET | `/v1/reportes/ahorro?lab=&desde=&hasta=` | Ahorro del mes | Encargado, auditor | campus o remoto | REQ-F-25 | DS-16 · P-02 |
| GET | `/v1/reportes/en-vivo?lab=` *(nueva)* | Últimos agregados de 30 s por laboratorio y nodo | Encargado, admin | campus o remoto | REQ-F-13, NF-13, NF-07 | DS-19 · P-11 |
| GET | `/v1/auditoria` | Cambios e intentos rechazados, con origen | Auditor, admin | campus o remoto | REQ-F-24, F-37 | DS-15 · P-08 |
| POST/PATCH | `/v1/usuarios` *(nueva)* | Crear usuarios y asignar laboratorios | Admin | **solo campus** | REQ-F-33, F-37, RN-06 | DS-12 · — |
| GET | `/v1/nodos/{id}/config?desde=v` | El nodo descarga la configuración firmada (cada 30 s) | Nodo (mTLS) | F10 | REQ-F-17, RN-08 | DS-15, DS-19 |
| POST | `/v1/nodos/{id}/kpi` | El nodo reporta versión aplicada, avance de precargas y agregados por laboratorio | Nodo (mTLS) | F10 | REQ-F-13, F-22, NF-16 | DS-16, DS-19 |

Las rutas marcadas *(nueva)* no están en C4.9 (hueco H-11).

## Huecos encontrados al diseñar (para el SRS y CE02)

Continúa la numeración de `../prototipo/pantallas.md` (H-01 a H-03). H-05, H-06 y H-07 de la v0.1 quedan cerrados:
el portal lo despliega JMP01 por F20 (está en el inventario), el *heartbeat* es el `POST /kpi` de F10 y ya no hay
operadores ni tokens de enrolamiento.

| ID | Hueco | Propuesta |
| --- | --- | --- |
| H-04 | C4.4 muestra `Cache-Status: celeris; fwd=miss; stored` y «collapsed»; el código responde `x-celeris-cache: MISS/HIT/REVALIDATED` y el que esperó en el coalescer recibe HIT. REQ-NF-11 exige Cache-Status (RFC 9211). | Implementar Cache-Status en R2 y corregir C4.4. DS-04 dibuja lo real. |
| H-08 | REQ-NF-14 exige TLS en el puerto de administración del nodo; está hecho en la rama `e1/matriz-pruebas`, falta fusionarlo en `main`. | Mantenerlo como «hecho en la rama» en el SRS. |
| H-09 | C4.7 lleva «Vencida → Llenando» con 200; en el código un 200 nuevo se guarda directo y la entrada queda Fresca. | DS-09 dibuja el comportamiento real; corregir C4.7. |
| H-10 | C4.8 no tiene `sesion` (con origen campus/remoto, que exige REQ-F-37), `ca_intermedia` (P-07), `kpi_intervalo` (P-11) ni las columnas `cambio.sesion_id`, `cambio.resultado` y `fuente.fija`. | Agregarlas a C4.8 (DS-12 las marca «nueva»). |
| H-11 | C4.9 no tiene rutas para solicitudes (REQ-F-35), usuarios, rotación de CA ni la vista en vivo (P-11). | Agregarlas a C4.9 (tabla de arriba, *(nueva)*). |
| H-12 | D-20, D-21 y D-22 estaban en CE02 C3.4 pero no en `infra/trazabilidad.yaml`. | **Cerrado** por CI-95: agregadas al YAML; DS-01, DS-12, DS-16, DS-17 y DS-18 las citan. |

## Cómo regenerar

Requiere Java 11+ y Graphviz. Desde la raíz del repositorio:

```
python docs/software/e1/diagramas/render.py --descargar   # la primera vez: baja PlantUML y verifica su SHA-256
python docs/software/e1/diagramas/render.py               # valida IDs contra infra/*.yaml y genera png/ y svg/
python docs/software/e1/diagramas/render.py --solo-validar
```

PlantUML queda en `.tools/plantuml/` (ignorado por git). La fuente PNG usa Arial para que el resultado sea igual en
Windows y Linux.
