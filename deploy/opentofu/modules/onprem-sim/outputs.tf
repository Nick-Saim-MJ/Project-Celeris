output "ip_publica_cgw" {
  description = "IP elástica de cgw-sim: la IP del customer gateway que se registra en AWS."
  value       = aws_eip.cgw.public_ip
}

output "ids_de_instancia" {
  description = "IDs de las instancias, para conectarse con Session Manager."
  value       = { "cgw-sim" = aws_instance.cgw.id, "labcli-sim" = aws_instance.labcli.id }
}

output "labcli_ip_privada" {
  description = "IP de labcli-sim (LABCLI01 del inventario)."
  value       = aws_instance.labcli.private_ip
}
