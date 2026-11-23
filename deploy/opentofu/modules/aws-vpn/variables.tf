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
  description = "IP pública del extremo del campus: la del FortiGate [S-15, S-29]."
  type        = string
}

variable "emulador" {
  description = "true: AWS Emulator, que no implementa la propagación de rutas del VGW; se usa una ruta estática hacia el campus."
  type        = bool
  default     = false
}

variable "rutas_al_campus" {
  description = "Rutas hacia el campus del diseño (tabla y destino) que la propagación de BGP traería en AWS real."
  type        = list(object({ tabla = string, destino = string }))
  default     = []
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
