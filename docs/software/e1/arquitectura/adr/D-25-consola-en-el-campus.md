# D-25 · Frontend, backend y base de la consola en el campus

- **Estado:** Aceptada
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

La configuración que reciben los nodos y la llave que la firma son lo más sensible del sistema. Además, los datos de uso no deben salir del campus.

## Factores de decisión

- Que el nodo no dependa de Internet para su configuración
- La llave de firma y los datos en el campus
- Mismo origen para la SPA y la API

## Opciones consideradas

- **SPA, API y PostgreSQL en CTRL01**
- Backend en AWS
- SPA en S3 + CloudFront

## Decisión

Todo en CTRL01 10.20.20.10. En AWS solo EC2-GW (sin datos) y el respaldo en S3.

## Consecuencias

**Positivas**

- Si el enlace a Internet cae, la consola local y los nodos siguen
- Una sola superficie de API, sin CORS

**Negativas**

- La consola depende de ESX01; su continuidad es por respaldo, no por réplica (D-12)

## Cómo se verifica

T58 (EC2-GW solo alcanza CTRL01:443 y SIEM01), T59.

## Enlaces

RS-06 · D-12, D-24 · DS-21
