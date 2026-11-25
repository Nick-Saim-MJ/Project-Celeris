# D-27 · BYOD sin descifrado y proxy opcional

- **Estado:** Aceptada; regla implementada en el nodo (`byod_networks`)
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

Los estudiantes usan equipos propios en el Wi-Fi (WIFI-EST). La universidad no los administra: no puede garantizar el consentimiento ni la instalación controlada de la CA.

## Factores de decisión

- Privacidad
- Ahorro posible en BYOD
- Que la regla no dependa de lo que configure una persona

## Opciones consideradas

- **BYOD siempre en passthrough; proxy opcional**
- Descifrar con una CA voluntaria
- Dejar BYOD fuera del servicio

## Decisión

El nodo nunca descifra el tráfico que llega desde las redes BYOD, aunque el dominio esté aprobado. La consola no ofrece la opción y el cambio del perfil BYOD es una acción crítica (solo desde el campus).

## Consecuencias

**Positivas**

- Se respeta la privacidad de equipos ajenos
- BYOD puede aprovechar lo que se cachea sin descifrar

**Negativas**

- El ahorro en BYOD es bajo y así se declara
- Hoy el nodo acepta una configuración que vacíe `byod_networks` (REQ-RN-11 parcial, se corrige en S2)

## Cómo se verifica

T56 (crítica), `byod.feature`.

## Enlaces

REQ-F-36, RN-11, F-37 · F31, F32 · DS-05
