# Parámetros del entorno de demostración. El diseño llega de diseno.auto.tfvars.json (generado por `python infra/genera.py tofu`
# desde infra/inventory.yaml; no se edita a mano). Aquí solo van las decisiones de despliegue.

variable "emulador" {
  description = "true (por defecto): el proveedor apunta al AWS Emulator local con credenciales ficticias. Reemplaza la propagación de rutas del VGW, que el emulador no implementa, por una ruta estática hacia el campus. false: AWS real (no probado)."
  type        = bool
  default     = true
}

variable "endpoint_emulador" {
  description = "URL del AWS Emulator (HTTPS, certificado autofirmado nuevo en cada arranque)."
  type        = string
  default     = "https://127.0.0.1:9297"
}

variable "ca_emulador" {
  description = "Ruta del ca.pem que el AWS Emulator genera al arrancar (~/.aws/emulator/9297/ca.pem)."
  type        = string
  default     = null
}

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
  description = "Perfil de instancia ya creado (AWS Academy: LabInstanceProfile). Si es null, se crea un rol con SSM para EC2-GW."
  type        = string
  default     = null
}

variable "ami_id" {
  description = "AMI x86_64 de EC2-GW. Si es null: con el emulador, una imagen de Amazon Linux 2023 que el propio emulador registra (no ejecuta instancias); con AWS real, la Debian 13 oficial por su parámetro público de SSM."
  type        = string
  default     = null
}

variable "crear_credencial_respaldo" {
  description = "Crea el usuario IAM de solo escritura del respaldo [S-30]. En AWS Academy puede no estar disponible."
  type        = bool
  default     = true
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
  description = "Subredes de D2.5 (pub-a y app-a)."
  type        = any
}

variable "tablas_de_rutas" {
  description = "Tablas de rutas de D2.5."
  type        = any
}

variable "security_groups" {
  description = "Security Groups de D2.5 (sg-gw)."
  type        = any
}

variable "nacls" {
  description = "NACL de D2.5."
  type        = any
}

variable "instancias" {
  description = "EC2-GW."
  type        = any
}

variable "vpn" {
  description = "Parámetros de D1.10."
  type        = any
}

variable "respaldo" {
  description = "Bucket de respaldos (D2.5, F18)."
  type        = any
}
