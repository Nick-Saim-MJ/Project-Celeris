## 1.11 Interfaces externas y datos

### 1.11.1 Interfaces de usuario

Son las 11 pantallas del prototipo v0.2 (Sección 2, `docs/software/e1/prototipo/`). Todas siguen estas reglas:

- No piden datos personales de los usuarios de laboratorio.
- Muestran cifras solo por laboratorio y por nodo (REQ-NF-07).
- Cuando la sesión es `remoto`, muestran el distintivo «acceso remoto» y deshabilitan las acciones críticas con su
  motivo (REQ-F-37).

| Pantalla | Rol | Requisitos |
| --- | --- | --- |
| P-01 Inicio de sesión con segundo factor | Todos | REQ-F-33, F-37 |
| P-02 Resumen: ahorro del mes, nodos, alertas | Encargado, admin, auditor | REQ-F-25, F-13 |
| P-03 Catálogo y simulador | Encargado | REQ-F-31, F-20, F-19 (v0.3), RN-07, RN-09 |
| P-04 Laboratorios: habilitar y horario | Encargado | REQ-F-32, RN-06 |
| P-05 Precargas | Encargado | REQ-F-34, F-22, RN-10 |
| P-06 Solicitudes de docentes | Encargado, docente (solo las suyas) | REQ-F-35 |
| P-07 Aprobaciones y certificados | Admin (acciones solo desde el campus) | REQ-RN-07, F-18, F-37 |
| P-08 Auditoría | Auditor, admin | REQ-F-24 |
| P-09 Portal: aviso de transparencia | Usuario | REQ-F-12, F-30 |
| P-10 Portal: instalación de la CA con verificación de huella | Usuario | REQ-RN-05 |
| P-11 Actividad en vivo (desviación de C2.1, sección 1.13.2) | Encargado, admin | REQ-F-13, NF-13, NF-07 |

### 1.11.2 Interfaces de software y comunicaciones

| Interfaz | Expone | Puerto y protección | Consumidor |
| --- | --- | --- | --- |
| Proxy del nodo | HTTP y `CONNECT` | TCP 3128 en 10.20.60.10 y .11 (F1, F31) | PCs de LAB; BYOD opcional |
| PAC | `wpad.dat` con EDGE01, EDGE02 y `DIRECT` | TCP 80 (F3); sin cifrar, con riesgo aceptado | GPO de las PCs |
| Administración del nodo | Panel local y métricas | TCP 9128 solo con TLS (REQ-NF-14) | JMP01 10.20.10.20 (F20) |
| API de la consola | REST JSON `/v1/…` (1.11.3) | TCP 443 en CTRL01 10.20.20.10: F28 (TLS) y F30 (mTLS de EC2-GW en IPsec) | SPA en ENC01 o por EC2-GW |
| API de nodos | `/v1/nodos/{id}/…` | TCP 8443 en CTRL01 10.20.20.10 (F10, mTLS) | Agente de EDGE01 y EDGE02 |
| Eventos de seguridad | Agente Wazuh | TCP 1514 y 1515 hacia 10.20.50.10 (F13) | SIEM01 |
| Respaldo | restic, cifrado en origen | TCP 443 a S3 `celeris-backups` (F18) | CTRL01 |
| Origen | HTTP y HTTPS verificado (webpki) | TCP 80 y 443 por el FortiGate (F8) | Nodo (MISS y precargas) |

### 1.11.3 API de la consola (cierra H-11)

Esta tabla reemplaza el borrador de CE02 C4.9. Las rutas marcadas *(nueva)* no estaban en C4.9; las pide el diseño
(DS-03) y el prototipo.

| Método | Ruta | Uso | Rol | Origen permitido | Requisitos |
| --- | --- | --- | --- | --- | --- |
| POST | `/v1/sesion` | Iniciar sesión con contraseña y TOTP. La sesión guarda su origen | Todos | campus o remoto | REQ-F-33, F-37 |
| GET/POST/PATCH | `/v1/fuentes` | Catálogo | Encargado | campus o remoto | REQ-F-31, RN-07, RN-09 |
| POST | `/v1/fuentes/{id}/simular` | ¿Se descifraría? ¿Se guardaría? ¿La CA lo cubre? | Encargado | campus o remoto | REQ-F-20, RN-04 |
| POST | `/v1/fuentes/{id}/purgar` *(nueva)* | Purgar la fuente, una URL o un prefijo | Encargado | campus o remoto | REQ-F-19, F-24 |
| POST | `/v1/fuentes/{id}/aprobar` | Aprobar o rechazar una fuente a descifrar | Admin | **solo campus** | REQ-RN-07, F-37 |
| POST | `/v1/ca/{nodo}/rotacion` *(nueva)* | Proponer y aprobar la rotación de una CA intermedia | Admin | **solo campus** | REQ-F-18, F-37 |
| GET/PATCH | `/v1/laboratorios/{id}` | Habilitar y fijar el horario (el rango /26 es de solo lectura) | Encargado asignado | campus o remoto | REQ-F-32, RN-06 |
| GET/POST/PATCH | `/v1/precargas` | Programar, editar y ver el avance | Encargado | campus o remoto | REQ-F-34, RN-10 |
| GET/POST | `/v1/solicitudes` *(nueva)* | El docente las crea y ve las suyas; el encargado las convierte en precarga | Docente, encargado | campus o remoto | REQ-F-35 |
| GET | `/v1/reportes/ahorro?lab=&desde=&hasta=` | Ahorro | Encargado, auditor | campus o remoto | REQ-F-25 |
| GET | `/v1/reportes/en-vivo?lab=` *(nueva)* | Últimos agregados de 30 s por laboratorio y nodo | Encargado, admin | campus o remoto | REQ-F-13, NF-13, NF-07 |
| GET | `/v1/auditoria` | Cambios e intentos rechazados, con su origen | Auditor, admin | campus o remoto | REQ-F-24, F-37 |
| POST/PATCH | `/v1/usuarios` *(nueva)* | Crear usuarios y asignar laboratorios | Admin | **solo campus** | REQ-F-33, F-37, RN-06 |
| PATCH | `/v1/perfil-byod` *(nueva)* | Cambiar las redes de origen BYOD de la configuración | Admin | **solo campus** | REQ-F-36, F-37, RN-11 |
| GET | `/v1/nodos/{id}/config?desde=v` | El nodo descarga la configuración firmada (cada 30 s) | Nodo (mTLS) | F10 | REQ-F-17, RN-08 |
| POST | `/v1/nodos/{id}/kpi` | El nodo reporta la versión aplicada, el avance de las precargas y los agregados por laboratorio | Nodo (mTLS) | F10 | REQ-F-13, F-22, NF-16 |

