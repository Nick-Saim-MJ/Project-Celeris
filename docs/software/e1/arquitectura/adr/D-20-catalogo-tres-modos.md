# D-20 · Catálogo de contenido con tres modos y aprobación DTI solo para descifrar

- **Estado:** Aceptada (R2)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

El encargado debe decidir qué se cachea sin esperar días a la DTI (OB-3), pero el descifrado afecta la privacidad y lo controla la DTI.

## Factores de decisión

- Autonomía del encargado (≤ 5 min, OB-3)
- Control de lo sensible
- Lo que nunca se toca (bancos, identidad)

## Opciones consideradas

- **Fuentes con modo `cachear`, `descifrar_y_cachear` o `nunca`**; aprobación solo para descifrar
- Una lista única editable por cualquiera
- Todo lo decide la DTI

## Decisión

El encargado activa sin aprobación las fuentes `cachear`. Las `descifrar_y_cachear` quedan pendientes hasta que un administrador las aprueba desde el campus. `nunca` gana siempre y las fuentes fijas de la DTI no se pueden mover.

## Consecuencias

**Positivas**

- El encargado resuelve solo la mayoría de los casos
- El descifrado siempre pasa por la DTI y queda auditado

**Negativas**

- Una fuente que requiere descifrado puede demorar hasta que la DTI la apruebe

## Cómo se verifica

`catalogo.feature`, T51, T54.

## Enlaces

REQ-F-31, RN-03, RN-07, RN-09, F-37 · DS-15, DS-17 · P-03, P-07
