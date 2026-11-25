# D-21 · Precarga en el nodo, no en un servicio aparte

- **Estado:** Aceptada (R2)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

El contenido de una clase debe estar listo antes de que empiece (OB-2), descargado una sola vez dentro de la ventana de la DTI (REQ-RN-10).

## Factores de decisión

- Reutilizar caché, coalescencia y verificación de hash
- Menos piezas que operar
- Respetar ventana y límite de ancho de banda

## Opciones consideradas

- **El nodo ejecuta las precargas que llegan en la configuración firmada**
- Un servicio de precarga independiente

## Decisión

La consola publica la precarga en la configuración firmada. El nodo la ejecuta dentro de la ventana de 00:00 a 05:00 y sin superar 50 Mbps, guarda cada objeto por SHA-256 e informa el avance por F10.

## Consecuencias

**Positivas**

- Al iniciar la clase, las PCs reciben HIT
- No hay otro servicio ni otro flujo

**Negativas**

- El nodo crece en responsabilidades: la precarga compite con el tráfico de la noche, acotada por el límite

## Cómo se verifica

T50, `precarga.feature`.

## Enlaces

REQ-F-22, F-34, F-35, RN-10 · DS-16, DS-18 · P-05, P-06
