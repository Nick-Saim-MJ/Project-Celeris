# Prototipo navegable — especificación de pantallas (CE02 E1, sección 2)

Versión: **v0.2** (24/11/2026), alineada con la **arquitectura v0.4** y con `docs/celeris/Celeris-CE02-Ingenieria-Software.md`
§C2.1. Sigue siendo **anterior a la validación con stakeholders** (ver «Validación» al final).
Herramienta: pen.dev (`celeris-prototipo.pen`, en esta misma carpeta).
Fuentes: CE02 C1.2–C1.6 (requisitos, reglas y casos de uso), C2.1 (pantallas), Arquitectura v0.4 §1, §8 y §9, e
`infra/inventory.yaml` (IP, rangos /26, URL del PAC).

## Qué cambió respecto de la v0.1

La v0.1 describía la consola de la v0.2 (flota de nodos, registro en vivo, aprobación por dos operadores). La v0.4 pone en
el centro al **encargado de laboratorio**, deja la consola completa en CTRL01 (D-25), agrega el acceso remoto por EC2-GW
(D-24, REQ-F-37) y el Wi-Fi de estudiantes sin descifrado (D-27, REQ-F-36).

| # | v0.1 (arquitectura v0.2) | v0.2 (arquitectura v0.4) | Cambio |
| --- | --- | --- | --- |
| P-01 | Inicio de sesión: cuenta institucional (OIDC) o token | Usuario + contraseña + segundo factor (TOTP); distintivo «Acceso remoto · EC2-GW» | Ajustada |
| P-02 | Resumen global del operador | Ahorro por laboratorio LAB-01…LAB-10, minutos ahorrados, precargas; EDGE01/02 con la configuración firmada aplicada | Ajustada |
| P-03 | Registro en vivo | **Catálogo de contenido**: fuentes con modo `cachear` / `descifrar_y_cachear` / `nunca` y simulador | Rehecha (desde la P-04 v0.1) |
| P-04 | Políticas de intercepción | **Laboratorios**: rango /26, acceso y horario | Nueva |
| P-05 | Flota de nodos | **Precargas**: ventana y límite de la DTI, avance | Nueva |
| P-06 | Detecciones | **Solicitudes de docentes** | Nueva |
| P-07 | Certificados | **Aprobaciones y certificados**: aprobar está bloqueado si la sesión llega por EC2-GW | Rehecha (P-07 + P-08 v0.1) |
| P-08 | Cambios pendientes (cuatro ojos) | **Auditoría** con origen campus/remoto e intentos rechazados | Rehecha |
| P-09 | Aviso servido por WAF01/WEB01 | Aviso en PORTAL01 (`portal.celeris.internal` [S-32]) + recuadro «tu equipo personal nunca se descifra» | Ajustada |
| P-10 | Instalación de la CA en equipos propios | Cómo llega la CA a las PCs institucionales (GPO); el equipo personal **no** la instala, PAC opcional | Ajustada |
| P-11 | (P-03 Registro en vivo) | **Actividad en vivo** solo con agregados por laboratorio y nodo, sin URL ni IP de equipos | Rehecha, fuera de la tabla C2.1 (ver «Desviación») |

Retirado del prototipo: EC2-SHIELD (D-19), WAF01/WEB01 (fusionados en PORTAL01), la flota con enrolamiento
(REQ-F-16, retirado) y la regla de cuatro ojos entre operadores (reemplazada por REQ-RN-07: el encargado propone y
la DTI aprueba solo lo que se descifra).

## Reglas del prototipo

- Todos los números en pantalla son **datos de ejemplo** y así lo dice el pie de cada pantalla. Las cifras de negocio
  salen de los supuestos [S-xx] del Marco común (S-04, S-05, S-26, S-27), no de una medición.
- Cada pantalla muestra en su pie su ID y los requisitos que cubre. Una pantalla sin requisito sobra; un requisito de
  interfaz sin pantalla falta.
- Las pantallas de la consola llevan la etiqueta **R2 — diseño**: la consola (`celeris-console`) no existe aún y se
  construye en S2 (CE023).
