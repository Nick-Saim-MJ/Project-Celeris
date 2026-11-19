# Módulo aws-vpc: la VPC del diseño (D2.5): subredes, tablas de rutas, Security Groups, NACL, instancia NAT y roles de SSM.
# Ningún valor de diseño tiene predeterminado: todo llega de infra/inventory.yaml por diseno.auto.tfvars.json.

variable "nombre" {
  description = "Nombre de la VPC (D2.5: celeris)."
  type        = string
}

variable "region" {
  description = "Región de AWS; las zonas de disponibilidad son <region>a y <region>b."
  type        = string
}

variable "vpc" {
  description = "CIDR de la VPC y bloque reservado para crecer."
  type = object({
    cidr      = string
    reservado = string
  })
}

variable "subredes" {
  description = "Subredes de D2.5 (pub-a, pub-b, app-a, app-b, data-a, data-b)."
  type = list(object({
    id      = string
    cidr    = string
    az      = string
    publica = bool
  }))
}

variable "tablas_de_rutas" {
  description = "Tablas de rutas. Las rutas con salto vgw no se crean aquí: las propaga el VGW por BGP (módulo aws-vpn)."
  type = list(object({
    id       = string
    subredes = list(string)
    rutas = list(object({
      destino = string
      salto   = string
    }))
  }))
}

variable "security_groups" {
  description = "Security Groups de D2.5."
  type = list(object({
    id         = string
    componente = string
    ingress = list(object({
      protocolo   = string
      desde       = number
      hasta       = number
      cidr        = string
      descripcion = string
    }))
    egress = list(object({
      protocolo   = string
      desde       = number
      hasta       = number
      cidr        = string
      descripcion = string
    }))
  }))
}

variable "nacls" {
  description = "NACL de D2.5 (nacl-private y nacl-public)."
  type = list(object({
    id       = string
    subredes = list(string)
    ingress = list(object({
      numero    = number
      accion    = string
      protocolo = string
      desde     = number
      hasta     = number
      cidr      = string
    }))
    egress = list(object({
      numero    = number
      accion    = string
      protocolo = string
      desde     = number
      hasta     = number
      cidr      = string
    }))
  }))
}

variable "nat" {
  description = "Instancia NAT (NAT01): IP, subred, tipo, disco y Security Group."
  type = object({
    ip                 = string
    subred             = string
    tipo               = string
    disco_gb           = number
    grupo_de_seguridad = string
  })
}

variable "ami_id" {
  description = "AMI de las instancias (x86_64)."
  type        = string
}

variable "perfil_de_instancia_existente" {
  description = "Nombre de un perfil de instancia ya creado (AWS Academy: LabInstanceProfile). Si es null, el módulo crea un rol por instancia con SSM."
  type        = string
  default     = null
}

variable "nombres_de_instancia" {
  description = "Instancias de la VPC que necesitan un rol (NAT01, EC2-SHIELD, EC2-CTRLR)."
  type        = list(string)
}

variable "etiquetas" {
  description = "Etiquetas de todos los recursos (Proyecto y Ttl)."
  type        = map(string)
}
