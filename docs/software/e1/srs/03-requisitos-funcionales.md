## 1.7 Requisitos funcionales

Cada requisito es verificable: la columna «Verifica» nombra la prueba de `infra/pruebas.yaml` o el archivo Gherkin
que lo comprueba. Los archivos `tests/features/*.feature` se escriben en S2 (CE024) a partir de la sección 1.10. Los
IDs retirados se listan en 1.13.3.

### 1.7.1 Nodo de caché (plano de datos)

| ID | Requisito | Prior. | Ver. | Estado | Verifica |
| --- | --- | :-: | :-: | --- | --- |
| REQ-F-01 | Atender como proxy explícito HTTP y HTTPS (`CONNECT`) | M | R1 | Hecho | T07 |
| REQ-F-02 | Descifrar TLS solo si el dominio pertenece a una fuente `descifrar_y_cachear` aprobada, no está en `nunca` y el SNI coincide con el `CONNECT` | M | R1 | Hecho (lista en `config.toml`) | `intercepcion.feature` |
| REQ-F-03 | Cachear respuestas compartibles según RFC 9111 | M | R1 | Hecho | Pruebas del nodo |
| REQ-F-04 | Revalidar copias vencidas (`If-None-Match` / `If-Modified-Since`) | M | R1 | Hecho | Pruebas del nodo |
| REQ-F-05 | Coalescer peticiones concurrentes al mismo objeto | M | R1 | Hecho | T55 |
| REQ-F-06 | Guardar por SHA-256 y verificar el hash antes de servir | M | R1 | Hecho | Pruebas del nodo |
| REQ-F-07 | Normalizar claves de caché (Store-ID, parámetros de rastreo) | M | R1 | Hecho | Pruebas del nodo |
| REQ-F-08 | Servir peticiones `Range` (206) desde el objeto completo | S | R2 | Pendiente | `rangos.feature` |
| REQ-F-09 | Respetar un límite de disco expulsando lo menos usado | M | R1 | Hecho | Pruebas del nodo |
| REQ-F-10 | Aceptar solo clientes de los rangos de laboratorios habilitados y limitar peticiones por IP | M | R1 | Hecho (rangos en `config.toml`) | T13, T52 |
| REQ-F-11 | Bloquear destinos internos (SSRF) y puertos no permitidos | M | R1 | Hecho | T13 |
| REQ-F-12 | Publicar el aviso de transparencia generado desde la configuración real | M | R1 | Hecho (servido por el proxy) | T15 |
| REQ-F-13 | Exponer métricas Prometheus por laboratorio | M | R2 | Parcial (métricas globales) | `reportes.feature` |
| REQ-F-14 | Enviar eventos de seguridad al SIEM | S | R2 | Parcial (JSONL propio) | T11 |
| REQ-F-15 | Detectar uso inusual del proxy por IP | S | R1 | Hecho | T13 |
| REQ-F-17 | Aplicar la configuración que publica la consola, solo si su firma es válida, y volver a la anterior si falla | M | R2 | Parcial (`signed.rs` verifica ed25519 y versión y conserva la anterior; falta la descarga por F10) | T51 |
| REQ-F-18 | Usar una CA intermedia por nodo, limitada por Name Constraints | S | R2 | Parcial (CA única limitada) | Revisión de certificados |
| REQ-F-22 | Ejecutar precargas en la ventana horaria indicada por la consola, con límite de ancho de banda | M | R2 | Pendiente | T50 |
| REQ-F-26 | Generar y servir el PAC con los nodos activos y `DIRECT` de respaldo | M | R1 | Hecho (`pac.rs`) | T09 |
| REQ-F-28 | Eliminar `X-Forwarded-For`, `Via` y `Forwarded` antes de enviar al origen | M | R2 | Hecho (`policy.rs`) | T26 (PASA en Modo L, emulado) |
| REQ-F-36 | Tratar como `nunca` (passthrough) todo el tráfico que llega desde las redes de origen marcadas como BYOD (WIFI-EST), aunque el dominio esté en una fuente `descifrar_y_cachear` | M | R2 | Hecho en el nodo (`byod_networks`); la consola debe publicar la lista | T56 |

### 1.7.2 Consola del encargado (plano de control)

