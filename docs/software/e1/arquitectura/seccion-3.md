# 3. Diseño arquitectónico (C4 + ADR)

La arquitectura responde a las cuatro causas del problema (00 M2.2):

| Causa del problema | Respuesta de la arquitectura |
| --- | --- |
| Cada estación repite la misma descarga | Un nodo de caché por campus que descarga una sola vez y distribuye por la LAN |
| Las descargas ocurren en horario de clase | Precargas nocturnas ejecutadas en el propio nodo (D-21) |
| La mayor parte del tráfico es HTTPS | Descifrado selectivo y aprobado (D-02, D-04, D-20) |
| No existe un rol que decida qué se reutiliza | Una consola para el encargado (D-25) |

La arquitectura se presenta con el modelo C4 en tres niveles: contexto, contenedores y componentes. El nivel de
contenedores se representa como vista de despliegue, dado que cada contenedor tiene asignadas una VM y una dirección
IP en `infra/inventory.yaml`. Las decisiones se documentan en formato MADR, en `adr/`.

**Convención.**

- «R1»: implementado en el código (`src/`).
- «R2»: se construirá en S2.

El color de cada estado se acompaña siempre del estereotipo escrito.

## 3.1 Vista de contexto (C1) — DS-20

**Celeris Edge** constituye un único sistema integrado por tres elementos: los nodos EDGE01/EDGE02, la consola en
CTRL01 y el portal en PORTAL01. En su entorno interactúan seis tipos de persona y cinco sistemas externos.

**Personas.** Cuatro disponen de cuenta en la consola: encargado, administrador DTI, docente y auditor. Dos operan
sin cuenta: el usuario de laboratorio y el usuario BYOD.

**Sistemas externos:**

- **Orígenes en Internet:** se accede a ellos únicamente a través del FortiGate de la DTI (F8).
- **EC2-GW:** punto de entrada remoto a la consola, sin almacenamiento de datos (F29 → F30).
- **S3 `celeris-backups`:** respaldo cifrado (F18).
- **SIEM01:** recibe los eventos de seguridad (F13).

**Qué observar en el diagrama:**

- El tráfico BYOD se representa con línea discontinua (F31, proxy opcional) y nunca se descifra (REQ-F-36).
- El encargado dispone de dos vías de acceso a la consola:
  - desde ENC01 (F28);
  - desde fuera del campus por EC2-GW (F29 → F30).
- El administrador aprueba únicamente desde JMP01 (F20) o ENC01 (F28) (REQ-F-37).

## 3.2 Vista de contenedores (C2), que cumple el rol de vista de despliegue — DS-21

| Contenedor | Tecnología | Dónde corre (IP) | Responsabilidad | Estado |
| --- | --- | --- | --- | --- |
| `celeris-node` | Rust: Hudsucker, rustls, Hyper, Tokio | EDGE01 10.20.60.10 y EDGE02 10.20.60.11 | Proxy (TCP 3128), caché CAS, TLS selectivo, PAC (TCP 80), configuración firmada; en R2, agente F10 y precarga | R1 + R2 |
| Consola web (SPA) | Servida por la API (mismo origen) | CTRL01 10.20.20.10 | P-01…P-08 y P-11 | R2 |
| `celeris-console` API | Rust: axum | CTRL01 10.20.20.10, TCP 443 (F28, F30) y TCP 8443 (F10) | Reglas del catálogo, laboratorios, precargas, solicitudes, aprobaciones, reportes, auditoría; compila y firma la configuración | R2 |
| PostgreSQL | Socket Unix, sin puerto de red | CTRL01 10.20.20.10 | Datos de la consola (DS-12); respaldo por F18 | R2 |
| Portal | Sitio estático firmado en Caddy + Coraza | PORTAL01 10.20.40.10 | Aviso y huella de la CA (P-09, P-10) | R2 (actualmente el aviso lo sirve el propio nodo) |
| Proxy inverso | Caddy + Coraza, sin estado | EC2-GW 10.30.0.10 | TLS público, WAF, límite de intentos; reenvía a CTRL01 con mTLS | Infraestructura (CE03) |

**Decisiones que fija esta vista:**

