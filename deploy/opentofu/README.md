# IaC de la demo de AWS (OpenTofu): solo contra el AWS Emulator

> **AWS emulado: plano de control, sin tráfico.** Esta demo crea la VPC, la VPN, EC2-GW y el bucket de respaldos de D2.5 (v0.4) en el
> [AWS Emulator](https://github.com/aws/aws-emulator) local. Comprueba que el código OpenTofu y el diseño son coherentes y que las APIs
> aceptan lo que se pide. **No** crea túneles ni instancias en ejecución, no mueve tráfico y no evalúa IAM ni políticas de bucket.
> Nada va contra una cuenta real: el proveedor usa credenciales ficticias y `var.emulador = true` es el valor por defecto.

Todo valor de diseño sale de `infra/inventory.yaml` (`python infra/genera.py tofu`); los módulos no llevan IP, ASN ni puertos escritos a mano
(lo comprueba `tests/gen/test_tofu.py`).

## Qué crea

| Módulo | Recursos |
|---|---|
| `modules/aws-vpc` | VPC 10.30.0.0/16, subredes pub-a y app-a, IGW, tablas de rutas, endpoint S3 de tipo gateway, `sg-gw` y las NACL (D2.5) |
| `modules/aws-vpn` | Virtual Private Gateway (ASN 64512), customer gateway (203.0.113.10, la IP del FortiGate), conexión VPN con BGP y las opciones de D1.10; rutas hacia el campus |
| `modules/aws-gw` | EC2-GW (10.30.0.10, pub-a, IMDSv2, disco gp3 cifrado), IP elástica y rol solo con Session Manager |
| `modules/aws-backup` | Bucket `celeris-backups` con versionado, Object Lock de 30 días (compliance), bloqueo de acceso público, usuario de solo escritura y política con condición de IP |

Fuera de la demo: EC2-DR y NAT-DR (temporales del simulacro T59), AWS Budgets y el runbook de una cuenta real. `modules/onprem-sim` (campus simulado
del Modo A real) no se usa aquí.

## Diferencias con AWS real (CI-55)

| Tema | AWS real | AWS Emulator (`var.emulador = true`) |
|---|---|---|
| Rutas hacia el campus (10.20.0.0/16) | El VGW las propaga por BGP | **Ruta estática** hacia el VGW en `rt-public` y `rt-private`: el emulador no implementa `EnableVgwRoutePropagation`. No sigue al BGP |
| Opciones de túnel | `ModifyVpnTunnelOptions` | No implementado; el recurso ignora la integridad de fase 2 y el rekey (D1.10 usa AES-GCM) |
| AMI de EC2-GW | Debian 13 por parámetro de SSM | Amazon Linux 2023 que el emulador registra; no ejecuta la instancia |
| IAM y política del bucket | Se evalúan | Se crean, pero no se hacen cumplir |

## Uso

Requisitos: Docker, `tofu` y el AWS CLI. El script hace todo contra el emulador local y deja el estado de OpenTofu **fuera del repositorio**
(`~/.aws-emulator-lab/demo.tfstate`: contiene las llaves de la VPN).

```bash
deploy/opentofu/emulador/demo.sh todo        # levanta el emulador, aplica y genera las evidencias
deploy/opentofu/emulador/demo.sh levantar    # construye la imagen aws-emulator (el Dockerfile baja el RPM de downloads.aws.com) y arranca el emulador limpio
deploy/opentofu/emulador/demo.sh aplicar     # tofu init + apply
deploy/opentofu/emulador/demo.sh evidencias  # aws ec2/s3 describe → evidencias/<fecha>-E/ y comparación con el inventario
deploy/opentofu/emulador/demo.sh destruir    # tofu destroy
deploy/opentofu/emulador/demo.sh bajar       # detiene el emulador (su estado solo vive en memoria)
```

`make tofu-check` solo valida el formato y la sintaxis; no planifica ni aplica nada. Las evidencias (`evidencias/<fecha>-E/`) no llevan secretos:
`evidencias.py` redacta las llaves de la VPN y las credenciales.

### Variables del entorno

| Variable | Predeterminado | Para qué |
|---|---|---|
| `emulador` | `true` | Apunta al emulador; `false` usaría AWS real con las credenciales del entorno (**sin probar**) |
| `endpoint_emulador` | `https://127.0.0.1:9297` | URL del emulador |
| `ca_emulador` | `null` | `ca.pem` que el emulador genera en cada arranque |
| `region` | `us-east-1` | Región del laboratorio (la candidata de producción, `sa-east-1`, está en el inventario) |
| `ttl` | el del inventario (`4h`) | Etiqueta `Ttl` |
| `modo_laboratorio` | `true` | Tipos de instancia de laboratorio |
| `perfil_de_instancia_existente` | `null` | Perfil ya creado (AWS Academy) |
| `ami_id` | `null` | AMI de EC2-GW |
| `crear_credencial_respaldo` | `true` | Usuario IAM de solo escritura [S-30]; en AWS Academy puede no estar disponible |

Todos los recursos llevan las etiquetas `Proyecto` y `Ttl`; con el emulador, también `Modo`.

## Seguridad

- Sin bastión ni puerto 22: la administración es por Session Manager.
- IMDSv2 obligatorio y discos gp3 cifrados.
- Las llaves de la VPN las genera el proveedor: quedan en el estado, que no se versiona (`.gitignore`) y vive fuera del repo.
- No hay llaves, tokens ni credenciales reales en este directorio.
