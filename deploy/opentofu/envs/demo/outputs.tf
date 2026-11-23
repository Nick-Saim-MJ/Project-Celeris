output "modo" {
  description = "Qué es este despliegue."
  value       = var.emulador ? "AWS emulado: plano de control, sin tráfico" : "AWS real"
}

output "vpc_id" {
  description = "ID de la VPC."
  value       = module.aws_vpc.vpc_id
}

output "vgw_id" {
  description = "ID del Virtual Private Gateway."
  value       = module.aws_vpn.vgw_id
}

output "vpn_conexion_id" {
  description = "ID de la conexión VPN: tras `tofu destroy`, `aws ec2 describe-vpn-connections --vpn-connection-ids <id>` debe mostrarla en estado deleted."
  value       = module.aws_vpn.conexion_id
}

output "ips_aws_de_los_tuneles" {
  description = "IP públicas de los dos extremos de AWS."
  value       = module.aws_vpn.ips_aws_de_los_tuneles
}

output "ec2_gw_id" {
  description = "ID de EC2-GW para Session Manager."
  value       = module.aws_gw.id_de_instancia
}

output "ec2_gw_ip_publica" {
  description = "IP elástica de EC2-GW."
  value       = module.aws_gw.ip_publica
}

output "bucket_respaldos" {
  description = "Bucket de respaldos con Object Lock."
  value       = module.aws_backup.bucket
}

output "etiquetas" {
  description = "Etiquetas aplicadas a todos los recursos."
  value       = local.etiquetas
}