- **La consola reside íntegramente en el campus (D-25).** En AWS se ubican únicamente EC2-GW y S3 (D-24).
- **Los nodos solicitan su configuración.** Cada 30 s consultan a CTRL01 por F10 con mTLS; la consola no envía
  configuración de forma activa. Si CTRL01 deja de estar disponible, cada nodo continúa con su última versión válida
  (D-11).
- **El sitio del portal no se transfiere directamente de la consola a PORTAL01.** El inventario no contempla un
  flujo directo CTRL01 → PORTAL01. El sitio firmado que genera `publisher` es desplegado por JMP01 mediante F20
  (TCP 22), y el certificado es renovado por FW01 mediante ACME y entregado por F33 (D-29).
- **Todo el tráfico entre zonas atraviesa FW01 (D-17).** El diagrama lo indica en el límite del campus; las reglas
  se especifican en CE03.

## 3.3 Vista de componentes (C3) — DS-22 y DS-13

**Consola (DS-22).** Los componentes se detallan en la tabla; sus clases se presentan en DS-03 y sus tablas en DS-12.

| Componente | Responsabilidad | Requisitos |
| --- | --- | --- |
| router + origen | Rutas `/v1` (443) y `/v1/nodos` (8443, mTLS). Marca cada sesión `campus` o `remoto` | REQ-F-37, NF-14 |
| auth | Contraseña + TOTP, RBAC por rol y laboratorio, bloqueo por intentos. Gestiona usuarios, perfil BYOD y rotación de CA solo con origen `campus` | REQ-F-33, F-37, RN-06 |
| catalog | Fuentes, dominios y modos; simulador; aprobación; purga | REQ-F-19, F-20, F-31, RN-04, RN-07, RN-09 |
| labs | Habilitar laboratorios y su horario | REQ-F-32, RN-06 |
| prefetch | Precargas y solicitudes de docentes | REQ-F-34, F-35, RN-10 |
| publisher | Compila y firma la versión de configuración (con las redes BYOD en `nunca`); genera el sitio del portal | REQ-F-17, F-30, F-36, RN-11 |
| reports | Recibe los KPI de 30 s; ahorro del mes y vista en vivo, solo por laboratorio | REQ-F-13, F-25, NF-07 |
| audit | Cambios e intentos rechazados, solo inserción | REQ-F-24 |

**Nodo (DS-13, Anexo C).** El diagrama relaciona cada componente del nodo con el archivo de código que lo implementa
actualmente y con el módulo al que se trasladará cuando se reorganice el código:

- ingress;
- tls;
- policy;
- privacy;
- cache.*;
- security;
- telemetry;
- pac;
- signed.

Restan tres componentes, que se construirán en S2 (R2): el agente que descarga la configuración por F10, la
precarga y las descargas parciales (`Range`, REQ-F-08).

## 3.4 Registro de decisiones arquitectónicas (ADR)

El proyecto registra 29 decisiones, numeradas de D-01 a D-29, con la misma numeración empleada en el informe de
infraestructura (CE03). La Sección 0.3 las enumera e indica el ámbito de cada una; en esta sección se presentan las
15 de software. Cada una se documenta en formato MADR: contexto, factores de decisión, opciones evaluadas, decisión,
consecuencias y método de verificación.

