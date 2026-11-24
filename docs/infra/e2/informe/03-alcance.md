# 3. Alcance del diseño de centro de datos híbrido

## 3.1 Declaración de alcance

El diseño comprende la infraestructura virtualizada VMware ESXi del centro de datos del campus (un host, su almacenamiento local, sus vSwitch, port groups y las {{dato:n_vm}} VM del servicio) y los recursos que se desplegarán en AWS (VPC, dos subredes, EC2-GW, S3, tablas de rutas, Security Groups y NACL), con su dimensionamiento, su costo y sus mecanismos de respaldo y recuperación. Es solo diseño: no se instala ESXi, no se crea ningún recurso en AWS y no se ejecuta OpenTofu.

## 3.2 Límites

- **Físicos:** un rack de 12U con el servidor ESX01, el switch núcleo SW-CORE01, la UPS01 con su PDU y el cableado hacia la capa de acceso y el FortiGate. Las PCs de los laboratorios quedan fuera del rack.
- **Tecnológicos:** ESXi, vSwitch0 y vSwitch1, port groups, datastores, VM, y en AWS la VPC, subredes, EC2, S3, tablas de rutas, Security Groups y NACL. La VPN que une ambos entornos es la de CE0311.
- **Organizacionales:** cada componente tiene un responsable, como muestra la tabla siguiente.

| Componente | Quién lo administra | Cómo |
| --- | --- | --- |
| FGT-EXT, SW-ACC y WIFI-EST | DTI | Existentes; se documentan tal como están [S-14, S-29] |
| ESX01, SW-CORE01, UPS01, IPMI01 | Equipo del proyecto con la DTI | Solo desde JMP01 (con MFA) o desde el puerto break-glass BRK01 |
| VM del servicio (FW01, EDGE01/02, CTRL01, SIEM01, PORTAL01, HNY01/02, JMP01, LABCLI01, KALI01) | Equipo del proyecto | SSH con llave desde JMP01; la GUI de FW01 solo desde JMP01 |
| Consola (CTRL01) | Encargado de laboratorio como usuario; equipo del proyecto como operador | Desde ENC01 en el campus o por EC2-GW fuera de él |
| Cuenta AWS, VPC, EC2-GW y S3 | Equipo del proyecto | Cuenta con MFA, CloudTrail y AWS Budgets [S-13]; sin puerto 22 público |

## 3.3 Exclusiones

| Exclusión | Por qué se excluye |
| --- | --- |
| PCs de usuario (PCS-LAB) y equipamiento de usuario final | Son los usuarios del servicio y ya existen; el diseño los trata como clientes |
| Alta disponibilidad entre hosts (H3) | Un segundo host y CARP superan el presupuesto de S1; se declara como hoja de ruta y como riesgo en la sección 10 |
| FortiGate FGT-EXT, Wi-Fi y capa de acceso | Los opera la DTI; reemplazarlos sería sobreingeniería. Se piden cambios mínimos [S-14, S-29] |
| Caché en AWS (D-19) | Un MISS servido desde AWS igual cruza el enlace del campus: no ahorra lo que el proyecto busca |
| Kubernetes u otros servicios en AWS | Solo se reserva el bloque 10.30.128.0/17 para crecimiento |
