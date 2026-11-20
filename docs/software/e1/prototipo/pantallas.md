# Prototipo navegable — especificación de pantallas (CE02 E1, sección 2)

Versión: v0.1 (primera versión, **antes** de la validación con stakeholders).
Herramienta: pen.dev (`celeris-prototipo.pen`, en esta misma carpeta).
Fuente: documento maestro C2.1 y C2.2, requisitos C1.2 a C1.4, panel real (`src/panel/`), métricas de `src/stats.rs`
y componentes de `infra/inventory.yaml`.

## Reglas del prototipo

- Todos los números que aparecen en pantalla son **datos de ejemplo** y así se rotula cada pantalla. Las cifras de
  negocio salen de los supuestos [S-xx] del documento maestro, no de una medición.
- Cada pantalla muestra en su pie los requisitos que cubre (columna «Requisitos»). Si una pantalla no cubre ningún
  requisito, sobra; si un requisito con pantalla no tiene una, falta.
- Las pantallas que dependen del plano de control (`celeris-control`, que todavía no existe) llevan la etiqueta
  **R2 — diseño**. Las que ya tienen equivalente en el panel actual llevan **R1 — existe en el panel**.
- Nombres, IP y puertos salen del inventario: EDGE01 10.20.60.10, EDGE02 10.20.60.11, CTRL01 10.20.20.10,
  WAF01 10.20.40.10 y WEB01 10.20.40.20; administración y métricas en 9128.

## Pantallas

| # | Pantalla | Actor | Requisitos | Versión | Equivalente actual |
| --- | --- | --- | --- | --- | --- |
| P-01 | Inicio de sesión | Operador, analista | REQ-NF-14 y requisito de autenticación de operadores (ver hueco H-01) | R2 (OIDC); R1 con token | Pantalla «Token de administración» |
| P-02 | Resumen | Operador, DTI | REQ-F-25, REQ-F-13, REQ-NF-13 | R1 parcial | Vista «Resumen» |
| P-03 | Registro en vivo | Operador | REQ-F-13, REQ-NF-07 | R1 | Vista «Registro en vivo» |
| P-04 | Políticas y simulador | Operador | REQ-F-17, REQ-F-20, REQ-RN-03, REQ-RN-04 | R2 | No existe (hoy `config.toml`) |
| P-05 | Flota de nodos | Operador | REQ-F-16, REQ-F-17 | R2 | No existe |
| P-06 | Detecciones y alertas | Analista | REQ-F-15, REQ-F-14 | R1 parcial | Tabla «Actividad inusual» |
| P-07 | Certificados | Operador, auditor | REQ-F-18, REQ-NF-05 | R2 | Alerta de vencimiento de la CA |
| P-08 | Cambios pendientes (cuatro ojos) | Operador | REQ-RN-07, REQ-F-24, REQ-RN-08 | R2 | No existe |
| P-09 | Portal público: aviso | Usuario, auditor | REQ-F-12, REQ-F-30, REQ-RN-06 | R1 (vía proxy); R2 portal | `http://celeris.aviso/` |
| P-10 | Portal público: onboarding de la CA | Usuario | REQ-F-12, REQ-RN-05 | R2 | No existe |

## Contenido de cada pantalla

### P-01 Inicio de sesión
- Botón «Iniciar sesión con la cuenta institucional» (OIDC) y, debajo, «Usar token local» (modo R1).
- Aviso fijo: «La conexión al panel usa TLS» (REQ-NF-14). Hoy el panel advierte cuando el token viajaría sin cifrar.
- Error: «Token inválido o vencido».

### P-02 Resumen
- Indicadores: GB evitados en el mes, byte hit ratio (BHR), costo evitado en US$ (con [S-03]), adopción del proxy
  (equipos que lo usan / 400 [S-01]) y alertas abiertas.
- Gráfico del tráfico atendido desde copia frente al traído del origen en los últimos 7 días.
- Reparto de peticiones: HIT, MISS, REVALIDATED, BYPASS, errores (mismos nombres que `/metrics`).
- Estado por nodo: EDGE01 y EDGE02, disco usado frente al límite, días para el vencimiento de la CA.
- Acción: «Exportar reporte de ahorro (CSV)» (REQ-F-25).

### P-03 Registro en vivo
- Tabla: fecha y hora, cliente (seudónimo diario, no IP), resultado, dominio, objeto **sin parámetros**, tamaño y tiempo.
- Filtros: resultado, dominio y nodo. Botón de pausa.
- Nota fija: «No se registran cookies, credenciales, cuerpos ni parámetros de URL» (REQ-NF-07).

### P-04 Políticas y simulador
- Dos listas: `intercept_domains` y `never_intercept`, con la regla visible «never_intercept gana siempre» (REQ-RN-03).
- Simulador «¿qué pasaría si?»: el operador escribe una URL y ve si se descifraría, si se cachearía y por qué
  (regla aplicada) (REQ-F-20).
- Al agregar un dominio que la CA no cubre: aviso «La CA de 2 nodos no cubre este dominio; se emitirán intermedias
  nuevas» (REQ-RN-04).
- Botón «Proponer cambio» → lleva a P-08. No hay botón «Aplicar»: nadie aplica solo (REQ-RN-07).

### P-05 Flota de nodos
- Tabla: nodo, IP, estado (Activo, Degradado, Drenando; estados de C4.5), versión de configuración, último heartbeat,
  versión del binario.
- Detalle del nodo: versión aplicada frente a la vigente, historial de rollout y botón «Revertir a la versión anterior»
  (REQ-F-17, CU-10).
- Acción «Registrar nodo» (CU-04, REQ-F-16).

