locals {
  o = var.vpn.opciones_aws
}

# VGW con el ASN de AWS de D1.10 y adjunto a la VPC.
resource "aws_vpn_gateway" "vgw" {
  vpc_id          = var.vpc_id
  amazon_side_asn = var.vpn.asn_aws
  tags            = merge(var.etiquetas, { Name = "${var.nombre}-vgw" })
}

# Extremo del campus: ASN privado de D1.10. La IP es la del firewall (producción) o la de cgw-sim (Modo A).
resource "aws_customer_gateway" "cgw" {
  bgp_asn    = var.vpn.asn_cliente
  ip_address = var.ip_publica_cliente
  type       = "ipsec.1"
  tags       = merge(var.etiquetas, { Name = "${var.nombre}-cgw" })
}

# Site-to-Site VPN con BGP (sin rutas estáticas), IKEv2 y los parámetros de fase 1 y 2 de D1.10 en los dos túneles.
# La llave precompartida la genera AWS: no se fija aquí y sale como salida sensible (D1.10: se guarda cifrada, nunca en el repositorio).
resource "aws_vpn_connection" "vpn" {
  vpn_gateway_id      = aws_vpn_gateway.vgw.id
  customer_gateway_id = aws_customer_gateway.cgw.id
  type                = "ipsec.1"
  static_routes_only  = false

  tunnel1_inside_cidr                  = var.vpn.tuneles[0].inside_cidr
  tunnel1_ike_versions                 = local.o.ike_versions
  tunnel1_phase1_encryption_algorithms = local.o.phase1_encryption_algorithms
  tunnel1_phase1_integrity_algorithms  = local.o.phase1_integrity_algorithms
  tunnel1_phase1_dh_group_numbers      = local.o.phase1_dh_group_numbers
  tunnel1_phase1_lifetime_seconds      = local.o.phase1_lifetime_seconds
  tunnel1_phase2_encryption_algorithms = local.o.phase2_encryption_algorithms
  tunnel1_phase2_dh_group_numbers      = local.o.phase2_dh_group_numbers
  tunnel1_phase2_lifetime_seconds      = local.o.phase2_lifetime_seconds
  tunnel1_dpd_timeout_seconds          = local.o.dpd_timeout_seconds
  tunnel1_dpd_timeout_action           = local.o.dpd_timeout_action
  tunnel1_startup_action               = local.o.startup_action

  tunnel2_inside_cidr                  = var.vpn.tuneles[1].inside_cidr
  tunnel2_ike_versions                 = local.o.ike_versions
  tunnel2_phase1_encryption_algorithms = local.o.phase1_encryption_algorithms
  tunnel2_phase1_integrity_algorithms  = local.o.phase1_integrity_algorithms
  tunnel2_phase1_dh_group_numbers      = local.o.phase1_dh_group_numbers
  tunnel2_phase1_lifetime_seconds      = local.o.phase1_lifetime_seconds
  tunnel2_phase2_encryption_algorithms = local.o.phase2_encryption_algorithms
  tunnel2_phase2_dh_group_numbers      = local.o.phase2_dh_group_numbers
  tunnel2_phase2_lifetime_seconds      = local.o.phase2_lifetime_seconds
  tunnel2_dpd_timeout_seconds          = local.o.dpd_timeout_seconds
  tunnel2_dpd_timeout_action           = local.o.dpd_timeout_action
  tunnel2_startup_action               = local.o.startup_action

  tags = merge(var.etiquetas, { Name = "${var.nombre}-vpn" })
}

# Las rutas del campus (10.20.0.0/14, aprendidas por BGP) entran solas en las tablas de rutas (D2.5: «propagada»).
resource "aws_vpn_gateway_route_propagation" "tabla" {
  for_each       = var.tablas_de_rutas
  vpn_gateway_id = aws_vpn_gateway.vgw.id
  route_table_id = each.value
}
