## 1.6 Descripción general

### 1.6.1 Perspectiva del producto

Celeris Edge se coloca entre las PCs institucionales de los laboratorios y el FortiGate de la DTI (FGT-EXT). No
reemplaza a ninguno de los dos. El FortiGate sigue filtrando la salida de los nodos con FortiGuard (F8), y las PCs
usan el proxy porque el PAC se publica por GPO en una URL fija (D-05, F3).

| Flujo | De → a | Puerto | Qué lleva |
| --- | --- | --- | --- |
| F3 | LAB → EDGE01/EDGE02 | TCP 80 | PAC (`pac.celeris.internal`) |
| F1 | LAB → EDGE01/EDGE02 | TCP 3128 | Proxy explícito (HTTP y `CONNECT`) |
| F31 | WIFI-EST → EDGE01/EDGE02 | TCP 3128, 80 | Proxy y PAC opcionales para BYOD, siempre sin descifrar |
| F8 | EDGE → Internet vía FortiGate | TCP 80, 443 | Solo MISS y precargas |
| F5 / F32 | LAB / WIFI-EST → PORTAL01 | TCP 443 | Aviso de transparencia y huella de la CA |
| F28 | ENC01 → CTRL01 | TCP 443 | Consola desde el campus (TLS + segundo factor) |
| F29 → F30 | Internet → EC2-GW → CTRL01 | TCP 443 | Consola desde fuera del campus (mTLS de EC2-GW dentro de IPsec) |
| F10 | EDGE → CTRL01 | TCP 8443 | Configuración firmada hacia el nodo, KPI hacia la consola (mTLS) |
| F18 | CTRL01 → S3 `celeris-backups` | TCP 443 | Respaldo cifrado en origen |

La figura de contexto C4 (Sección 3) y DS-14 (casos de uso, Sección 4) muestran lo mismo en diagrama.

### 1.6.2 Funciones del producto

| Función | Lo que hace | Quién la usa | Requisitos |
| --- | --- | --- | --- |
| Caché compartida | Descarga una vez y sirve a las 40 PCs del laboratorio; coalesce las peticiones simultáneas y verifica cada objeto con SHA-256 | Usuario de laboratorio | REQ-F-01…F-09 |
| Descifrado autorizado | Descifra solo las fuentes aprobadas para descifrar, nunca BYOD ni `nunca` | Nodo, por política | REQ-F-02, F-36, RN-03, RN-09, RN-11 |
| Catálogo de contenido | El encargado decide qué se cachea; la DTI aprueba lo que requiere descifrado | Encargado, administrador DTI | REQ-F-20, F-31, RN-07 |
| Acceso por laboratorio | Habilitar un laboratorio y su horario | Encargado | REQ-F-10, F-32, RN-06 |
| Precarga | Descargar de noche lo que una clase necesita | Encargado, docente | REQ-F-22, F-34, F-35, RN-10 |
| Ahorro y actividad | GB evitados, BHR y minutos ahorrados; agregados de 30 s por laboratorio | Encargado, auditor | REQ-F-13, F-25, NF-13 |
| Transparencia | Aviso y huella de la CA antes de instalarla | Usuario, auditor | REQ-F-12, F-30, RN-05 |
| Gobierno | Inicio de sesión con segundo factor, RBAC, origen de sesión, auditoría | Todos los roles | REQ-F-24, F-33, F-37 |

### 1.6.3 Características de los usuarios

| Actor | Quién es | Cuántos | Rol RBAC | Desde dónde |
| --- | --- | --- | --- | --- |
| Encargado de laboratorio | Responsable de uno o más laboratorios; sin acceso a la red de gestión | 10, uno por laboratorio [S-36] | `encargado` (laboratorios asignados, REQ-RN-06) | ENC01 (F28) o EC2-GW (F29 → F30) |
| Administrador DTI | Técnico de infraestructura | Sin cifra [S-36] | `admin` | JMP01 o ENC01 para acciones críticas; EC2-GW solo para lectura y acciones no críticas |
| Docente | Solicita que un software esté disponible para su clase | Sin cifra (sección 1.13.1, H-03) | `docente`: solo crea y ve sus solicitudes | ENC01 o EC2-GW |
| Auditor | Docente evaluador u oficial de datos personales | Sin cifra [S-36] | `auditor` (solo lectura) | ENC01 o EC2-GW |
| Usuario de laboratorio | Estudiante o docente en una PC institucional | Hasta 400 simultáneos [S-36] | Sin cuenta | PC de LAB-01…LAB-10 |
| Usuario BYOD | Estudiante con equipo propio en el Wi-Fi | Sin cifra [S-36] | Sin cuenta | WIFI-EST [S-28] |