### P-06 Detecciones y alertas
- Tabla con los cuatro tipos que ya existen: volumen, rechazos, puerto inusual y nombre que no coincide
  (`host_mismatch`), con IP, número de veces, último evento y detalle.
- Indicador «Enviado al SIEM (SIEM01)» por evento (REQ-F-14).
- Acción: «Ver en Wazuh».

### P-07 Certificados
- Una fila por nodo: CA intermedia, número de serie, vence el, dominios permitidos (Name Constraints), huella SHA-256.
- Raíz offline: solo la huella y la fecha; nunca la llave (REQ-NF-05).
- Acción: «Rotar la intermedia» (requiere aprobación en P-08).

### P-08 Cambios pendientes de aprobación
- Lista de cambios propuestos: versión, autor, fecha, resumen del diff, reporte de impacto del simulador.
- Botón «Aprobar» deshabilitado para el autor del cambio, con la nota «Debe aprobarlo otro operador» (REQ-RN-07).
- Tras aprobar: «Bundle v42 firmado (ed25519). Rollout al 10 % de los nodos» (REQ-RN-08, C4.3).
- Pestaña «Auditoría»: quién, qué y cuándo (REQ-F-24).

### P-09 Portal público: aviso
- Página pública, sin login, servida por WAF01/WEB01 con certificado público (D-15).
- Qué dominios se descifran, cuáles nunca, qué registros están activos y su retención (REQ-RN-06), huella de la CA y
  contacto del operador (`operator_contact`).
- Versión de la política publicada y su firma.

### P-10 Portal público: onboarding de la CA
- Pasos numerados: 1) leer el aviso (enlace a P-09), 2) verificar la huella, 3) descargar la CA, 4) instalarla según
  el sistema (Windows, Linux, Firefox), 5) configurar la URL fija del PAC.
- Código QR para abrir la página desde un teléfono.
- El botón «Descargar la CA» se habilita solo después de marcar «Leí el aviso» (REQ-RN-05).

## Flujo de navegación

```
P-10 Onboarding ──▶ P-09 Aviso                (portal público, sin login)

P-01 Login ──▶ P-02 Resumen ──┬──▶ P-03 Registro en vivo
                              ├──▶ P-04 Políticas ──▶ P-08 Aprobación
                              ├──▶ P-05 Flota ──▶ P-07 Certificados
                              └──▶ P-06 Detecciones
```

## Archivos del prototipo v0.1

| Archivo | Contenido |
| --- | --- |
| `celeris-prototipo.pen` | Las 10 pantallas, el tablero de flujo y trazabilidad y los componentes base (barra lateral, estructura de la consola, botones, etiqueta R1/R2, pie de trazabilidad, cabecera del portal) |
| `png/00-flujo-navegacion.png` | Flujo de navegación y tabla pantalla → requisitos → casos de uso |
| `png/P-01-…png` a `png/P-10-…png` | Una imagen por pantalla (1440 px de ancho), para el informe |
| `navegable.html` | Prototipo clicable: las mismas imágenes con zonas activas sobre el menú y los botones |

### Prototipo navegable (`navegable.html`)

Las zonas clicables usan las coordenadas exactas de cada elemento en `celeris-prototipo.pen`. Si se cambia una pantalla
en pen.dev, hay que volver a exportar su PNG y, si un botón cambió de lugar, actualizar sus coordenadas en el HTML.

- Abrir: servir la carpeta por HTTP (abierto como archivo, algunos navegadores no cargan las imágenes):
  `python -m http.server 8765 --directory docs/software/e1/prototipo` y entrar a `http://127.0.0.1:8765/navegable.html`.
  En la app de Claude existe la configuración `prototipo-ce02` en `.claude/launch.json`.
- Empieza en el mapa de flujo (`#00`). Cada tarjeta y cada fila de la tabla abre su pantalla; `#P-04` abre directo P-04.
- Recorrido de la consola: P-01 → P-02 → menú lateral a P-03…P-08. Atajos: P-02 «Alertas abiertas» → P-06,
  nodos → P-05; P-04 «Proponer cambio» → P-08; P-05 «Certificado mTLS» → P-07 y «Revertir» → P-08;
  P-07 «Proponer rotación» → P-08; «Operador A» → P-01 (cerrar sesión).
- Portal: P-09 «Cómo instalar la CA» → P-10 y «Volver al aviso» → P-09.
- Las acciones que no cambian de pantalla (Exportar, Simular, Drenar, Aprobar bloqueado, Descargar la CA…) muestran un
  mensaje que explica lo que haría el sistema y qué requisito aplica.
- `Z` muestra u oculta las zonas clicables; `←` `→` recorren las pantallas en orden; `Retroceso` vuelve atrás.

Cada pantalla lleva en su pie su ID, los requisitos que cubre y la nota «datos de ejemplo, no medidos». P-05 y P-07
incluyen EC2-SHIELD (10.30.10.10) del inventario como caché de segundo nivel; su certificado es solo mTLS (D-13).

## Huecos encontrados al especificar (para el SRS)

| ID | Hueco | Propuesta |
| --- | --- | --- |
| H-01 | No hay requisito funcional de autenticación de operadores, aunque existen el actor OIDC y P-01. En el maestro, P-01 está trazada a REQ-F-13 (métricas). | Agregar un RF de autenticación (OIDC en R2, token en R1) y retrazar P-01 |
| H-02 | La tabla C1.2 marca REQ-F-26 como pendiente; el PAC ya se genera en `infra/gen/pac.py`. | Actualizar el estado en el SRS |
| H-03 | Las pantallas P-04, P-05, P-07 y P-08 dependen de `celeris-control`, que no existe. | Rotularlas como R2 — diseño |
