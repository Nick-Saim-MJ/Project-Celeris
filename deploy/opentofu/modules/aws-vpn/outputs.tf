output "vgw_id" {
  description = "ID del Virtual Private Gateway."
  value       = aws_vpn_gateway.vgw.id
}

output "conexion_id" {
  description = "ID de la conexión Site-to-Site (para `aws ec2 describe-vpn-connections` al verificar que el destroy no deja nada)."
  value       = aws_vpn_connection.vpn.id
}

output "tuneles" {
  description = "IP pública de AWS de cada túnel (los extremos remotos del campus) y direcciones internas /30."
  value = [
    {
      ip_aws         = aws_vpn_connection.vpn.tunnel1_address
      cgw_inside     = aws_vpn_connection.vpn.tunnel1_cgw_inside_address
      vgw_inside     = aws_vpn_connection.vpn.tunnel1_vgw_inside_address
      clave_asignada = aws_vpn_connection.vpn.tunnel1_preshared_key
    },
    {
      ip_aws         = aws_vpn_connection.vpn.tunnel2_address
      cgw_inside     = aws_vpn_connection.vpn.tunnel2_cgw_inside_address
      vgw_inside     = aws_vpn_connection.vpn.tunnel2_vgw_inside_address
      clave_asignada = aws_vpn_connection.vpn.tunnel2_preshared_key
    },
  ]
  sensitive = true
}

output "ips_aws_de_los_tuneles" {
  description = "IP públicas de los dos extremos AWS (no sensible)."
  value       = [aws_vpn_connection.vpn.tunnel1_address, aws_vpn_connection.vpn.tunnel2_address]
}
