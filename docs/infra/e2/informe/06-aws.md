# 6. Arquitectura AWS — diseño

## 6.1 Selección de región y justificación

La región es una variable de OpenTofu (`var.region`). El laboratorio y el costo de referencia usan **us-east-1**; **sa-east-1** (São Paulo) es la candidata de producción y se confirma midiendo la latencia desde Juliaca con `mtr` hacia ambas [S-11]. El documento CE03 D2.5 declaraba us-east-1 también para producción y el inventario la deja como candidata a confirmar; manda el inventario (CI-81).

{{tabla:region}}

Los tres criterios del enunciado se resuelven así. **Latencia:** no se ha medido; us-east-1 suele tener menor latencia desde Perú, pero por eso la prueba queda como pendiente de S2. El tráfico que depende de la latencia es solo el panel remoto, de pocos usuarios. **Cumplimiento:** a AWS no llegan datos personales. Por EC2-GW pasan sesiones cifradas que no se almacenan y a S3 llegan respaldos cifrados en origen por restic, sin la llave; por eso la residencia de datos de la Ley 29733 no obliga a una región de Sudamérica. **Disponibilidad de servicios:** las tres piezas usadas (VPC con VGW, EC2 y S3 con Object Lock) existen en ambas regiones, y us-east-1 es la región disponible en AWS Academy [S-13].

## 6.2 Diseño de VPC

La VPC es 10.30.0.0/16. No se solapa con el campus (10.20.0.0/16) ni con sus reservas, requisito para que BGP intercambie ambas redes sin traducción.

{{tabla:subredes}}

Se usa una sola zona de disponibilidad (a). La alta disponibilidad entre zonas se descartó con D-28: EC2-GW no guarda datos y se recrea con OpenTofu en 15 min, de modo que una segunda instancia costaría más de lo que protege. Las rutas de cada subred son las siguientes:

{{tabla:rutas_aws}}

**Internet Gateway (IGW01).** Solo pub-a tiene ruta 0.0.0.0/0 hacia el IGW. Por ahí entra el TCP 443 de los usuarios del panel (F29) y sale el tráfico de ACME y de actualizaciones de EC2-GW. app-a no tiene ruta a Internet.

**VGW.** Es el extremo AWS de la VPN de CE0311 (sección 7). Propaga a las dos tablas la ruta 10.20.0.0/16 aprendida por BGP.

**Gateway Endpoint de S3 (VPCE-S3).** La subred privada llega a S3 por este endpoint, que no tiene costo por hora. Sirve a EC2-DR durante el simulacro, que restaura la consola desde S3.

**Por qué no hay NAT permanente.** app-a está vacía en operación normal y EC2-GW está en una subred pública con su propia IP: nada del diseño necesita salir a Internet desde una subred privada, y el acceso a S3 va por el endpoint. Un NAT Gateway administrado costaría US$ {{dato:nat_gw_mes}} al mes, el {{dato:nat_gw_pct}} del presupuesto total de AWS, para no usarse. NAT-DR existe solo durante el simulacro T59 (etiqueta Ttl) para que EC2-DR instale paquetes y demuestre NAT; rt-private apunta a ella únicamente entonces, y el simulacro de {{dato:costo_sim}} US$ en total no pesa en el costo mensual.

{{tabla:nat}}

{{figura:DC-3|Qué observar: la VPC 10.30.0.0/16 con pub-a (EC2-GW) y app-a (vacía); IGW01 solo en pub-a; VGW en el borde de la VPC; S3 fuera de la VPC, con Object Lock; EC2-DR y NAT-DR punteados porque solo existen durante el simulacro T59; las tablas de rutas, SG y NACL de cada subred.}}

## 6.3 Servicios EC2 planeados

EC2-GW es la única instancia permanente. EC2-DR y NAT-DR son temporales y se crean solo durante el simulacro.

{{tabla:instancias_ec2}}

**Por qué un t3.micro para EC2-GW.** El tipo se elige frente a la carga: EC2-GW solo termina TLS, aplica el WAF (Coraza con OWASP CRS) y reenvía a CTRL01:443; no guarda datos ni llaves. Un t3.micro tiene 2 vCPU, 1 GiB y una línea base de CPU de 10 % por vCPU, es decir {{dato:gw_base}} vCPU sostenidos, y gana {{dato:gw_cred_g}} créditos de CPU por hora. Con la carga de diseño de la tabla siguiente el margen es de {{dato:gw_margen_cpu}} en CPU y {{dato:gw_margen_ram}} en RAM, y el saldo de créditos crece. Un t3.small duplicaría la RAM y el precio sin que la carga lo pida; se sube de tipo si el piloto mide los créditos agotándose.

{{tabla:gw}}

> La carga de diseño es el supuesto S-33, derivado de S-26 (una sesión por laboratorio): 10 sesiones, 5 solicitudes por segundo, 0,10 vCPU y 512 MiB. D2.8 solo decía «pocos usuarios» (CI-82, resuelto con S-33). Se mide con el piloto en S2 y, si la media supera la línea base del t3.micro, se pasa a t3.small.

**Costo mensual 24×7.** Con precios de lista de noviembre de 2026 en us-east-1 [S-12], la AWS del diseño cuesta ≈ US$ {{dato:costo_total}} al mes (meta de D2.3: ≤ US$ {{dato:costo_meta}}). La mayor parte es la VPN (US$ 36,50) y las tres IPv4 públicas, entre ellas las dos de los túneles, que AWS cobra por hora. El laboratorio efímero (Modo A) cuesta US$ {{dato:costo_lab_h}} por hora, bajo la meta de US$ 0,10. Los precios se confirman en AWS Pricing Calculator.

{{tabla:costo}}

## 6.4 Security Groups y NACL planeados

Hay dos Security Groups y dos NACL, uno de cada por subred. Los Security Groups filtran con estado por instancia; las NACL filtran sin estado por subred y son la segunda capa.

{{tabla:sg_nacl}}

**Administración, IAM y gobierno.** Sin bastion: SSM Session Manager o EC2 Instance Connect, sin puerto 22 público (la NACL de pub-a también lo deniega). El perfil de instancia de EC2-GW no tiene permisos sobre S3. Los respaldos usan una credencial aparte con solo `s3:PutObject` en el bucket y condición de IP de origen igual a la IP pública del campus [S-30]; en AWS Academy se usa el perfil que provee el laboratorio [S-13]. La cuenta lleva MFA, CloudTrail y AWS Budgets al 80 %, y los recursos efímeros llevan la etiqueta `Ttl`. CloudWatch registra las métricas básicas de EC2-GW y el estado de los túneles. El bucket celeris-backups tiene versionado y Object Lock de 30 días en modo compliance, y solo acepta la IP pública del campus. No se guarda ninguna clave ni secreto en este repositorio.
