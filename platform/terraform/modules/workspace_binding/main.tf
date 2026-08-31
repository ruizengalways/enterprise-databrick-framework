resource "databricks_workspace_binding" "this" {
  securable_name = var.securable_name
  securable_type = var.securable_type
  workspace_id   = var.workspace_id
  binding_type   = var.binding_type
}
