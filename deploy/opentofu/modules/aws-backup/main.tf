locals {
  modo_lock = upper(var.respaldo.object_lock.modo)
}

# celeris-backups: la copia fuera del sitio que nadie del campus puede borrar (Object Lock de 30 días en modo compliance).
# restic cifra en origen; la llave no está en AWS.
resource "aws_s3_bucket" "respaldos" {
  bucket              = var.respaldo.bucket
  object_lock_enabled = true
  tags                = merge(var.etiquetas, { Name = var.respaldo.bucket })
}

resource "aws_s3_bucket_versioning" "respaldos" {
  bucket = aws_s3_bucket.respaldos.id
  versioning_configuration {
    status = var.respaldo.versionado ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "respaldos" {
  bucket = aws_s3_bucket.respaldos.id
  rule {
    default_retention {
      mode = local.modo_lock
      days = var.respaldo.object_lock.dias
    }
  }

  depends_on = [aws_s3_bucket_versioning.respaldos]
}

resource "aws_s3_bucket_public_access_block" "respaldos" {
  bucket                  = aws_s3_bucket.respaldos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Credencial aparte con solo s3:PutObject y condición de IP de origen = IP pública del campus [S-30].
resource "aws_iam_user" "respaldo" {
  count = var.crear_credencial ? 1 : 0
  name  = var.respaldo.usuario
  tags  = var.etiquetas
}

resource "aws_iam_user_policy" "respaldo" {
  count = var.crear_credencial ? 1 : 0
  name  = "solo-escritura-desde-el-campus"
  user  = aws_iam_user.respaldo[0].name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "SoloPutObjectDesdeElCampus"
      Effect    = "Allow"
      Action    = ["s3:PutObject"]
      Resource  = ["${aws_s3_bucket.respaldos.arn}/*"]
      Condition = { IpAddress = { "aws:SourceIp" = "${var.respaldo.ip_campus}/32" } }
    }]
  })
}

# El bucket «solo acepta la IP pública del campus» para esa credencial: la política niega cualquier acción del usuario de respaldo
# que no venga de esa IP. No se niega a los demás principales para no dejar fuera a quien administra el bucket.
resource "aws_s3_bucket_policy" "respaldos" {
  count  = var.crear_credencial ? 1 : 0
  bucket = aws_s3_bucket.respaldos.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "NegarElUsuarioDeRespaldoFueraDelCampus"
      Effect    = "Deny"
      Principal = { AWS = aws_iam_user.respaldo[0].arn }
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.respaldos.arn, "${aws_s3_bucket.respaldos.arn}/*"]
      Condition = { NotIpAddress = { "aws:SourceIp" = "${var.respaldo.ip_campus}/32" } }
    }]
  })

  depends_on = [aws_s3_bucket_public_access_block.respaldos]
}
