# D-12 · PostgreSQL local en CTRL01 para la consola

- **Estado:** Aceptada (R2)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

La consola guarda catálogo, laboratorios, precargas, usuarios, auditoría y KPI (DS-12). Los datos de uso no deben salir del campus (D-25).

## Factores de decisión

- Transacciones y restricciones (auditoría solo de inserción)
- Sin dependencia de Internet
- Recuperación ante la caída de ESX01

## Opciones consideradas

- **PostgreSQL local, por socket Unix**
- SQLite
- Base administrada en AWS

## Decisión

PostgreSQL en la misma VM que la API, sin puerto de red. La continuidad es por respaldo cifrado en S3 (F18), sin réplica.

## Consecuencias

**Positivas**

- Tipos ricos (`cidr`, `jsonb`) y reglas en la base
- Sin superficie de red adicional

**Negativas**

- Sin alta disponibilidad: si cae ESX01, la consola espera la restauración [S-34]; los nodos siguen con la última configuración

## Cómo se verifica

T59 (restaurar la consola desde S3), T40 (respaldo con Object Lock).

## Enlaces

D-25 · F18 · DS-12, DS-21, DS-22