- Nombres, IP y rangos salen del inventario: CTRL01 10.20.20.10, EDGE01 10.20.60.10, EDGE02 10.20.60.11,
  ENC01 10.20.35.10, LAB-01 10.20.32.0/26 … LAB-10 10.20.34.64/26, PAC en `http://pac.celeris.internal/wpad.dat`.
- La barra superior muestra **desde dónde llega la sesión**: verde «Sesión desde el campus» (ENC01 o JMP01) o ámbar
  «Acceso remoto · EC2-GW» (REQ-F-37).
- Roles de ejemplo: *Encargado LAB-03* (asignado a LAB-03 y LAB-04) en P-02…P-06; *Admin DTI* entrando de forma remota
  en P-07; *Auditor* en P-08.

## Pantallas

| # | Pantalla | Rol | Requisitos | Casos de uso |
| --- | --- | --- | --- | --- |
| P-01 | Inicio de sesión con segundo factor | Todos | REQ-F-33, REQ-F-37, REQ-NF-14 | CU-11 |
| P-02 | Resumen: ahorro por laboratorio, nodos, precargas | Encargado, admin, auditor | REQ-F-25, REQ-F-13, REQ-NF-13 | CU-06 |
| P-03 | Catálogo de contenido y simulador | Encargado | REQ-F-31, REQ-F-20, REQ-RN-03, REQ-RN-04, REQ-RN-07, REQ-RN-09, REQ-F-36 | CU-03 |
| P-04 | Laboratorios: acceso, rango y horario | Encargado | REQ-F-32, REQ-F-10, REQ-F-24, REQ-RN-06, REQ-NF-16 | CU-04 |
| P-05 | Precargas | Encargado | REQ-F-34, REQ-F-22, REQ-RN-10, REQ-F-05 | CU-05 |
| P-06 | Solicitudes de docentes | Encargado (el docente registra) | REQ-F-35, REQ-F-34, REQ-F-31 | CU-09, CU-05 |
| P-07 | Aprobaciones pendientes y certificados | Admin DTI | REQ-RN-07, REQ-F-37, REQ-F-18, REQ-RN-04, REQ-NF-05 | CU-07, CU-11 |
| P-08 | Auditoría de cambios | Auditor, admin | REQ-F-24, REQ-F-37, REQ-RN-08, REQ-NF-16 | CU-10 |
| P-09 | Portal público: aviso de transparencia | Usuario, usuario BYOD, auditor | REQ-F-12, REQ-F-30, REQ-F-36, REQ-RN-05 | CU-02 |
| P-10 | Portal público: instalación de la CA y verificación de la huella | Usuario, técnico DTI | REQ-RN-05, REQ-F-12, REQ-F-36 | CU-02 |
| P-11 | Actividad en vivo por laboratorio y nodo | Encargado, admin DTI | REQ-F-13, REQ-NF-13, REQ-NF-07 | CU-06 |

Cobertura: los 11 casos de uso salvo CU-01 (descargar por la caché, sin interfaz: lo hace el navegador vía PAC) y
CU-08 (purgar, REQ-F-19, *Should* de R2; queda como acción del catálogo en una versión posterior).

## Contenido de cada pantalla

### P-01 Inicio de sesión
- Usuario, contraseña y **código de 6 dígitos** (TOTP), obligatorio también desde el campus (REQ-F-33).
- Distintivo «Acceso remoto · llegaste por EC2-GW» y nota: desde fuera se puede revisar y cambiar lo propio, pero no
  aprobar descifrado, rotar llaves, gestionar usuarios ni cambiar el perfil BYOD (REQ-F-37).
- Tras 10 intentos fallidos, bloqueo temporal y alerta en el SIEM (prueba T53). Solo TLS (REQ-NF-14).
- Panel izquierdo: qué promete la consola (solo se descifra lo aprobado; RBAC por laboratorio; todo queda auditado).

### P-02 Resumen
- Indicadores: descarga evitada en el mes (5,8 TB = 30 % de ≈ 19,4 TB [S-04, S-05]), byte hit ratio frente a la meta
  OB-1, costo de enlace evitado [S-03], **minutos de descarga ahorrados** de los laboratorios del encargado (OB-2) y
  **alertas abiertas** (precarga fallida SOL-10, CA-EDGE02 vence en 8 días), como pide C2.1.
