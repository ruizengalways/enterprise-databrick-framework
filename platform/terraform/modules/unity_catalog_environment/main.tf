resource "databricks_catalog" "environment" {
  name           = var.catalog_name
  comment        = "Enterprise data platform ${var.environment} catalog managed by Terraform"
  owner          = var.catalog_owner
  isolation_mode = "ISOLATED"
  storage_root   = var.storage_root

  properties = {
    environment = var.environment
    managed_by  = "terraform"
    platform    = "enterprise-databricks-framework"
  }
}

resource "databricks_schema" "base" {
  for_each = var.schemas

  catalog_name = databricks_catalog.environment.name
  name         = each.value
  owner        = var.catalog_owner
  comment      = "${var.environment} ${each.value} schema managed by enterprise-databricks-framework"

  properties = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "databricks_grants" "catalog" {
  catalog = databricks_catalog.environment.name

  grant {
    principal  = var.catalog_owner
    privileges = ["ALL_PRIVILEGES"]
  }

  grant {
    principal  = var.runtime_principal
    privileges = ["USE_CATALOG"]
  }
}

resource "databricks_grants" "schema" {
  for_each = databricks_schema.base

  schema = "${databricks_catalog.environment.name}.${each.value.name}"

  grant {
    principal  = var.catalog_owner
    privileges = ["ALL_PRIVILEGES"]
  }

  grant {
    principal  = var.runtime_principal
    privileges = var.runtime_schema_privileges
  }
}
