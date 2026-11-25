# D-11 · Configuración firmada (ed25519) publicada por la consola

- **Estado:** Aceptada; parcial en el código (verificación hecha, descarga por F10 en R2)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

El encargado cambia qué se cachea y quién accede sin tocar servidores. Esos cambios viajan de CTRL01 a los nodos por F10 y no deben poder alterarse ni repetirse una versión vieja.

## Factores de decisión

- Integridad aunque alguien intercepte F10
- Rechazar versiones viejas (repetición)
- El nodo sigue funcionando si la consola cae

## Opciones consideradas

- **Versión de configuración firmada con ed25519**; el nodo la pide cada 30 s
- Editar `config.toml` en cada nodo
- Empujar la configuración desde la consola

## Decisión

La consola compila una versión inmutable y la firma con una llave que no sale de CTRL01. El nodo verifica la firma con la llave pública fijada al arrancar, rechaza versiones menores que la aplicada y, si algo falla, conserva la anterior.

## Consecuencias

**Positivas**

- Nadie puede inyectar configuración sin la llave de firma
- Si CTRL01 cae, el nodo sigue con la última versión válida

**Negativas**

- La llave de firma es un activo crítico: se respalda cifrada (F18) y nunca va a AWS
- Un cambio tarda hasta una consulta (≤ 30 s) en llegar (REQ-NF-16 pide ≤ 60 s)

## Cómo se verifica

T51 (cambio del encargado y configuración sin firma). Hoy `signed.rs` ya rechaza `sin_firma`, `firma_invalida` y `version_anterior`.

## Enlaces

REQ-F-17, RN-08, NF-16 · F10 · DS-02, DS-13, DS-19
