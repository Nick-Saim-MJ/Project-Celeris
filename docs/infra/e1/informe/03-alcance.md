# 3. Alcance del diseño de red

## 3.1 Declaración de alcance

El diseño comprende la conectividad, el direccionamiento, la segmentación, la seguridad perimetral, la detección y la protección en tránsito de la red de los laboratorios de cómputo del Campus Juliaca y de los servicios que la atienden: nodos de caché, consola del encargado, portal de transparencia y SIEM. Incluye la integración del Wi-Fi de estudiantes como cliente sin descifrado y la integración por VPN IPsec con una VPC de AWS (10.30.0.0/16) para el acceso remoto al panel y los respaldos fuera del sitio. Todo lo diseñado cuelga de la supernet del proyecto 10.20.0.0/16 (RFC 1918), detrás del FortiGate existente.

La etapa es de análisis y diseño. Ningún componente se presenta como instalado en el campus: lo que se ejecutó en el laboratorio emulado se informa como validación previa en el anexo E.

## 3.2 Límites

**Físicos.** El rack del servicio: un servidor ESXi (ESX01), el switch núcleo SW-CORE01, la UPS UPS01 y el puerto de emergencia BRK01, más sus enlaces con la capa de acceso de los laboratorios (SW-ACC) y con el FortiGate (red de tránsito 10.20.0.0/29). En AWS, la región definida por la variable `var.region` de OpenTofu [S-11].

**Tecnológicos.** OPNsense (FW01) con Suricata, CrowdSec, Unbound y NTP; las {{dato:n_vlan}} VLAN y los rangos /26 de laboratorio; la VPN IPsec con BGP; el WAF Coraza de PORTAL01 y de EC2-GW; los señuelos HNY01 y HNY02; Wazuh; la VPC con sus subredes, tablas de rutas, Security Groups y NACL; EC2 y S3.

**Organizacionales.**

| Segmento | Quién lo administra | Cómo |
| --- | --- | --- |
| FortiGate, Wi-Fi de estudiantes y capa de acceso | DTI | Se documentan AS-IS; el proyecto solo pide cambios mínimos y escritos [S-14, S-28, S-29] |
| FW01, VLAN del proyecto, VPN y AWS | Equipo del proyecto durante el piloto; DTI después | Administración solo desde JMP01 con MFA (F20); reglas exportadas a Git y revisadas por el otro integrante |
| Contenido de la caché y acceso de cada laboratorio | Encargado de laboratorio | Desde la consola (ENC01, F28, o EC2-GW, F29/F30), sin acceso a la red de gestión |
| Aprobación de dominios a descifrar y perfil BYOD | Administrador de la DTI | Desde la consola, solo con origen campus (REQ-F-37, T54) |

## 3.3 Exclusiones

| Exclusión | Justificación |
| --- | --- |
| Descifrar el tráfico de equipos personales (BYOD) | La universidad no administra esos equipos: no puede garantizar consentimiento ni la instalación controlada de la CA. El nodo trata la red WIFI-EST siempre en *passthrough* (D-27, REQ-F-36, T56) |
| Rediseño del FortiGate, del Wi-Fi y de la capa de acceso | Son de la DTI y ya están en producción para todo el campus. El diseño los incorpora tal como están y pide solo los cambios de [S-14, S-28, S-29] |
| Red administrativa y PCs de docentes | Fuera del piloto. Quedan protegidas indirectamente: desde LAB y WIFI-EST no se alcanza ninguna zona del proyecto salvo los servicios listados (sección 7.3) |
| Modo examen | Necesidad futura de la universidad. El diseño deja preparados los rangos por laboratorio y la configuración firmada, sin implementarlo en S1 |
| Caché de segundo nivel en AWS (D-19) | Un MISS servido desde AWS igual cruza el enlace del campus: no ahorra ancho de banda |
| Varias sedes | Solo hay bloques reservados (10.21.0.0/16 y 10.22.0.0/16); su diseño no es parte de este entregable |