| ADR | Decisión | Alternativa descartada principal | Consecuencia clave | Verificación |
| --- | --- | --- | --- | --- |
| D-01 | Rust + Tokio para nodo y consola | Go, Python | Seguridad de memoria; curva de aprendizaje elevada para un equipo de dos integrantes | REQ-NF-01, NF-09 |
| D-02 | Hudsucker para el proxy con descifrado selectivo | Squid, mitmproxy | Descifrado decidido por `CONNECT` y por SNI; por defecto no se descifra | T07, T56 |
| D-03 | Almacenamiento por SHA-256 | Archivo por URL | Deduplica y detecta objetos corruptos | REQ-NF-04 |
| D-04 | Raíz offline + intermedia por nodo con Name Constraints | Una CA única | Un nodo comprometido no compromete al otro; **parcial en el código** | REQ-F-18 |
| D-05 | Proxy explícito con PAC por URL fija (GPO) | Transparente, WPAD | `DIRECT` de respaldo; F3 sin cifrar con riesgo aceptado | T09 |
| D-06 | Bloquear UDP/443 en laboratorios | Permitir QUIC | Las descargas pasan por la caché | T08 |
| D-09 | OpenTofu + Ansible | Terraform, scripts | EC2-GW se recrea en ≈ 15 min | `make tofu-check` |
| D-11 | Configuración firmada con ed25519 | Editar `config.toml` en cada nodo | Integridad aunque se intercepte F10; **verificación hecha, descarga en R2** | T51 |
| D-12 | PostgreSQL local en CTRL01 | SQLite, base en AWS | Sin réplica: continuidad por respaldo | T40, T59 |
| D-20 | Catálogo con tres modos; la DTI aprueba solo lo que se descifra | Lista única; todo por la DTI | Autonomía del encargado sin ceder lo sensible | T51, T54 |
| D-21 | Precarga en el nodo | Servicio aparte | Reutiliza caché y verificación; menos piezas | T50 |
| D-22 | Ahorro por laboratorio, nunca por persona | Reporte por IP | Minimización; sin vista por PC | T26 |
| D-24 | Acceso remoto por EC2-GW a través de la VPN | NAT del campus, VPN de acceso remoto | El campus no publica la consola | T53, T54, T58 |
| D-25 | Consola completa en el campus | Backend o SPA en AWS | El nodo no depende de Internet; llave y datos en el campus | T58, T59 |
| D-27 | BYOD sin descifrado, proxy opcional | CA voluntaria; dejar BYOD fuera | Privacidad; ahorro bajo en BYOD, declarado | T56 |

### Decisiones que no se mantienen

Cinco decisiones de la versión anterior del diseño (v0.2) ya no se aplican. Conservan su número para preservar la
trazabilidad de la evolución del diseño, y dicha numeración no se reutiliza:

| ADR | Decisión anterior | Por qué no se mantiene |
| --- | --- | --- |
| D-07 | Cedar como motor de políticas | Las reglas del nodo ya se expresan con el catálogo de fuentes y la configuración firmada (D-11, D-20). Un motor independiente no aporta valor a esta escala; se reevaluará si el catálogo crece |
| D-08 | OCSF para eventos de seguridad | Se mantiene como meta de REQ-NF-11, pero actualmente el nodo registra los eventos de seguridad en un formato JSON propio (REQ-F-14, parcial) |
| D-10 | Intercambio de claves X25519MLKEM768 con aws-lc-rs | El nodo ya emplea aws-lc-rs para TLS, pero este intercambio de claves aún no se ha configurado ni medido. Se verificará con testssl.sh (REQ-NF-06) |
| D-13 | Caché intermedia (*shield*) en AWS | Fue reemplazada por D-19: no se contempla caché en AWS |
| D-14 | Foyer como índice de la caché | No se adoptó: el índice usa una caché en memoria (moka) y un índice en disco propio (D-03) |

## 3.5 Cómo responde la arquitectura a los atributos de calidad

| Atributo (ISO/IEC 25010) | Requisito | Táctica en la arquitectura |
| --- | --- | --- |
| Fiabilidad | REQ-NF-03, NF-16 | Dos nodos + `DIRECT` en el PAC (D-05); el nodo conserva la última configuración válida (D-11) |
| Seguridad | REQ-F-37, NF-05, NF-14, RN-08 | Origen de sesión y acciones críticas solo desde el campus (D-24); CA por nodo (D-04); firma ed25519 (D-11); mTLS en F10 y F30 |
| Privacidad | REQ-NF-07, F-36 | Agregados por laboratorio (D-22); BYOD nunca descifrado (D-27); datos de uso en el campus (D-25) |
| *Safety* | REQ-NF-08 | Por defecto no se descifra (D-02) |
| Eficiencia | REQ-NF-01, NF-02 | CAS y coalescencia (D-03); precarga fuera de clase (D-21); QUIC bloqueado para que todo pase por la caché (D-06) |
| Mantenibilidad | REQ-NF-09 | Un solo lenguaje para nodo y consola (D-01); código del nodo separado en módulos (DS-13) |
