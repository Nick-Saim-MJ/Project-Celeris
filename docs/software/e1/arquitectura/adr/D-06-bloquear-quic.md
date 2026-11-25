# D-06 · Bloquear UDP/443 (QUIC) en los laboratorios

- **Estado:** Aceptada (regla de red en CE03)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

Si los navegadores usan QUIC, las descargas salen por UDP y no pasan por el proxy, que solo atiende TCP.

## Factores de decisión

- Que las descargas pasen por la caché (OB-1)
- No romper la navegación

## Opciones consideradas

- **Bloquear UDP/443 desde LAB y desactivar QUIC por política de equipo**
- Permitir QUIC

## Decisión

FW01 bloquea QUIC, DoT y la fuga por IPv6 desde LAB (F7, «bloqueado»). Además, la política de los equipos desactiva QUIC. Los navegadores vuelven a TCP y usan el PAC.

## Consecuencias

**Positivas**

- Las descargas pasan por la caché
- Menos tráfico que se salta el control

**Negativas**

- Se pierde la mejora de latencia de HTTP/3 en los laboratorios

## Cómo se verifica

T08 (LAB → UDP 443): FW01 cuenta paquetes bloqueados por la regla de F7.

## Enlaces

F7 · OB-1 · D-17 (CE03)
