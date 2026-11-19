terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Todo recurso lleva Proyecto y Ttl (Parte F5.2): el Ttl permite barrer lo que quede olvidado tras la demostración.
provider "aws" {
  region = var.region

  default_tags {
    tags = local.etiquetas
  }
}
