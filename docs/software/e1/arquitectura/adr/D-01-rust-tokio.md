# D-01 · Rust + Tokio para el nodo y la consola

- **Estado:** Aceptada (R1 en el nodo; R2 en la consola)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

El nodo de caché ya existe en Rust (`celeris-cache`, `src/`) y atiende a 40 PCs que descargan a la vez (REQ-NF-02). La consola tiene que verificar y firmar la misma configuración ed25519 que el nodo verifica (D-11). El equipo es de dos personas (RS-04).

## Factores de decisión

- Seguridad de memoria en un proxy que recibe tráfico de toda una red (REQ-F-11)
- Rendimiento: p95 ≤ 5 ms en HIT desde memoria (REQ-NF-01)
- Reutilizar tipos y verificación entre nodo y consola
- Curva de aprendizaje para un equipo de dos

## Opciones consideradas

- **Rust + Tokio** (axum en la consola)
- Go
- Python (FastAPI) para la consola

## Decisión

Rust + Tokio en ambos. La consola usa axum para compartir con el nodo los tipos de la configuración firmada y la verificación ed25519.

## Consecuencias

**Positivas**

- Sin errores de memoria en el plano de datos
- Un solo lenguaje, una sola cadena de CI (`clippy`, `cargo-deny`, REQ-NF-09)

**Negativas**

- Curva alta para la consola web; más tiempo de desarrollo en S2
- Menos bibliotecas de administración web que en Python

## Cómo se verifica

REQ-NF-01 (k6 / oha), REQ-NF-09 (cobertura ≥ 70 % y `clippy` sin advertencias en CI).

## Enlaces

RS-01 · REQ-NF-01, NF-09, NF-10 · DS-02, DS-03, DS-13, DS-21
