# Integración v0.4 — Celeris Edge

Rama `integracion/v0.4`. Reúne cinco ramas que nunca se fusionaron en `main`. No aplica la v0.4 (eso es I1): integra el trabajo tal como estaba. No se tocó ningún dato de `infra/*.yaml`, no se borró trabajo de ninguna rama y no se hizo push.

## 1. Ramas integradas

Base: `origin/e1/matriz-pruebas` (64f21c1), que ya contiene a `e1/codigo-lab`. Las tres ramas de Henyelrey divergen de 9b00fa6 y están apiladas (diagramas → componentes → ce02). Se fusionaron en este orden, con `--no-ff`:

| Orden | Rama | Commit de fusión |
|---|---|---|
| base | `e1/codigo-lab` + `e1/matriz-pruebas` | 64f21c1 |
| 1 | `e1/diagramas` | 7c9e337 |
| 2 | `e1/matriz-componentes` | 1351b42 |
| 3 | `ce02/e1-requerimientos-diseno` | 7b8ffef |

`git merge-base --is-ancestor` da verdadero para las cinco ramas. Ningún archivo de `entregables/` de las cinco ramas falta en `integracion/v0.4` (23 archivos).

## 2. Conflictos y cómo se resolvieron

| Fusión | Archivo | Resolución |
|---|---|---|
| diagramas | `Makefile` | Solo el texto de ayuda. Se conserva «genera el XLSX de pruebas» de matriz-pruebas y la línea de `diagrams-check` de diagramas. El cuerpo de `diagrams-check` entró limpio. |
| diagramas | `CAMBIOS-INVENTARIO.md` | Unión. Las entradas de diagramas chocaban en número (ver §3). |
| diagramas | `validacion.md` | Regenerado con `infra/validate.py`, no a mano. |
| diagramas | `FIG-*.drawio` | Sin conflicto de texto, pero V-54 fallaba: FIG-5.5b no tenía F27 (flujo de matriz-pruebas). Se regeneraron los `.drawio` con `infra/gen/drawio.py` desde el inventario. |
| componentes | `Makefile` | Dos cuerpos distintos del objetivo `matrices`. Los mostré y propuse la combinación; **elegiste «Combinar»**: `xlsx_componentes.py --verificar` y luego `infra/genera.py xlsx-pruebas`. Se descartó la rama condicional de componentes porque `infra/gen/xlsx_pruebas.py` no tiene `__main__` y no habría generado nada. |
| componentes | `CAMBIOS-INVENTARIO.md` | Unión. CI-24 y CI-25 de esa rama eran los de diagramas, ya integrados; solo se añadió su CI-26 renumerado. |
| componentes | `validacion.md` | Regenerado. |
| ce02 | `.gitattributes` | Unión sin duplicados: `*.sh`, `siem/wazuh/*`, `*.tftpl`, el JSON de OpenTofu y `*.pen`. |
| ce02 | `.gitignore` | Unión sin duplicados: lo de laboratorio, evidencias y OpenTofu más `.tools/`. |
| ce02 | `CAMBIOS-INVENTARIO.md` | Unión con renumeración (ver §3). |
| ce02 | `validacion.md` | Regenerado. |
| ce02 | `e2e/origin.py` | Cada rama añadió un endpoint: `/echo` (matriz-pruebas, devuelve todas las cabeceras recibidas) y `/ident` (CE02, solo las de identidad). Se conservan los dos; `e2e/run.sh` usa ambos. |
| ce02 | `src/handler.rs`, `src/policy.rs` | **Sin conflicto de texto, pero con conflicto semántico:** ambas ramas definieron `CLIENT_IDENTITY_HEADERS` y `strip_client_identity` (REQ-F-28), y el handler la llamaba dos veces. Habría fallado `cargo build` por definiciones duplicadas. Se conserva una definición (la de matriz-pruebas) y una llamada, antes de la guarda del CONNECT. El test de CE02 se renombró (`quita_la_identidad_de_una_peticion_completa`) y se mantiene. Se conserva todo lo demás: `tls_decision` y los tests de SNI = CONNECT (CE02), `Cache-Status` y el shield (matriz-pruebas). |

## 3. Renumeración de CI y supuestos

El número ya usado en la rama base se conserva; la rama de Henyelrey pasa al siguiente libre. Se actualizaron las referencias en los archivos de esa rama.

