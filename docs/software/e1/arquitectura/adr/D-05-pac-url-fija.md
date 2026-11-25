# D-05 · Proxy explícito con PAC por URL fija (GPO)

- **Estado:** Aceptada (R1, PAC implementado en `pac.rs`)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

Las PCs deben usar la caché sin que el usuario configure nada y seguir navegando si los nodos caen (REQ-NF-03).

## Factores de decisión

- Funcionar con HTTPS y ECH
- Evitar el secuestro de WPAD
- Respaldo si caen los nodos

## Opciones consideradas

- **Proxy explícito con PAC en URL fija por GPO**
- Proxy transparente (intercepción en la red)
- Autodescubrimiento WPAD

## Decisión

La GPO apunta a `pac.celeris.internal` (F3, TCP 80), que sirven EDGE01 y EDGE02. El PAC lista los nodos activos y termina en `DIRECT`. El proxy transparente queda como opción, no como diseño.

## Consecuencias

**Positivas**

- Funciona con HTTPS sin tocar la red de la DTI
- Si los dos nodos caen, las PCs pasan a `DIRECT` (piloto, F6)

**Negativas**

- F3 viaja sin cifrar (riesgo aceptado en el inventario; HTTPS en evaluación para S2)
- Un equipo sin la GPO no usa la caché

## Cómo se verifica

T09 (caída de EDGE01).

## Enlaces

REQ-F-26, NF-03 · F3, F6 · DS-13, DS-21
