# Módulo aws-gw: EC2-GW, el proxy inverso del panel remoto (D2.5, F29/F30). Sin datos ni llaves de firma.

variable "instancia" {
  description = "EC2-GW del inventario (ip, subred, tipos, disco, grupo de seguridad)."
  type = object({
    ip                 = string
    subred             = string
    tipo_produccion    = string
    tipo_laboratorio   = string
    disco_gb           = number
    grupo_de_seguridad = string
  })
}

variable "nombre" {
  description = "Prefijo de los nombres."
  type        = string
}

variable "subredes" {
  description = "ID de cada subred por nombre."
  type        = map(string)
}

variable "zonas_de_disponibilidad" {
  description = "Zona de disponibilidad de cada subred por nombre."
  type        = map(string)
}

variable "grupos_de_seguridad" {
  description = "ID de cada Security Group por nombre."
  type        = map(string)
}

variable "modo_laboratorio" {
  description = "true usa el tipo de instancia del laboratorio."
  type        = bool
}

variable "ami_id" {
  description = "AMI x86_64."
  type        = string
}

variable "perfil_de_instancia_existente" {
  description = "Perfil ya creado (AWS Academy). Si es null se crea un rol con Session Manager y sin permisos sobre S3 (D2.5)."
  type        = string
  default     = null
}

variable "etiquetas" {
  description = "Etiquetas de todos los recursos."
  type        = map(string)
}
