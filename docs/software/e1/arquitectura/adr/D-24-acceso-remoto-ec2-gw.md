# D-24 · Acceso remoto por un proxy inverso en AWS (EC2-GW) a través de la VPN

- **Estado:** Aceptada
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

El encargado y la DTI necesitan la consola desde fuera del campus, sin publicar CTRL01 en Internet (OD-12).

## Factores de decisión

- Cero puertos del campus abiertos hacia CTRL01
- Un ataque consume recursos de AWS y no el enlace del campus
- Distinguir el origen de la sesión

## Opciones consideradas

- **EC2-GW (Caddy + Coraza) que reenvía por IPsec con certificado de cliente**
- Publicar la consola con NAT en el campus
- VPN de acceso remoto
- Túnel de un tercero

## Decisión

EC2-GW 10.30.0.10 termina TLS público (F29), aplica WAF y límite de intentos, y reenvía a CTRL01:443 por IPsec con mTLS (F30). La API marca la sesión como `remoto` y rechaza las acciones críticas (REQ-F-37).

## Consecuencias

**Positivas**

- El campus no publica la consola
- Una sesión robada desde fuera no puede ampliar el descifrado

**Negativas**

- Depende de la VPN: si cae, solo se pierde el acceso remoto
- Costo de AWS de ≈ US$ 70 al mes en 24×7 [S-12]

## Cómo se verifica

T53, T54, T58.

## Enlaces

REQ-F-33, F-37, NF-14 · F29, F30 · DS-15, DS-21 · OD-12
