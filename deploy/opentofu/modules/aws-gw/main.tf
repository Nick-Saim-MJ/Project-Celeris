locals {
  crear_iam = var.perfil_de_instancia_existente == null
  tipo      = var.modo_laboratorio ? var.instancia.tipo_laboratorio : var.instancia.tipo_produccion
}

# Perfil de instancia solo con Session Manager: sin permisos sobre S3 (D2.5, «iam.ec2_gw»). En AWS Academy se usa el perfil existente [S-13].
resource "aws_iam_role" "gw" {
  count = local.crear_iam ? 1 : 0
  name  = "${var.nombre}-ec2-gw"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
  tags = var.etiquetas
}

resource "aws_iam_role_policy_attachment" "ssm" {
  count      = local.crear_iam ? 1 : 0
  role       = aws_iam_role.gw[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "gw" {
  count = local.crear_iam ? 1 : 0
  name  = aws_iam_role.gw[0].name
  role  = aws_iam_role.gw[0].name
  tags  = var.etiquetas
}

# EC2-GW: sin user_data. El software (Caddy + Coraza, mTLS hacia CTRL01, agente Wazuh) lo define CE02 y se instala en el Modo A real;
# este módulo crea la instancia con su red, su grupo de seguridad y su perfil (CI-54).
resource "aws_instance" "gw" {
  ami                    = var.ami_id
  instance_type          = local.tipo
  subnet_id              = var.subredes[var.instancia.subred]
  availability_zone      = var.zonas_de_disponibilidad[var.instancia.subred]
  private_ip             = var.instancia.ip
  vpc_security_group_ids = [var.grupos_de_seguridad[var.instancia.grupo_de_seguridad]]
  iam_instance_profile   = local.crear_iam ? aws_iam_instance_profile.gw[0].name : var.perfil_de_instancia_existente

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.instancia.disco_gb
    encrypted   = true
  }

  tags = merge(var.etiquetas, { Name = "EC2-GW" })
}

# IP pública estable de EC2-GW (F29): AWS la asigna; no se documenta una IP real.
resource "aws_eip" "gw" {
  domain   = "vpc"
  instance = aws_instance.gw.id
  tags     = merge(var.etiquetas, { Name = "EC2-GW" })
}
