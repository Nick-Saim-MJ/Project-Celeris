output "vpc_id" {
  description = "ID de la VPC."
  value       = aws_vpc.este.id
}

output "subredes" {
  description = "ID de cada subred por nombre (pub-a, app-a…)."
  value       = { for k, s in aws_subnet.este : k => s.id }
}

output "tablas_de_rutas" {
  description = "ID de cada tabla de rutas (rt-public, rt-private)."
  value       = { for k, t in aws_route_table.tabla : k => t.id }
}

output "grupos_de_seguridad" {
  description = "ID de cada Security Group."
  value       = { for k, g in aws_security_group.grupo : k => g.id }
}

output "perfiles_de_instancia" {
  description = "Perfil de instancia por componente (el existente de AWS Academy o el creado aquí)."
  value       = { for n in var.nombres_de_instancia : n => local.crear_iam ? aws_iam_instance_profile.instancia[n].name : var.perfil_de_instancia_existente }
}

output "ip_publica_nat" {
  description = "IP elástica de NAT01."
  value       = aws_eip.nat.public_ip
}
