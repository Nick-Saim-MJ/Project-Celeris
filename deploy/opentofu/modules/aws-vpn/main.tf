locals {
  o = var.vpn.opciones_aws
}

# VGW con el ASN de AWS de D1.10 y adjunto a la VPC.
resource "aws_vpn_gateway" "vgw" {
  vpc_id          = var.vpc_id
  amazon_side_asn = var.vpn.asn_aws
  tags            = merge(var.etiquetas, { Name = "${var.nombre}-vgw" })
}

# Extremo del campus: ASN privado de D1.10. La IP es la pública del FortiGate (S-29): FW01 está detrás de su NAT 1:1 y usa NAT-T (UDP 4500);
# el lado AWS lo admite sin opciones propias.
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

  # D1.10 usa AES-GCM (AEAD): la integridad de fase 2 y el margen de rekey no son de diseño. AWS (y el emulador) devuelven sus valores
  # por defecto y el proveedor quiere «corregirlos» con ModifyVpnTunnelOptions, que el AWS Emulator no implementa (CI-55).
  lifecycle {
    ignore_changes = [
      tunnel1_phase2_integrity_algorithms, tunnel2_phase2_integrity_algorithms,
      tunnel1_rekey_margin_time_seconds, tunnel2_rekey_margin_time_seconds,
    ]
  }
}

# Rutas hacia el campus en las tablas de rutas (D2.5: «propagada»).
# AWS real: el VGW propaga las rutas aprendidas por BGP.
# Emulador (var.emulador = true): el AWS Emulator no implementa EnableVgwRoutePropagation (NotImplemented), así que se crea una ruta
# estática hacia el VGW con el mismo destino. DIFERENCIA CON AWS REAL: la ruta estática no sigue al BGP (no desaparece si cae el túnel).
resource "aws_vpn_gateway_route_propagation" "tabla" {
  for_each       = var.emulador ? {} : var.tablas_de_rutas
  vpn_gateway_id = aws_vpn_gateway.vgw.id
  route_table_id = each.value
}

resource "aws_route" "campus_estatica" {
  for_each               = var.emulador ? { for r in var.rutas_al_campus : "${r.tabla}|${r.destino}" => r } : {}
  route_table_id         = var.tablas_de_rutas[each.value.tabla]
  destination_cidr_block = each.value.destino
  gateway_id             = aws_vpn_gateway.vgw.id

  depends_on = [aws_vpn_gateway.vgw]
}
