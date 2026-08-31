resource "databricks_service_principal" "automation" {
  display_name = var.display_name
}

resource "databricks_service_principal_federation_policy" "github" {
  service_principal_id = tonumber(databricks_service_principal.automation.id)
  policy_id            = var.policy_id
  description          = "GitHub Actions OIDC for ${var.github_owner}/${var.github_repository} environment ${var.github_environment}"

  oidc_policy = {
    issuer        = "https://token.actions.githubusercontent.com"
    audiences     = [var.databricks_account_id]
    subject_claim = "sub"
    subject       = "repo:${var.github_owner}/${var.github_repository}:environment:${var.github_environment}"
  }
}
