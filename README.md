# CloudPilot AI GKE Terraform Module

Terraform module for deploying [CloudPilot AI](https://cloudpilot.ai/) on Google Kubernetes Engine clusters. This module wraps the `cloudpilotai_gke_cluster` and shared `cloudpilotai_workload_autoscaler` provider resources behind a simpler GKE-focused interface.

## Features

- Register a GKE cluster with CloudPilot AI and manage cluster-level settings
- Manage scheduled rebalance policies without taking over policies when the input is null
- Install and manage the GKE node autoscaler directly through the cluster resource
- Reuse `nodeclass_templates` and `nodepool_templates` at the module layer, following the same pattern as the EKS module
- Optionally deploy the shared Workload Autoscaler with recommendation and autoscaling policies
- Reuse the provider's typed `GCENodeClass` and `GCENodePool` inputs directly
- Configure automatic Local SSD counts, dynamic boot disk sizing, disruption cooldowns, and Job NodePool optimization
- Manage per-workload rebalancing, Spot placement, and minimum non-Spot replicas
- Configure JVM Xms and Xmx heap bounds through the shared Workload Autoscaler inputs

## Requirements

- Terraform >= 1.0
- `gcloud` CLI configured for the target GKE cluster
- `kubectl` available for cluster-side install flows
- A CloudPilot AI API key
- `cloudpilot-ai/cloudpilotai` provider >= 0.7.0 (planned release)

## Server v1.36.4 Provider Compatibility

This module targets the configuration supported by server v1.36.4 and the provider changes in [PR #44](https://github.com/cloudpilot-ai/terraform-provider-cloudpilotai/pull/44). This prepares module v0.3.0 for provider v0.7.0. Both versions are pending release; use this local module checkout and a provider build containing that PR for prerelease testing. The new `workloads` resource argument requires that provider build even when the module input is null.

| Module input | Supported settings |
| --- | --- |
| `cluster_setting` | `disruption_cooldown` plus the existing cluster settings |
| `nodeclasses`, `nodeclass_templates` | `ephemeral_storage_local_ssd.auto_count` or `count`; boot `disks[].size_policy` with `per_vcpu_gib` and `max_size_gib` |
| `nodepools`, `nodepool_templates` | `disruption_cooldown`; `job_nodepool_optimization.min_active_nodes` and `provisioning_delay` |
| `workloads` | `name`, `type`, `namespace`, `rebalance_able`, `spot_friendly`, `min_non_spot_replicas` |
| `recommendation_policies` | `jvm_min_heap_xms`, `jvm_max_heap_xms`, `jvm_min_heap_xmx`, `jvm_max_heap_xmx` plus the existing recommendation fields |
| `autoscaling_policies` | `startup_boost_recommendation_policy_name` for an independent startup policy; `startup_boost_update_resources` for CPU and/or memory |
| `enable_proactive`, `disable_proactive` | `startup_boost_enabled` filters alongside the existing workload filters |

Maintenance mode, Saving Report baseline fields, `memory_request_multiplier`, and `zero_memory_request_mib` are outside this module's server v1.36.4 configuration contract.

Set an optional passthrough input to `null` to leave its server value unmanaged. Existing public input defaults remain unchanged, so pass `null` explicitly when a default would otherwise manage a setting. Explicit null values on a NodeClass or NodePool override values from its module template; omitted keys still inherit from the template. In a non-empty policy, null child fields preserve their server values. `false` and zero remain explicit values where valid.

Explicit empty values request a reset: `job_nodepool_optimization = {}` removes the Job policy, `disks[].size_policy = {}` removes dynamic disk sizing, and `ephemeral_storage_local_ssd = {}` clears its explicit sizing mode. An object whose optional children are all null is treated as an empty object. A pool's `disruption_cooldown = ""` removes its override; `"0s"` explicitly disables the extra delay. A new non-empty disk policy needs a valid `max_size_gib`. Required fields and values rejected by the server cannot be cleared with an invalid empty value.

For `nodeclasses`, `nodepools`, recommendation policies, and autoscaling policies, `[]` removes only objects previously managed by the provider. For `workloads`, `[]` stops managing workloads without resetting previously applied settings. Proactive filters are operations rather than persistent policy lists.

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
