variable "environment" {
  description = "Logical environment name, for example dev, ci, uat, or prod."
  type        = string

  validation {
    condition     = contains(["dev", "ci", "uat", "prod"], var.environment)
    error_message = "environment must be one of dev, ci, uat, prod"
  }
}

variable "catalog_name" {
  description = "Unity Catalog catalog name for the environment."
  type        = string
}

variable "catalog_owner" {
  description = "Stable group or service principal that owns the catalog. Prefer a platform-admin group over a human user."
  type        = string
}

variable "runtime_principal" {
  description = "Service-principal application ID used by production workloads."
  type        = string
}

variable "schemas" {
  description = "Long-lived schemas owned by platform IaC. Workload-specific schemas can be added by explicit ADR."
  type        = set(string)
  default = [
    "bronze",
    "silver",
    "gold",
    "reference",
    "quarantine",
    "platform_control",
  ]
}

variable "runtime_schema_privileges" {
  description = "Least-privilege capabilities required by framework jobs/pipelines inside managed schemas."
  type        = set(string)
  default = [
    "USE_SCHEMA",
    "CREATE_TABLE",
    "CREATE_VIEW",
    "CREATE_MATERIALIZED_VIEW",
    "SELECT",
    "MODIFY",
  ]
}

variable "storage_root" {
  description = "Optional managed storage root. Leave null to inherit the metastore managed location."
  type        = string
  default     = null
}
