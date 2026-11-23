output "vpc_id" {
  description = "ID de la VPC."
  value       = aws_vpc.este.id
}

output "subredes" {
  description = "ID de cada subred por nombre (pub-a, app-a…)."
  value       = { for k, s in aws_subnet.este : k => s.id }
}

output "zonas_de_disponibilidad" {
  description = "Zona de disponibilidad de cada subred por nombre."
  value       = { for k, s in aws_subnet.este : k => s.availability_zone }
}

output "tablas_de_rutas" {
  description = "ID de cada tabla de rutas (rt-public, rt-private)."
  value       = { for k, t in aws_route_table.tabla : k => t.id }
}

output "grupos_de_seguridad" {
  description = "ID de cada Security Group."
  value       = { for k, g in aws_security_group.grupo : k => g.id }
}
