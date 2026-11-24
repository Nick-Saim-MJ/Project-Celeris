# 11. Conclusiones y hoja de ruta hacia la implementación

**Resumen del diseño.** Un host ESXi gratuito de 12 núcleos y 96 GB aloja las {{dato:n_vm}} VM del servicio con {{dato:h_cpu}} de holgura de CPU, {{dato:h_ram}} de RAM (después de la sobrecarga de ESXi) y {{dato:h_disco}} de disco; dos vSwitch separan el trunk de las siete zonas de la red de tránsito del FortiGate. En AWS, una VPC 10.30.0.0/16 con EC2-GW (t3.micro) y S3 con Object Lock completan el diseño por unos US$ {{dato:costo_total}} al mes, sin NAT permanente. La integración con el Entregable 1 es la misma VPN, y los RTO y RPO cubren los {{dato:n_servicios}} servicios, incluida la caída del host: los laboratorios pasan a `DIRECT` y la consola se restaura desde S3 en 2 h una vez repuesto el servidor (plazo S-34, por confirmar).

**Qué queda pendiente y se hace en CE0332 y CE0333 (Semestre 2).**

- Instalar ESXi y desplegar las VM de la fase F1; crear los vSwitch y port groups tal como están en la Figura 5.2.
- Crear la VPC, EC2-GW y la VPN con OpenTofu, ya probada en el entorno efímero, y medir que se recrean en ≤ 15 min.
- Coordinar con la DTI el NAT 1:1 del FortiGate y la ruta hacia 10.20.0.0/16.
- Desplegar EDGE02 (F2) y su datastore NVMe.
- Ejecutar el simulacro de recuperación (T59) y medir el RTO real; medir con iperf3 el rendimiento LAB → EDGE con y sin IPS.
- Medir la carga real de EC2-GW y la latencia a us-east-1 y sa-east-1.

**Qué es emulado.** El AWS Emulator validó el plano de control del diseño de AWS (anexo C) y el Modo L emuló la red; ninguno prueba tráfico real ni rendimiento. Nada de lo emulado se presenta como implementado.

**Contradicciones y vacíos abiertos.** Los CI del Entregable 2 son:

{{tabla:ci}}

Los dos abiertos son CI-87 (el trunk de 1 GbE hacia SW-ACC no deja holgura frente a ≈ 1 Gbps por laboratorio) y CI-88 (`DIRECT` con ESX01 caído depende de FW01, que corre en ESX01). Además, el supuesto S-34 (plazo de reposición del servidor) espera valor de la DTI, y la latencia a AWS [S-11] y la carga de EC2-GW [S-33] se miden en S2. Ninguno cambia una IP, un puerto ni una regla.
