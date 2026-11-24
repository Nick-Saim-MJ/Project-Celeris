# Anexo C. Validación emulada del plano de control de AWS

> **AWS emulado: plano de control, sin tráfico.** Esta validación no es una implementación. Es la demostración del AWS Emulator local (fecha {{dato:fecha_e}}, credenciales ficticias, sin cuenta real) que comprueba que la VPC, las subredes, las tablas de rutas, el VGW, la conexión VPN, los Security Groups y las NACL del diseño pueden crearse con OpenTofu tal como están descritos. No mide rendimiento ni demuestra tráfico.

Resultado: {{dato:n_verif_e}} de las comprobaciones pasan, todas emuladas. Las evidencias están en `evidencias/` (carpeta `*-E`). El emulador tiene diferencias conocidas con AWS real, por ejemplo no propaga rutas por BGP: la ruta 10.20.0.0/16 hacia el VGW se verifica como estática (CI-55 del Entregable 1). Nada de esto sustituye al despliegue real de S2.

{{tabla:emulada}}
