# 2. Descripción de la organización y necesidades de red

## 2.1 Descripción general

La organización es la Universidad Peruana Unión (UPeU), Campus Juliaca. La Dirección de Tecnologías de la Información (DTI) es el área de la UPeU que opera la red: el FortiGate perimetral, la red Wi-Fi y la capa de acceso de los laboratorios. El servicio que se diseña da soporte a la actividad académica: las clases en laboratorio dependen de que los equipos tengan instalado y actualizado el software de cada curso antes de la sesión.

| Necesidad | Valor de diseño | Fuente |
| --- | --- | --- |
| Equipos institucionales en alcance | 400 PCs en 10 laboratorios de 40 | [S-01, S-26] |
| Usuarios (personas, no equipos) | Estudiantes y docentes en laboratorio: hasta 400 puestos simultáneos (una persona por PC). Encargados de laboratorio: 10 (uno por laboratorio). Administradores de la DTI, auditor y usuarios BYOD del Wi-Fi: sin cifra definida | [S-26, S-28, S-36] |
| Equipos personales | BYOD en el Wi-Fi de estudiantes (red de la DTI) | [S-28] |
| Sedes | Una (Juliaca); las sedes futuras tienen bloques reservados en el plan de direccionamiento | Sección 9 |
| Enlace a Internet | 300 Mbps simétricos; IP pública fija en el FortiGate | [S-02, S-15, S-29] |
| Descarga típica que se repite | ≈ 3 GB por PC en cada ciclo de actualización o instalación | [S-27] |
| Servicios que dependen de la red | Descargas de clase, actualizaciones, consola del encargado, portal de transparencia, SIEM | Sección 2.2 |
| Uso previsto de la nube | Acceso remoto al panel sin publicar el campus; copia de respaldo inmutable fuera del sitio | D-24, D-25 |
| Uso de infraestructura local | Un servidor ESXi en el rack del servicio con las VM del diseño | Sección 5.1 |
| Disponibilidad | La navegación de los laboratorios no debe depender de la caché (≥ 99,5 %, REQ-NF-03) | Sección 9 |
| Crecimiento | Hasta 16 laboratorios de /26 dentro del mismo /22 y paso a /21 sin renumerar | Sección 9 |

El dato que justifica el diseño es la repetición: un laboratorio de {{dato:n_pcs_lab}} PCs que descarga 3 GB por equipo mueve unos 120 GB por el enlace cuando bastaría con traerlos una vez [S-27]. Por eso la pieza central es un nodo de caché HTTP [8] dentro de la LAN y no un aumento del ancho de banda.

## 2.2 Servicios y procesos críticos dependientes de la red

La criticidad se asigna según el efecto de una caída sobre la clase o sobre la seguridad del servicio. Los procesos P1 y P2 son los definidos en el análisis de procesos del proyecto (CE01).

| Proceso | Servicio TI | Criticidad | Qué pasa si la red falla |
| --- | --- | --- | --- |
| Clases en laboratorio | Descargas por la caché (F1), DNS (F2) y PAC (F3) | Alta | Las PCs pasan a `DIRECT` (piloto): siguen navegando, sin ahorro (T09) |
| P1 Actualización masiva | Nodos de caché y precarga nocturna | Alta | Cada PC vuelve a descargar por su cuenta y satura el enlace |
| P2 Preparación de laboratorio | Consola del encargado (F28) y precarga | Alta | El nodo sigue con la última configuración válida; no se pueden hacer cambios |
| Consentimiento informado | Portal de transparencia (F5, F21, F32) | Alta (previo al uso) | No se pueden enrolar PCs nuevas; las enroladas siguen funcionando |
| Administración fuera del campus | EC2-GW y VPN (F29, F30) | Media | El encargado usa ENC01 dentro del campus |
| Monitoreo de seguridad | Wazuh, Suricata, WAF y señuelos (F13, F14) | Media | Se pierden alertas; los servicios siguen funcionando |
| Respaldo | Copia local y S3 (F18) | Media | Se pierde la copia externa; queda la local |

## 2.3 Partes interesadas relevantes a la red

| Parte interesada | Rol frente a la red | Qué espera de la conectividad y la seguridad |
| --- | --- | --- |
| Encargados de laboratorio | Administradores del servicio | Decidir qué se guarda en la caché y qué laboratorio tiene acceso, también desde fuera del campus, sin recibir acceso a la red de gestión |
| Estudiantes y docentes (PC institucional) | Usuarios | Descargas rápidas y disponibles; saber qué se inspecciona antes de usar el proxy |
| Estudiantes con equipo propio (BYOD) | Usuarios | Que su tráfico no se descifre y que el Wi-Fi siga funcionando como hoy |
| Técnicos de la DTI | Administradores de red | Segmentación clara, cambios mínimos en el FortiGate, administración solo desde JMP01 con MFA, reglas versionadas |
| Dirección del campus | Dirección | Liberar el enlace sin pagar más ancho de banda; riesgo controlado y medible |
| ISP local | Proveedor | Enlace e IP pública fija estables [S-15] |
| AWS | Proveedor de nube | Extremo VPN, EC2 y S3 operados con mínimo privilegio y costo acotado (≈ US$ 70 al mes) |
| Oficial de datos personales y Autoridad Nacional de Protección de Datos Personales | Organismo regulador | Cumplimiento de la Ley 29733 [9]: sin datos personales hacia orígenes ni hacia la nube (AM-07, T26) |
