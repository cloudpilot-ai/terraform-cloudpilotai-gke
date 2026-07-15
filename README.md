# CloudPilot AI GKE Terraform Module

Terraform module for deploying [CloudPilot AI](https://cloudpilot.ai/) on Google Kubernetes Engine clusters. This module wraps the `cloudpilotai_gke_cluster` and shared `cloudpilotai_workload_autoscaler` provider resources behind a simpler GKE-focused interface.

## Features

- Register a GKE cluster with CloudPilot AI and manage cluster-level settings
- Install and manage the GKE node autoscaler directly through the cluster resource
- Reuse `nodeclass_templates` and `nodepool_templates` at the module layer, following the same pattern as the EKS module
- Optionally deploy the shared Workload Autoscaler with recommendation and autoscaling policies
- Reuse the provider's typed `GCENodeClass` and `GCENodePool` inputs directly

## Requirements

- Terraform >= 1.0
- `gcloud` CLI configured for the target GKE cluster
- `kubectl` available for cluster-side install flows
- A CloudPilot AI API key
- `cloudpilot-ai/cloudpilotai` provider >= 0.5.1

## Usage

```hcl
provider "cloudpilotai" {
  api_key = var.cloudpilotai_api_key
}

module "cloudpilotai_gke" {
  source = "cloudpilot-ai/gke/cloudpilotai"

  cluster_name = "my-gke-cluster"
  region       = "us-central1"

  only_install_agent = false
  enable_rebalance       = true

  nodeclass_templates = [
    {
      template_name            = "default"
      enable_image_accelerator = false
    }
  ]

  nodeclasses = [
    {
      name          = "cloudpilot"
      template_name = "default"
    }
  ]

  nodepool_templates = [
    {
      template_name   = "default"
      capacity_type   = ["spot", "on-demand"]
      instance_arch   = ["amd64"]
      instance_family = ["n4", "n2", "e2"]
    }
  ]

  nodepools = [
    {
      name          = "cloudpilot-general"
      template_name = "default"
      enable        = true
      nodeclass     = "cloudpilot"
    }
  ]
}
```

For fresh GKE installs, the module can usually stay at `cluster_name + region` plus your API key as long as your local `gcloud` credential is already pointed at the correct project and the generated kubeconfig can read the cluster. `project_id` and `cluster_uid` remain available as explicit overrides when local discovery is not enough.

The module always creates `cloudpilotai_gke_cluster`. Set `only_install_agent = true` if you only want agent + cluster-setting management. If you still have older configs that used `enable_node_autoscaler = false`, the module keeps that flag as a compatibility alias and maps it to `only_install_agent = true`. The Workload Autoscaler remains the shared provider resource and can be toggled with `enable_workload_autoscaler`.

Template support is intentionally implemented only in this module layer. The provider itself accepts final `nodeclasses` and `nodepools`, while the module adds `nodeclass_templates`, `nodepool_templates`, and `template_name` merge behavior so GKE stays aligned with the EKS module pattern.

For destroy behavior, the GKE cluster resource now follows the same high-level pattern as the EKS provider path: it does not enter an interactive restore flow by default. If you want Terraform destroy to restore regular GKE node pools before removing the CloudPilot components, set either `restore_node_number` for a uniform size or `restore_desired_sizes` for per-pool overrides. Set `skip_restore = true` to use the same top-level switch as the EKS module. The older `node_autoscaler_*` restore inputs remain available as compatibility aliases.

If the cluster is already registered with CloudPilot AI, you can also pass an existing `cluster_id` to keep the module aligned with the current CloudPilot identity during import/migration flows. In that path, `project_id` and `cluster_uid` can usually stay unset at first; the provider will try to auto-discover the missing GKE access metadata for import-driven kubeconfig generation as long as your local `gcloud` access is already valid.

For GKE, `cluster_uid` should be the Kubernetes cluster UID exposed by the `kube-system` namespace:

```bash
kubectl get ns kube-system -o jsonpath='{.metadata.uid}'
```

## Example

- [examples/complete](examples/complete/) - Full GKE example with node autoscaler, Workload Autoscaler, and restore-aware destroy settings
- [examples/minimal](examples/minimal/) - Cluster registration, node autoscaler, and shared Workload Autoscaler
- [examples/import-existing](examples/import-existing/) - Discovery-first migration of an already-registered GKE cluster into this module

## Outputs

- `cluster_id`
- `kubeconfig`
- `node_autoscaler_enabled`
- `workload_autoscaler_enabled`

## Upgrading from provider-generated kubeconfig state

Provider versions before 0.5.1 could store a generated path from the local Terraform or Terragrunt working directory. After upgrading the provider and this module, run a fresh plan instead of reusing an older saved plan. When `kubeconfig` is omitted, the plan removes the old path from state in place; no state edit, import, or resource replacement is required. The cluster and Workload Autoscaler resources generate their own kubeconfigs in each execution environment.

Keep `enable_workload_autoscaler = true` for this upgrade apply before disabling it or destroying legacy Workload Autoscaler state. Terraform does not pass module configuration to the provider when deleting an old resource directly, so this apply records the discovered project/location access fields and removes the stale path first.
