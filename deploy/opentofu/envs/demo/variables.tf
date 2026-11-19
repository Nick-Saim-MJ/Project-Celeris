# Parámetros del entorno de demostración. El diseño llega de diseno.auto.tfvars.json (generado por `python infra/genera.py tofu`
# desde infra/inventory.yaml; no se edita a mano). Aquí solo van las decisiones de despliegue.

variable "region" {
  description = "Región de AWS del laboratorio (el inventario registra us-east-1 para el laboratorio y sa-east-1 como candidata de producción)."
  type        = string
  default     = "us-east-1"
}

variable "ttl" {
  description = "Valor de la etiqueta Ttl. Si es null se usa el del inventario (aws.etiquetas.Ttl_por_defecto)."
  type        = string
  default     = null
}

variable "modo_laboratorio" {
  description = "true usa los tipos de instancia del laboratorio (D2.5, 6.3); false, los de producción."
  type        = bool
  default     = true
}

variable "perfil_de_instancia_existente" {
  description = "Perfil de instancia ya creado (AWS Academy: LabInstanceProfile). Si es null, se crea un rol con SSM por instancia, lo que AWS Academy no permite."
  type        = string
  default     = null
}

variable "ami_id" {
  description = "AMI x86_64 de todas las instancias. Si es null se resuelve la Debian 13 oficial por su parámetro público de SSM."
  type        = string
  default     = null
}

variable "imagen_celeris_node" {
  description = "Imagen OCI de celeris-node fijada por digest (REQ-NF-15), p. ej. ghcr.io/<dueño>/celeris-node@sha256:…; la publica el flujo .github/workflows/imagen.yml."
  type        = string
}

variable "presupuesto_usd" {
  description = "Tope mensual en USD del presupuesto de AWS Budgets (RE-07). Si es null no se crea el presupuesto; el valor no está en el inventario [S-xx pendiente]."
  type        = number
  default     = null
}

variable "correo_alarma" {
  description = "Correo que recibe la alarma del presupuesto. Obligatorio si presupuesto_usd no es null."
  type        = string
  default     = null
}

# Variables generadas (diseno.auto.tfvars.json). Se tipan en los módulos que las consumen.

variable "_generado" {
  description = "Marca del archivo generado."
  type        = string
  default     = ""
}

variable "region_por_defecto" {
  description = "Región de laboratorio del inventario; una prueba la compara con el valor por defecto de var.region."
  type        = string
}

variable "etiquetas_base" {
  description = "Etiquetas fijas del inventario (Proyecto)."
  type        = map(string)
}

variable "ttl_por_defecto" {
  description = "Ttl del inventario."
  type        = string
}

variable "vpc" {
  description = "VPC del diseño."
  type        = any
}

variable "subredes" {
  description = "Subredes de D2.5."
  type        = any
}

variable "tablas_de_rutas" {
  description = "Tablas de rutas de D2.5."
  type        = any
}

variable "security_groups" {
  description = "Security Groups de D2.5."
  type        = any
}

variable "nacls" {
  description = "NACL de D2.5."
  type        = any
}

variable "instancias" {
  description = "EC2-SHIELD, EC2-CTRLR y NAT01."
  type        = any
}

variable "presupuesto_alarma_porcentaje" {
  description = "Porcentaje del presupuesto que dispara la alarma (RE-07)."
  type        = number
}

variable "shield" {
  description = "Puertos y clientes del nodo shield."
  type        = any
}

variable "vpn" {
  description = "Parámetros de D1.10."
  type        = any
}

variable "frr_conf" {
  description = "frr.conf de cgw-sim, el mismo que genera el Modo L."
  type        = string
}

variable "onprem_sim" {
  description = "Campus simulado."
  type        = any
}