- Gráfico de **descarga por laboratorio** (LAB-01…LAB-10), desde la caché frente a desde el origen; en negrita los
  laboratorios del encargado.
- Reparto HIT / REVALIDATED / MISS / BYPASS / error (mismos nombres que las métricas del nodo).
- EDGE01 y EDGE02: disco usado y «config v43 firmada y aplicada» (F10).
- Acción «Exportar reporte de ahorro (CSV)» (REQ-F-25). Clic en «Alertas abiertas» → P-05; en el gráfico → P-04.

### P-03 Catálogo de contenido
- Tabla de fuentes: nombre y categoría, dominios, **modo** y **estado** (Activa, Pendiente DTI, Inactiva, Fija).
- Ejemplos: Repos de Ubuntu y Windows Update en `cachear`; Instaladores de JetBrains en `descifrar_y_cachear`
  **pendiente**; Bancos, inicios de sesión e identidad en `nunca`, fija y con candado (REQ-RN-09).
- Reglas visibles: «nunca» gana siempre (REQ-RN-03); `cachear` se activa al guardar y `descifrar_y_cachear` espera a la
  DTI (REQ-RN-07); WIFI-EST nunca se descifra (REQ-F-36, REQ-RN-11).
- Simulador «¿qué pasaría si?» (REQ-F-20): ¿se descifraría?, ¿se guardaría?, ¿la CA cubre el dominio? (REQ-RN-04), con
  el impacto estimado sobre los registros de ayer de LAB-03 y LAB-04.
- «Nueva fuente» abre el formulario. La fila pendiente lleva a P-07.

### P-04 Laboratorios
- Los 10 laboratorios con su rango /26, tomado del inventario de red (no se edita en la consola). Solo LAB-03 y LAB-04 son editables para este encargado; los demás aparecen
  atenuados con candado, «Otro encargado» (REQ-RN-06).
- LAB-04 en mantenimiento desde el 23/11 18:40 (ver P-08): el nodo responde 403 a 10.20.32.192/26 (prueba T52). Por eso
  todas las precargas y solicitudes atendidas desde esa fecha son de LAB-03.
- Detalle de LAB-03: interruptor «Usa la caché», horario semanal (Lun–Vie 07:00–22:00, Sáb 08:00–13:00) y
  «Qué cambia al guardar»: `allowed_clients` del nodo, firma de la configuración v44 (REQ-F-17) y aplicación por mTLS
  en ≤ 60 s (REQ-NF-16).

### P-05 Precargas
- Franja con la ventana y el límite fijados por la DTI: 00:00–05:00, 50 Mbps por nodo (REQ-RN-10).
- Lista con los cinco estados del diagrama C4.6: Programada, Completada (con HIT al inicio de la clase), Pausada (se
  acabó la ventana; sigue la noche siguiente), Fallida (404 del origen tras reintentos). Todas las filas usan fuentes del
  catálogo de P-03; la de JetBrains avisa que solo se cachea si la DTI aprueba la fuente antes de la ventana.
- Formulario **«Editar precarga»** de la SOL-12 (la misma de la primera fila): URLs, laboratorio, fecha; ventana y límite bloqueados;
  estimación «1,1 GB por el enlace en ≈ 3 min, en vez de 44 GB en hora de clase» (coalescencia, REQ-F-05).

### P-06 Solicitudes de docentes
- Tablero de tres columnas: Nuevas, En preparación, Listas (REQ-F-35).
- Cada pedido: ID, laboratorio, curso, fecha de la clase, qué se necesita y una nota de estado (fuente inactiva,
  precarga programada, precarga fallida, HIT logrado).
- Acciones: «Activar fuente» → P-03, «Crear precarga» / «Ver precarga» → P-05, «Responder» al docente.

### P-07 Aprobaciones y certificados
- La sesión es del **Admin DTI entrando por EC2-GW**: franja ámbar que explica que aprobar descifrado, rotar llaves,
  gestionar usuarios y cambiar el perfil BYOD solo se hace desde el campus, JMP01 o ENC01 (REQ-F-37).
- Pendientes: la fuente «Instaladores de JetBrains» (con el resultado del simulador y la nota de que la CA no cubre el
  dominio, REQ-RN-04) y la rotación de CA-EDGE02. «Rechazar» funciona; **«Aprobar» aparece deshabilitado con candado**
  y la razón «solo desde el campus». En el navegable, hacer clic responde «403» (prueba T54).
