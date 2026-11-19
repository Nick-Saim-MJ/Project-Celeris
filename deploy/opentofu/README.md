# IaC del Modo A (OpenTofu): AWS efímero

Despliega en AWS la VPC de D2.5, la VPN híbrida de D1.10 y un campus simulado que hace de cliente de la VPN. Es el **Modo A** del laboratorio (Parte F). Todo valor de diseño sale de `infra/inventory.yaml`; los módulos no llevan IP, ASN ni puertos escritos a mano (lo comprueba `tests/gen/test_tofu.py`).

**Estado: validado sin desplegar.** `tofu fmt -check` y `tofu validate` pasan, y un plan estructural con credenciales falsas crea 78 recursos. Nunca se ejecutó `tofu apply` ni `tofu plan` contra una cuenta de AWS. Lo que dependa de AWS real está sin verificar y figura en CI-25.

## Qué crea

| Módulo | Recursos |
|---|---|
| `modules/aws-vpc` | VPC 10.30.0.0/16, subredes de D2.5, IGW, tablas de rutas, endpoint S3 de tipo gateway, Security Groups, NACL, NAT01 (instancia NAT con IP elástica), roles de SSM |
| `modules/aws-vpn` | Virtual Private Gateway, customer gateway, conexión VPN con BGP y las opciones de D1.10, propagación de rutas |
| `modules/aws-shield` | EC2-SHIELD (imagen OCI de celeris-node fijada por digest, F9 y F12) y EC2-CTRLR (réplica del plano de control, sin software) |
| `modules/onprem-sim` | VPC 10.20.0.0/16, `cgw-sim` (strongSwan + FRR, IP elástica = customer gateway) y `labcli-sim` (LABCLI01) |

**Emulado, no implementado:** `onprem-sim` representa al campus; no es FW01 (OPNsense) ni existe la sede. La VPN del lado AWS sí es el servicio real.

## Uso

```bash
python infra/genera.py tofu        # regenera envs/demo/diseno.auto.tfvars.json desde el inventario
cd deploy/opentofu/envs/demo
tofu init
tofu validate
```

Para desplegar (solo con la confirmación del equipo; crea recursos con costo):

```bash
tofu plan  -var 'imagen_celeris_node=ghcr.io/<dueño>/celeris-node@sha256:<digest>'
tofu apply -var 'imagen_celeris_node=ghcr.io/<dueño>/celeris-node@sha256:<digest>'
tofu destroy
```

La imagen sale del flujo `.github/workflows/imagen.yml`; el módulo rechaza una referencia sin `@sha256:` (REQ-NF-15).

### Variables del entorno

| Variable | Predeterminado | Para qué |
|---|---|---|
| `region` | `us-east-1` | Región del laboratorio (la candidata de producción, `sa-east-1`, está en el inventario) |
| `ttl` | el del inventario (`4h`) | Etiqueta `Ttl` para barrer lo que quede |
| `modo_laboratorio` | `true` | Tipos de instancia de laboratorio (D2.5, 6.3) en lugar de los de producción |
| `perfil_de_instancia_existente` | `null` | Perfil ya creado (AWS Academy: `LabInstanceProfile`); evita crear roles de IAM |
| `ami_id` | `null` | AMI x86_64; si es `null` se usa la Debian 13 oficial por su parámetro de SSM |
| `imagen_celeris_node` | (obligatoria) | Imagen OCI por digest |
| `presupuesto_usd`, `correo_alarma` | `null` | Presupuesto de AWS Budgets con alarma al 80 % (RE-07); sin valor, no se crea |

Todos los recursos llevan las etiquetas `Proyecto` y `Ttl`.

## Seguridad

- Sin bastión ni puerto 22: la administración es por Session Manager (`aws ssm start-session --target <id>`; los IDs salen en `outputs`).
- IMDSv2 obligatorio y discos gp3 cifrados en todas las instancias.
- Las llaves precompartidas de la VPN las genera AWS: quedan en el estado de OpenTofu y en el `user_data` de `cgw-sim`. El estado es local y no se versiona; es aceptable solo para el laboratorio efímero (CI-25).
- No hay llaves, tokens ni credenciales en este directorio.

## Comprobar que el destroy no deja nada

Con las credenciales del equipo, tras `tofu destroy`:

```bash
aws ec2 describe-vpn-connections --vpn-connection-ids <vpn_conexion_id> --query 'VpnConnections[].State'
aws ec2 describe-addresses --filters Name=tag:Proyecto,Values=celeris-edge
```

La primera debe devolver `deleted`; la segunda, una lista vacía.

## Límites conocidos (CI-25)

- AWS no admite un DPD menor de 30 s; D1.10 pide 10 s. Los módulos usan 30 s del lado AWS.
- D2.5 no define reglas de salida de Security Groups ni NACL: se permite todo.
- `cgw-sim` queda tras una IP elástica y usa interfaces XFRM, no VTI como el Modo L. Sin verificar con una VPN real.
- AWS Emulator no está instalado; no hay salida de plan en `evidencias/`.
- El Modo A' (sin VGW) no está implementado.
