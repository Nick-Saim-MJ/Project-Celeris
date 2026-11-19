output "ip_publica_nat" {
  description = "IP elástica de NAT01."
  value       = module.aws_vpc.ip_publica_nat
}

output "ip_publica_cgw_sim" {
  description = "IP elástica de cgw-sim (customer gateway)."
  value       = module.onprem_sim.ip_publica_cgw
}

output "vpn_conexion_id" {
  description = "ID de la conexión VPN: tras `tofu destroy`, `aws ec2 describe-vpn-connections --vpn-connection-ids <id>` debe mostrarla en estado deleted."
  value       = module.aws_vpn.conexion_id
}

output "ips_aws_de_los_tuneles" {
  description = "IP públicas de los dos extremos de AWS."
  value       = module.aws_vpn.ips_aws_de_los_tuneles
}

output "instancias_aws" {
  description = "IDs de EC2-SHIELD y EC2-CTRLR para Session Manager."
  value       = module.aws_shield.ids_de_instancia
}

output "instancias_onprem_sim" {
  description = "IDs de cgw-sim y labcli-sim para Session Manager."
  value       = module.onprem_sim.ids_de_instancia
}

output "etiquetas" {
  description = "Etiquetas aplicadas a todos los recursos."
  value       = local.etiquetas
}
