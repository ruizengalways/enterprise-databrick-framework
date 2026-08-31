terraform {
  required_version = ">= 1.7.5, < 2.0.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.128"
    }
  }
}
