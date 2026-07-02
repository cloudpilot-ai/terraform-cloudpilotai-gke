# Import Existing GKE Cluster Example

This example migrates a GKE cluster that is **already registered with CloudPilot AI** into the `cloudpilot-ai/gke/cloudpilotai` module in two phases:

1. Use Terraform `import` blocks plus `terraform plan -generate-config-out=generated.tf` to discover the current provider resource configuration.
2. Use the bundled migration script to convert `generated.tf` into a module-based `main.tf`, then import the existing resources directly into `module.cloudpilotai_gke.*`.

This follows the same discovery-first shape as the EKS `import-existing` example. For GKE, the provider now tries to match the AWS experience during import-driven flows: if your local `gcloud` access is already valid, it can often infer the missing project access metadata from the registered GKE NodeClass configuration and auto-generate kubeconfig for later delete or upgrade paths. The generated module config therefore preserves the discovered `cluster_name` and `region`, keeps `cluster_id` wired through a variable, and leaves `project_id`, `cluster_uid`, `cluster_location`, and `kubeconfig` as optional manual follow-up only when auto-discovery is not enough.

The conversion script is intentionally scoped to the exact `generated.tf` format emitted by Terraform. It is **not** a generic HCL refactoring tool. Run it against a fresh `generated.tf` before manual edits; if you hand-edit the provider resource file first, regenerate it instead of expecting the script to understand arbitrary HCL.

## GitHub Links

- Example directory: https://github.com/cloudpilot-ai/terraform-cloudpilotai-gke/tree/main/examples/import-existing
- Bootstrap import file: https://github.com/cloudpilot-ai/terraform-cloudpilotai-gke/blob/main/examples/import-existing/bootstrap_import.tf
- Migration script: https://github.com/cloudpilot-ai/terraform-cloudpilotai-gke/blob/main/examples/import-existing/scripts/generated_to_module.py

## What This Example Does

- Uses `terraform plan -generate-config-out=generated.tf` to discover:
  - `cloudpilotai_gke_cluster`
  - optionally `cloudpilotai_workload_autoscaler`
