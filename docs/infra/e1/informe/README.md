# Texto del informe CE0311 (H3)

Cada archivo `NN-*.md` es el texto de una sección de la plantilla
`docs/fuentes/CE03/S1_E1_Analisis_y_Diseno_de_Red.docx`; `00-*.md` son los preliminares y `A…F-*.md` los anexos.
`docs/infra/e1/build_informe.py` los une a una copia de la plantilla (`make informe`). No edite el DOCX a mano.

## Sintaxis que entiende el generador

| Marca | Resultado |
| --- | --- |
| `# 5. Topologías de red (diseño)` | Título 1. En las secciones 1–11 debe coincidir con el título de la plantilla |
| `## 5.1 …` / `### …` | Título 2 / Título 3 |
| Párrafo separado por una línea en blanco | Párrafo normal. `**negrita**` y `` `código` `` dentro del texto |
| `- elemento` | Viñeta (estilo de lista de la plantilla) |
| `\| a \| b \|` | Tabla de contexto escrita aquí (procesos, partes interesadas, alternativas). Nunca IP, VLAN, flujos ni pruebas |
| `{{tabla:nombre}}` | Tabla generada desde `infra/*.yaml` (ver `TABLAS` en el generador) |
| `{{figura:FIG-5.1\|Qué observar…}}` | PNG de `entregables/CE0311/diagramas/`, su pie (de `trazabilidad.yaml`) y la frase de qué observar |
| `{{dato:clave}}` | Cifra calculada desde la fuente única (ver `datos()` en el generador) |
| `> texto` | Nota destacada |

Las IP, puertos, VLAN, componentes, flujos, pruebas, amenazas y supuestos del texto deben existir en `infra/*.yaml`;
V-80…V-89 lo comprueban sobre el DOCX generado.