| Rama | Antes | Ahora | Tema | Referencias actualizadas |
|---|---|---|---|---|
| diagramas | CI-24 | **CI-30** | Capas de defensa en profundidad y salto del ISP | `infra/gen/drawio.py`, `FIG-5.2/5.3/5.4.drawio` |
| diagramas | CI-25 | **CI-31** | Prefijo on-premise /16 frente a /14 | `infra/gen/drawio.py`, `FIG-5.4.drawio` |
| componentes | CI-26 | **CI-32** | Textos de componentes sin dato verificable (V-66) | solo `CAMBIOS-INVENTARIO.md` |
| ce02 | CI-27 | **CI-33** | Publicación del portal: CTRL01 → WEB01 sin flujo | `docs/software/e1/diagramas/` (README, 2 `.puml`, 2 `.svg`) |
| ce02 | CI-28 | **CI-34** | Supuestos nuevos del diseño de software | README de diagramas |

`CI-24` a `CI-29` (laboratorio, IaC, críticas, matriz de pruebas, laboratorio ampliado, F27) siguen siendo de matriz-pruebas; `infra/gen/lab.py` y los YAML los citan con esos números.

Colisión adicional, no pedida pero del mismo tipo: CE02 proponía registrar los supuestos **S-16 y S-17**, pero `infra/trazabilidad.yaml` (matriz-pruebas) ya los usa para otros temas, además de S-18 y S-19. Los de CE02 pasan a **S-20 (vigencia del token de enrolamiento) y S-21 (umbral de errores del rollout)** en la entrada CI-34, el README y los diagramas DS-07, DS-08, DS-10, DS-11 y DS-12 (`.puml` y `.svg`). Siguen sin registrarse en `trazabilidad.yaml`, como ya decía CI-34. Revísalo si prefieres otro criterio.

## 4. Verificación

Entorno: Windows para Python y WSL Ubuntu para `make`, Rust 1.100 (instalado con rustup en WSL para esta tarea) y `e2e/run.sh`.

| Chequeo | Resultado |
|---|---|
| `cargo build` | OK |
| `cargo test` | OK, 125 pruebas |
| `cargo clippy -- -D warnings` | OK |
| `make validate` | OK: 0 FALLA, 6 advertencias, 52 PASA, 1 pendiente (V-80) |
| `make test-gen` | OK, 133 pasan y 7 se omiten (140 pasan en Windows) |
| `e2e/run.sh` | OK sobre el sistema de archivos nativo de WSL: 365 verificaciones, «TODO OK» |
| `make lab-up` | No se ejecutó, como se pidió |

### Chequeos que no están limpios, y por qué

- **`e2e/run.sh` sobre `/mnt/d` falla 4 verificaciones**, todas del tipo «solo el dueño puede leer la llave/token/log: esperaba 600, obtuve 777». Es el disco NTFS montado en WSL, que no admite `chmod`. En una copia dentro del disco de WSL no falla ninguna.
- **V-50 (advertencia):** los `.png` y `.pdf` de las figuras son anteriores a los `.drawio`. No hay draw.io Desktop en esta máquina, así que no se pudieron reexportar. Además, `FIG-5.2/5.3/5.4` cambiaron de CI-24/25 a CI-30/31 y `FIG-5.5b` ganó F27: sus PNG y PDF muestran lo anterior hasta que alguien ejecute `make diagrams-check` con draw.io instalado.
- **V-42 (advertencia):** la prueba crítica T23 (fuga IPv6) está en NO_APLICA en el último ensayo del Modo L. Ya era así en matriz-pruebas.
- **V-66 (advertencia):** textos de componentes sin dato verificable. Es el CI-32 (antes CI-26), de la rama de componentes.
- **V-11 y V-33 (advertencias):** contradicciones ya registradas (CI-03, CI-04, CI-06, CI-16).
- **V-26 (advertencia):** la correspondencia de contenidos mínimos es una propuesta (CI-02).
- **V-80:** pendiente de P5 (informe DOCX), igual que antes.
- **gitleaks** no está instalado: `make validate` lo omite y lo ejecuta el CI.
- **V-65** recalculó con Excel (COM) en la ejecución de Windows; en WSL no hay LibreOffice ni Excel y el chequeo depende del entorno.

## 5. Para revisar antes del PR

- La fusión semántica de `strip_client_identity` es la decisión más delicada: compila y las pruebas pasan, pero conviene que quien escribió REQ-F-28 mire `src/handler.rs` (una sola llamada, antes del CONNECT).
- Los CI y supuestos renumerados (CI-30 a CI-34, S-20 y S-21) cambian lo que cada autor tiene en su rama. Hay que avisarles.
- Los finales de línea: el repo usa `core.autocrlf` en Windows y Git avisó de que convertirá LF a CRLF en `validacion.md`, `cobertura-figuras.*`, los `.drawio` y `drawio.py`. No cambia el contenido.
