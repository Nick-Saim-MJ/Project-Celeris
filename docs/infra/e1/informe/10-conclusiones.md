# 10. Conclusiones del diseño y siguientes pasos

El diseño resuelve el problema de conectividad con una caché dentro de la LAN, no con más ancho de banda: una descarga entra una vez por el enlace (F8) y se reparte a los laboratorios (F1). Además da al encargado control por laboratorio sin darle acceso a la red de gestión (F28, OD-11). En seguridad, el diseño:

- separa el servicio en {{dato:n_vlan}} VLAN con denegación por defecto y una regla por flujo (OD-06, sección 7.3);
- incorpora el FortiGate existente en lugar de reemplazarlo, a cambio de tres pedidos explícitos a la DTI [S-29];
- aísla el Wi-Fi de estudiantes sin descifrarlo (D-27, T56, T57);
- no publica ningún puerto del campus para la consola: el acceso remoto entra por AWS y cruza la VPN con mTLS (D-24, OD-12);
- protege cada tramo del trayecto de los datos, o documenta por qué no (OD-07, sección 5.5);
- planifica la detección con IDS/IPS, honeypot, canary, WAF y auditoría, todo correlacionado en Wazuh (sección 8).

La nube se usa solo donde aporta algo que el campus no puede dar por sí mismo: una entrada pública que no expone el campus y una copia inmutable fuera del sitio. La consola, la llave de firma y los datos quedan en el campus (D-25, anexo F).

**Qué se validó y qué no.** El comportamiento de las reglas, la VPN con NAT-T y BGP, la caché y la detección se ejecutó en un laboratorio **emulado** (anexo E): {{dato:l_pasa}} PASA, {{dato:l_falla}} FALLA, {{dato:l_parcial}} PARCIAL y {{dato:l_no_aplica}} NO_APLICA. Ese resultado reduce el riesgo del diseño, pero no reemplaza las pruebas sobre OPNsense, el VGW de AWS y la red real del campus.

**Pendiente para el entregable «Implementación, testing y monitoreo de red» (Semestre 2).**

| Qué falta | Cómo se cierra | Evidencia |
| --- | --- | --- |
| Confirmar con la DTI el NAT 1:1, la ruta de retorno, la exclusión de inspección SSL y la ventana del señuelo | Reunión y aprobación escrita | [S-29], [S-31] |
| Confirmar la red real del Wi-Fi de estudiantes | Levantamiento con la DTI | [S-28] |
| Verificar que la capa de acceso soporta los controles de capa 2 | Levantamiento por modelo de switch | [S-14], T23 |
| Implementar FW01, las VLAN, los nodos, la consola, el portal, los señuelos y Wazuh | Despliegue en el Modo H | Matriz de pruebas completa |
| Crear la VPC, EC2-GW, la VPN y S3 en AWS | OpenTofu en el Modo A y luego definitivo | T01–T05, T21, T40, T58, T59 |
| Ejecutar las pruebas NO_APLICA y PARCIAL del Modo L | Modos A y H | Anexo E |
| Medir los indicadores OD-01…OD-12 en el piloto | Un laboratorio piloto con la DTI | Sección 4 |
| Monitorear la operación | Alertas de Wazuh de nivel ≥ 10 y revisión mensual de reglas | DET-09 |

**Hoja de ruta.** Laboratorio emulado (hecho) → AWS efímero (Modo A) → piloto en un laboratorio con la DTI → ampliación a los diez laboratorios → modo examen como trabajo futuro.
