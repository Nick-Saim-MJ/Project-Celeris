# 2. Descripción de la organización y necesidades de infraestructura

La organización es una universidad; el escenario es el Campus Juliaca y su Dirección de Tecnologías de la Información (DTI), que opera el FortiGate perimetral, el Wi-Fi y la capa de acceso de los laboratorios. La actividad principal es académica: las clases en laboratorio dependen de que cada PC tenga el software del curso instalado y actualizado antes de la sesión. El servicio Celeris Edge evita que esas descargas repetidas saturen el enlace del campus.

**Servicios que necesitan cómputo, almacenamiento o base de datos**


| Servicio | Componente | Qué necesita | Dónde se aloja |
| --- | --- | --- | --- |
| Caché de descargas y PAC | EDGE01, EDGE02 | 4 vCPU y 8 GB por nodo; 500 GB de caché en NVMe propio; ≈ 1 Gbps hacia un laboratorio (REQ-NF-02) | Campus (ESX01) |
| Consola del encargado | CTRL01 | SPA, API y PostgreSQL; 2 vCPU, 8 GB, 100 GB; la base es el dato crítico | Campus (ESX01) |
| Firewall, VPN, IPS, DNS y NTP | FW01 | 4 vCPU y 8 GB; es el punto de paso de todo el tráfico entre zonas (D-17) | Campus (ESX01) |
| Correlación de eventos | SIEM01 | 4 vCPU, 16 GB y 300 GB para ≈ 90 días de eventos | Campus (ESX01) |
| Portal de transparencia, señuelos, jump host y pruebas | PORTAL01, HNY01, HNY02, JMP01, LABCLI01, KALI01 | VM pequeñas de 1 a 2 vCPU | Campus (ESX01) |
| Entrada pública al panel | EC2-GW | Termina TLS y reenvía; sin datos | AWS (EC2) |
| Respaldo fuera del sitio e inmutable | S3 celeris-backups | ≈ 300 GB con Object Lock de 30 días | AWS (S3) |

**Criterio de reparto entre el campus y la nube (D-25)**


| Va en… | Criterio | Qué queda ahí |
| --- | --- | --- |
| Campus | Debe estar en la LAN para ahorrar enlace | Nodos de caché EDGE01 y EDGE02 |
| Campus | El nodo lo necesita para funcionar sin Internet | Consola y base (CTRL01): el nodo consulta su configuración firmada cada 30 s |
| Campus | Maneja datos de uso o llaves | Consola (llave de firma ed25519) y SIEM01 (alertas con IP del campus) |
| AWS | No tiene datos | EC2-GW: si se compromete, se destruye y se recrea con OpenTofu |
| AWS | Ya va cifrado en origen | Respaldos en S3: restic cifra y la llave no está en AWS |
| Ninguno | Un MISS servido desde AWS igual cruza el enlace del campus | Caché en AWS (D-19): no existe |

La consola no va en la nube por cuatro razones: el nodo dejaría de recibir cambios justo cuando el enlace está mal; la llave que firma debe estar donde está el control físico; la base guarda uso por laboratorio y la Ley 29733 exige cuidar el flujo de datos personales; y una VM más en el host existente cuesta menos que base y API en AWS 24×7. La SPA tampoco va en S3: es estática y sin secretos, y separarla obligaría a abrir CORS y a publicar la API de todos modos.

**Crecimiento e importancia de la información**


El crecimiento previsto a mediano plazo es de dos tipos: el segundo nodo de caché (EDGE02, fase F2) y hasta 16 laboratorios de /26 dentro del mismo /22 sin renumerar. El dimensionamiento de la sección 9 reserva un 20 % de RAM para ese crecimiento. La importancia de la información de cada entorno es distinta:

| Entorno | Información | Importancia | Por qué |
| --- | --- | --- | --- |
| Campus | Base de la consola, llave de firma, configuración de FW01, eventos del SIEM | Alta | Define qué aplica cada nodo y contiene IP de equipos del campus |
| Campus | Contenido en caché | Media | Se reconstruye solo desde Internet (CT-02) |
| AWS | Sesiones cifradas por EC2-GW | Media | Pasan sin almacenarse |
| AWS | Respaldos en S3 | Alta | Es la única copia que sobrevive a la pérdida del sitio; llegan cifrados y sin la llave |
