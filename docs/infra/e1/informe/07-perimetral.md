# 7. Diseño de seguridad perimetral

## 7.1 Firewall

**Producto.** FW01 es OPNsense en una VM de ESX01 (4 vCPU, 8 GB). Se elige porque integra en un solo equipo lo que el diseño necesita en el perímetro del proyecto: filtrado con estado, IPsec con VTI y BGP (FRR), Suricata en modo IPS, CrowdSec, Unbound con DNSSEC, NTP y DHCP. Además exporta su configuración completa como XML, que se versiona en Git y permite restaurarlo en una hora (sección 9). Detrás de FW01, el FortiGate de la DTI sigue siendo el perímetro del campus.

**Interfaces previstas.**

{{tabla:fw_interfaces}}

La WAN usa una NIC física dedicada (vSwitch1, vmnic2) y no comparte enlace con el trunk interno. En la WAN se bloquean las redes *bogon* y las privadas entrantes, con tres excepciones: la red de tránsito, la red del Wi-Fi solo hacia F31 y F32, y 10.30.0.0/16 solo por las VTI.

**Política por defecto.** Se deniega y registra todo el tráfico entrante, saliente y entre zonas (OD-06). Solo pasa lo que una regla permite de forma explícita, y cada regla corresponde a un flujo de la sección 5.5.

**Criterio de las reglas.**
1. Una regla corresponde a un flujo F-nn, y el ID figura en la descripción de la regla. La columna «Regla en FW01» de la tabla de flujos es el texto de esa descripción.
2. Mínimo privilegio por zona, host (alias) y puerto, sin «any» entre zonas internas.
3. Filtrado de salida por zona: ninguna zona sale a Internet salvo los flujos F6 (piloto), F8, F18, F25, F26 y F27.
4. La interfaz de administración de FW01 solo es alcanzable desde JMP01, con MFA (F20).
5. Las reglas se exportan a Git y las revisa el otro integrante antes de aplicarse.
6. Las reglas de prueba de KALI01 quedan deshabilitadas por defecto y solo se activan en una ventana autorizada.
7. Cada mes se revisan las reglas sin uso.
8. Los alias de los rangos de laboratorio quedan preparados para un futuro modo examen.

## 7.2 DMZ

La DMZ se divide en dos VLAN porque sus equipos tienen propósitos opuestos (D-16). DMZ-SVC (VLAN 40) aloja un servicio que debe protegerse; DMZ-HONEY (VLAN 41) aloja un señuelo hecho para ser atacado. Si compartieran VLAN, un honeypot comprometido quedaría en la misma red de capa 2 que el portal.

**DMZ-SVC: PORTAL01 (10.20.40.10).** Es el portal de transparencia: explica qué se descifra y publica la huella de la CA del proyecto para que el usuario la compare **antes** de usar el proxy (D-15). Debe estar en una DMZ porque se publica a Internet (F21, por el NAT 1:1 del FortiGate) y también lo consultan LAB (F5) y el Wi-Fi (F32), es decir, zonas de menor confianza que los servidores.

| Capa | Control | Por qué |
| --- | --- | --- |
| Perímetro | NAT 1:1 del FortiGate solo para TCP 80/443; Suricata IPS en FW01; CrowdSec | Superficie mínima expuesta |
| WAF | Caddy + Coraza con OWASP CRS; límite de peticiones por IP | Bloquea inyecciones y escáneres web (T17, T18) |
| TLS | Certificado público (ACME), TLS 1.3 con 1.2 de respaldo, HSTS | El visitante aún no tiene instalada la CA del proyecto (T16) |
| Contenido | Sitio estático firmado que genera la consola; sin base de datos ni login; sistema de archivos de solo lectura | Lo que no existe no se puede explotar |
| Salida | Ninguna hacia la WAN; solo el agente Wazuh hacia SIEM01 (F13) | No sirve de trampolín (T19) |

**Por qué PORTAL01 no sale a Internet (D-29).** Un servidor publicado que puede iniciar conexiones hacia Internet sirve, si se compromete, para descargar herramientas o exfiltrar datos. PORTAL01 solo necesitaría salir para renovar su certificado público por ACME. El diseño traslada esa tarea a FW01: FW01 renueva el certificado y se lo entrega a PORTAL01 por SFTP en TCP 22 (F33), con una llave dedicada y un usuario confinado (*chroot*) en la carpeta del certificado. Así PORTAL01 no tiene ninguna regla de salida a la WAN. T19 verifica que no establece conexiones hacia Internet y T49, que la entrega por F33 funciona. Este diseño depende de que el FortiGate permita a FW01 llegar a la CA por TCP 443 y 80 [S-31].

**Qué alcanza y qué no la DMZ.** Desde DMZ-SVC solo sale F13 hacia SIEM01. No alcanza LAB, SERVERS (ni siquiera CTRL01:5432, T46), MGMT ni AWS (T03, T10). Desde DMZ-HONEY solo sale F13; cualquier otro destino se deniega (T20, T47).

**DMZ-HONEY: HNY01 (10.20.41.20).** Su función y lo que detecta se describen en la sección 8. Publicar sus puertos a Internet (F24) requiere autorización escrita de la DTI y una ventana definida, porque atrae tráfico hostil al mismo enlace que el proyecto quiere descongestionar.

## 7.3 Segmentación planeada

La segmentación se valida en el Semestre 2 con las pruebas indicadas. La tabla muestra cada par de zonas con tráfico permitido y los pares denegados que protegen activos críticos. El resto de los pares está denegado por defecto y figura en la matriz completa del anexo A.

{{tabla:segmentacion}}

**Tráfico que el firewall no ve.** El tráfico entre PCs de una misma VLAN se conmuta en capa 2 y no cruza FW01. Lo compensan tres medidas. El canary HNY02 detecta barridos dentro de LAB (T30). La capa de acceso debe aplicar controles de capa 2: DHCP snooping, DAI, IP source guard, RA guard, port-security, BPDU guard y VLAN nativa 999; si un switch no los soporta, se registra como brecha [S-14]. Y cada servidor tiene su propio firewall de host (nftables).

**Acceso por laboratorio en dos capas.** FW01 permite F1 desde toda la VLAN 30 y el nodo acepta solo los rangos /26 habilitados. Un laboratorio deshabilitado recibe 403 en el nodo (T52); en modo gestionado tampoco tiene `DIRECT`.

**Por qué el Wi-Fi de estudiantes no se descifra (D-27).** Descifrar exige instalar la CA del proyecto en el equipo y contar con el consentimiento informado de su dueño. En equipos personales la universidad no puede garantizar ninguna de las dos cosas. Por eso la red WIFI-EST está en la lista de redes que el nodo nunca intercepta, regla que no depende de la configuración que llegue de la consola (REQ-F-36, REQ-RN-11). Un cliente del Wi-Fi que pida un dominio aprobado recibe el certificado del origen y no el del proyecto (T56). El Wi-Fi solo alcanza EDGE (F31) y el portal (F32); hacia CTRL01, MGMT o LAB se deniega y se registra (T57). El ahorro que se obtiene de BYOD es pequeño, porque casi todo su tráfico es HTTPS y no se descifra. El beneficio de integrarlo es otro: mantener el Wi-Fi lejos de los servidores y los laboratorios.
