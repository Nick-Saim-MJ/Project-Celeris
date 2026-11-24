# Anexo E. Validación emulada (Modo L y AWS Emulator)

> Lo que describe este anexo es una **emulación**. No es la implementación del diseño, no se ejecutó sobre OPNsense, el VGW de AWS ni la red del campus, y no reemplaza las pruebas del Semestre 2.

**Por qué se emuló.** Antes de pedir equipos y cambios a la DTI conviene comprobar que el diseño es coherente: que las reglas generadas del inventario dejan pasar lo que deben y bloquean lo demás, que la VPN con NAT-T y BGP converge y que cada escenario de ataque produce su alerta. Para eso se usaron dos entornos reproducibles que se generan desde la misma fuente única que este informe.

## Modo L: laboratorio emulado local

Es una topología containerlab con un contenedor por equipo del diseño y las mismas IP del inventario. La WAN emulada usa direcciones de documentación (RFC 5737 [10]). FW01 se emula con Debian, nftables (reglas generadas del inventario), strongSwan, FRR, Suricata, Unbound, NTP y CrowdSec. Los nodos de caché ejecutan el mismo binario de producción y el SIEM es un Wazuh 4.9.2 real.

**Resultado del ensayo del {{dato:l_fecha}}:** {{dato:l_pasa}} PASA, {{dato:l_falla}} FALLA, {{dato:l_parcial}} PARCIAL y {{dato:l_no_aplica}} NO_APLICA. Un resultado PARCIAL o NO_APLICA nunca cuenta como PASA.

{{tabla:ensayo_l}}

**Qué no se probó en L, y por qué.**
- Las pruebas que necesitan AWS real (T01–T04, T21, T59) o el hardware del campus (T23, T25, T33, T34, T36, T40, T42, T43) se ejecutan en los Modos A y H.
- T50, T53 y T54 necesitan la consola completa, que corresponde al Semestre 2.
- T58 quedó PARCIAL: se midió la denegación de FW01, pero el Security Group sg-gw no existe en el laboratorio.
- El FortiGate emulado reenvía todo y deja la política a FW01. Tampoco se emulan FortiGuard, la inspección SSL ni la exclusión de los nodos [S-29].
- No hay trunk 802.1Q ni controles de capa 2, ni Internet real. Los certificados son de una CA de laboratorio, no de ACME público.

## AWS Emulator: plano de control

`tofu apply` se ejecutó contra un emulador local de AWS y el resultado se leyó con la CLI de AWS. Se crearon la VPC, las subredes, las tablas de rutas, el VGW, el customer gateway, la conexión VPN, sg-gw, las NACL, EC2-GW, el bucket con versionado, Object Lock y su política, el usuario de respaldo y las etiquetas. Las {{dato:e_verificaciones}} comprobaciones contra el inventario dieron {{dato:e_resultado}}.

El emulador **no** abre túneles, no ejecuta instancias, no mueve tráfico ni evalúa IAM o políticas de bucket. Tampoco propaga las rutas del VGW, así que en el emulador la ruta a 10.20.0.0/16 es estática (CI-55). Las llaves de la VPN y las credenciales aparecen como `[REDACTADO]` en las evidencias.

## Por qué esto no es implementación

La emulación valida la lógica del diseño: reglas, rutas, orden de los controles y alertas. No valida el rendimiento real, el comportamiento de OPNsense y del VGW gestionado, ni los cambios en el FortiGate y la capa de acceso de la DTI. Por eso cada prueba conserva el modo en que se ejecutará en el Semestre 2, y las metas de los OD-xx se medirán en el piloto.
