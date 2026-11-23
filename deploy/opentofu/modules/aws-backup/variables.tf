# Módulo aws-backup: bucket de respaldos con versionado y Object Lock (D2.5, F18, OD-07).

variable "respaldo" {
  description = "Parámetros del inventario (aws.s3 y la IP pública del campus)."
  type = object({
    bucket     = string
    versionado = bool
    object_lock = object({
      dias = number
      modo = string
    })
    ip_campus = string
    usuario   = string
  })

  validation {
    condition     = contains(["compliance", "governance"], var.respaldo.object_lock.modo)
    error_message = "El modo de Object Lock es compliance o governance."
  }
}

variable "crear_credencial" {
  description = "Crea el usuario IAM de solo escritura (s3:PutObject desde la IP del campus). En AWS Academy puede no estar disponible [S-30]."
  type        = bool
  default     = true
}

variable "etiquetas" {
  description = "Etiquetas de todos los recursos."
  type        = map(string)
}
