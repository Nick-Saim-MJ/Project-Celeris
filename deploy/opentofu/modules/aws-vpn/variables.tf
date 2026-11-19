# Módulo aws-vpn: el extremo AWS de la VPN híbrida (D1.10): VGW, customer gateway y conexión IPsec con BGP.

variable "nombre" {
  description = "Prefijo de los nombres."
  type        = string
}

variable "vpc_id" {
  description = "VPC a la que se adjunta el VGW."
  type        = string
}

variable "tablas_de_rutas" {
  description = "Tablas de rutas (id por nombre) donde el VGW propaga las rutas aprendidas por BGP."
  type        = map(string)
}

variable "ip_publica_cliente" {
  description = "IP pública del extremo del campus (en el Modo A, la IP elástica de cgw-sim; en producción, la del firewall perimetral [S-15])."
  type        = string
}

variable "vpn" {
  description = "Parámetros de D1.10 generados desde el inventario."
  type = object({
    asn_aws     = number
    asn_cliente = number
    tuneles = list(object({
      nombre      = string
      inside_cidr = string
    }))
    opciones_aws = object({
      ike_versions                 = list(string)
      phase1_encryption_algorithms = list(string)
      phase1_integrity_algorithms  = list(string)
      phase1_dh_group_numbers      = list(number)
      phase1_lifetime_seconds      = number
      phase2_encryption_algorithms = list(string)
      phase2_dh_group_numbers      = list(number)
      phase2_lifetime_seconds      = number
      dpd_timeout_seconds          = number
      dpd_timeout_action           = string
      startup_action               = string
    })
  })

  validation {
    condition     = length(var.vpn.tuneles) == 2
    error_message = "D1.10 define dos túneles (activo y respaldo)."
  }
}

variable "etiquetas" {
  description = "Etiquetas de todos los recursos."
  type        = map(string)
}
