output "bucket" {
  description = "Nombre del bucket de respaldos."
  value       = aws_s3_bucket.respaldos.id
}

output "bucket_arn" {
  description = "ARN del bucket de respaldos."
  value       = aws_s3_bucket.respaldos.arn
}
