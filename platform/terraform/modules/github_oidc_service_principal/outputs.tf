output "service_principal_id" {
  value = databricks_service_principal.automation.id
}

output "application_id" {
  description = "Use as DATABRICKS_CLIENT_ID and Bundle run_as.service_principal_name."
  value       = databricks_service_principal.automation.application_id
}

output "oidc_subject" {
  value = "repo:${var.github_owner}/${var.github_repository}:environment:${var.github_environment}"
}