Los sistemas externos son cuatro:

- **EC2-GW**: proxy inverso, sin datos (D-24).
- **Origen**: servidores de contenido en Internet.
- **SIEM01**: Wazuh; recibe los eventos por F13.
- **FortiGate de la DTI.**

Ninguna cifra del diseño depende de los actores «sin cifra»: el dimensionamiento se basa en las 400 PCs y en los 10
encargados.

### 1.6.4 Restricciones generales

Se detallan en la sección 1.9.2 (RS-01…RS-06). Las que más condicionan el diseño son estas:

- La consola completa corre en el campus; en AWS solo están EC2-GW y S3 (RS-06, D-24, D-25).
- Hay que cumplir la Ley 29733 (RS-05).
- El ESXi gratuito admite hasta 8 vCPU por VM (RS-02).
- El equipo es de dos personas (RS-04).

### 1.6.5 Supuestos y dependencias

| Supuesto | De qué depende este SRS | Si no se cumple |
| --- | --- | --- |
| [S-02] Enlace de 300 Mbps | Límite de precarga de 50 Mbps (REQ-RN-10) y metas de ahorro | Se recalcula el límite con la DTI |
| [S-04] BHR alcanzable del 30 % | Meta de OB-1 | Se informa el BHR medido en el piloto |
| [S-14] Capa de acceso con 802.1Q y DHCP | Rangos /26 por laboratorio (REQ-F-10, F-32) | Sin rangos propios no hay control por laboratorio |
| [S-26] 10 laboratorios × 40 PCs | Capacidad (REQ-NF-02) y datos del prototipo | Se redimensiona |
| [S-28] Wi-Fi de estudiantes 172.16.0.0/16 | Red BYOD que el nodo trata como `nunca` (REQ-F-36) | La configuración firmada lleva el rango real |
| [S-29] El FortiGate excluye EDGE01/02 de la inspección SSL | REQ-F-02 y F8 | Los MISS fallan con el certificado de FortiGate |
| [S-32] Nombre del portal | Aviso y huella (REQ-F-12, F-30) | Se usa `portal.celeris.internal` hasta que la DTI entregue el FQDN |
| [S-33] Carga de EC2-GW | Acceso remoto (CU-11) | Pasar de t3.micro a t3.small |
| [S-34], [S-35] Caída de ESX01 | REQ-NF-03 | Contingencia manual de la DTI; RTO objetivo 30 min |
| [S-36] Personas usuarias | Cuentas de la consola (REQ-F-33) | Las cuentas de admin, auditor y docente se crean cuando la DTI las defina |

**Dependencias.** La DTI aplica la GPO del PAC y de la CA, la regla del FortiGate y la contingencia de [S-35]. CE03
entrega la red (`infra/*.yaml`): zonas, FW01, VPN y EC2-GW.

### 1.6.6 Distribución de requisitos por entrega

| Entrega | Qué cubre | Requisitos |
| --- | --- | --- |
| R1 (S1, prueba de concepto) | Nodo de caché con política en `config.toml` | REQ-F-01…F-07, F-09…F-12, F-15, F-26 |
| R2 (S2) | Consola, agente del nodo para F10, portal estático, BYOD por red de origen | REQ-F-08, F-13, F-14, F-17…F-20, F-22, F-24, F-25, F-28, F-30…F-37 |
| R3 (futuro) | Modo examen, varias sedes, *shield* | Fuera de este SRS (00 M2.4, M3.2) |
