output "catalog_name" {
  description = "Created Unity Catalog catalog name."
  value       = databricks_catalog.environment.name
}

output "schema_names" {
  description = "Long-lived platform schemas created by this module."
  value       = sort([for schema in databricks_schema.base : schema.name])
}

output "isolation_mode" {
  value = databricks_catalog.environment.isolation_mode
}
