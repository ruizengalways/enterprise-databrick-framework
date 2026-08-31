variable "workspace_id" {
  description = "Databricks workspace ID allowed to access the isolated securable."
  type        = number
}

variable "securable_name" {
  description = "Name of the isolated catalog/external-location/storage-credential to bind."
  type        = string
}

variable "securable_type" {
  description = "Unity Catalog securable type."
  type        = string
  default     = "catalog"

  validation {
    condition     = contains(["catalog", "external_location", "storage_credential", "credential"], var.securable_type)
    error_message = "unsupported securable_type"
  }
}

variable "binding_type" {
  description = "Read/write or read-only binding."
  type        = string
  default     = "BINDING_TYPE_READ_WRITE"

  validation {
    condition     = contains(["BINDING_TYPE_READ_ONLY", "BINDING_TYPE_READ_WRITE"], var.binding_type)
    error_message = "binding_type must be READ_ONLY or READ_WRITE"
  }
}
