# D-02 · Hudsucker para el proxy con descifrado selectivo

- **Estado:** Aceptada (R1, implementada)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

El nodo debe atender como proxy explícito HTTP y `CONNECT` (REQ-F-01) y descifrar solo los dominios aprobados, comparando el SNI con el `CONNECT` (REQ-F-02).

## Factores de decisión

- Decidir el descifrado antes del handshake (por `CONNECT`) y después (por SNI)
- Integración con rustls y Tokio
- Ya funcionando en el repositorio

## Opciones consideradas

- **Hudsucker 0.25** (Rust)
- Squid con ssl-bump
- mitmproxy

## Decisión

Hudsucker: expone `should_intercept_connect` y `should_intercept_tls`, que el nodo usa para aplicar la política de `signed.rs` (incluida la red BYOD, REQ-F-36).

## Consecuencias

**Positivas**

- El descifrado se decide en dos puntos; por defecto no se descifra (REQ-NF-08)
- Mismo proceso para proxy, caché y TLS

**Negativas**

- Dependencia de una biblioteca pequeña: si se abandona, hay que mantener un fork
- No expone los bytes del túnel: los túneles solo se cuentan, no se miden

## Cómo se verifica

T07 (LAB → EDGE 3128), `intercepcion.feature`, `byod.feature` y T56.

## Enlaces

REQ-F-01, F-02, F-36, NF-08 · DS-05
