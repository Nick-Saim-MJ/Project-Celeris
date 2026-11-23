# Evidencias de la demo de OpenTofu — AWS emulado: plano de control, sin tráfico

- **Qué es:** lo que `tofu apply` creó en el AWS Emulator local (`https://127.0.0.1:9297`), leído con `aws ec2 describe-*`, `aws s3api get-*` y `aws iam get-*`.
- **Qué no es:** una cuenta de AWS. El emulador no abre túneles, no ejecuta instancias, no mueve tráfico y no evalúa IAM ni políticas de bucket.
- **Diferencia con AWS real (CI-55):** el emulador no implementa la propagación de rutas del VGW; la ruta a 10.20.0.0/16 es estática (`var.emulador = true`).
- **Sin secretos:** las llaves de la VPN y las credenciales aparecen como `[REDACTADO]`.
- **`verificaciones.json`:** 17 comprobaciones contra `infra/inventory.yaml` (VPC, subredes, rutas, VGW, customer gateway, VPN, sg-gw, NACL, EC2-GW, bucket, versionado, Object Lock, política, usuario y etiquetas).
- **Reproducir:** `deploy/opentofu/emulador/demo.sh todo`.
