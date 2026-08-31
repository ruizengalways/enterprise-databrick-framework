# Terraform Boundary

Terraform is reserved for stable platform/admin infrastructure such as workspaces, Unity Catalog metastores/catalogs/base schemas, workspace-catalog bindings, service principals/groups, storage credentials, external locations and related grants.

Lakeflow Jobs/Pipelines belong to Declarative Automation Bundles, not Terraform.

Cloud-specific modules are intentionally deferred until the deployment cloud (Azure/AWS/GCP) is selected. Do not fake portability with empty provider modules.
