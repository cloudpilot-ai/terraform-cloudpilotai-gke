terraform {
  required_version = ">= 1.0"

  required_providers {
    cloudpilotai = {
      source  = "cloudpilot-ai/cloudpilotai"
      version = ">= 0.7.0"
    }
  }
}

provider "cloudpilotai" {
  api_endpoint = var.cloudpilotai_api_endpoint
  api_key      = var.cloudpilotai_api_key
}

module "cloudpilotai_gke" {
  source = "cloudpilot-ai/gke/cloudpilotai"

  cluster_name        = var.cluster_name
  region              = var.region
  project_id          = var.project_id
  cluster_uid         = var.cluster_uid
  cluster_location    = var.cluster_location
  kubeconfig          = var.kubeconfig
  skip_restore        = var.skip_restore
  restore_node_number = var.restore_node_number

  enable_upgrade             = true
  enable_rebalance           = true
  enable_workload_autoscaler = true

  cluster_setting = {
    enable_node_repair  = true
    enable_disk_monitor = true
    discount            = 0.15
    disruption_cooldown = "5m"
  }

  nodeclasses = [
    {
      name                               = "cloudpilot"
      enable_local_ssd_ephemeral_storage = true
      ephemeral_storage_local_ssd = {
        auto_count = true
        count      = null
      }
      image_selector_terms = [{
        family  = "ContainerOptimizedOS"
        channel = "cluster"
      }]
      disks = [{
        boot     = true
        category = "pd-balanced"
        size_gib = 80
        size_policy = {
          per_vcpu_gib = 2
          max_size_gib = 512
        }
      }]
    }
  ]

  nodepools = [
    {
      name                = "cloudpilot-general"
      enable              = true
      nodeclass           = "cloudpilot"
      capacity_type       = ["on-demand"]
      instance_arch       = ["amd64"]
      instance_family     = ["n2"]
      disruption_cooldown = "10m"
      job_nodepool_optimization = {
        min_active_nodes   = 1
        provisioning_delay = "30s"
      }
      labels = {
        codex-example = "complete"
        workload      = "cloudpilot-managed"
      }
    }
  ]

  # Replace this illustrative target with an existing workload in your cluster.
  workloads = [{
    name                  = "example-api"
    type                  = "deployment"
    namespace             = "default"
    rebalance_able        = true
    spot_friendly         = true
    min_non_spot_replicas = 0
  }]

  recommendation_policies = [
    {
      name                  = "balanced"
      strategy_type         = "percentile"
      percentile_cpu        = 95
      percentile_memory     = 99
      history_window_cpu    = "24h"
      history_window_memory = "24h"
      evaluation_period     = "1h"
      jvm_min_heap_xms      = "128Mi"
      jvm_max_heap_xms      = "2Gi"
      jvm_min_heap_xmx      = "256Mi"
      jvm_max_heap_xmx      = "4Gi"
    }
  ]

  autoscaling_policies = [
    {
      name                       = "readonly"
      enable                     = false
      recommendation_policy_name = "balanced"
      priority                   = 0
      on_policy_removal          = "off"
      target_refs = [
        {
          api_version = "apps/v1"
          kind        = "Deployment"
          namespace   = "default"
        }
      ]
    }
  ]
}