- Certificados: intermedias CA-EDGE01 y CA-EDGE02 con serie, vencimiento, huella y Name Constraints
  (files.pythonhosted.org, registry.npmjs.org); certificado de cliente mTLS de EC2-GW, que solo autentica F30 hacia
  CTRL01:443. Raíz offline dividida 2 de 3 (REQ-NF-05).

### P-08 Auditoría
- Filtros por fecha, usuario, laboratorio y **origen**; exportar CSV.
- Tabla: cuándo, quién, origen (campus/remoto/sistema, con el equipo: ENC01, JMP01, EC2-GW, CTRL01), acción y objeto,
  versión de configuración.
- Orden de la más nueva a la más antigua. La primera fila es el intento del Admin DTI de aprobar desde EC2-GW,
  **rechazado con 403** (REQ-F-37); la segunda, el encargado programando la precarga SOL-12 desde remoto, que sí está
  permitido porque no es una acción crítica.
- Detalle de la fila seleccionada (LAB-04 deshabilitado): antes y después, firma ed25519 de la v43 y tiempo en que
  EDGE01 (29 s) y EDGE02 (40 s) la aplicaron (REQ-NF-16).
- Nota: registro de solo inserción (REQ-F-24) y sin datos de navegación de las personas (REQ-NF-07).

### P-09 Portal público: aviso
- Página pública en PORTAL01, sin login, con certificado público (lo renueva FW01 por ACME y lo entrega por F33, D-29).
- Configuración v43 publicada como sitio estático firmado por la consola (REQ-F-30).
- Tres columnas: qué se descifra (solo las fuentes **activas** de la v43: files.pythonhosted.org; la de JetBrains está
  pendiente y la de Node.js inactiva, así que no aparecen), qué nunca se descifra y
  «todo lo demás» en túnel.
- **Recuadro BYOD:** en el Wi-Fi de estudiantes tu equipo nunca se descifra, no instales la CA y el proxy es opcional
  (REQ-F-36).
- Qué se registra y por cuánto tiempo; el ahorro se reporta por laboratorio y no sale del campus. Huella de la CA y
  contacto de la DTI.

### P-11 Actividad en vivo
- Reemplaza al «Registro en vivo» de la v0.1, adaptado a la v0.4: la consola solo recibe **agregados por laboratorio**
  dentro de F10 (Arquitectura v0.4 §8.3), con cada consulta del nodo (cada 30 s). No muestra URL, IP de equipos ni
  usuarios (REQ-NF-07); los eventos de seguridad los revisa la DTI en SIEM01.
- Indicador «En vivo · hora del último informe» y botón «Pausar» (solo detiene la vista).
- Indicadores: peticiones por segundo, byte hit ratio de los últimos 5 min, Mbps servidos desde la caché frente a los
  traídos del origen, rechazos 403 (LAB-04 en mantenimiento, T52).
- Gráfico de peticiones por minuto de los últimos 30 min, apilado en HIT / MISS / BYPASS (REQ-NF-13).
- Tabla por laboratorio (estado, peticiones/s, reparto, 403) y por nodo (EDGE01 10.20.60.10, EDGE02 10.20.60.11, hace
  cuánto llegó su último informe y versión de configuración aplicada).
- «Decisiones por informe»: una fila por laboratorio y nodo cada 30 s con las cantidades HIT, REVALIDATED, MISS,
  BYPASS y 403. Las cifras cuadran entre sí (51 + 35 = 86 pet./s; 6 rechazos cada 30 s = 12/min).
- En el navegable: «Rechazos 403» y la fila de LAB-04 llevan a P-04; «Pausar» muestra un mensaje.

### P-10 Portal público: instalación de la CA
- Explica que en las PCs institucionales la DTI instala la CA y la URL del PAC por GPO **después** de publicar el aviso
  (REQ-RN-05).
- Pasos: leer el aviso (casilla obligatoria), verificar la huella, descargar el certificado (técnicos de la DTI; se
  habilita solo tras marcar la casilla), instalación por GPO / Windows / Linux y la URL fija del PAC (sin WPAD, T60).
