# D-09 · OpenTofu + Ansible para la infraestructura como código

- **Estado:** Aceptada
- **Fecha:** 2026-11-24 (revisión v0.4)
- **Decide:** equipo del proyecto; la DTI valida lo que toca su red

## Contexto y problema

El laboratorio se levanta en local (Modo L), en AWS (Modo A) y en el campus (Modo H) con la misma definición (D-18). EC2-GW debe poder recrearse si se compromete.

## Factores de decisión

- Licencia abierta
- Reproducibilidad en una cuenta AWS volátil [S-13]
- Recrear EC2-GW en minutos

## Opciones consideradas

- **OpenTofu + Ansible**
- Terraform
- Scripts manuales

## Decisión

OpenTofu para AWS y Ansible para configurar las VM. Ningún secreto en el repositorio (RS-03).

## Consecuencias

**Positivas**

- EC2-GW, que no guarda datos, se destruye y se recrea con OpenTofu (≈ 15 min, Arquitectura v0.4 §4.2)
- La misma IaC sirve para las pruebas de CE03

**Negativas**

- Dos herramientas que mantener

## Cómo se verifica

`make tofu-check` (CE03).

## Enlaces

D-18 (CE03) · RS-03 · EC2-GW
