# Módulo onprem-sim (Parte F5.1): la VPC 10.20.0.0/16 que simula el campus, con cgw-sim (strongSwan + FRR, IP elástica = customer gateway)
# y labcli-sim (10.20.32.50). EMULADO: no es OPNsense ni el campus; la VPN del otro lado sí es el VGW real (Modo A).

variable "nombre" {
  description = "Nombre de la VPC (onprem-sim)."
  type        = string
}

variable "onprem" {
  description = "Direccionamiento del campus simulado (del inventario)."
  type = object({
    vpc_cidr        = string
    subred_wan_cidr = string
    subred_lab_cidr = string
    cgw_tipo        = string
    labcli_ip       = string
    labcli_tipo     = string
    campus_resumen  = string
  })
}

variable "region" {
  description = "Región de AWS; cgw-sim y labcli-sim van en la zona <region>a."
  type        = string
}

variable "vpn" {
  description = "Parámetros de D1.10 para cgw-sim (strongSwan y BGP), del inventario."
  type = object({
    asn_aws     = number
    asn_cliente = number
    redes       = object({ campus = string, aws = string })
    tuneles = list(object({
      nombre      = string
      inside_cidr = string
      ip_aws      = string
      ip_cliente  = string
      rol         = string
      prepend     = bool
      clave_vti   = number
    }))
    strongswan = object({
      ike                   = string
      esp                   = string
      dpd_s                 = number
      dpd_accion            = string
      reautenticacion_ike_s = number
      vida_child_s          = number
    })
    bgp = object({ keepalive_s = number, hold_s = number })
    mtu = number
    mss = number
  })
}

variable "frr_conf" {
  description = "frr.conf de cgw-sim, generado desde la sección vpn del inventario (el mismo del Modo L)."
  type        = string
}

variable "tuneles_aws" {
  description = "IP pública de AWS y llave precompartida de cada túnel (salidas del módulo aws-vpn)."
  type = list(object({
    ip_aws         = string
    clave_asignada = string
  }))
  sensitive = true
}

variable "ips_aws_de_los_tuneles" {
  description = "IP públicas de AWS de los túneles: las únicas que pueden hablar IKE/ESP con cgw-sim."
  type        = list(string)
}

variable "ami_id" {
  description = "AMI de las instancias (x86_64)."
  type        = string
}

variable "perfil_de_instancia_existente" {
  description = "Perfil de instancia ya creado (AWS Academy). Si es null, el módulo crea un rol con SSM por instancia."
  type        = string
  default     = null
}

variable "etiquetas" {
  description = "Etiquetas de todos los recursos."
  type        = map(string)
}