**Errores comunes.**

| Código | Cuándo |
| --- | --- |
| 401 | Sin sesión o sin segundo factor |
| 403 | Rol o laboratorio no asignado (REQ-RN-06), o acción crítica con origen `remoto` (REQ-F-37) |
| 409 | Versión de configuración desactualizada al editar |
| 422 | Regla de negocio violada (REQ-RN-04, RN-09, RN-10, RN-11) |

Todo 403 y todo 422 queda en `cambio` con `resultado = rechazado` (REQ-F-24).

### 1.11.4 Requisitos de datos lógicos (cierra H-10)

La base es PostgreSQL local en CTRL01 (D-12, D-25). DS-12 es el diagrama entidad-relación. Esta tabla reemplaza a
CE02 C4.8. Lo marcado *(nueva)* no estaba en C4.8.

| Tabla | Columnas principales | Regla |
| --- | --- | --- |
| `laboratorio` | id, nombre, rango_cidr, habilitado, horario | Los rangos vienen de `infra/inventory.yaml` (LAB-01 10.20.32.0/26 … LAB-10 10.20.34.64/26) y no se editan |
| `usuario` | id, nombre, rol (`encargado`, `admin`, `auditor`, `docente`), hash_contraseña, totp_secreto_cifrado, bloqueado_hasta | El rol `docente` es nuevo (H-03) |
| `asignacion` | usuario_id, laboratorio_id | REQ-RN-06 |
| `sesion` *(nueva)* | id, usuario_id, origen (`campus`, `remoto`), equipo (ENC01, JMP01, EC2-GW), vence | REQ-F-37 |
| `fuente` | id, nombre, categoria, modo, estado, fija *(nueva)* | `fija` = lista de la DTI (REQ-RN-09) |
| `fuente_dominio` | fuente_id, sufijo | — |
| `aprobacion` | id, objeto_tipo (fuente, rotacion_ca), objeto_id, decision, por, sesion_id, fecha | La sesión debe ser de origen `campus` (REQ-F-37) |
| `ca_intermedia` *(nueva)* | serie, nodo_id, vence, huella_sha256, name_constraints | P-07, REQ-F-18 |
| `precarga` | id, laboratorio_id, fecha, ventana_inicio, ventana_fin, estado, bytes_total, fuente_id | REQ-RN-10 |
| `precarga_item` | precarga_id, url_sin_query, sha256, estado | La URL se guarda sin parámetros (REQ-NF-07) |
| `solicitud` | id, docente_id *(antes `docente` en texto)*, laboratorio_id, fecha_clase, descripcion, estado, precarga_id | REQ-F-35 |
| `version_config` | version, contenido, firma, publicada_por, publicada_en | Inmutable. Incluye las órdenes de purga (REQ-F-19) y las redes BYOD (REQ-RN-11) |
| `nodo` | id (EDGE01, EDGE02), version_aplicada, ultimo_informe | — |
| `kpi_intervalo` *(nueva)* | nodo_id, laboratorio_id, ts, hit, revalidated, miss, bypass, rechazos_403, bytes_cache, bytes_origen | Fuente de P-11. Ningún campo identifica a una PC o a una persona (REQ-NF-07, D-22) |
| `kpi_diario` | fecha, laboratorio_id, fuente_id, bytes_cache, bytes_origen, hits, misses | Fuente de P-02 y REQ-F-25 |
| `cambio` | id, usuario_id, sesion_id *(nueva)*, accion, objeto, antes, despues, resultado *(nueva)*, fecha | Solo inserción (REQ-F-24) |

**Retención.**

- **`kpi_intervalo`.** Se agrega a `kpi_diario` cada día. Cuánto tiempo se conservan los intervalos no está
  definido: se fija con la DTI y el oficial de datos personales junto con la evaluación de impacto (00 M11). Hasta
  entonces no se usa ninguna cifra.
- **`cambio` y `version_config`.** No se borran. Se respaldan por F18.
