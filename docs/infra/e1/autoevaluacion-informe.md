# Autoevaluación del informe CE0311 contra la rúbrica (H3)

Informe evaluado: `entregables/CE0311/Informe_Diseno_Red_v1.1.docx` y `.pdf` (46 páginas). Lo genera `make informe`
desde la fuente única. Las páginas citadas son las del PDF y salen de `docs/infra/e1/informe-paginas.json`, que el
generador escribe en cada construcción. Si el texto cambia, las páginas pueden moverse: hay que releer ese archivo.

Criterios y pesos de `infra/trazabilidad.yaml` → `rubrica` (descriptor del nivel 4 de `Rubrica_S1_E1_Diseno_de_Red.xlsx`).
La validación V-87 comprueba que toda la evidencia declarada por criterio esté en el informe: secciones con contenido,
figuras y pruebas citadas. Hoy pasa en R1–R8. Eso prueba que la evidencia existe; no garantiza la calificación.

| Criterio | Peso | Nivel estimado | Evidencia (página del PDF) | Qué falta para asegurar el nivel 4 |
| --- | --- | --- | --- | --- |
| R1 Contexto y alcance | 10 | 4 | 2.1 necesidades con fuente [S-xx] (p. 6); 2.2 procesos críticos con criticidad (p. 7); 2.3 partes interesadas (p. 7); 3.1–3.3 alcance, límites y exclusiones justificadas (p. 8–9); FIG-1.1 (p. 5) | Completar en la portada el docente/curso y los nombres completos de los autores ([COMPLETAR], V-88). Las tablas de procesos y partes interesadas se escriben en el texto: no están en `infra/*.yaml`. |
| R2 Arquitectura lógica | 20 | 4 | Tabla de VLAN, CIDR, gateway y hosts (p. 12); rangos /26 por laboratorio (p. 12–13); rutas de AWS (p. 13); FIG-5.2 (p. 14); matriz zona × zona resumida en 7.3 (p. 28–29) y completa en el anexo A (p. 35); `Matriz_Componentes_Red_v1.1.xlsx` | CI-72 sigue abierto: confianza de la zona AWS «Media» en el inventario frente a «Baja» en el documento de diseño. El informe lo declara (p. 16), pero el equipo debe decidirlo. |
| R3 Conectividad híbrida (VPN) | 15 | 4 | 5.4 con los dos extremos, redes anunciadas, BGP, fase 1 y 2, DPD, MTU/MSS (p. 17–18); FIG-5.4 (p. 19); 6 con pruebas de conectividad planeadas y resultado del Modo L (p. 25–26); `Matriz_Pruebas_Conectividad_v*.xlsx` | La convergencia (T05, 27,2 s) es una medición **emulada**. La medición real queda para el Semestre 2 y el informe lo rotula así. |
| R4 Seguridad perimetral | 20 | 4 | Política por defecto y defensa en profundidad (p. 15–17); FIG-5.3 (p. 16); 7.1 interfaces de FW01 y 8 criterios de reglas (p. 26–27); 7.2 DMZ y D-29 (p. 27–28); 7.3 segmentación con pruebas por celda (p. 28–29); columna «Regla en FW01» por flujo (p. 20–21); anexo A (p. 35) | Depende de tres cambios en el FortiGate que la DTI debe aprobar [S-29] (NAT 1:1, ruta de retorno, exclusión SSL). Si la DTI no los aprueba, cambian 5.1 y 7.1. |
| R5 Detección (IDS/IPS y honeypot) | 10 | 3–4 | 8 con tecnología, ubicación, qué detecta, ATT&CK y prueba de validación por DET-xx (p. 30–31); HNY01 y HNY02 ubicados y justificados (p. 31); FIG-5.3 (p. 16); anexo E (p. 43) | Riesgo de quedar en 3: la publicación de HNY01 a Internet necesita la autorización escrita de la DTI [S-29], y la validación solo se ejecutó en el laboratorio emulado, sin las reglas ET Open completas. Conviene adjuntar la solicitud a la DTI y el escenario de ataque de S2. |
| R6 Flujos y matriz de componentes | 10 | 4 | Tabla de flujos con protocolo, puerto, protección y regla (p. 20–21); FIG-5.5a y FIG-5.5b (p. 22–23); 5.6 con los 31 componentes vigentes, IP planeada y criticidad (p. 24–25); la cobertura del 100 % de lo dibujado la verifica V-62 | CI-74 sigue abierto: el motivo de retiro de 4 subredes de AWS. No afecta a la matriz vigente; solo a la hoja «Retirados en v0.4». |
| R7 Calidad documental y trazabilidad | 8 | 4 | Control de versiones con inventario y commit (p. 2); glosario (p. 2–3); tabla de contenidos (p. 4); 10 conclusiones y pendientes (p. 32); 11 referencias IEEE (p. 33–34); anexo C necesidad → OD → D-xx → componente → F → T (p. 39–40); anexo D supuestos (p. 41–42); validación V-01…V-89 en `docs/infra/e1/validacion.md` | Los dos [COMPLETAR] de la portada. Si se edita el DOCX a mano, se pierde la trazabilidad con la fuente: los cambios van en `docs/infra/e1/informe/*.md` o en `infra/*.yaml` y luego `make informe`. |
| R8 Sustentación | 7 | No evaluable en el documento | Base escrita para responder: «por qué» en cada decisión (5.1 p. 12, 7.2 p. 27, 7.3 p. 30, 9 p. 31–32, anexo F p. 46); demostración preparada en el Modo L con T06, T18, T05 y T26 (anexo E) | Depende de la exposición. Hace falta ensayar la demostración de 5 minutos y que cada integrante pueda explicar, sin leer, las siete preguntas que el informe responde: FW01 detrás del FortiGate, nube y consola, protección por tramo, Wi-Fi sin descifrar, honeypot, PORTAL01 sin Internet y falla de FW01/EDGE01/VPN. |

## Criterios bajo el nivel 4 y por qué

- **R5 (3–4).** El diseño está completo, pero dos piezas dependen de terceros: la autorización de la DTI para publicar el
  honeypot y una validación que hasta ahora solo es emulada. Ninguna de las dos se resuelve escribiendo más.
- **R8 (no evaluable aquí).** Es la sustentación oral. El informe da los argumentos; el nivel lo decide la exposición.

## Pendientes del equipo antes de entregar

1. ~~Nombres completos y docente en la portada~~ Resuelto: `build_informe.py` toma los nombres del campo `equipo` del Marco común y pone el área «Infraestructura Tecnológica»; no hay docente (son tres jurados).
2. ~~CI-72 y CI-74~~ Resueltos el 2026-11-23: la zona AWS pasa a «Baja, expuesta» y el motivo de las 4 subredes es D-28.
3. Abrir el DOCX en Word y revisar la tabla de contenidos: el generador la actualiza con Word por COM; con LibreOffice
   habría que pulsar F9.