| ID | Requisito | Prior. | Ver. | Estado | Pantalla | Verifica |
| --- | --- | :-: | :-: | --- | --- | --- |
| REQ-F-19 | Purgar contenido por fuente, URL o prefijo | S | R2 | Pendiente | P-03 (v0.3, H-01) | `purga.feature` |
| REQ-F-20 | Simular una fuente: "¿esta URL se cachearía? ¿se descifraría?" sin aplicarla | S | R2 | Pendiente | P-03 | `catalogo.feature` |
| REQ-F-24 | Registrar en auditoría todo cambio (quién, qué, cuándo, antes y después) | M | R2 | Pendiente | P-08 | `auditoria.feature`, T51 |
| REQ-F-25 | Reportar el ahorro por laboratorio y por fuente (GB evitados, BHR, minutos ahorrados) | M | R2 | Parcial (panel local global) | P-02 | `reportes.feature` |
| REQ-F-30 | Publicar el portal de transparencia como sitio estático firmado | S | R2 | Pendiente | P-09, P-10 | T15, T16 |
| REQ-F-31 | Gestionar el **catálogo de contenido**: crear, editar, activar o desactivar fuentes con sus dominios, categoría y modo | M | R2 | Pendiente (hoy se edita `config.toml`) | P-03, P-07 | `catalogo.feature`, T51 |
| REQ-F-32 | Gestionar el **acceso por laboratorio**: habilitar o deshabilitar un laboratorio, su rango de IP y su horario | M | R2 | Pendiente | P-04 | `laboratorios.feature`, T52 |
| REQ-F-33 | Autenticar usuarios de la consola con contraseña + segundo factor y aplicar RBAC por rol y laboratorio | M | R2 | Pendiente (hoy: token único) | P-01 | `auth.feature`, T53 |
| REQ-F-34 | Programar una **precarga** (lista de URLs o fuente completa, laboratorio, fecha y ventana horaria) y ver su avance | M | R2 | Pendiente | P-05 | `precarga.feature`, T50 |
| REQ-F-35 | Registrar solicitudes de los docentes para preparar un laboratorio y convertirlas en precargas | S | R2 | Pendiente | P-06 | `solicitudes.feature` |
| REQ-F-37 | Distinguir el origen de cada sesión (`campus`: ENC01/JMP01; `remoto`: por EC2-GW con su certificado de cliente) y rechazar desde `remoto` las acciones críticas: aprobar fuentes a descifrar, rotar llaves, gestionar usuarios, cambiar el perfil BYOD | M | R2 | Pendiente | P-01, P-07 | `origen.feature`, T54 |

### 1.7.3 Precisiones que salen del diseño

Estas precisiones no agregan requisitos: concretan cómo se cumplen los que ya existen. Cada una viene del prototipo
(Sección 2) o de los diagramas UML (Sección 4).

| Requisito | Precisión | De dónde sale |
| --- | --- | --- |
| REQ-F-01 | Escucha en TCP 3128 (F1 desde LAB, F31 desde WIFI-EST) | `infra/inventory.yaml` |
| REQ-F-10 | Más allá del límite por minuto responde 429 con `Retry-After: 60`; fuera de rango, 403 | DS-05, código (`handler.rs`) |
| REQ-F-13 | Además de las métricas, el nodo envía a la consola agregados de 30 s por laboratorio en `POST /v1/nodos/{id}/kpi` (F10). La vista «Actividad en vivo» (P-11) los muestra por laboratorio y por nodo, sin URL, IP de equipos ni usuarios (REQ-NF-07): por eso no hay vista por PC | Desviación P-11 (1.13.2), DS-19 |
| REQ-F-17 | Hoy el nodo recarga `config.toml` + `config.toml.sig` por intervalo o con SIGHUP y rechaza una firma inválida o una versión menor que la aplicada (DS-02, DS-13). En R2 el agente consulta `GET /v1/nodos/{id}/config?desde=v` cada 30 s, escribe esos dos archivos y reporta la versión aplicada en su KPI | DS-15, DS-19 |
| REQ-F-19 | Se lanza desde una acción «Purgar» en cada fila del catálogo (P-03). La orden llega a los nodos en la siguiente configuración firmada (F10) y queda en auditoría | H-01 |
| REQ-F-20 | El simulador responde también si la CA del nodo cubre el dominio (REQ-RN-04) | P-03, DS-15 |
| REQ-F-24 | También se auditan los intentos rechazados (p. ej., una acción crítica desde `remoto`), con el origen de la sesión | P-08, DS-15 |
| REQ-F-32 | El rango /26 de cada laboratorio lo fija el diseño de red (CE03) y en la consola es de solo lectura. Fuera del horario configurado, el nodo responde 403 a los clientes de ese rango, igual que con el laboratorio deshabilitado | H-02 |
| REQ-F-33 | El segundo factor es TOTP. Los roles son `encargado`, `admin`, `auditor` y `docente`. El docente tiene un rol propio, `docente`: entra con el mismo inicio de sesión (P-01), solo crea y ve sus solicitudes y no ve el catálogo, las precargas ni la auditoría | H-03 |
| REQ-F-37 | En una sesión `remoto`, P-01 y P-02 muestran el distintivo «acceso remoto» y las acciones críticas aparecen deshabilitadas con el motivo. La API responde 403 aunque se llame directo | P-01, P-07, DS-15 |
