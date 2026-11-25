# D-03 · Almacenamiento direccionado por contenido (SHA-256)

- **Estado:** Aceptada (R1, implementada)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

El mismo instalador se descarga desde URLs distintas (espejos, parámetros de rastreo) y un corte de energía no debe dejar servir un objeto corrupto (REQ-NF-04).

## Factores de decisión

- Deduplicar el mismo contenido
- Verificar el objeto antes de servirlo (REQ-F-06)
- Escritura atómica

## Opciones consideradas

- **Objeto guardado por su SHA-256** con un índice clave → hash
- Archivo por URL

## Decisión

El cuerpo se guarda en `objects/ab/cd…` por su SHA-256 y el índice (`moka` + `DiskIndex`) une la clave normalizada con el hash. `read_object` verifica el hash en cada HIT.

## Consecuencias

**Positivas**

- Un mismo instalador ocupa disco una sola vez
- Un objeto alterado o truncado se detecta y se borra (estado Corrupta en DS-09)

**Negativas**

- Costo de calcular SHA-256 en cada escritura y lectura
- Hace falta un índice aparte para expulsar por LRU (REQ-F-09)

## Cómo se verifica

Pruebas del nodo (hash y kill -9) y REQ-NF-04.

## Enlaces

REQ-F-06, F-07, F-09, NF-04 · DS-04, DS-09
