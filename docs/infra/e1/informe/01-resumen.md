# 1. Resumen ejecutivo del diseño de red

**Proyecto y escenario.** Celeris Edge es un servicio de caché de descargas para los laboratorios de cómputo del Campus Juliaca [S-01]. El alcance son {{dato:n_lab}} laboratorios de {{dato:n_pcs_lab}} PCs institucionales ({{dato:n_pcs}} equipos) [S-26] y, como cliente sin descifrado, el Wi-Fi de estudiantes que administra la DTI [S-28].

**Problema de conectividad.** Cada PC descarga por separado los mismos archivos grandes: actualizaciones del sistema operativo, instaladores de los cursos y paquetes, del orden de 3 GB por PC en cada ciclo [S-27]. Cuando un laboratorio entero lo hace a la vez, el enlace de {{dato:enlace}} [S-02] se satura y las clases se retrasan. El FortiGate existente filtra categorías de sitios, pero no evita que el mismo archivo cruce el enlace 40 veces.

**Problema de seguridad.** La red de laboratorios es plana respecto de los servicios, no tiene detección interna y el usuario no puede saber qué se inspecciona. Además, un estudiante que llegue a los servidores podría alterar la configuración de la caché o, en el futuro, los sistemas académicos.

**Topología propuesta.** Detrás del FortiGate existente (FGT-EXT), un firewall OPNsense virtual (FW01) separa el servicio en {{dato:n_vlan}} VLAN con política de denegación por defecto (D-17, D-26). Los nodos EDGE01 y EDGE02 atienden las descargas dentro de la LAN; solo los MISS y las precargas salen a Internet (F8), y lo hacen por el FortiGate, de modo que FortiGuard sigue aplicando la política institucional. La consola del encargado (CTRL01) queda en el campus y firma la configuración que aplican los nodos (D-25). La Figura 1.1 resume el diseño en doce bloques.

{{figura:FIG-1.1|Qué observar: la descarga entra una sola vez por el FortiGate (F8) y se reparte desde EDGE01/EDGE02 a los laboratorios (F1); la nube solo recibe el acceso remoto (F29) y los respaldos (F18), y la consola no está en AWS.}}

**Integración con AWS.** Una VPN IPsec IKEv2 con dos túneles en activo/pasivo y BGP une FW01 con un Virtual Private Gateway de AWS (D1.10). La VPN tiene un uso concreto: transporta el panel remoto del encargado (EC2-GW → CTRL01, F30) y los eventos de EC2-GW hacia el SIEM (F13). En AWS solo hay dos piezas: EC2-GW, un proxy inverso sin datos que evita publicar la consola en el campus (D-24), y el bucket S3 de respaldos con Object Lock.

**Zonas principales.** MGMT (gestión, solo desde JMP01), SERVERS (consola), LAB (un rango /26 por laboratorio), DMZ-SVC (portal de transparencia detrás de WAF), DMZ-HONEY (honeypot), SECURITY (SIEM) y EDGE (nodos de caché). El Wi-Fi de estudiantes queda fuera de FW01 y solo alcanza EDGE y el portal, sin descifrado (D-27).

**Riesgos de red preliminares.**
- FW01 es virtual y único: si cae, no hay ruteo entre zonas (AM-12). Se mitiga con el puerto de emergencia BRK01 y el XML de configuración en Git (RTO 1 h).
- El diseño depende de tres cambios en el FortiGate que debe aprobar la DTI: NAT 1:1 hacia FW01, ruta de retorno y exclusión de los nodos de la inspección SSL [S-29].
- Hay tres puntos expuestos a Internet: el portal (F21), el honeypot en ventana autorizada (F24) y el panel remoto en AWS (F29).
- Los clientes pueden intentar saltarse el proxy por QUIC, DNS cifrado, IPv6 o WPAD falso (F7, T08, T23, T24, T60).

**Resultados esperados y siguientes pasos.** Al terminar el Semestre 2, cada OD-xx de la sección 4 debe tener su medición, y la matriz de pruebas planeadas (sección 6 y matriz XLSX) debe haberse ejecutado sobre el equipamiento real. Como validación previa, el diseño se ejecutó en un laboratorio **emulado** (Modo L, anexo E): {{dato:l_pasa}} pruebas PASA, {{dato:l_falla}} FALLA, {{dato:l_parcial}} PARCIAL y {{dato:l_no_aplica}} NO_APLICA. Ese resultado muestra que las reglas y los flujos se comportan como se describen; no es una implementación.
