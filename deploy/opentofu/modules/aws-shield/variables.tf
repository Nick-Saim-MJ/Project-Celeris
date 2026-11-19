# Módulo aws-shield: las instancias de aplicación de la VPC (D2.5, 6.3): EC2-SHIELD (caché de segundo nivel) y EC2-CTRLR (réplica del plano de control).

variable "instancias" {
  description = "EC2-SHIELD y EC2-CTRLR: IP, subred, tipos, disco y Security Group (del inventario)."
  type = map(object({
    ip                 = string
    subred             = string
    tipo_produccion    = string
    tipo_laboratorio   = string
    disco_gb           = number
    grupo_de_seguridad = string
  }))

  validation {
    condition     = contains(keys(var.instancias), "EC2-SHIELD") && contains(keys(var.instancias), "EC2-CTRLR")
    error_message = "Se esperan las instancias EC2-SHIELD y EC2-CTRLR."
  }
}

variable "subredes" {
  description = "ID de cada subred por nombre."
  type        = map(string)
}

variable "grupos_de_seguridad" {
  description = "ID de cada Security Group por nombre."
  type        = map(string)
}

variable "perfiles_de_instancia" {
  description = "Perfil de instancia por componente."
  type        = map(string)
}

variable "modo_laboratorio" {
  description = "true usa los tipos de instancia del laboratorio (D2.5, 6.3); false, los de producción."
  type        = bool
}

variable "ami_id" {
  description = "AMI de las instancias (x86_64)."
  type        = string
}

variable "shield" {
  description = "Puertos y clientes del nodo shield (F9 y F12)."
  type = object({
    puerto_f9           = number
    puerto_admin        = number
    clientes_permitidos = list(string)
  })
}

variable "imagen_celeris_node" {
  description = "Imagen OCI de celeris-node fijada por digest (REQ-NF-15), p. ej. ghcr.io/<dueño>/celeris-node@sha256:…"
  type        = string

  validation {
    condition     = can(regex("@sha256:[0-9a-f]{64}$", var.imagen_celeris_node))
    error_message = "La imagen debe ir fijada por digest (@sha256:…): no se despliega por etiqueta."
  }
}

variable "etiquetas" {
  description = "Etiquetas de todos los recursos."
  type        = map(string)
}
