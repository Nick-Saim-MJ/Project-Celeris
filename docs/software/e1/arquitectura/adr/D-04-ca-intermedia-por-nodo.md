# D-04 · CA raíz offline y CA intermedia por nodo con Name Constraints

- **Estado:** Aceptada; parcial en el código (hoy una CA única limitada)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

Para descifrar, cada nodo firma certificados de hoja con una CA que las PCs institucionales confían. Si esa llave se filtra, alguien podría suplantar cualquier sitio ante las PCs.

## Factores de decisión

- Limitar el daño de un nodo comprometido
- Que la CA solo pueda firmar los dominios aprobados (REQ-RN-04)
- La llave nunca sale de su nodo (REQ-NF-05)

## Opciones consideradas

- **Raíz offline + intermedia por nodo con Name Constraints**
- Una CA única para todos los nodos

## Decisión

La raíz vive offline; cada nodo tiene su intermedia, limitada por Name Constraints a los dominios de las fuentes `descifrar_y_cachear`. La rotación la aprueba un administrador desde el campus (`POST /v1/ca/{nodo}/rotacion`, REQ-F-37).

## Consecuencias

**Positivas**

- Un nodo comprometido no compromete al otro
- Un dominio fuera de las restricciones no se puede firmar aunque se pida

**Negativas**

- Agregar un dominio a descifrar puede exigir reemitir la intermedia
- Más pasos de operación (P-07: huella y vencimiento)

## Cómo se verifica

Revisión de certificados (REQ-F-18). El nodo ya rechaza una configuración cuyo dominio la CA no cubre (`ca_no_cubre`, REQ-RN-04).

## Enlaces

REQ-F-18, NF-05, RN-04, F-37 · DS-05, DS-12 (`ca_intermedia`) · P-07
