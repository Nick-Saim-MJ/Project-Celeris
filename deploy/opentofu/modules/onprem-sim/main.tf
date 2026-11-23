locals {
  az        = "${var.region}a"
  crear_iam = var.perfil_de_instancia_existente == null
  nombres   = ["cgw-sim", "labcli-sim"]
  # IP privada fija de cgw-sim en su subred (la décima dirección): permite escribir su configuración sin referirse a sí misma.
  cgw_ip_privada = cidrhost(var.onprem.subred_wan_cidr, 10)

  tuneles_cgw = [
    for i, t in var.vpn.tuneles : {
      nombre     = t.nombre
      ip_aws     = var.tuneles_aws[i].ip_aws
      ip_cliente = t.ip_cliente
      clave      = t.clave_vti
      psk        = var.tuneles_aws[i].clave_asignada
    }
  ]
}

resource "aws_vpc" "sim" {
  cidr_block           = var.onprem.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(var.etiquetas, { Name = var.nombre })
}

resource "aws_internet_gateway" "sim" {
  vpc_id = aws_vpc.sim.id
  tags   = merge(var.etiquetas, { Name = "${var.nombre}-igw" })
}

resource "aws_subnet" "wan" {
  vpc_id                  = aws_vpc.sim.id
  cidr_block              = var.onprem.subred_wan_cidr
  availability_zone       = local.az
  map_public_ip_on_launch = false
  tags                    = merge(var.etiquetas, { Name = "wan-sim" })
}

resource "aws_subnet" "lab" {
  vpc_id            = aws_vpc.sim.id
  cidr_block        = var.onprem.subred_lab_cidr
  availability_zone = local.az
  tags              = merge(var.etiquetas, { Name = "lab-sim" })
}

resource "aws_route_table" "wan" {
  vpc_id = aws_vpc.sim.id
  tags   = merge(var.etiquetas, { Name = "wan-sim" })
}

resource "aws_route" "wan_internet" {
  route_table_id         = aws_route_table.wan.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.sim.id
}

resource "aws_route_table_association" "wan" {
  route_table_id = aws_route_table.wan.id
  subnet_id      = aws_subnet.wan.id
}

# La subred de los PC de laboratorio sale por cgw-sim: hacia la VPC de AWS por la VPN y hacia Internet con NAT en cgw-sim.
resource "aws_route_table" "lab" {
  vpc_id = aws_vpc.sim.id
  tags   = merge(var.etiquetas, { Name = "lab-sim" })
}

resource "aws_route" "lab_hacia_aws" {
  route_table_id         = aws_route_table.lab.id
  destination_cidr_block = var.vpn.redes.aws
  network_interface_id   = aws_instance.cgw.primary_network_interface_id
}

resource "aws_route" "lab_internet" {
  route_table_id         = aws_route_table.lab.id
  destination_cidr_block = "0.0.0.0/0"
  network_interface_id   = aws_instance.cgw.primary_network_interface_id
}

resource "aws_route_table_association" "lab" {
  route_table_id = aws_route_table.lab.id
  subnet_id      = aws_subnet.lab.id
}

# IKE (UDP 500 y 4500) y ESP solo desde los dos extremos de AWS; el resto del tráfico, solo desde la propia VPC.
resource "aws_security_group" "cgw" {
  name        = "cgw-sim"
  description = "cgw-sim: IKE y ESP desde los extremos de AWS"
  vpc_id      = aws_vpc.sim.id

  ingress {
    protocol    = "udp"
    from_port   = 500
    to_port     = 500
    cidr_blocks = [for ip in var.ips_aws_de_los_tuneles : "${ip}/32"]
    description = "IKE"
  }

  ingress {
    protocol    = "udp"
    from_port   = 4500
    to_port     = 4500
    cidr_blocks = [for ip in var.ips_aws_de_los_tuneles : "${ip}/32"]
    description = "IKE con NAT-T"
  }

  ingress {
    protocol    = "50"
    from_port   = 0
    to_port     = 0
    cidr_blocks = [for ip in var.ips_aws_de_los_tuneles : "${ip}/32"]
    description = "ESP"
  }

  ingress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = [var.onprem.vpc_cidr, var.vpn.redes.aws]
    description = "Trafico de la VPC simulada y de la VPC de AWS"
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
    description = "Salida sin restriccion"
  }

  tags = merge(var.etiquetas, { Name = "cgw-sim" })
}

