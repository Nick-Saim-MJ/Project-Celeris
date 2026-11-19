locals {
  etiquetas = merge(var.etiquetas_base, { Ttl = coalesce(var.ttl, var.ttl_por_defecto) })
  ami_id    = coalesce(var.ami_id, try(data.aws_ssm_parameter.debian[0].value, null))
  nat = {
    ip                 = var.instancias["NAT01"].ip
    subred             = var.instancias["NAT01"].subred
    tipo               = var.modo_laboratorio ? var.instancias["NAT01"].tipo_laboratorio : var.instancias["NAT01"].tipo_produccion
    disco_gb           = var.instancias["NAT01"].disco_gb
    grupo_de_seguridad = var.instancias["NAT01"].grupo_de_seguridad
  }
}

# Debian 13 oficial (x86_64) por su parámetro público de SSM; no se elige una AMI a mano.
data "aws_ssm_parameter" "debian" {
  count = var.ami_id == null ? 1 : 0
  name  = "/aws/service/debian/release/13/latest/amd64"
}

module "aws_vpc" {
  source = "../../modules/aws-vpc"

  nombre                        = var.vpc.nombre
  region                        = var.region
  vpc                           = { cidr = var.vpc.cidr, reservado = var.vpc.reservado }
  subredes                      = var.subredes
  tablas_de_rutas               = var.tablas_de_rutas
  security_groups               = var.security_groups
  nacls                         = var.nacls
  nat                           = local.nat
  ami_id                        = local.ami_id
  perfil_de_instancia_existente = var.perfil_de_instancia_existente
  nombres_de_instancia          = ["NAT01", "EC2-SHIELD", "EC2-CTRLR"]
  etiquetas                     = local.etiquetas
}

module "aws_vpn" {
  source = "../../modules/aws-vpn"

  nombre             = var.vpc.nombre
  vpc_id             = module.aws_vpc.vpc_id
  tablas_de_rutas    = module.aws_vpc.tablas_de_rutas
  ip_publica_cliente = module.onprem_sim.ip_publica_cgw
  vpn                = var.vpn
  etiquetas          = local.etiquetas
}

module "aws_shield" {
  source = "../../modules/aws-shield"

  instancias            = { for k, v in var.instancias : k => v if k != "NAT01" }
  subredes              = module.aws_vpc.subredes
  grupos_de_seguridad   = module.aws_vpc.grupos_de_seguridad
  perfiles_de_instancia = module.aws_vpc.perfiles_de_instancia
  modo_laboratorio      = var.modo_laboratorio
  ami_id                = local.ami_id
  shield                = var.shield
  imagen_celeris_node   = var.imagen_celeris_node
  etiquetas             = local.etiquetas
}

module "onprem_sim" {
  source = "../../modules/onprem-sim"

  nombre                        = "onprem-sim"
  onprem                        = var.onprem_sim
  region                        = var.region
  vpn                           = var.vpn
  frr_conf                      = var.frr_conf
  tuneles_aws                   = module.aws_vpn.tuneles
  ips_aws_de_los_tuneles        = module.aws_vpn.ips_aws_de_los_tuneles
  ami_id                        = local.ami_id
  perfil_de_instancia_existente = var.perfil_de_instancia_existente
  etiquetas                     = local.etiquetas
}

# Alarma de presupuesto (RE-07). El tope no está en el inventario: sin valor no se crea.
resource "aws_budgets_budget" "demo" {
  count        = var.presupuesto_usd == null ? 0 : 1
  name         = "celeris-demo"
  budget_type  = "COST"
  limit_amount = tostring(var.presupuesto_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = var.presupuesto_alarma_porcentaje
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.correo_alarma]
  }

  lifecycle {
    precondition {
      condition     = var.correo_alarma != null
      error_message = "presupuesto_usd requiere correo_alarma."
    }
  }
}
