output "shield_ip_privada" {
  description = "IP privada de EC2-SHIELD (F9, F12)."
  value       = aws_instance.shield.private_ip
}

output "ctrlr_ip_privada" {
  description = "IP privada de EC2-CTRLR (F16)."
  value       = aws_instance.ctrlr.private_ip
}

output "ids_de_instancia" {
  description = "IDs de las instancias, para conectarse con Session Manager (`aws ssm start-session --target <id>`)."
  value       = { "EC2-SHIELD" = aws_instance.shield.id, "EC2-CTRLR" = aws_instance.ctrlr.id }
}
