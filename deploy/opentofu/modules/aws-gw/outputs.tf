output "id_de_instancia" {
  description = "ID de EC2-GW (Session Manager: aws ssm start-session --target <id>)."
  value       = aws_instance.gw.id
}

output "ip_publica" {
  description = "IP elástica de EC2-GW."
  value       = aws_eip.gw.public_ip
}
