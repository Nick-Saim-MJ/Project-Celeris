locals {
  tipo = { for k, i in var.instancias : k => var.modo_laboratorio ? i.tipo_laboratorio : i.tipo_produccion }
}

# EC2-SHIELD: caché de segundo nivel. Solo atiende los MISS de los nodos del campus, en ráfagas (instancia con créditos).
# Ejecuta la misma imagen OCI que los nodos del campus y del Modo L, fijada por digest (F6).
resource "aws_instance" "shield" {
  ami                    = var.ami_id
  instance_type          = local.tipo["EC2-SHIELD"]
  subnet_id              = var.subredes[var.instancias["EC2-SHIELD"].subred]
  private_ip             = var.instancias["EC2-SHIELD"].ip
  vpc_security_group_ids = [var.grupos_de_seguridad[var.instancias["EC2-SHIELD"].grupo_de_seguridad]]
  iam_instance_profile   = var.perfiles_de_instancia["EC2-SHIELD"]

  user_data = templatefile("${path.module}/templates/shield.sh.tftpl", {
    ip           = var.instancias["EC2-SHIELD"].ip
    puerto_f9    = var.shield.puerto_f9
    puerto_admin = var.shield.puerto_admin
    clientes     = join(", ", [for c in var.shield.clientes_permitidos : "\"${c}\""])
    imagen       = var.imagen_celeris_node
  })
  user_data_replace_on_change = true

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.instancias["EC2-SHIELD"].disco_gb
    encrypted   = true
  }

  tags = merge(var.etiquetas, { Name = "EC2-SHIELD" })
}

# EC2-CTRLR: réplica en espera de PostgreSQL y de la API del plano de control. El plano de control es R2 (REQ-F-16 y REQ-F-17
# pendientes): la instancia se crea para la conectividad y la medición de F16, sin software de aplicación.
resource "aws_instance" "ctrlr" {
  ami                    = var.ami_id
  instance_type          = local.tipo["EC2-CTRLR"]
  subnet_id              = var.subredes[var.instancias["EC2-CTRLR"].subred]
  private_ip             = var.instancias["EC2-CTRLR"].ip
  vpc_security_group_ids = [var.grupos_de_seguridad[var.instancias["EC2-CTRLR"].grupo_de_seguridad]]
  iam_instance_profile   = var.perfiles_de_instancia["EC2-CTRLR"]

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.instancias["EC2-CTRLR"].disco_gb
    encrypted   = true
  }

  tags = merge(var.etiquetas, { Name = "EC2-CTRLR" })
}
