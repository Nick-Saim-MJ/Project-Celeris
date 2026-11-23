locals {
  etiquetas = merge(
    var.etiquetas_base,
    { Ttl = coalesce(var.ttl, var.ttl_por_defecto) },
    var.emulador ? { Modo = "AWS emulado - plano de control sin trafico" } : {},
  )

  # El emulador no ejecuta instancias ni trae la Debian 13: usa una de las imágenes que él mismo registra (Amazon Linux 2023).
  ami_id = coalesce(var.ami_id, try(data.aws_ami.emulador[0].id, null), try(data.aws_ssm_parameter.debian[0].value, null))

  # Rutas hacia el campus del diseño (salto «vgw»): en AWS real las trae la propagación de BGP; en el emulador se crean estáticas.
  rutas_al_campus = flatten([
    for t in var.tablas_de_rutas : [for r in t.rutas : { tabla = t.id, destino = r.destino } if r.salto == "vgw"]
  ])
}

# AWS EMULADO: el emulador registra sus propias imágenes; no tiene las de SSM.
data "aws_ami" "emulador" {
  count       = var.emulador && var.ami_id == null ? 1 : 0
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# Debian 13 oficial (x86_64) por su parámetro público de SSM; no se elige una AMI a mano. Solo con AWS real.
data "aws_ssm_parameter" "debian" {
  count = var.emulador || var.ami_id != null ? 0 : 1
  name  = "/aws/service/debian/release/13/latest/amd64"
}

module "aws_vpc" {
  source = "../../modules/aws-vpc"

  nombre          = var.vpc.nombre
  region          = var.region
  vpc             = { cidr = var.vpc.cidr, reservado = var.vpc.reservado }
  subredes        = var.subredes
  tablas_de_rutas = var.tablas_de_rutas
  security_groups = var.security_groups
  nacls           = var.nacls
  etiquetas       = local.etiquetas
}

module "aws_vpn" {
  source = "../../modules/aws-vpn"

  nombre             = var.vpc.nombre
  vpc_id             = module.aws_vpc.vpc_id
  tablas_de_rutas    = module.aws_vpc.tablas_de_rutas
  ip_publica_cliente = var.vpn.ip_publica_campus
  vpn                = var.vpn
  emulador           = var.emulador
  rutas_al_campus    = local.rutas_al_campus
  etiquetas          = local.etiquetas
}

module "aws_gw" {
  source = "../../modules/aws-gw"

  nombre                        = var.vpc.nombre
  instancia                     = var.instancias["EC2-GW"]
  subredes                      = module.aws_vpc.subredes
  zonas_de_disponibilidad       = module.aws_vpc.zonas_de_disponibilidad
  grupos_de_seguridad           = module.aws_vpc.grupos_de_seguridad
  modo_laboratorio              = var.modo_laboratorio
  ami_id                        = local.ami_id
  perfil_de_instancia_existente = var.perfil_de_instancia_existente
  etiquetas                     = local.etiquetas
}

module "aws_backup" {
  source = "../../modules/aws-backup"

  respaldo         = var.respaldo
  crear_credencial = var.crear_credencial_respaldo
  etiquetas        = local.etiquetas
}
