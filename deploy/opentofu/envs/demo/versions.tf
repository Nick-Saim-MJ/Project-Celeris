terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS EMULADO: PLANO DE CONTROL, SIN TRÁFICO. Con var.emulador = true (valor por defecto) el proveedor apunta al AWS Emulator local
# (https://github.com/aws/aws-emulator, en Docker), con credenciales ficticias y sin validar la cuenta: no toca ninguna cuenta real.
# Con var.emulador = false usaría las credenciales del entorno contra AWS real; ese camino no se ha probado (CI-53).
# Todo recurso lleva Proyecto y Ttl (Parte F5.2): el Ttl permite barrer lo que quede olvidado tras la demostración.
provider "aws" {
  region = var.region

  access_key                  = var.emulador ? "ficticia" : null
  secret_key                  = var.emulador ? "ficticia" : null
  skip_credentials_validation = var.emulador
  skip_requesting_account_id  = var.emulador
  skip_metadata_api_check     = var.emulador
  skip_region_validation      = var.emulador
  s3_use_path_style           = var.emulador
  custom_ca_bundle            = var.emulador ? var.ca_emulador : null

  dynamic "endpoints" {
    for_each = var.emulador ? [var.endpoint_emulador] : []
    content {
      ec2 = endpoints.value
      iam = endpoints.value
      s3  = endpoints.value
      sts = endpoints.value
      ssm = endpoints.value
    }
  }

  default_tags {
    tags = local.etiquetas
  }
}