- Converts the generated provider resources into a `module "cloudpilotai_gke"` block automatically
- Writes a helper import script so you can import the real resources into:
  - `module.cloudpilotai_gke.cloudpilotai_gke_cluster.this`
  - `module.cloudpilotai_gke.cloudpilotai_workload_autoscaler.this[0]`

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [Python 3](https://www.python.org/downloads/) for the migration script
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) configured for the target GKE cluster
- [kubectl](https://kubernetes.io/docs/tasks/tools/) for cluster operations
- A CloudPilot AI API key -- see [Getting API Keys](https://docs.cloudpilot.ai/guide/getting_started/get_apikeys)
- The target cluster must already be connected to CloudPilot AI

## Files in This Example

- [main.tf](main.tf): provider setup shared by both phases
- [bootstrap_import.tf](bootstrap_import.tf): temporary import blocks used only to generate `generated.tf`
- [variables.tf](variables.tf): inputs for the bootstrap step and the final module config
- [scripts/generated_to_module.py](scripts/generated_to_module.py): converts `generated.tf` into a module block and helper import script

## Step 1: Create `terraform.tfvars`

Start from the example file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Fill in:

- `cloudpilot_api_key`
- `cluster_id`

Important:

- `cluster_id` is used by the bootstrap import blocks and later by the helper import script
- keep your local `gcloud` auth ready for this cluster if you want the provider to auto-generate kubeconfig later, similar to the AWS import flow using local profile and assume-role setup
- if you later need to add `cluster_uid` manually, use the Kubernetes cluster UID from the `kube-system` namespace:

```bash
kubectl get ns kube-system -o jsonpath='{.metadata.uid}'
```

## Step 2: Initialize Terraform

```bash
terraform init
```

## Step 3: Generate `generated.tf`

Run:

```bash
terraform plan -generate-config-out=generated.tf
```

This reads the existing CloudPilot AI configuration from the API and writes provider resource blocks into `generated.tf`.

If the cluster does **not** have the Workload Autoscaler installed:

- comment out the `cloudpilotai_workload_autoscaler` import block in [bootstrap_import.tf](bootstrap_import.tf)
- rerun the command

## Step 4: Review the Generated Provider Config

Open `generated.tf` and check that it contains the resources you expect:

- `resource "cloudpilotai_gke_cluster" "imported"`
- optionally `resource "cloudpilotai_workload_autoscaler" "imported"`

This file is still in the raw provider resource format. Do **not** keep it as your final module configuration.

## Step 5: Convert `generated.tf` Into Module Configuration

Run the migration script:

```bash
python3 scripts/generated_to_module.py --input generated.tf
```

By default it writes:

- `module.generated.tf`
- `import-module.sh`

What the script does:

- converts the discovered provider resource config into `module "cloudpilotai_gke" { source = "cloudpilot-ai/gke/cloudpilotai" ... }`
- preserves `cloudpilotai_gke_cluster.cluster_setting`
- keeps the GKE node autoscaler settings on the same cluster module call, including:
  - `only_install_agent`
  - `enable_rebalance`
  - `skip_restore`
  - `restore_node_number`
  - `restore_desired_sizes`
  - `nodeclasses`
  - `nodepools`
- leaves `nodeclass_templates` and `nodepool_templates` available for later manual refactoring if you want to deduplicate the generated `nodeclasses` / `nodepools` after the import is stable
- maps Workload Autoscaler settings into module inputs like:
  - `wa_storage_class`
  - `wa_enable_node_agent`
- wires `cluster_id` through `var.cluster_id`
- preserves the discovered `cluster_name` and `region` directly from `generated.tf`
- leaves `project_id`, `cluster_uid`, `cluster_location`, and `kubeconfig` as optional commented follow-up inputs instead of forcing them for the initial import
- relies on provider-side GKE auto-discovery for later kubeconfig generation when the cluster already exposes enough node networking metadata

If you are testing the local checkout of this module instead of the published module, override the source explicitly:

```bash
python3 scripts/generated_to_module.py --input generated.tf --module-source ../..
```

## Step 6: Switch the Example From Bootstrap Mode to Module Mode

Delete the discovery files:

```bash
rm -f bootstrap_import.tf generated.tf
```

Then rename the generated module config:

```bash
mv module.generated.tf main.module.tf
```

At this point the Terraform configuration should contain:

- provider setup in `main.tf`
- variables in `variables.tf`
- the module call in `main.module.tf`

It should **not** contain the bootstrap import blocks or the raw provider resources anymore.

Before moving on, explicitly verify:

- `cluster_name`
- `region`
- whether you want to keep relying on provider-side GKE auto-discovery or add `project_id`, `cluster_uid`, `cluster_location`, and `kubeconfig` explicitly now

## Step 7: Import the Existing Resources Into the Module Addresses

Run the helper script generated in Step 5:

```bash
./import-module.sh
```

It imports into:

- `module.cloudpilotai_gke.cloudpilotai_gke_cluster.this`
- `module.cloudpilotai_gke.cloudpilotai_workload_autoscaler.this[0]` when Workload Autoscaler exists

## Step 8: Verify the Migration

Run:

```bash
terraform plan
```

Expected result:

- You may see a small number of operational-only updates on the first module plan, such as:
  - optional local execution fields you chose to add manually later, such as `project_id`, `cluster_uid`, `kubeconfig`, or `cluster_location`
  - a first-time local kubeconfig backfill for imported GKE resources when the provider can auto-discover it from existing cluster metadata
- You should **not** see unexpected creates, deletes, or typed nodeclass/nodepool rewrites

If Terraform still shows drift:

- If the drift is only the operational fields listed above, review it and apply once to normalize state for future runs.
- If the drift includes nodeclasses, nodepools, Workload Autoscaler policies, or other large rewrites, stop and compare `main.module.tf` with the original `generated.tf` before applying.

## Notes

- This example uses `generated.tf` only as a discovery artifact
- The actual Terraform state import happens **after** the module configuration exists
- GKE import still has some limits compared with EKS: fresh create flows still need explicit `project_id`, and imported flows can only auto-discover kubeconfig when CloudPilot already has enough GKE node networking metadata to infer the project

## Next Steps

- If you want a lighter setup instead of a full migration, see the [minimal](../minimal/) example