resource "aws_security_group" "lab" {
  name        = "labcli-sim"
  description = "labcli-sim: trafico de la VPC simulada y de AWS"
  vpc_id      = aws_vpc.sim.id

  ingress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = [var.onprem.vpc_cidr, var.vpn.redes.aws]
    description = "VPC simulada y VPC de AWS"
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
    description = "Salida sin restriccion"
  }

  tags = merge(var.etiquetas, { Name = "labcli-sim" })
}

resource "aws_iam_role" "instancia" {
  for_each = local.crear_iam ? toset(local.nombres) : toset([])
  name     = "${var.nombre}-${each.key}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
  tags = var.etiquetas
}

resource "aws_iam_role_policy_attachment" "ssm" {
  for_each   = local.crear_iam ? toset(local.nombres) : toset([])
  role       = aws_iam_role.instancia[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "instancia" {
  for_each = local.crear_iam ? toset(local.nombres) : toset([])
  name     = aws_iam_role.instancia[each.key].name
  role     = aws_iam_role.instancia[each.key].name
  tags     = var.etiquetas
}

# IP elástica de cgw-sim: es la IP del customer gateway que se registra en AWS (módulo aws-vpn).
resource "aws_eip" "cgw" {
  domain = "vpc"
  tags   = merge(var.etiquetas, { Name = "cgw-sim" })

  depends_on = [aws_internet_gateway.sim]
}

# cgw-sim emula a FW01: strongSwan (IKEv2, VTI/XFRM por túnel) y FRR (BGP, ASN 65020, prepending del túnel 2).
# source_dest_check desactivado para poder enrutar hacia su VPC (F5.1).
resource "aws_instance" "cgw" {
  ami                    = var.ami_id
  instance_type          = var.onprem.cgw_tipo
  subnet_id              = aws_subnet.wan.id
  private_ip             = local.cgw_ip_privada
  vpc_security_group_ids = [aws_security_group.cgw.id]
  source_dest_check      = false
  iam_instance_profile   = local.crear_iam ? aws_iam_instance_profile.instancia["cgw-sim"].name : var.perfil_de_instancia_existente

  user_data = templatefile("${path.module}/templates/cgw.sh.tftpl", {
    ip_privada   = local.cgw_ip_privada
    ip_publica   = aws_eip.cgw.public_ip
    tuneles      = local.tuneles_cgw
    ike          = var.vpn.strongswan.ike
    esp          = var.vpn.strongswan.esp
    dpd_s        = var.vpn.strongswan.dpd_s
    dpd_accion   = var.vpn.strongswan.dpd_accion
    ike_vida_s   = var.vpn.strongswan.reautenticacion_ike_s
    vida_child_s = var.vpn.strongswan.vida_child_s
    mtu          = var.vpn.mtu
    mss          = var.vpn.mss
    frr_conf     = var.frr_conf
    lab_cidr     = var.onprem.subred_lab_cidr
    aws_cidr     = var.vpn.redes.aws
  })
  user_data_replace_on_change = true

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }

  tags = merge(var.etiquetas, { Name = "cgw-sim" })
}

resource "aws_eip_association" "cgw" {
  allocation_id = aws_eip.cgw.id
  instance_id   = aws_instance.cgw.id
}

# labcli-sim: el PC de laboratorio con la IP del inventario (LABCLI01).
resource "aws_instance" "labcli" {
  ami                    = var.ami_id
  instance_type          = var.onprem.labcli_tipo
  subnet_id              = aws_subnet.lab.id
  private_ip             = var.onprem.labcli_ip
  vpc_security_group_ids = [aws_security_group.lab.id]
  iam_instance_profile   = local.crear_iam ? aws_iam_instance_profile.instancia["labcli-sim"].name : var.perfil_de_instancia_existente

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }

  tags = merge(var.etiquetas, { Name = "labcli-sim" })
}