- Recuadro «¿Tu propio equipo en WIFI-EST?»: no instales la CA; PAC opcional; si un sitio te muestra un certificado
  «Celeris» en el Wi-Fi, avisa a la DTI (prueba T56).

## Flujo de navegación

```
P-10 Instalación de la CA ──▶ P-09 Aviso                         (portal público, sin login)

P-01 Login ──▶ P-02 Resumen ──┬──▶ P-04 Laboratorios
                              ├──▶ P-03 Catálogo ──(fuente a descifrar)──▶ P-07 Aprobaciones
                              ├──▶ P-06 Solicitudes ──(crear precarga)──▶ P-05 Precargas
                              ├──▶ P-08 Auditoría
                              └──▶ P-11 Actividad en vivo
            (la barra lateral salta entre P-02 y P-08 en cualquier momento)
```

## Desviación de la tabla C2.1 (P-11)

CE02 C2.1 fija 10 pantallas y da por retirado el «registro en vivo» de la v0.2. P-11 se agrega a pedido del equipo
(24/11/2026) con estas condiciones, para que no choque con la v0.4:

- Solo muestra lo que el nodo ya envía a CTRL01 por F10: agregados por laboratorio (Arquitectura v0.4 §8.3). No se
  agrega ningún flujo, puerto ni componente.
- Sin URL, sin IP de equipos y sin usuarios (REQ-NF-07); respeta lo que promete el aviso de P-09.
- Se apoya en requisitos existentes (REQ-F-13, REQ-NF-13) y en CU-06; no crea requisitos nuevos.
- **Registrada** en `docs/celeris/Celeris-CE02-Ingenieria-Software.md` C2.1 (fila P-11 y nota «Desviación registrada»,
  24/11/2026). Si el revisor no la acepta, se retira sin afectar a las demás pantallas.

## Revisión de fidelidad con la arquitectura v0.4 (24/11/2026)

Contrastado contra `infra/inventory.yaml`, Arquitectura v0.4 y CE02 C1–C2:

| Aspecto | En el prototipo | Fuente |
| --- | --- | --- |
| Dónde vive la consola | CTRL01 10.20.20.10, en el campus; en AWS solo EC2-GW, sin datos | D-25, D-24 |
| Acceso remoto | Chip ámbar «Acceso remoto · EC2-GW»; «Aprobar» bloqueado; 403 en la auditoría | REQ-F-37, T54 |
| Acciones solo desde el campus | aprobar descifrado, rotar llaves, gestionar usuarios, cambiar el perfil BYOD (P-01, P-07) | REQ-F-37, ENC01 en el inventario |
| BYOD | WIFI-EST nunca se descifra (P-03, P-09, P-10) | REQ-F-36, REQ-RN-11, D-27 |
| Modos de fuente | `cachear` / `descifrar_y_cachear` / `nunca`; «nunca» gana; la DTI aprueba el descifrado | REQ-RN-03, RN-07, RN-09 |
| Configuración | firmada ed25519, F10 TCP 8443 mTLS, aplicada en ≤ 60 s | REQ-F-17, REQ-NF-16 |
| Precargas | 00:00–05:00, 50 Mbps por nodo | REQ-RN-10, T50 |
| IP y rangos | EDGE01 .60.10, EDGE02 .60.11, ENC01 10.20.35.10, LAB-01…LAB-10 /26 | `infra/inventory.yaml` |
| Portal | PORTAL01 `portal.celeris.internal` [S-32], certificado ACME de FW01 por F33 | D-29 |
| Segundo factor | TOTP obligatorio, también en el campus; bloqueo tras 10 intentos | REQ-F-33, T53 |

Incoherencias corregidas en esta revisión: la lista de acciones críticas no incluía «cambiar el perfil BYOD»; el aviso
de P-09 listaba como descifrados dominios pendientes o inactivos; P-05 tenía una fila fuera del catálogo y un formulario
que duplicaba la precarga SOL-12; LAB-04 aparecía con actividad después de deshabilitarse; SOL-12 decía «para hoy»; el
indicador de P-02 no era de alertas (C2.1); la auditoría no estaba en orden cronológico; textos que se salían de su
caja en P-01, P-02, P-05 y P-07.

