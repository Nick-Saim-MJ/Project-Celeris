# Anexo F. Por qué la consola no está en la nube (D-24, D-25)

**La decisión.** La consola completa del encargado (interfaz web, API y base de datos PostgreSQL) vive en el campus, en CTRL01 (10.20.20.10, VLAN 20). En AWS solo hay dos piezas: EC2-GW, un proxy inverso sin datos que da entrada al panel desde fuera del campus, y el bucket S3 de respaldos con Object Lock.

**Por qué el backend queda en el campus (D-25).**
- **El nodo depende de la consola.** El nodo consulta su configuración firmada de forma periódica por F10. Con la consola en AWS, una caída del enlace o de la VPN dejaría al nodo sin recibir cambios justo cuando el enlace está mal, que es cuando más se necesita la caché.
- **La llave que firma debe estar donde hay control físico.** La llave ed25519 decide qué aplica cada nodo. Llevarla a la nube agregaría superficies de ataque (cuenta de AWS, IAM, una instancia pública) sin ganar protección.
- **Datos personales.** La base guarda el uso por laboratorio y registros con IP de equipos del campus. En el campus no hay flujo transfronterizo de datos (Ley 29733 [9]).
- **Costo y latencia.** Una base y una API 24×7 en AWS cuestan más que una VM adicional en el host que ya existe. Además, el encargado en ENC01 llega a CTRL01 sin salir a Internet (F28).

**Por qué el frontend tampoco va a la nube.** La interfaz son archivos estáticos sin secretos: lo sensible es la API. Separarla en S3 obligaría a abrir CORS, manejar dos dominios y publicar la API de todos modos. Servida desde el mismo origen que la API, las cookies quedan en un solo sitio y la política CSP puede ser `default-src 'self'`.

**Por qué el acceso remoto entra por AWS (D-24).** Publicar la consola en el campus, con un NAT del FortiGate hacia CTRL01, expondría a Internet el servidor que firma la configuración. Además, cada escaneo o ataque consumiría el mismo enlace que el proyecto quiere liberar. Con EC2-GW, el tráfico hostil se queda en AWS. Al campus solo llega lo que pasó el WAF y el segundo factor, y llega por la VPN (F30) con un certificado de cliente que CTRL01 verifica. EC2-GW no guarda datos ni llaves: si se compromete, se destruye y se recrea con OpenTofu en 15 minutos, y su Security Group y FW01 le impiden alcanzar algo distinto de CTRL01:443 y SIEM01 (AM-18, T58). Las acciones críticas se rechazan si llegan por EC2-GW (REQ-F-37, T54).

| Alternativa evaluada | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| EC2-GW en AWS + VPN | El campus no publica nada para el panel; el ataque consume AWS y no el enlace; la VPN tiene un uso real | Si la VPN cae, el panel remoto no funciona (el local sí) | Elegida |
| NAT del FortiGate hacia CTRL01 | Más simple, sin AWS | Expone el servidor que firma y consume el enlace del campus | Descartada |
| VPN de acceso remoto (WireGuard en OPNsense) | Nada público | Requiere un cliente en cada equipo del encargado; no deja una URL simple | Alternativa si la DTI no aprueba EC2-GW |
| Túnel de un tercero (Cloudflare Tunnel, Tailscale) | Muy rápido de montar | Dependencia de un proveedor externo; la rúbrica pide una VPN propia | Descartada |
| Sin acceso remoto (solo ENC01) | Lo más seguro | El encargado no puede actuar fuera del campus | Es el modo degradado si la VPN cae |

**Qué se pierde y qué no.** Si la VPN o EC2-GW fallan, solo se pierde el acceso remoto: la consola local, los nodos y las descargas siguen funcionando. La continuidad de la consola no depende de AWS para operar, solo para guardar la copia externa (F18).
