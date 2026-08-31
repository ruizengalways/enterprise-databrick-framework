variable "display_name" {
  description = "Display name of the Databricks-managed automation service principal."
  type        = string
}

variable "github_owner" {
  type = string
}

variable "github_repository" {
  type = string
}

variable "github_environment" {
  description = "GitHub Environment name encoded into the OIDC subject, for example dev, ci, uat, prod."
  type        = string
}

variable "databricks_account_id" {
  description = "Databricks account ID used as the recommended OIDC audience."
  type        = string
}

variable "policy_id" {
  description = "Stable federation policy ID."
  type        = string
  default     = "github-actions"
}