## Archivos del prototipo v0.2

| Archivo | Contenido |
| --- | --- |
| `celeris-prototipo.pen` | Las 11 pantallas, el tablero de flujo y trazabilidad y los componentes base (barra lateral, estructura de la consola con el indicador de origen, botones, etiqueta R2, pie de trazabilidad, cabecera del portal) |
| `png/00-flujo-navegacion.png` | Flujo de navegación y tabla pantalla → actor → requisitos → casos de uso |
| `png/P-01-…png` a `png/P-11-…png` | Una imagen por pantalla (1440 px de ancho), para el informe |
| `navegable.html` | Prototipo clicable: las mismas imágenes con zonas activas sobre el menú y los botones |

### Prototipo navegable (`navegable.html`)

- Abrir: `python -m http.server 8765 --directory docs/software/e1/prototipo` y entrar a
  `http://127.0.0.1:8765/navegable.html`. En la app de Claude existe la configuración `prototipo-ce02` en
  `.claude/launch.json`.
- Empieza en el mapa de flujo (`#00`). Cada tarjeta y cada fila de la tabla abre su pantalla; `#P-04` abre directo P-04.
- Recorrido: P-01 «Entrar» → P-02 → menú lateral a P-03…P-08 y P-11 («En vivo»). Atajos: P-02 «Alertas abiertas» → P-05 y el
  gráfico → P-04; P-03 fila pendiente → P-07; P-05 fila SOL-12 → P-06; P-06 «Activar fuente» → P-03 y «Crear / Ver
  precarga» → P-05; P-08 intento rechazado → P-07; usuario de la barra superior → P-01 (cerrar sesión).
- Portal: P-09 «Cómo instalar la CA» → P-10 y «Volver al aviso» / «Aviso» → P-09.
- Las acciones que no cambian de pantalla (Guardar y publicar, Guardar cambios, Simular, Aprobar bloqueado, Descargar la CA…)
  muestran un mensaje con lo que haría el sistema y el requisito o la prueba que aplica.
- `Z` muestra u oculta las zonas clicables; `←` `→` recorren las pantallas en orden; `Retroceso` vuelve atrás.
- Si se cambia una pantalla en pen.dev hay que volver a exportar su PNG y, si un botón cambió de lugar, actualizar sus
  coordenadas en el HTML.

## Validación con stakeholders (pendiente)

La v0.2 es la versión que se lleva a la validación de CE02 C2.2. **Todavía no se ha validado con usuarios**; no hay
acta ni resultados, y esta sección no debe presentarse como evidencia hasta completarla.

| Elemento | Plan (CE02 C2.2) |
| --- | --- |
| Participantes | ≥ 2 encargados de laboratorio, 1 técnico DTI, 1 docente, 1 estudiante [COMPLETAR: nombres o cargos] |
| Tareas | 1) agregar una fuente sin descifrado (P-03); 2) agregar una que requiere descifrado y verla pendiente (P-03 → P-07); 3) habilitar un laboratorio en un horario (P-04); 4) programar una precarga (P-06 → P-05); 5) encontrar el ahorro del mes (P-02); 6) verificar la huella de la CA desde el portal (P-09 → P-10) |
| Medición | Éxito por tarea, tiempo por tarea (meta ≤ 5 min, REQ-NF-12), SUS ≥ 75 |
| Evidencia | Acta firmada, hallazgos priorizados y cambios aplicados (v0.2 → v0.3) [COMPLETAR] |

## Huecos detectados al especificar (para el SRS)

| ID | Hueco | Propuesta |
| --- | --- | --- |
| H-01 | CU-08 (purgar, REQ-F-19) no tiene pantalla. | Agregar la acción «Purgar contenido» en cada fila del catálogo (P-03) en la v0.3 |
| H-02 | El horario por laboratorio (P-04) no tiene regla de negocio que diga qué pasa fuera del horario. | Agregar una RN: fuera del horario el nodo responde 403 a ese rango (hoy solo lo dice la prueba T52) |
| H-03 | El docente es actor de CU-09, pero su forma de registrar la solicitud (cuenta, formulario) no está especificada. | Definir en el SRS si el docente tiene rol propio en la consola o usa un formulario aparte |
