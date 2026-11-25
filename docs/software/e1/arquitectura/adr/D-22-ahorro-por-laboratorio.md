# D-22 · Ahorro reportado por laboratorio, nunca por persona

- **Estado:** Aceptada (R2)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

Hay que medir el ahorro (OB-1) sin vigilar a los estudiantes (Ley 29733, RS-05; 00 M11).

## Factores de decisión

- Minimización de datos
- Suficiente para el caso de negocio
- Vista en vivo útil para el encargado (P-11)

## Opciones consideradas

- **Agregados por laboratorio y por nodo**
- Reporte por IP o por usuario

## Decisión

El nodo envía agregados de 30 s por laboratorio (peticiones, HIT, MISS, BYPASS, 403, bytes) y la consola los guarda en `kpi_intervalo` y `kpi_diario`. No hay URL, IP de equipos ni usuarios. Por eso no hay vista por PC.

## Consecuencias

**Positivas**

- Cumple minimización (REQ-NF-07)
- Alcanza para el ahorro del mes (P-02) y la actividad en vivo (P-11)

**Negativas**

- No se puede diagnosticar desde la consola qué PC concreta falla; eso se hace en el nodo, con el registro local seudonimizado

## Cómo se verifica

`envivo.feature`, `reportes.feature`, T26.

## Enlaces

REQ-F-13, F-25, NF-07, NF-13 · DS-12, DS-19 · P-02, P-11
