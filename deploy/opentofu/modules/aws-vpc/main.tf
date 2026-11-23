locals {
  az_de = { a = "${var.region}a", b = "${var.region}b" }

  rutas_estaticas = flatten([
    for t in var.tablas_de_rutas : [
      for r in t.rutas : {
        clave   = "${t.id}|${r.destino}"
        tabla   = t.id
        destino = r.destino
        salto   = r.salto
      } if r.salto == "internet_gateway"
    ]
  ])

  asociaciones = flatten([
    for t in var.tablas_de_rutas : [for s in t.subredes : { tabla = t.id, subred = s }]
  ])

  reglas_nacl = flatten([
    for n in var.nacls : concat(
      [for r in n.ingress : merge(r, { nacl = n.id, egress = false })],
      [for r in n.egress : merge(r, { nacl = n.id, egress = true })],
    )
  ])

  tablas_con_s3 = [for t in var.tablas_de_rutas : t.id if anytrue([for r in t.rutas : r.salto == "gateway_endpoint_s3"])]
}

resource "aws_vpc" "este" {
  cidr_block           = var.vpc.cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(var.etiquetas, { Name = var.nombre })
}

resource "aws_subnet" "este" {
  for_each                = { for s in var.subredes : s.id => s }
  vpc_id                  = aws_vpc.este.id
  cidr_block              = each.value.cidr
  availability_zone       = local.az_de[each.value.az]
  map_public_ip_on_launch = false
  tags                    = merge(var.etiquetas, { Name = each.key, Tipo = each.value.publica ? "publica" : "privada" })
}

resource "aws_internet_gateway" "este" {
  vpc_id = aws_vpc.este.id
  tags   = merge(var.etiquetas, { Name = "${var.nombre}-igw" })
}

resource "aws_route_table" "tabla" {
  for_each = { for t in var.tablas_de_rutas : t.id => t }
  vpc_id   = aws_vpc.este.id
  tags     = merge(var.etiquetas, { Name = each.key })
}

resource "aws_route_table_association" "subred" {
  for_each       = { for a in local.asociaciones : "${a.tabla}|${a.subred}" => a }
  route_table_id = aws_route_table.tabla[each.value.tabla].id
  subnet_id      = aws_subnet.este[each.value.subred].id
}

resource "aws_route" "estatica" {
  for_each               = { for r in local.rutas_estaticas : r.clave => r }
  route_table_id         = aws_route_table.tabla[each.value.tabla].id
  destination_cidr_block = each.value.destino
  gateway_id             = aws_internet_gateway.este.id
}

# Prefijo de S3 por Gateway Endpoint: sin costo por hora (D2.5).
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.este.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [for t in local.tablas_con_s3 : aws_route_table.tabla[t].id]
  tags              = merge(var.etiquetas, { Name = "${var.nombre}-s3" })
}

resource "aws_security_group" "grupo" {
  for_each    = { for s in var.security_groups : s.id => s }
  name        = "${var.nombre}-${each.key}" # AWS no admite nombres que empiecen con «sg-»
  description = "D2.5: ${each.key} (${each.value.componente})"
  vpc_id      = aws_vpc.este.id

  dynamic "ingress" {
    for_each = each.value.ingress
    content {
      protocol    = ingress.value.protocolo
      from_port   = ingress.value.desde
      to_port     = ingress.value.hasta
      cidr_blocks = [ingress.value.cidr]
      description = ingress.value.descripcion
    }
  }

  dynamic "egress" {
    for_each = each.value.egress
    content {
      protocol    = egress.value.protocolo
      from_port   = egress.value.desde
      to_port     = egress.value.hasta
      cidr_blocks = [egress.value.cidr]
      description = egress.value.descripcion
    }
  }

  tags = merge(var.etiquetas, { Name = each.key })
}

resource "aws_network_acl" "acl" {
  for_each   = { for n in var.nacls : n.id => n }
  vpc_id     = aws_vpc.este.id
  subnet_ids = [for s in each.value.subredes : aws_subnet.este[s].id]
  tags       = merge(var.etiquetas, { Name = each.key })
}

resource "aws_network_acl_rule" "regla" {
  for_each       = { for r in local.reglas_nacl : "${r.nacl}|${r.egress ? "out" : "in"}|${r.numero}" => r }
  network_acl_id = aws_network_acl.acl[each.value.nacl].id
  rule_number    = each.value.numero
  egress         = each.value.egress
  rule_action    = each.value.accion
  protocol       = each.value.protocolo == "tcp" ? "6" : each.value.protocolo
  cidr_block     = each.value.cidr
  from_port      = each.value.protocolo == "-1" ? null : each.value.desde
  to_port        = each.value.protocolo == "-1" ? null : each.value.hasta
}
